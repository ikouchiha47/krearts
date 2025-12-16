import asyncio
from typing import Any, Type, TypeVar, Optional, List, Dict

from crewai.utilities.types import LLMMessage
from pydantic import BaseModel
from crewai.llm import LLM


T = TypeVar("T", bound=BaseModel)


class GenericLLMExecutor:
    """
    Generic, framework-agnostic LLM executor.

    - No Crew concepts
    - No fixed output model
    - Output can be ANY BaseModel subclass
    - Sync LLM call, async-safe wrapper
    - Optional observability hook
    """

    def __init__(
        self,
        *,
        model: str,
        temperature: float = 0.0,
        observability: Optional[Any] = None,
        name: str = "llm_generation",
    ):
        self.model = model
        self.temperature = temperature
        self.observability = observability
        self.name = name

    # -----------------------------
    # Prompt construction
    # -----------------------------

    def build_system_prompt(
        self,
        *,
        role: str,
        goal: str,
        backstory: Optional[str] = None,
        expected_output: Optional[str] = None,
    ) -> str:
        parts = [f"You are {role}."]

        if backstory:
            parts.append(backstory)

        parts.append(f"Your goal is: {goal}")

        if expected_output:
            parts.append(f"Your final answer must be: {expected_output}")

        return "\n".join(parts)

    # -----------------------------
    # Core sync LLM call
    # -----------------------------

    def _call_llm_sync(
        self,
        *,
        messages: List[LLMMessage],
        output_model: Type[T],
    ) -> T:
        llm = LLM(
            model=self.model,
            temperature=self.temperature,
            response_format=output_model,
        )

        raw = llm.call(messages)
        return output_model.model_validate_json(raw)

    # -----------------------------
    # Async public API
    # -----------------------------

    async def kickoff_async(
        self,
        *,
        role: str,
        goal: str,
        user_input: str,
        output_model: Type[T],
        backstory: Optional[str] = None,
        expected_output: Optional[str] = None,
        extra_messages: Optional[List[LLMMessage]] = None,
    ) -> T:
        system_prompt = self.build_system_prompt(
            role=role,
            goal=goal,
            backstory=backstory,
            expected_output=expected_output,
        )

        messages: List[LLMMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        if extra_messages:
            messages.extend(extra_messages)

        return await asyncio.to_thread(
            self._call_llm_sync,
            messages=messages,
            output_model=output_model,
        )
