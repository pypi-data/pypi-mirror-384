"""
Tools module for GUI agents.

This module provides various tools for GUI agents to perform tasks such as web search,
context fusion, subtask planning, trajectory reflection, memory retrieval, grounding,
evaluation, and action generation.
"""

import time
from typing import Dict, Any, Optional, List, Union, Tuple
from abc import ABC, abstractmethod
import logging
from gui_agents.core.mllm import LLMAgent, WebSearchAgent, EmbeddingAgent
import threading
from gui_agents.prompts.prompts import system_prompts

logger = logging.getLogger("desktopenv.tools")

class BaseTool(ABC):
    """Base class for all tools."""
    _prompts_dict = None
    _prompts_dict_lock = threading.Lock()

    @classmethod
    def _load_prompts_dict(cls):
        """
        Lazily load and cache the prompts dictionary on the class using thread-safe double-checked locking.
        
        If the prompts module cannot be loaded, sets `_prompts_dict` to an empty dict and logs an error.
        """
        if cls._prompts_dict is None:
            with cls._prompts_dict_lock:
                if cls._prompts_dict is None:
                    try:
                        # Import prompts from prompts.py module
                        cls._prompts_dict = system_prompts
                    except Exception as e:
                        logger.error(f"Failed to load prompts from prompts.py: {e}")
                        cls._prompts_dict = {}

    def __init__(self, provider: str, model_name: str, tool_name: str, **kwargs):
        """
        Initialize the base tool, populate engine parameters from provided arguments, load the tool prompt, and create the LLMAgent instance used for LLM calls.
        
        Parameters:
            provider (str): API provider identifier (e.g., "gemini", "openai"); used as the engine_type in engine parameters.
            model_name (str): Model identifier to use (e.g., "gemini-2.5-pro"); stored as the model in engine parameters.
            tool_name (str): Tool key used to look up the system prompt template.
        
        Keyword Arguments:
            api_key, base_url, endpoint_url, azure_endpoint, api_version: If present, each is copied into engine parameters and logged as set for the tool.
            Any other kwargs: Forwarded into engine parameters as-is.
        
        Notes:
            - Loads the prompt template for the tool and stores it on the instance.
            - Constructs self.engine_params and instantiates self.llm_agent with the system prompt.
        """
        self.provider = provider
        self.model_name = model_name
        self.tool_name = tool_name
        self._load_prompts_dict()
        self._prompt_template = self._get_prompt_template()
        # Create LLMAgent instance for tool usage
        self.engine_params = {
            "engine_type": provider,
            "model": model_name
        }

        auth_keys = ['api_key', 'base_url', 'endpoint_url', 'azure_endpoint', 'api_version']
        for key in auth_keys:
            if key in kwargs:
                self.engine_params[key] = kwargs[key]
                logger.info(f"Setting {key} for tool '{tool_name}' with provider '{provider}'")

        for key, value in kwargs.items():
            if key not in auth_keys:
                self.engine_params[key] = value

        self.llm_agent = LLMAgent(engine_params=self.engine_params, system_prompt=self._prompt_template)

    def _get_prompt_template(self) -> str:
        """
        Return the prompt template associated with this tool from the class-level prompts cache.
        
        Returns:
        	(prompt_template (str)): The prompt template for this tool's name, or an empty string if the tool has no name or no template is available.
        """
        if self.tool_name is None:
            return ""
        prompts = self.__class__._prompts_dict
        if prompts is None:
            return ""
        return prompts.get(self.tool_name, "")
    
    def _call_lmm(self, input_data: Dict[str, Any], temperature: float = 0.0):
        """
        Call the LMM model for inference using the prompt template with retry mechanism
        
        Args:
            input_data: Dictionary containing input data to format the prompt template
            temperature: Temperature parameter to control randomness of output
            
        Returns:
            Model response as text
        """
        # self.llm_agent.reset()
        
        # Extract text and image inputs
        text_input = input_data.get('str_input', '')
        image_input = input_data.get('img_input', None)
        
        # Add the message with the formatted prompt
        self.llm_agent.add_message(text_input, image_content=image_input, role="user")
        
        # Implement safe retry mechanism
        max_retries = 3
        attempt = 0
        content, total_tokens, cost_string = "", [0, 0, 0], ""
        
        while attempt < max_retries:
            try:
                content, total_tokens, cost_string = self.llm_agent.get_response(temperature=temperature)
                break  # If successful, break out of the loop
            except Exception as e:
                attempt += 1
                logger.error(f"LLM call attempt {attempt} failed: {str(e)}")
                if attempt == max_retries:
                    logger.error("Max retries reached. Returning error message.")
                    return f"Error: LLM call failed after {max_retries} attempts: {str(e)}", [0, 0, 0], ""
                time.sleep(1.0)
        return content, total_tokens, cost_string
    
    @abstractmethod
    def execute(self, tool_input: Dict[str, Any]) -> Tuple[str, List[int], str]:
        """
        Execute the tool with the given input.
        
        Args:
            tool_input: Dictionary containing the input for the tool
                        Expected to have 'str_input' and/or 'img_input' keys
        
        Returns:
            The output of the tool as a string
        """
        pass


