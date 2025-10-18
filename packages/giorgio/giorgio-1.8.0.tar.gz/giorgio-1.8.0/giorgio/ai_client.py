from __future__ import annotations
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from importlib.metadata import distribution
import re
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union
)

import instructor
from openai import OpenAI
from pydantic import BaseModel, create_model, Field
import questionary

from .project_manager import get_project_config


logger = logging.getLogger("giorgio.ai_client")


# Cache for wrapping primitive/composite types into Pydantic models
_MODEL_CACHE: Dict[Any, Type[BaseModel]] = {}


MessageRole = Literal["system", "user", "assistant", "tool"]
T = TypeVar("T")


@dataclass
class AIClientConfig:
    """Configuration settings for the AI backend via Instructor."""
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("AI_API_KEY"))
    base_url: Optional[str] = None
    model: str = "codestral/22b"
    temperature: float = field(default_factory=lambda: float(os.getenv("AI_TEMPERATURE", "0.0")))
    request_timeout: Optional[float] = 60.0
    max_output_tokens: Optional[int] = field(default_factory=lambda: int(os.getenv("AI_MAX_TOKENS", "0")))
    instructor_mode: instructor.Mode = instructor.Mode.JSON
    max_retries: int = 2


@dataclass
class Message:
    """A single chat message with a role and content."""
    role: MessageRole
    content: str


