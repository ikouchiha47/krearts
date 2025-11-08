from typing import Generic, List, Optional, TypeVar

IT = TypeVar("IT")
OT = TypeVar("OT")
NewOT = TypeVar("NewOT")


class Runner(Generic[IT, OT]):
    async def run(self, inputs: IT) -> OT: ...


class Pipeline(Generic[IT, OT]):
    """
    Pipeline accepts an input
    And transforms to an output

    There can be intermediate steps
    in between

    Ex:
    int -> str -> float -> bool
    signified: Pipeline[int, bool]
    """

    steps: List[Runner]

    def __init__(self, steps: Optional[List[Runner]] = None):
        if not steps:
            steps = []

        self.steps = steps

    def then(self, step: Runner[OT, NewOT]):
        """
        Runner accepts the prev step output,
        and returns new output
        """
        steps = self.steps + [step]
        return Pipeline[IT, NewOT](steps)

    async def execute(self, inputs: IT) -> OT:
        final = inputs

        for step in self.steps:
            output = await step.run(final)
            final = output

        return final

    async def run(self, inputs: IT) -> OT:
        """Make Pipeline compatible with Runner interface"""

        return await self.execute(inputs)
