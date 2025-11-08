from dataclasses import dataclass

from cinema.registry import LLMStore


@dataclass
class DirectorsContext:
    llmstore: LLMStore
    script_count: int = 3
    scene_count: int = 3
    debug: bool = False