class AIClient(Generic[T]):
    """
    High-level AI client using Instructor + Pydantic for typed prompts.
    """

    def __init__(self, config: AIClientConfig) -> None:
        """
        Initialize the AIClient with configuration and raw OpenAI client.

        :param config: Settings for API key, model, retries, etc.
        :type config: AIClientConfig
        :returns: None
        :rtype: None
        """
        self.config = config

        # Prepare kwargs for low-level OpenAI client
        base_kwargs: Dict[str, Any] = {}
        if config.base_url:
            base_kwargs["base_url"] = config.base_url
        if config.api_key:
            base_kwargs["api_key"] = config.api_key

        # Instantiate the raw OpenAI client
        self._raw_client = OpenAI(**{k: v for k, v in vars(config).items() if k in ("api_key", "base_url") and v})

        # Wrap raw client with Instructor to enforce JSON schema & retries
        self.client = instructor.from_openai(
            self._raw_client,
            mode=config.instructor_mode,
        )
        logger.debug(
            "AIClient initialized (model=%s, base_url=%s, retries=%d)",
            config.model,
            config.base_url or "default",
            config.max_retries,
        )

        # Initialize per-call state
        self._messages: List[Message] = []
        self._response_model: Optional[Type[BaseModel]] = None
        self._wrapped_value = False

    def _wrap_primitive_in_model(self, py_type: Any) -> Type[BaseModel]:
        """
        Build and cache a Pydantic model wrapping a primitive or typing type.

        :param py_type: A Python builtin or typing hint to wrap.
        :type py_type: Any
        :returns: A Pydantic model class with a single `value` field.
        :rtype: Type[BaseModel]
        """
        if py_type in _MODEL_CACHE:
            return _MODEL_CACHE[py_type]

        model = create_model(
            "Value",
            value=(py_type, Field(..., description="Return the result in this field named 'value'")),
            __base__=BaseModel,
        )

        _MODEL_CACHE[py_type] = model
        logger.debug("Cached Pydantic wrapper for %s", py_type)
        
        return model


    def _resolve_response_model(self, target: Union[Type[T], Any]) -> Tuple[Type[BaseModel], bool]:
        """
        Select or wrap a response type into a Pydantic model for validation.

        :param target: Either a BaseModel subclass or a Python/typing hint.
        :type target: Union[Type[T], Any]
        :returns: The model to use and a flag indicating whether it was wrapped.
        :rtype: Tuple[Type[BaseModel], bool]
        """
        is_model = isinstance(target, type) and issubclass(target, BaseModel)
        if is_model:
            logger.debug("Using provided response model %s", target.__name__)
            return target, False  # already a Pydantic model

        wrapped = self._wrap_primitive_in_model(target)
        logger.debug("Wrapped response type %s into Pydantic model", target)

        return wrapped, True

    @property
    def messages(self) -> List[Dict[str, str]]:
        """
        Returns the list of message dicts for the AI API, merging all system
        messages into one at the beginning.
        """
        system_msgs = [m.content for m in self._messages if m.role == "system"]
        merged_system = None
        
        if system_msgs:
            merged_system = {"role": "system", "content": "\n\n".join(system_msgs)}
        
        other_msgs = [
            {"role": m.role, "content": m.content}
            for m in self._messages
            if m.role != "system"
        ]
        
        result = []
        
        if merged_system:
            result.append(merged_system)
        
        result.extend(other_msgs)
        return result

    def with_instructions(self, text: str) -> "AIClient[T]":
        """
        Add system instructions guiding the AI’s overall behavior.

        :param text: Instructional text to prepend as a system message.
        :type text: str
        :returns: Self, for method chaining.
        :rtype: AIClient[T]
        """
        self._messages.append(Message(role="system", content=text))
        logger.debug("Added system instructions (%d chars)", len(text))

        return self

    def with_example(self, example: str) -> "AIClient[T]":
        """
        Include an example user→assistant exchange to shape formatting.

        :param example: An example assistant output.
        :type example: str
        :returns: Self, for method chaining.
        :rtype: AIClient[T]
        """
        self._messages.append(Message(role="user", content="Show me an example"))
        self._messages.append(Message(role="assistant", content=example))
        logger.debug("Appended example interaction (%d chars)", len(example))

        return self

    def with_doc(
        self,
        name: str,
        content: str
    ) -> "AIClient[T]":
        """
        Attach a named context document to the prompt as a user–assistant message pair.

        :param name: Identifier for the document (e.g., "README").
        :type name: str
        :param content: Raw text of the document.
        :type content: str
        :returns: Self, for method chaining.
        :rtype: AIClient[T]
        """
        user_msg = f"Context document [{name}]:\n{content}"
        assistant_msg = f"Document '{name}' received and understood."

        self._messages.append(Message(role="user", content=user_msg))
        self._messages.append(Message(role="assistant", content=assistant_msg))
        logger.debug("Attached context document '%s' (%d chars)", name, len(content))

        return self

    def with_schema(self, type_hint: Union[Type[T], Any], json_only: bool = True) -> "AIClient[T]":
        """
        Define the expected response schema or native type.

        :param type_hint: A BaseModel subclass or typing hint.
        :type type_hint: Union[Type[T], Any]
        :param json_only: If True, enforce pure JSON output.
        :type json_only: bool
        :returns: Self, for method chaining.
        :rtype: AIClient[T]
        """
        model, wrapped = self._resolve_response_model(type_hint)
        self._response_model, self._wrapped_value = model, wrapped

        fmt = (
            "You MUST return ONLY valid JSON. No text outside the JSON."
            if json_only
            else "Your output MUST strictly conform to the expected schema."
        )

        user_msg = f"Output constraint:\n{fmt}"
        assistant_msg = "Output constraint received and understood."

        self._messages.append(Message(role="user", content=user_msg))
        self._messages.append(Message(role="assistant", content=assistant_msg))
        logger.debug("Declared output schema %s (json_only=%s)", model.__name__, json_only)

        return self

    def ask(self, prompt: str) -> T:
        """
        Send the prompt to the AI, enforce schema, and return a typed result.

        :param prompt: The final user input to append before calling the API.
        :type prompt: str
        :returns: The validated and typed response.
        :rtype: T
        """
        if self._response_model is None:
            self._response_model, self._wrapped_value = self._wrap_primitive_in_model(str), True

        self._messages.append(Message(role="user", content=prompt))
        logger.info("Requesting AI completion with %d messages", len(self._messages))

        # Perform chat completion with schema enforcement and retries
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=self.messages,
            temperature=self.config.temperature,
            response_model=self._response_model,
            max_retries=self.config.max_retries,
        )

        message = response.value if self._wrapped_value else response  # type: ignore
        self._messages.append(Message(role="assistant", content=message))
        logger.debug("Received structured AI response (%d chars)", len(str(message)))

        return message

    def ask_raw(self, prompt: str) -> str:
        """
        Send the prompt to the AI and return raw assistant text (no JSON).

        :param prompt: The user prompt to send.
        :type prompt: str
        :returns: The raw assistant response.
        :rtype: str
        """
        self._messages.append(Message(role="user", content=prompt))
        logger.info("Requesting raw AI completion with %d messages", len(self._messages))
        
        # Perform chat completion without schema enforcement
        response = self._raw_client.chat.completions.create(
            model=self.config.model,
            messages=self.messages,
            temperature=self.config.temperature,
            timeout=self.config.request_timeout,
        )

        message = response.choices[0].message.content  # type: ignore
        self._messages.append(Message(role="assistant", content=message))
        logger.debug("Received raw AI response (%d chars)", len(message or ""))
        
        return message

    def reset(self) -> None:
        """
        Clear accumulated messages and schema settings for a fresh session.

        :returns: None
        :rtype: None
        """
        self._messages.clear()
        self._response_model = None
        self._wrapped_value = False
    logger.debug("AIClient state reset")