class ToolFactory:
    """Factory class for creating tools."""
    
    @staticmethod
    def create_tool(tool_name: str, provider: str, model_name: str, **kwargs) -> 'BaseTool':
        """
        Create a tool instance based on the tool name.
        
        Args:
            tool_name: Name of the tool to create
            provider: API provider name
            model_name: Model name to use
            **kwargs: Additional parameters to pass to the tool
            
        Returns:
            An instance of the specified tool
        
        Raises:
            ValueError: If the tool name is not recognized
        """
        tool_map = {
            "websearch": (WebSearchTool, None),
            "context_fusion": (ContextFusionTool, "context_fusion"),
            "subtask_planner": (SubtaskPlannerTool, "subtask_planner"),
            "traj_reflector": (TrajReflectorTool, "traj_reflector"),
            "grounding": (GroundingTool, "grounding"),
            "evaluator": (EvaluatorTool, "evaluator"),
            "action_generator": (ActionGeneratorTool, "action_generator"),
            "action_generator_with_takeover": (ActionGeneratorTool, "action_generator_with_takeover"),
            "fast_action_generator": (FastActionGeneratorTool, "fast_action_generator"),
            "fast_action_generator_with_takeover": (FastActionGeneratorTool, "fast_action_generator_with_takeover"),
            "dag_translator": (DAGTranslatorTool, "dag_translator"),
            "embedding": (EmbeddingTool, None),
            "query_formulator": (QueryFormulatorTool, "query_formulator"),
            "text_span": (TextSpanTool, "text_span"),
            "narrative_summarization": (NarrativeSummarizationTool, "narrative_summarization"),
            "episode_summarization": (EpisodeSummarizationTool, "episode_summarization")
        }
        
        if tool_name not in tool_map:
            raise ValueError(f"Unknown tool name: {tool_name}")
        
        tool_class, prompt_key = tool_map[tool_name]
        
        # WebSearchTool and EmbeddingTool don't need a prompt
        if tool_name == "websearch":
            return tool_class(provider, model_name, None, **kwargs)
        if tool_name == "embedding":
            return tool_class(provider, model_name, None, **kwargs)
        
        return tool_class(provider, model_name, prompt_key, **kwargs)


