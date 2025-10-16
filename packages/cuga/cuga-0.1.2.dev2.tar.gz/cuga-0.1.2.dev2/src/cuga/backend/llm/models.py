import threading
from datetime import date
from typing import Dict, Any, Optional
import hashlib
import json
import os
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_ibm import ChatWatsonx
from langchain_core.language_models.chat_models import BaseChatModel
from loguru import logger

try:
    from langchain_groq import ChatGroq
except ImportError:
    logger.warning("Langchain Groq not installed, using OpenAI instead")
    ChatGroq = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    logger.warning("Langchain Google GenAI not installed, using OpenAI instead")
    ChatGoogleGenerativeAI = None


class LLMManager:
    """Singleton class to manage LLM instances based on agent name and settings"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._models: Dict[str, Any] = {}
            self._pre_instantiated_model: Optional[BaseChatModel] = None
            self._initialized = True

    def convert_dates_to_strings(self, obj):
        if isinstance(obj, dict):
            return {k: self.convert_dates_to_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_dates_to_strings(item) for item in obj]
        elif isinstance(obj, date):
            return obj.isoformat()
        else:
            return obj

    def set_llm(self, model: BaseChatModel) -> None:
        """Set a pre-instantiated model to use for all tasks

        Args:
            model: Pre-instantiated ChatOpenAI or BaseChatModel instance
        """
        if not isinstance(model, BaseChatModel):
            raise ValueError("Model must be an instance of BaseChatModel or its subclass")

        self._pre_instantiated_model = model
        logger.info(f"Pre-instantiated model set: {type(model).__name__}")

    def _update_model_parameters(
        self, model: BaseChatModel, temperature: float = 0.1, max_tokens: int = 1000
    ) -> BaseChatModel:
        """Update model parameters (temperature and max_tokens) for the task

        Args:
            model: The model to update
            temperature: Temperature setting (default: 0.1)
            max_tokens: Maximum tokens for the task

        Returns:
            Updated model with new parameters
        """
        model_kwargs = {}
        if hasattr(model, 'model_kwargs') and model.model_kwargs is not None:
            model_kwargs = model.model_kwargs.copy()

        # Update temperature
        if hasattr(model, 'temperature'):
            logger.debug(f"Updating model temperature: {temperature}")
            if hasattr(model, 'model_kwargs') and model.model_kwargs is not None:
                logger.debug(f"Model keys: {model.model_kwargs.keys()}")
            logger.debug(f"Model instance: {type(model)}")
            model.temperature = temperature
        elif 'temperature' in model_kwargs:
            model_kwargs['temperature'] = temperature

        # Update max_tokens
        if hasattr(model, 'max_tokens'):
            model.max_tokens = max_tokens
        elif hasattr(model, 'max_completion_tokens'):
            model.max_completion_tokens = max_tokens
        elif 'max_tokens' in model_kwargs:
            model_kwargs['max_tokens'] = max_tokens

        # Update model_kwargs if it exists
        if hasattr(model, 'model_kwargs') and model.model_kwargs is not None:
            model.model_kwargs = model_kwargs

        logger.debug(f"Updated model parameters: temperature={temperature}, max_tokens={max_tokens}")
        return model

    def clear_pre_instantiated_model(self) -> None:
        """Clear the pre-instantiated model and return to normal model creation"""
        self._pre_instantiated_model = None
        logger.info("Pre-instantiated model cleared, returning to normal model creation")

    def _create_cache_key(self, model_settings: Dict[str, Any]) -> str:
        """Create a unique cache key from model settings including resolved values"""
        # Sort settings to ensure consistent hashing
        d = self.convert_dates_to_strings(model_settings.to_dict())
        keys_to_delete = [key for key in d if "prompt" in key]

        for key in keys_to_delete:
            del d[key]

        # Add resolved values to ensure cache key reflects actual configuration
        platform = model_settings.get('platform')
        if platform:
            d['resolved_model_name'] = self._get_model_name(model_settings, platform)
            d['resolved_api_version'] = self._get_api_version(model_settings, platform)
            d['resolved_base_url'] = self._get_base_url(model_settings, platform)

        settings_str = json.dumps(d, sort_keys=True)
        return hashlib.md5(settings_str.encode()).hexdigest()

    def _get_model_name(self, model_settings: Dict[str, Any], platform: str) -> str:
        """Get model name with environment variable override support"""
        # Check if model_name is defined in TOML settings
        toml_model_name = model_settings.get('model_name')

        if platform == "openai":
            # For OpenAI, check environment variables
            env_model_name = os.environ.get('MODEL_NAME')
            if env_model_name:
                logger.info(f"Using MODEL_NAME from environment: {env_model_name}")
                return env_model_name
            elif toml_model_name:
                logger.debug(f"Using model_name from TOML: {toml_model_name}")
                return toml_model_name
            else:
                # Default fallback
                default_model = "gpt-4o"
                logger.info(f"No model_name specified, using default: {default_model}")
                return default_model
        elif platform == "groq":
            # For Groq, check environment variables
            env_model_name = os.environ.get('MODEL_NAME')
            if env_model_name:
                logger.info(f"Using MODEL_NAME from environment for Groq: {env_model_name}")
                return env_model_name
            elif toml_model_name:
                logger.debug(f"Using model_name from TOML: {toml_model_name}")
                return toml_model_name
            else:
                # Default fallback
                default_model = "openai/gpt-oss-20b"
                logger.info(f"No model_name specified, using default: {default_model}")
                return default_model
        elif platform == "watsonx":
            # For WatsonX, check environment variables
            env_model_name = os.environ.get('MODEL_NAME')
            if env_model_name:
                logger.info(f"Using MODEL_NAME from environment for WatsonX: {env_model_name}")
                return env_model_name
            elif toml_model_name:
                logger.debug(f"Using model_name from TOML: {toml_model_name}")
                return toml_model_name
            else:
                # Default fallback for WatsonX
                default_model = "meta-llama/llama-4-maverick-17b-128e-instruct-fp8"
                logger.info(f"No model_name specified for WatsonX, using default: {default_model}")
                return default_model
        elif platform == "azure":
            # For Azure, check environment variables
            env_model_name = os.environ.get('MODEL_NAME')
            if env_model_name:
                logger.info(f"Using MODEL_NAME from environment for Azure: {env_model_name}")
                return env_model_name
            elif toml_model_name:
                logger.debug(f"Using model_name from TOML: {toml_model_name}")
                return toml_model_name
            else:
                # Default fallback for Azure
                default_model = "gpt-4o"
                logger.info(f"No model_name specified for Azure, using default: {default_model}")
                return default_model
        elif platform == "google-genai":
            # For Google GenAI, check environment variables
            env_model_name = os.environ.get('MODEL_NAME')
            if env_model_name:
                logger.info(f"Using MODEL_NAME from environment for Google GenAI: {env_model_name}")
                return env_model_name
            elif toml_model_name:
                logger.debug(f"Using model_name from TOML: {toml_model_name}")
                return toml_model_name
            else:
                # Default fallback for Google GenAI
                default_model = "gemini-1.5-pro"
                logger.info(f"No model_name specified for Google GenAI, using default: {default_model}")
                return default_model
        else:
            # For other platforms, use TOML or default
            if toml_model_name:
                return toml_model_name
            else:
                raise ValueError(f"model_name must be specified for platform: {platform}")

    def _get_api_version(self, model_settings: Dict[str, Any], platform: str) -> str:
        """Get API version with environment variable override support"""
        if platform == "openai":
            # Check environment variable first
            env_api_version = os.environ.get('OPENAI_API_VERSION')
            if env_api_version:
                logger.info(f"Using OPENAI_API_VERSION from environment: {env_api_version}")
                return env_api_version

            # Check TOML settings
            toml_api_version = model_settings.get('api_version')
            if toml_api_version:
                # Validate if it's a date type and transform to string
                if isinstance(toml_api_version, date):
                    toml_api_version = toml_api_version.isoformat()
                    logger.debug(f"Converted date to string: {toml_api_version}")
                logger.debug(f"Using api_version from TOML: {toml_api_version}")
                return toml_api_version

            # Default fallback
            logger.info("No api_version specified, using default: None")
            return None
        else:
            # For other platforms, use TOML or default
            api_version = model_settings.get('api_version', "2024-08-06")
            # Validate if it's a date type and transform to string
            if isinstance(api_version, date):
                api_version = api_version.isoformat()
                logger.debug(f"Converted date to string: {api_version}")
            return api_version

    def _get_base_url(self, model_settings: Dict[str, Any], platform: str) -> str:
        """Get base URL with environment variable override support"""
        if platform == "openai":
            # Check environment variable first
            env_base_url = os.environ.get('OPENAI_BASE_URL')
            if env_base_url:
                logger.info(f"Using OPENAI_BASE_URL from environment: {env_base_url}")
                return env_base_url

            # Check TOML settings (for litellm compatibility)
            toml_url = model_settings.get('url')
            if toml_url:
                logger.debug(f"Using url from TOML: {toml_url}")
                return toml_url

            # Default to None (uses OpenAI's default endpoint)
            logger.debug("No base URL specified, using OpenAI default endpoint")
            return None
        else:
            # For other platforms, use TOML settings
            return model_settings.get('url')

    def _create_llm_instance(self, model_settings: Dict[str, Any]):
        """Create LLM instance based on platform and settings"""
        platform = model_settings.get('platform')
        temperature = model_settings.get('temperature', 0.7)
        max_tokens = model_settings.get('max_tokens', 1000)

        # Handle environment variable overrides
        model_name = self._get_model_name(model_settings, platform)
        api_version = self._get_api_version(model_settings, platform)
        base_url = self._get_base_url(model_settings, platform)

        if platform == "azure":
            api_version = str(model_settings.get('api_version'))
            if model_name == "o3":
                llm = AzureChatOpenAI(
                    model_version=api_version,
                    timeout=61,
                    api_version="2025-04-01-preview",
                    azure_deployment=model_name + "-" + api_version,
                    max_completion_tokens=max_tokens,
                )
            else:
                logger.debug(f"Creating AzureChatOpenAI model: {model_name} - {api_version}")
                llm = AzureChatOpenAI(
                    timeout=61,
                    azure_deployment=model_name + "-" + api_version,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
        elif platform == "openai":
            # Build ChatOpenAI parameters
            openai_params = {
                "model_name": model_name,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": 61,
            }

            # Add API key if specified
            apikey_name = model_settings.get("apikey_name")
            if apikey_name:
                openai_params["openai_api_key"] = os.environ.get(apikey_name)

            # Add base URL if specified
            if base_url:
                openai_params["openai_api_base"] = base_url

            llm = ChatOpenAI(**openai_params)
        elif platform == "groq":
            logger.debug(f"Creating Groq model: {model_name}")
            llm = ChatGroq(
                max_tokens=max_tokens,
                model=model_name,
                temperature=temperature,
            )
        elif platform == "watsonx":
            llm = ChatWatsonx(
                model_id=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                project_id=os.environ['WATSONX_PROJECT_ID'],
            )
        elif platform == "rits":
            llm = ChatOpenAI(
                api_key=os.environ.get(model_settings.get('apikey_name')),
                base_url=model_settings.get('url'),
                max_tokens=max_tokens,
                model=model_name,
                temperature=temperature,
                seed=42,
            )
        elif platform == "rits-restricted":
            llm = ChatOpenAI(
                api_key=os.environ["RITS_API_KEY_RESTRICT"],
                base_url="http://nocodeui.sl.cloud9.ibm.com:4001",
                max_tokens=max_tokens,
                model=model_name,
                top_p=0.95,
                temperature=temperature,
                seed=42,
            )
        elif platform == "google-genai":
            logger.debug(f"Creating Google GenAI model: {model_name}")
            # Build ChatGoogleGenerativeAI parameters

            # Add API key if specified
            # apikey_name = model_settings.get("apikey_name")
            # if apikey_name:
            #     google_params["api_key"] = os.environ.get(apikey_name)

            llm = ChatGoogleGenerativeAI(
                api_key=os.environ.get("GOOGLE_API_kEY"),
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            raise ValueError(f"Unsupported platform: {platform}")

        return llm

    def get_model(self, model_settings: Dict[str, Any], max_tokens: int = 1000):
        """Get or create LLM instance for the given model settings

        Args:
            model_settings: Model configuration dictionary
            max_tokens: Maximum tokens for the task (default: 1000)
        """
        # Check if pre-instantiated model is available
        if self._pre_instantiated_model is not None:
            logger.debug(f"Using pre-instantiated model: {type(self._pre_instantiated_model).__name__}")
            # Update parameters for the task
            updated_model = self._update_model_parameters(
                self._pre_instantiated_model, temperature=0.1, max_tokens=max_tokens
            )
            return updated_model

        # Get resolved values for logging and cache key
        platform = model_settings.get('platform', 'unknown')
        model_name = self._get_model_name(model_settings, platform)
        api_version = self._get_api_version(model_settings, platform)
        base_url = self._get_base_url(model_settings, platform)

        cache_key = self._create_cache_key(model_settings)

        if cache_key in self._models:
            logger.debug(
                f"Returning cached model: {platform}/{model_name} (api_version={api_version}, base_url={base_url})"
            )
            # Update parameters for the task
            cached_model = self._models[cache_key]
            updated_model = self._update_model_parameters(
                cached_model, temperature=0.1, max_tokens=max_tokens
            )
            return updated_model

        # Create new model instance
        logger.debug(
            f"Creating new model: {platform}/{model_name} (api_version={api_version}, base_url={base_url})"
        )
        model = self._create_llm_instance(model_settings)
        self._models[cache_key] = model

        # Update parameters for the task
        updated_model = self._update_model_parameters(model, temperature=0.1, max_tokens=max_tokens)
        return updated_model
