import ast
import re
import logging
from typing import Dict, List
import time

from gui_agents.tools.tools import Tools
from gui_agents.utils.common_utils import parse_single_code_from_string
from gui_agents.store.registry import Registry
from gui_agents.agents.global_state import GlobalState

logger = logging.getLogger("desktopenv.agent")


class ACI:

    def __init__(self):
        self.notes: List[str] = []


def agent_action(func):
    func.is_agent_action = True
    return func


class Grounding(ACI):

    def __init__(
        self,
        Tools_dict: Dict,
        platform: str,
        width: int = 1920,
        height: int = 1080,
    ):
        """
        Initialize a Grounding instance: configure screen dimensions, prepare tool instances, and load global state.
        
        Parameters:
            Tools_dict (Dict): Mapping of tool names to their configuration dictionaries used to register tools.
            platform (str): Target platform identifier (e.g., "windows", "macos") used by the grounding agents.
            width (int): Current screen width in pixels.
            height (int): Current screen height in pixels.
        
        Detailed behavior:
            - Creates and registers two Tools instances ("grounding" and "text_span") using entries from Tools_dict; registration will include any authentication-related parameters present in the tool configuration.
            - Obtains grounding tool dimensions (grounding_width, grounding_height) and falls back to the provided width and height when the grounding tool does not supply them.
            - Initializes coordinate placeholders (coords1, coords2) and stores a reference to the global state store.
        """
        self.platform = platform
        self.Tools_dict = Tools_dict
        self.width = width
        self.height = height
        self.coords1 = None
        self.coords2 = None

        def _register(tools_instance, tool_name):
            """
            Register a tool into the provided tools instance using configuration from Tools_dict.
            
            Reads the tool configuration for `tool_name` from the surrounding `Tools_dict`, extracts optional `provider` and `model`, collects common authentication parameters (api_key, base_url, endpoint_url, azure_endpoint, api_version), merges them with any remaining configuration, logs the registration, and calls tools_instance.register_tool with the assembled parameters.
            
            Parameters:
                tools_instance: The tools manager/registry instance that exposes register_tool(tool_name, provider, model, **params).
                tool_name (str): Key name of the tool in Tools_dict whose configuration will be used to register the tool.
            """
            config = Tools_dict.get(tool_name, {}).copy()
            provider = config.pop("provider", None)
            model = config.pop("model", None)

            auth_keys = ['api_key', 'base_url', 'endpoint_url', 'azure_endpoint', 'api_version']
            auth_params = {}
            for key in auth_keys:
                if key in config:
                    auth_params[key] = config[key]
                    logger.info(f"Grounding._register: Setting {key} for tool '{tool_name}'")

            # 合并所有参数
            all_params = {**config, **auth_params}

            logger.info(f"Grounding._register: Registering tool '{tool_name}' with provider '{provider}', model '{model}'")
            tools_instance.register_tool(tool_name, provider, model, **all_params)

        self.grounding_model = Tools()
        _register(self.grounding_model, "grounding")

        self.grounding_width, self.grounding_height = self.grounding_model.tools[
            "grounding"].get_grounding_wh()
        if self.grounding_width is None or self.grounding_height is None:
            self.grounding_width = self.width
            self.grounding_height = self.height

        self.text_span_agent = Tools()
        _register(self.text_span_agent, "text_span")

        # GlobalState will be initialized when task_id is set
        self.global_state: GlobalState = None  # type: ignore

    def set_task_id(self, task_id: str) -> None:
        """Set the task identifier and update global state reference"""
        # Update global state reference with task-specific registry
        self.global_state = Registry.get_from_context("GlobalStateStore", task_id)  # type: ignore

    def generate_coords(self, ref_expr: str, obs: Dict) -> List[int]:
        grounding_start_time = time.time()
        self.grounding_model.tools["grounding"].llm_agent.reset()
        prompt = (
            f"Task: Visual Grounding - Locate and return coordinates\n Query:{ref_expr}\n Instructions: 1. Carefully analyze the provided screenshot image \n 2. Locate the EXACT element/area described in the query \n 3. Return ONLY the pixel coordinates [x, y] of one representative point within the target area \n 4. Choose a point that is clearly inside the described element/region \n 5. Coordinates must be integers representing pixel positions on the image \n 6. If the described element has multiple instances, select the most prominent or central one 7. - If this appears to be for dragging (selecting text, moving items, etc.): * For START points: Position slightly to the LEFT of text/content in empty space  * For END points: Position slightly to the RIGHT of text/content in empty space  * Avoid placing coordinates directly ON text characters to prevent text selection issues  * Keep offset minimal (3-5 pixels) - don't go too far from the target area  * Still return only ONE coordinate as requested \n Output Format: Return only two integers separated by comma, like: (900, 400)\n Important Notes: - Focus on the main descriptive elements in the query (colors, positions, objects) - Ignore any additional context that doesn't help locate the target - The returned point should be clickable/actionable within the target area \n CRITICAL REQUIREMENTS: - MUST return exactly ONE coordinate pair under ALL circumstances - NO explanations, NO multiple coordinates, NO additional text \n"
        )
        response, total_tokens, cost_string = self.grounding_model.execute_tool(
            "grounding", {
                "str_input": prompt,
                "img_input": obs["screenshot"]
            })
        logger.info(
            f"Grounding model tokens: {total_tokens}, cost: {cost_string}")
        grounding_end_time = time.time()
        grounding_duration = grounding_end_time - grounding_start_time
        logger.info(
            f"Grounding model execution time: {grounding_duration:.2f} seconds")
        logger.info(f"RAW GROUNDING MODEL RESPONSE: {response}")
        self.global_state.log_operation(module="grounding",
                                        operation="grounding_model_response",
                                        data={
                                            "tokens": total_tokens,
                                            "cost": cost_string,
                                            "content": response,
                                            "duration": grounding_duration
                                        })
        numericals = re.findall(r"\d+", response)
        assert len(numericals) >= 2
        return [int(numericals[0]), int(numericals[1])]

    def assign_coordinates(self, plan: str, obs: Dict):
        self.coords1, self.coords2 = None, None
        try:
            action = parse_single_code_from_string(
                plan.split("Grounded Action")[-1])
            function_name = re.match(r"(\w+\.\w+)\(",
                                     action).group(1)  # type: ignore
            args = self.parse_function_args(action)
        except Exception as e:
            raise RuntimeError(f"Error in parsing grounded action: {e}") from e

        if (function_name in [
                "agent.click", "agent.doubleclick", "agent.move", "agent.scroll"
        ] and len(args) >= 1 and args[0] is not None):
            self.coords1 = self.generate_coords(args[0], obs)
        elif function_name == "agent.drag" and len(args) >= 2:
            self.coords1 = self.generate_coords(args[0], obs)
            self.coords2 = self.generate_coords(args[1], obs)

    def reset_screen_size(self, width: int, height: int):
        self.width = width
        self.height = height

    def resize_coordinates(self, coordinates: List[int]) -> List[int]:
        return [
            round(coordinates[0] * self.width / self.grounding_width),
            round(coordinates[1] * self.height / self.grounding_height),
        ]

    def resize_coordinates_with_padding(self,
                                        coordinates: List[int]) -> List[int]:
        grounding_size = max(self.grounding_width, self.grounding_height)
        original_size = max(self.width, self.height)
        coordinates = [
            round(coordinates[0] * original_size / grounding_size),
            round(coordinates[1] * original_size / grounding_size),
        ]
        padding_left = round((original_size - self.width) / 2)
        padding_top = round((original_size - self.height) / 2)
        return [
            coordinates[0] - padding_left,
            coordinates[1] - padding_top,
        ]

    def parse_function_args(self, function: str) -> List[str]:
        if not function or not isinstance(function, str):
            return []
        pattern = r'(\w+\.\w+)\((?:"([^"]*)")?(?:,\s*(\d+))?\)'
        match = re.match(pattern, function)
        if match:
            args = []
            if match.group(2) is not None:
                args.append(match.group(2))
            if match.group(3) is not None:
                args.append(int(match.group(3)))
            if args:
                return args
        try:
            tree = ast.parse(function)
        except Exception:
            return []
        if not tree.body or not hasattr(tree.body[0], 'value'):
            return []
        call_node = tree.body[0].value  # type: ignore
        if not isinstance(call_node, ast.Call):
            return []

        def safe_eval(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif hasattr(ast, 'Str') and isinstance(node, ast.Str):
                return node.s
            else:
                try:
                    return ast.unparse(node)
                except Exception:
                    return str(node)

        positional_args = []
        try:
            positional_args = [safe_eval(arg) for arg in call_node.args]
        except Exception:
            positional_args = []
        keyword_args = {}
        try:
            keyword_args = {
                kw.arg: safe_eval(kw.value) for kw in call_node.keywords
            }
        except Exception:
            keyword_args = {}
        res = []
        for key, val in keyword_args.items():
            if key and "description" in key:
                res.append(val)
        for arg in positional_args:
            res.append(arg)
        return res

    def _record_passive_memory(self, action_type: str, action_details: str):
        memory_content = f"Hardware action `{action_type}` has been executed. Details: {action_details}"
        self.global_state.add_agent_log({
            "type": "passive",
            "content": memory_content
        })

    @agent_action
    def click(
        self,
        element_description: str,
        button: int = 1,
        holdKey: List[str] = [],
    ):
        x, y = self.resize_coordinates(self.coords1)  # type: ignore
        actionDict = {
            "type": "Click",
            "x": x,
            "y": y,
            "element_description": element_description,
            "button": button,
            "holdKey": holdKey
        }
        action_details = f"Clicked at coordinates ({x}, {y}) with button {button}, element: {element_description}"
        self._record_passive_memory("Click", action_details)
        return actionDict

    @agent_action
    def doubleclick(
        self,
        element_description: str,
        button: int = 1,
        holdKey: List[str] = [],
    ):
        x, y = self.resize_coordinates(self.coords1)  # type: ignore
        actionDict = {
            "type": "DoubleClick",
            "x": x,
            "y": y,
            "element_description": element_description,
            "button": button,
            "holdKey": holdKey
        }
        action_details = f"Double clicked at coordinates ({x}, {y}) with button {button}, element: {element_description}"
        self._record_passive_memory("DoubleClick", action_details)
        return actionDict

    @agent_action
    def move(
        self,
        element_description: str,
        holdKey: List[str] = [],
    ):
        x, y = self.resize_coordinates(self.coords1)  # type: ignore
        actionDict = {
            "type": "Move",
            "x": x,
            "y": y,
            "element_description": element_description,
            "holdKey": holdKey
        }
        action_details = f"Moved to coordinates ({x}, {y}), element: {element_description}"
        self._record_passive_memory("Move", action_details)
        return actionDict

    @agent_action
    def scroll(
        self,
        element_description: str,
        clicks: int,
        vertical: bool = True,
        holdKey: List[str] = [],
    ):
        x, y = self.resize_coordinates(self.coords1)  # type: ignore
        if vertical:
            actionDict = {
                "type": "Scroll",
                "x": x,
                "y": y,
                "element_description": element_description,
                "stepVertical": clicks,
                "holdKey": holdKey
            }
            action_details = f"Scrolled vertically at coordinates ({x}, {y}) with {clicks} clicks, element: {element_description}"
        else:
            actionDict = {
                "type": "Scroll",
                "x": x,
                "y": y,
                "element_description": element_description,
                "stepHorizontal": clicks,
                "holdKey": holdKey
            }
            action_details = f"Scrolled horizontally at coordinates ({x}, {y}) with {clicks} clicks, element: {element_description}"
        self._record_passive_memory("Scroll", action_details)
        return actionDict

    @agent_action
    def drag(
        self,
        starting_description: str,
        ending_description: str,
        holdKey: List[str] = [],
    ):
        x1, y1 = self.resize_coordinates(self.coords1)  # type: ignore
        x2, y2 = self.resize_coordinates(self.coords2)  # type: ignore
        actionDict = {
            "type": "Drag",
            "startX": x1,
            "startY": y1,
            "endX": x2,
            "endY": y2,
            "holdKey": holdKey,
            "starting_description": starting_description,
            "ending_description": ending_description
        }
        action_details = f"Dragged from ({x1}, {y1}) to ({x2}, {y2}), starting: {starting_description}, ending: {ending_description}"
        self._record_passive_memory("Drag", action_details)
        return actionDict

    @agent_action
    def type(
        self,
        text: str = "",
    ):
        actionDict = {
            "type": "TypeText",
            "text": text,
        }
        action_details = f"Typed text: {text}"
        self._record_passive_memory("TypeText", action_details)
        return actionDict

    @agent_action
    def hotkey(
        self,
        keys: List[str] = [],
        duration: int = 0,
    ):
        keys = [f"{key}" for key in keys]
        if 1 <= duration <= 5000:
            actionDict = {
                "type": "Hotkey",
                "keys": keys,
                "duration": duration,
            }
            action_details = f"Pressed hotkey combination: {', '.join(keys)} with duration {duration}ms"
        else:
            actionDict = {
                "type": "Hotkey",
                "keys": keys,
            }
            action_details = f"Pressed hotkey combination: {', '.join(keys)}"
        self._record_passive_memory("Hotkey", action_details)
        return actionDict

    @agent_action
    def wait(self, duration: int):
        actionDict = {"type": "Wait", "duration": duration}
        action_details = f"Waited for {duration} milliseconds"
        self._record_passive_memory("Wait", action_details)
        return actionDict

    @agent_action
    def done(
        self,
        message: str = '',
    ):
        self.returned_info = message
        actionDict = {"type": "Done", "message": message}
        return actionDict

    @agent_action
    def fail(
        self,
        message: str = '',
    ):
        actionDict = {"type": "Failed", "message": message}
        return actionDict

    @agent_action
    def memorize(
        self,
        information: str,
        memory_type: str = "active",
    ):
        self.global_state.add_agent_log({
            "type": memory_type,
            "content": information
        })
        actionDict = {
            "type": "Memorize",
            "information": information,
        }
        return actionDict

    @agent_action
    def passive_memorize(
        self,
        information: str,
    ):
        return self.memorize(information, memory_type="passive")

    @agent_action
    def user_takeover(
        self,
        message: str = '',
    ):
        self.global_state.set_running_state("stopped")
        actionDict = {"type": "UserTakeover", "message": message}
        return actionDict


class FastGrounding(ACI):

    def __init__(
        self,
        Tools_dict: Dict,
        platform: str,
        width: int = 1920,
        height: int = 1080,
        grounding_width: int = 1920,
        grounding_height: int = 1080,
    ):
        self.platform = platform
        self.Tools_dict = Tools_dict
        self.width = width
        self.height = height
        self.grounding_width = grounding_width
        self.grounding_height = grounding_height
        # GlobalState will be initialized when task_id is set
        self.global_state: GlobalState = None  # type: ignore

    def set_task_id(self, task_id: str) -> None:
        """Set the task identifier and update global state reference"""
        # Update global state reference with task-specific registry
        self.global_state = Registry.get_from_context("GlobalStateStore", task_id)  # type: ignore

    def reset_screen_size(self, width: int, height: int):
        self.width = width
        self.height = height

    def resize_coordinates(self, coordinates: List[int]) -> List[int]:
        return [
            round(coordinates[0] * self.width / self.grounding_width),
            round(coordinates[1] * self.height / self.grounding_height),
        ]

    def _record_passive_memory(self, action_type: str, action_details: str):
        memory_content = f"Hardware action `{action_type}` has been executed. Details: {action_details}"
        self.global_state.add_agent_log({
            "type": "passive",
            "content": memory_content
        })

    @agent_action
    def click(
        self,
        x: int,
        y: int,
        element_description: str = "",
        button: int = 1,
        holdKey: List[str] = [],
    ):
        x, y = self.resize_coordinates([x, y])
        actionDict = {
            "type": "Click",
            "x": x,
            "y": y,
            "element_description": element_description or f"Coordinates ({x}, {y})",
            "button": button,
            "holdKey": holdKey
        }
        action_details = f"Clicked at coordinates ({x}, {y}) with button {button}, element: {element_description or f'Coordinates ({x}, {y})'}"
        self._record_passive_memory("Click", action_details)
        return actionDict

    @agent_action
    def doubleclick(
        self,
        x: int,
        y: int,
        element_description: str = "",
        button: int = 1,
        holdKey: List[str] = [],
    ):
        x, y = self.resize_coordinates([x, y])
        actionDict = {
            "type": "DoubleClick",
            "x": x,
            "y": y,
            "element_description": element_description or f"Coordinates ({x}, {y})",
            "button": button,
            "holdKey": holdKey
        }
        action_details = f"Double clicked at coordinates ({x}, {y}) with button {button}, element: {element_description or f'Coordinates ({x}, {y})'}"
        self._record_passive_memory("DoubleClick", action_details)
        return actionDict

    @agent_action
    def move(
        self,
        x: int,
        y: int,
        element_description: str = "",
        holdKey: List[str] = [],
    ):
        x, y = self.resize_coordinates([x, y])
        actionDict = {
            "type": "Move",
            "x": x,
            "y": y,
            "element_description": element_description or f"Coordinates ({x}, {y})",
            "holdKey": holdKey
        }
        action_details = f"Moved to coordinates ({x}, {y}), element: {element_description or f'Coordinates ({x}, {y})'}"
        self._record_passive_memory("Move", action_details)
        return actionDict

    @agent_action
    def scroll(
        self,
        x: int,
        y: int,
        clicks: int,
        element_description: str = "",
        vertical: bool = True,
        holdKey: List[str] = [],
    ):
        x, y = self.resize_coordinates([x, y])
        if vertical:
            actionDict = {
                "type": "Scroll",
                "x": x,
                "y": y,
                "element_description": element_description or f"Coordinates ({x}, {y})",
                "stepVertical": clicks,
                "holdKey": holdKey
            }
            action_details = f"Scrolled vertically at coordinates ({x}, {y}) with {clicks} clicks, element: {element_description or f'Coordinates ({x}, {y})'}"
        else:
            actionDict = {
                "type": "Scroll",
                "x": x,
                "y": y,
                "element_description": element_description or f"Coordinates ({x}, {y})",
                "stepHorizontal": clicks,
                "holdKey": holdKey
            }
            action_details = f"Scrolled horizontally at coordinates ({x}, {y}) with {clicks} clicks, element: {element_description or f'Coordinates ({x}, {y})'}"
        self._record_passive_memory("Scroll", action_details)
        return actionDict

    @agent_action
    def drag(
        self,
        startX: int,
        startY: int,
        endX: int,
        endY: int,
        starting_description: str = "",
        ending_description: str = "",
        holdKey: List[str] = [],
    ):
        startX, startY = self.resize_coordinates([startX, startY])
        endX, endY = self.resize_coordinates([endX, endY])
        actionDict = {
            "type": "Drag",
            "startX": startX,
            "startY": startY,
            "endX": endX,
            "endY": endY,
            "holdKey": holdKey,
            "starting_description": starting_description or f"Coordinates ({startX}, {startY})",
            "ending_description": ending_description or f"Coordinates ({endX}, {endY})"
        }
        action_details = f"Dragged from ({startX}, {startY}) to ({endX}, {endY}), starting: {starting_description or f'Coordinates ({startX}, {startY})'}, ending: {ending_description or f'Coordinates ({endX}, {endY})'}"
        self._record_passive_memory("Drag", action_details)
        return actionDict

    @agent_action
    def type(
        self,
        text: str = "",
    ):
        actionDict = {
            "type": "TypeText",
            "text": text,
        }
        action_details = f"Typed text: {text}"
        self._record_passive_memory("TypeText", action_details)
        return actionDict

    @agent_action
    def hotkey(
        self,
        keys: List[str] = [],
        duration: int = 0,
    ):
        keys = [f"{key}" for key in keys]
        if 1 <= duration <= 5000:
            actionDict = {
                "type": "Hotkey",
                "keys": keys,
                "duration": duration,
            }
            action_details = f"Pressed hotkey combination: {', '.join(keys)} with duration {duration}ms"
        else:
            actionDict = {
                "type": "Hotkey",
                "keys": keys,
            }
            action_details = f"Pressed hotkey combination: {', '.join(keys)}"
        self._record_passive_memory("Hotkey", action_details)
        return actionDict

    @agent_action
    def wait(self, duration: int):
        actionDict = {"type": "Wait", "duration": duration}
        action_details = f"Waited for {duration} milliseconds"
        self._record_passive_memory("Wait", action_details)
        return actionDict

    @agent_action
    def done(
        self,
        message: str = '',
    ):
        self.returned_info = message
        actionDict = {"type": "Done", "message": message}
        return actionDict

    @agent_action
    def fail(
        self,
        message: str = '',
    ):
        actionDict = {"type": "Failed", "message": message}
        return actionDict

    @agent_action
    def memorize(
        self,
        information: str,
    ):
        self.global_state.add_agent_log({
            "type": "active",
            "content": information
        })
        actionDict = {
            "type": "Memorize",
            "information": information,
        }
        return actionDict

    @agent_action
    def user_takeover(
        self,
        message: str = '',
    ):
        self.global_state.set_running_state("stopped")
        actionDict = {"type": "UserTakeover", "message": message}
        return actionDict