class WebSearchTool(BaseTool):
    """Tool for performing web searches."""
    
    def __init__(self, provider: str, model_name: str, tool_name: str, base_url='', api_key=''):
        """
        Initialize the WebSearchTool and configure its WebSearchAgent.
        
        Parameters:
            provider (str): Identifier of the search API provider (e.g., "bocha", "exa").
            model_name (str): Model identifier to include in engine configuration.
            tool_name (str): Tool name or prompt key associated with this tool.
            base_url (str, optional): Custom endpoint URL for the search service.
            api_key (str, optional): API key or credential for authenticating with the search service.
        """
        self.provider = provider
        
        # Create WebSearchAgent instance for search
        self.engine_params = {
            "engine_type": provider,
            "model": model_name,
        }
        
        # Initialize WebSearchAgent
        self.search_agent = WebSearchAgent(engine_params=self.engine_params)
    
    def execute(self, tool_input: Dict[str, Any]) -> Tuple[str, List[int], str]:
        """
        Execute a web search with the given query.
        
        Args:
            tool_input: Dictionary containing the search query
                        Expected to have 'str_input' key with the search query
        
        Returns:
            Search results as a string
        """
        query = tool_input.get('str_input', '')
        if not query:
            return "Error: No search query provided", [0, 0, 0], ""
        
        try:
            # Get the answer from the search results
            answer, total_tokens, cost = self.search_agent.get_answer(query)
            
            # Return just the answer
            return answer, total_tokens, cost # type: ignore
        
        except Exception as e:
            logger.error(f"Error during web search: {str(e)}")
            return f"Error: Web search failed: {str(e)}", [0, 0, 0], ""


class ContextFusionTool(BaseTool):
    """Tool for fusing multiple contexts together."""
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Fuse multiple contexts together.
        
        Args:
            tool_input: Dictionary containing the contexts to fuse
                        Expected to have 'str_input' key with JSON-formatted contexts
        
        Returns:
            Fused context as a string
        """
        contexts = tool_input.get('str_input', '')
        if not contexts:
            return "Error: No contexts provided"
        
        # Use the prompt template and LMM for context fusion
        return self._call_lmm(tool_input)


class SubtaskPlannerTool(BaseTool):
    """Tool for planning subtasks."""
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Plan subtasks for a given task.
        
        Args:
            tool_input: Dictionary containing the task description
                        Expected to have 'str_input' key with the task description
                        May also have 'img_input' key with a screenshot
        
        Returns:
            Subtask plan as a string
        """
        task = tool_input.get('str_input', '')
        if not task:
            return "Error: No task description provided"
        
        # Use the prompt template and LMM for subtask planning
        return self._call_lmm(tool_input)


class NarrativeSummarizationTool(BaseTool):
    """Tool for summarizing narrative memories."""
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Summarize narrative memories.
        
        Args:
            tool_input: Dictionary containing the narrative memory data
                        Expected to have 'str_input' key with the narrative memory data
                        May also have 'img_input' key with relevant images
        
        Returns:
            Summarized narrative as a string
        """
        narrative_data = tool_input.get('str_input', '')
        if not narrative_data:
            return "Error: No narrative memory data provided"
        
        # Use the prompt template and LMM for narrative summarization
        return self._call_lmm(tool_input)


class EpisodeSummarizationTool(BaseTool):
    """Tool for summarizing episodic memories."""
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Summarize episodic memories.
        
        Args:
            tool_input: Dictionary containing the episodic memory data
                        Expected to have 'str_input' key with the episodic memory data
                        May also have 'img_input' key with relevant images
        
        Returns:
            Summarized episode as a string
        """
        episode_data = tool_input.get('str_input', '')
        if not episode_data:
            return "Error: No episodic memory data provided"
        
        # Use the prompt template and LMM for episode summarization
        return self._call_lmm(tool_input)


class TextSpanTool(BaseTool):
    """Tool for processing text spans."""
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Process text spans for a given input.
        
        Args:
            tool_input: Dictionary containing the text input
                        Expected to have 'str_input' key with the text content
                        May also have 'img_input' key with a screenshot
        
        Returns:
            Processed text spans as a string
        """
        text = tool_input.get('str_input', '')
        if not text:
            return "Error: No text content provided"
        
        # Use the prompt template and LMM for text span processing
        return self._call_lmm(tool_input)


class DAGTranslatorTool(BaseTool):
    """Tool for translating task descriptions into a DAG (Directed Acyclic Graph) structure."""
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Translate task descriptions into a DAG structure.
        
        Args:
            tool_input: Dictionary containing the task description
                        Expected to have 'str_input' key with the task description
                        May also have 'img_input' key with a screenshot
        
        Returns:
            DAG representation as a string
        """
        task = tool_input.get('str_input', '')
        if not task:
            return "Error: No task description provided"
        
        # Use the prompt template and LMM for DAG translation
        return self._call_lmm(tool_input)


