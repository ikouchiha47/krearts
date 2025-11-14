from dataclasses import dataclass

from cinema.registry import LLMStore


@dataclass
class DirectorsContext:
    llmstore: LLMStore
    debug: bool = False
