from typing import List, Optional, Type

from crewai import Agent, Crew, CrewOutput, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase
from pydantic import BaseModel

from cinema.context import DirectorsContext
from cinema.models import SubScenes
from cinema.registry import LLMLongPlannerIntent


@CrewBase
class SceneSplitterWithCuts:
    agents_config = "agents.yaml"
    tasks_config = "tasks.yaml"

    agents: List[BaseAgent] = []
    tasks: List[Task] = []

    _ctx: Optional[DirectorsContext] = None

    def __init__(self, ctx):
        self._ctx = ctx

    def _validate_ctx(self):
        assert self._ctx is not None, "EmptyCtx"

    def bootstrap(self):
        assert self._ctx is not None

        agent = Agent(
            config=self.agents_config["cinematographer"],  # type: ignore[index],
            llm=self._ctx.llmstore.load(LLMLongPlannerIntent),
            verbose=self._ctx.debug,
        )

        task = Task(
            config=self.tasks_config["subscene_builder"],  # type: ignore[index]
            agent=agent,
            output_pydantic=SubScenes,
        )

        self.agents.append(agent)
        self.tasks.append(task)

    def crew(self):
        self.bootstrap()

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
        )

    @classmethod
    def collect(
        cls,
        result: CrewOutput,
        output_model: Type[BaseModel],
    ) -> BaseModel | None:

        # print("lololololol", result.tasks_output)
        return output_model.model_validate(result.pydantic)