class TrajReflectorTool(BaseTool):
    """Tool for reflecting on execution trajectories."""
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Reflect on an execution trajectory.
        
        Args:
            tool_input: Dictionary containing the trajectory
                        Expected to have 'str_input' key with the trajectory
        
        Returns:
            Reflection as a string
        """
        trajectory = tool_input.get('str_input', '')
        if not trajectory:
            return "Error: No trajectory provided"
        
        # Use the prompt template and LMM for trajectory reflection
        return self._call_lmm(tool_input)

class GroundingTool(BaseTool):
    """Tool for grounding agent actions in the environment."""
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Ground agent actions in the environment.
        
        Args:
            tool_input: Dictionary containing the action and environment state
                        Expected to have 'str_input' key with the action
                        Expected to have 'img_input' key with a screenshot
        
        Returns:
            Grounded action as a string
        """
        action = tool_input.get('str_input', '')
        screenshot = tool_input.get('img_input')
        
        if not action:
            return "Error: No action provided"
        if not screenshot:
            return "Error: No screenshot provided"
        
        # Use the prompt template and LMM for action grounding
        return self._call_lmm(tool_input)
    
    def get_grounding_wh(self):
        """
        Get grounding width and height based on provider and model name.
        
        Returns:
            If provider is doubao and model_name contains 'ui-tars', returns two values:
            grounding_width (int): Width value (1024)
            grounding_height (int): Height value (768)
            Otherwise returns None, None
        """
        if self.provider == "doubao" and "ui-tars" in self.model_name:
            grounding_width = 1000
            grounding_height = 1000
            return grounding_width, grounding_height
        return None, None


class EvaluatorTool(BaseTool):
    """Tool for evaluating agent performance."""
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Evaluate agent performance.
        
        Args:
            tool_input: Dictionary containing the evaluation data
                        Expected to have 'str_input' key with the evaluation data
        
        Returns:
            Evaluation result as a string
        """
        eval_data = tool_input.get('str_input', '')
        if not eval_data:
            return "Error: No evaluation data provided"
        
        # Use the prompt template and LMM for performance evaluation
        return self._call_lmm(tool_input)


class ActionGeneratorTool(BaseTool):
    """Tool for generating executable actions."""
    
    def __init__(self, provider: str, model_name: str, tool_name: str, **kwargs):
        """
        Create an ActionGeneratorTool and configure optional web search support.
        
        Parameters:
            provider (str): Name of the API provider to use for the tool.
            model_name (str): Model identifier used by the underlying LLM engine.
            tool_name (str): Tool key used to select the prompt template.
            **kwargs: Additional configuration options:
                enable_search (bool): If True, a WebSearchTool will be created and attached to the tool as `self.search_tool`. Defaults to False.
                search_provider (str): Provider to use for the optional web search. Defaults to "bocha".
                search_model (str): Model identifier to use for the optional web search. Defaults to an empty string.
        
        Side effects:
            Sets `self.enable_search` and, when `enable_search` is True, initializes `self.search_tool` with a WebSearchTool instance and logs the enabling of web search.
        """
        super().__init__(provider, model_name, tool_name, **kwargs)
        
        # Extract search-related parameters
        self.enable_search = kwargs.get("enable_search", False)
        search_provider = kwargs.get("search_provider", "bocha")
        search_model = kwargs.get("search_model", "")
        
        # Initialize search tool if enabled
        self.search_tool = None
        if self.enable_search:
            self.search_tool = WebSearchTool(search_provider, search_model, "")
            logger.info(f"Web search enabled for {tool_name} using provider: {search_provider}")
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Generate executable actions.
        
        Args:
            tool_input: Dictionary containing the action request
                        Expected to have 'str_input' key with the action request
                        May also have 'img_input' key with a screenshot
        
        Returns:
            Generated action as a string
        """
        action_request = tool_input.get('str_input', '')
        if not action_request:
            return "Error: No action request provided", [0, 0, 0], ""
        
        # Check if search is enabled
        if self.enable_search and self.search_tool:
            try:
                # Use the input text directly as search query
                search_query = action_request
                logger.info(f"Performing web search for query: {search_query}")
                search_results, tokens, cost = self.search_tool.execute({"str_input": search_query})
                
                # Enhance the action request with search results
                enhanced_request = f"[Action Request]\n{action_request}\n[End of Action Request]\n\n[Web Search Results for '{action_request}']\n{search_results}\n\n[End of Web Search Results]"
                tool_input["str_input"] = enhanced_request
                
                logger.info(f"Search completed. Found information: {len(search_results)} characters")
            except Exception as e:
                logger.error(f"Error during web search: {e}")
                # Continue with original request if search fails
        
        # Use the prompt template and LMM for action generation
        return self._call_lmm(tool_input)


