from typing import List

from crewai import Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tools import BaseTool
from pydantic import BaseModel


class MediaLib(BaseModel):
    image_urls: list[str] = []
    characters: list[str] = []

    def images(self):
        return [
            *self.image_urls,
            *self.characters,
        ]


class CrewConfig(BaseModel):
    agents: List[BaseAgent] = []
    tasks: List[Task] = []

    tools: List[BaseTool] = []