class AIScriptingClient:
    """
    Minimal client to generate Python automation scripts based on project
    context and AI instructions.
    """

    role_description = """Your role

You are a seasoned Python developer, attentive to best practices and coding standards—especially PEP 8.
Your code (in English only) must be:
  - Readable and well-documented (with docstrings where appropriate)
  - Modular, following DRY, KISS, and SRP principles
  - Structured according to Giorgio’s CONFIG/PARAMS/run pattern
"""

    mission_description = """Your mission

You have to write a script using the Giorgio library.
- Your output MUST strictly follow the structure and standards shown in the script_template.py example and the README documentation.
- Use the script_template.py as a skeleton for your output.
- Do NOT output anything except the code itself, and do NOT add any extra text, comments, or explanations outside the code.
- Do NOT wrap the code in any additional formatting (e.g., triple quotes, code blocks).
- The script must include CONFIG, PARAMS, and a run(context) function as shown in the template.
"""

    def __init__(self, project_root: Union[str, Path]):
        """
        Initialize the scripting client using AI config from environment variables.

        :param project_root: Root directory of the project.
        :type project_root: Union[str, Path]
        :returns: None
        :rtype: None
        :raises RuntimeError: If required AI config env vars are missing.
        """
        logger.debug("Initializing AIScriptingClient for project root %s", project_root)
        project_root = Path(project_root)

        env_file = project_root / ".env"

        if env_file.exists():
            try:
                from dotenv import load_dotenv

            except ImportError:
                logger.error("python-dotenv is required to load AI config from %s", env_file)
                raise RuntimeError("python-dotenv is required to load .env files.")

            load_dotenv(dotenv_path=str(env_file), override=False)
            logger.info("Loaded AI environment configuration from %s", env_file)

        # Read AI config from environment variables
        api_key = os.getenv("AI_API_KEY")
        api_url = os.getenv("AI_BASE_URL")
        model = os.getenv("AI_MODEL") or os.getenv("AI_API_MODEL")  # fallback for legacy env var
        temperature = float(os.getenv("AI_TEMPERATURE", "0.0"))
        max_tokens_env = os.getenv("AI_MAX_TOKENS")
        max_output_tokens = int(max_tokens_env) if max_tokens_env is not None else None

        if not (api_key and api_url and model):
            raise RuntimeError(
                "Missing AI config: set AI_API_KEY, AI_BASE_URL, and AI_MODEL in your environment or .env file."
            )

        cfg = AIClientConfig(
            api_key=api_key,
            base_url=api_url,
            model=model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        self.ai_client = AIClient(cfg)
        self.project_root = project_root
        logger.debug(
            "AIScriptingClient configured (model=%s, base_url=%s, max_tokens=%s)",
            model,
            api_url,
            max_output_tokens,
        )
    
    def _get_modules_content(self) -> List[Tuple[str, str]]:
        """
        Get Python modules content from the project's configured module paths.

        :returns: A list of tuples containing module names and their corresponding code.
        :rtype: List[Tuple[str, str]]
        """
        config = get_project_config(self.project_root)
        module_paths: List[str] = config.get("module_paths", ["modules"])

        modules: List[Tuple[str, str]] = []
        for module_dir in module_paths:
            abs_dir = (self.project_root / module_dir).resolve()
            if abs_dir.exists() and abs_dir.is_dir():
                for py_file in abs_dir.rglob("*.py"):
                    try:
                        rel_path = py_file.relative_to(self.project_root)
                    except ValueError:
                        rel_path = py_file

                    content = py_file.read_text(encoding="utf-8").strip()
                    
                    if py_file.name == "__init__.py":
                        if not content:
                            continue  # skip empty __init__.py
                        # Use parent folder as module path
                        python_path = ".".join(rel_path.parent.parts)
                    
                    else:
                        python_path = ".".join(rel_path.with_suffix("").parts)
                    
                    modules.append((python_path, content))

        logger.debug("Loaded %d modules for AI context", len(modules))
        return modules

    def _select_modules(self) -> List[Tuple[str, str]]:
        """
        Prompt the user to select modules from a list.

        :returns: List of selected module contents.
        :rtype: List[Tuple[str, str]]
        """
        modules = self._get_modules_content()
        if not modules:
            logger.debug("No modules available for AI context selection")
            return []

        choices = [
            questionary.Choice(title=name, value=(name, content))
            for name, content in modules
        ]

        selected = questionary.checkbox(
            "Select modules to include as context documents:",
            choices=choices,
        ).ask() or []

        logger.debug("Selected %d modules for AI context", len(selected))
        return selected

    def _get_script_template_content(self) -> str:
        """
        Get the content of the script template file.

        :returns: The content of the template file.
        :rtype: str
        """
        template_path = Path(__file__).parent / "templates" / "script_template.py"
        content = template_path.read_text().strip()
        logger.debug("Loaded script template from %s", template_path)
        return content
    
    def _get_scripts_content(self) -> List[Tuple[str, str]]:
        """
        Get Python scripts content from the project's scripts directory.

        :returns: A list of tuples containing script names and their corresponding code.
        :rtype: List[Tuple[str, str]]
        """
        scripts_dir = self.project_root / "scripts"
        scripts: List[Tuple[str, str]] = []

        if scripts_dir.exists() and scripts_dir.is_dir():
            for script_file in scripts_dir.rglob("script.py"):
                try:
                    rel_path = script_file.relative_to(self.project_root)
                except ValueError:
                    rel_path = script_file

                content = script_file.read_text(encoding="utf-8").strip()
                script_name = str(rel_path.parent.with_suffix(""))
                scripts.append((script_name, content))

        logger.debug("Loaded %d existing scripts for examples", len(scripts))
        return scripts

    def _select_scripts(self) -> List[str]:
        """
        Prompt the user to select scripts from a list.

        :returns: List of selected script contents.
        :rtype: List[str]
        """
        scripts = self._get_scripts_content()
        if not scripts:
            logger.debug("No existing scripts available for AI examples")
            return []

        choices = [
            questionary.Choice(title=name, value=content)
            for name, content in scripts
        ]

        selected = questionary.checkbox(
            "Select existing scripts to include as examples:",
            choices=choices,
        ).ask() or []

        logger.debug("Selected %d scripts as AI examples", len(selected))
        return selected

    def _find_readme(self) -> Path:
        """
        Find the README.md file in the package distribution or fallback to the
        parent directory or project root.
        """
        try:
            dist = distribution("giorgio")
            for f in dist.files or []:
                if f.name == "README.md" and "share/doc/giorgio" in str(f).replace("\\", "/"):
                    path = Path(dist.locate_file(f))
                    logger.debug("Found README via installed distribution at %s", path)
                    return path
        except Exception as exc:
            logger.debug("Could not locate README in installed distribution: %s", exc)

        # Try parent directory of this file
        p = Path(__file__).resolve().parents[1] / "README.md"
        if p.is_file():
            logger.debug("Found README alongside package at %s", p)
            return p

        # Fallback: try project root (self.project_root/README.md)
        project_readme = getattr(self, "project_root", None)
        if project_readme:
            project_readme = Path(project_readme) / "README.md"
            if project_readme.is_file():
                logger.debug("Found README in project root at %s", project_readme)
                return project_readme

        raise FileNotFoundError("README.md not found.")

    def _get_script_anatomy_content(self) -> str:
        """
        Get the project's README.md script anatomy section for context.
        Only extract the section between <!-- BEGIN GIORGIO_SCRIPT_ANATOMY -->
        and <!-- END GIORGIO_SCRIPT_ANATOMY -->.

        :returns: The content of the script anatomy section in README.md.
        :rtype: str
        :raises FileNotFoundError: If README.md does not exist.
        """
        content = self._find_readme().read_text().strip()

        start = "<!-- BEGIN GIORGIO_SCRIPT_ANATOMY -->"
        end = "<!-- END GIORGIO_SCRIPT_ANATOMY -->"
        start_idx = content.find(start)
        end_idx = content.find(end)
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            section = content[start_idx + len(start):end_idx].strip()
            logger.debug("Extracted script anatomy section from README (%d chars)", len(section))
            return section
        
        logger.debug("Using full README content as anatomy fallback (%d chars)", len(content))
        return content

    def _unwrap_script(self, response: str) -> str:
        """
        Extract the Python script from a possibly wrapped response.
        If markdown code fences exist, return only the text inside them.
        Otherwise, return the response as-is.
        """
        script = response.strip()
        code_fence_pattern = r"```(?:python)?\s*([\s\S]*?)\s*```"
        match = re.search(code_fence_pattern, script, re.IGNORECASE)
        
        if match:
            unwrapped = match.group(1).strip()
            logger.debug("Unwrapped script from markdown fences (%d chars)", len(unwrapped))
            return unwrapped
        
        logger.debug("AI response contained no fences; using raw script (%d chars)", len(script))
        return script

    def generate_script(self, instructions: str) -> str:
        """
        Generate a Python automation script based on instructions and context.

        :param instructions: User-provided instructions for the script.
        :type instructions: str
        :returns: Generated Python script.
        :rtype: str
        """
        self.ai_client.reset()
        logger.info("Generating script with AI instructions (%d chars)", len(instructions))

        # Build prompt
        client = self.ai_client
        client.reset()
        client.with_instructions(
            f"""{self.role_description.strip()}\n\n{self.mission_description.strip()}"""
        )
        client.with_doc("Giorgio README", self._get_script_anatomy_content())

        # Add selected modules as context documents
        selected_modules = self._select_modules()
        for mod_name, mod_content in selected_modules:
            client.with_doc(f"Module: {mod_name}", mod_content)

        # Add selected scripts as examples (or the template if none)
        exemples = self._select_scripts()
        if not exemples:
            exemples.append(self._get_script_template_content())
        for exemple in exemples:
            client.with_example(exemple)

        # Ask for the script
        script = client.ask(instructions)
        script = self._unwrap_script(script)
        logger.info("AI script generation completed (%d chars)", len(script))

        return script