class FastActionGeneratorTool(BaseTool):
    """Tool for directly generating executable actions without intermediate planning."""
    
    def __init__(self, provider: str, model_name: str, tool_name: str, **kwargs):
        """
        Initialize the FastActionGeneratorTool and optionally enable web search augmentation.
        
        Parameters:
            provider (str): API provider name used to configure the underlying LLM/engine.
            model_name (str): Model identifier to use for generation.
            tool_name (str): Tool key used to select the prompt template.
            **kwargs: Additional keyword arguments. Recognized keys:
                enable_search (bool): If true, instantiate a WebSearchTool to augment requests with search results.
                search_provider (str): Provider name for the optional web search (default "bocha").
                search_model (str): Model name for the optional web search (default "").
                Any other kwargs are forwarded to BaseTool for engine/auth configuration.
        """
        super().__init__(provider, model_name, tool_name, **kwargs)
        
        # Extract search-related parameters
        self.enable_search = kwargs.get("enable_search", False)
        search_provider = kwargs.get("search_provider", "bocha")
        search_model = kwargs.get("search_model", "")
        
        # Initialize search tool if enabled
        self.search_tool = None
        if self.enable_search:
            self.search_tool = WebSearchTool(search_provider, search_model, "")
            logger.info(f"Web search enabled for {tool_name} using provider: {search_provider}")
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Generate executable actions directly from the instruction and screenshot.
        
        Args:
            tool_input: Dictionary containing the action request
                        Expected to have 'str_input' key with the instruction
                        Expected to have 'img_input' key with a screenshot
        
        Returns:
            Generated action as a string, token count, and cost
        """
        action_request = tool_input.get('str_input', '')
        screenshot = tool_input.get('img_input')
        if not action_request:
            return "Error: No action request provided", [0, 0, 0], ""
        if not screenshot:
            return "Error: No screenshot provided", [0, 0, 0], ""
        # Check if search is enabled
        if self.enable_search and self.search_tool:
            try:
                # Use the input text directly as search query
                search_query = action_request
                logger.info(f"Performing web search for query: {search_query}")
                search_results, tokens, cost = self.search_tool.execute({"str_input": search_query})
                
                # Enhance the action request with search results
                enhanced_request = f"[Action Request]\n{action_request}\n[End of Action Request]\n\n[Web Search Results for '{action_request}']\n{search_results}\n\n[End of Web Search Results]"
                tool_input["str_input"] = enhanced_request
                
                logger.info(f"Search completed. Found information: {len(search_results)} characters")
            except Exception as e:
                logger.error(f"Error during web search: {e}")
                # Continue with original request if search fails
        
        # Use the prompt template and LMM for action generation
        return self._call_lmm(tool_input)

    def get_grounding_wh(self):
        """
        Get grounding width and height based on provider and model name.
        
        Returns:
            If provider is doubao and model_name contains 'ui-tars', returns two values:
            grounding_width (int): Width value (1024)
            grounding_height (int): Height value (768)
            Otherwise returns None, None
        """
        if self.provider == "doubao" and "ui-tars" in self.model_name:
            grounding_width = 1000
            grounding_height = 1000
            return grounding_width, grounding_height
        return None, None

class EmbeddingTool(BaseTool):
    """Tool for generating text embeddings."""
    
    def __init__(self, provider: str, model_name: str, tool_name: str, base_url='', api_key=''):
        """
        Create and configure an EmbeddingTool backed by an EmbeddingAgent.
        
        Parameters:
            provider (str): Name of the embedding service provider (e.g., "openai", "gemini").
            model_name (str): Embedding model identifier to use.
            tool_name (str): Tool key used to look up prompts or register the tool.
            base_url (str, optional): Custom endpoint URL for the provider; defaults to ''.
            api_key (str, optional): API key or credential for authenticating with the provider; defaults to ''.
        """
        self.provider = provider
        self.model_name = model_name
        self.tool_name = tool_name
        
        # Create EmbeddingAgent instance
        self.engine_params = {
            "engine_type": provider,
            "embedding_model": model_name,
            "base_url": base_url,
            "api_key": api_key
        }
        
        # Initialize EmbeddingAgent
        self.embedding_agent = EmbeddingAgent(engine_params=self.engine_params)
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Generate embeddings for the given text.
        
        Args:
            tool_input: Dictionary containing the text to embed
                        Expected to have 'str_input' key with the text
        
        Returns:
            Embeddings as a JSON string
        """
        text = tool_input.get('str_input', '')
        
        if not text:
            return "Error: No text provided for embedding", [0, 0, 0], ""
        
        try:
            # Get embeddings for the text
            embeddings, total_tokens, cost_string = self.embedding_agent.get_embeddings(text)
            return embeddings, total_tokens, cost_string
                
        except Exception as e:
            logger.error(f"Error during embedding operation: {str(e)}")
            return f"Error: Embedding operation failed: {str(e)}", [0, 0, 0], ""

class QueryFormulatorTool(BaseTool):
    """Tool for formulating queries from tasks or contexts."""
    
    def execute(self, tool_input: Dict[str, Any]):
        """
        Formulate a query for a given task or context.
        
        Args:
            tool_input: Dictionary containing the task or context description
                        Expected to have 'str_input' key with the description
                        May also have 'img_input' key with a screenshot
        
        Returns:
            Formulated query as a string
        """
        task = tool_input.get('str_input', '')
        if not task:
            return "Error: No task or context description provided"
        
        # Use the prompt template and LMM for query formulation
        return self._call_lmm(tool_input)

class Tools:
    """Main Tools class that provides access to all available tools."""
    
    def __init__(self):
        """Initialize the Tools class."""
        self.tools = {}
    
    def register_tool(self, tool_name: str, provider: str, model_name: str, **kwargs):
        """
        Register a tool with the specified parameters.
        
        Args:
            tool_name: Name of the tool to register
            provider: API provider name
            model_name: Model name to use
            **kwargs: Additional parameters to pass to the tool
        """
        tool: BaseTool = ToolFactory.create_tool(tool_name, provider, model_name, **kwargs)
        self.tools[tool_name] = tool
    
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]):
        """
        Execute a tool with the given input.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Input for the tool
        
        Returns:
            The output of the tool as a string
        
        Raises:
            ValueError: If the tool is not registered
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} is not registered")
        
        return self.tools[tool_name].execute(tool_input)

    def reset(self, tool_name: Optional[str] = None):
        """
        Reset tools by resetting their llm_agent if available.
        
        Args:
            tool_name: Optional name of the specific tool to reset. If None, resets all tools.
        """
        if tool_name is not None:
            # Reset a specific tool
            if tool_name not in self.tools:
                raise ValueError(f"Tool {tool_name} is not registered")
            
            tool = self.tools[tool_name]
            if hasattr(tool, 'llm_agent') and tool.llm_agent is not None:
                tool.llm_agent.reset()
        else:
            # Reset all tools
            for tool in self.tools.values():
                # Only reset if the tool has an llm_agent attribute
                if hasattr(tool, 'llm_agent') and tool.llm_agent is not None:
                    tool.llm_agent.reset() 