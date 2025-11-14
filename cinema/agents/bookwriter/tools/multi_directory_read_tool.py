import os
from typing import Any, List

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class FixedDirectoryReadToolSchema(BaseModel):
    """Input for DirectoryReadTool."""


class DirectoryReadToolSchema(BaseModel):
    """Input for DirectoryReadTool."""

    directories: List[str] = Field(..., description="Mandatory list of directories to list content. Can be single element array")


class MultiDirectoryReadTool(BaseTool):
    name: str = "List files in multiple directories"
    description: str = (
        "A tool that can be used to recursively list multiple directories content."
    )
    args_schema: type[BaseModel] = DirectoryReadToolSchema
    directories: List[str] | None = None

    def __init__(self, directories: List[str] | None = None, **kwargs):
        super().__init__(**kwargs)
        if directories is not None:
            self.directories = directories
            self.description = f"A tool that can be used to list contents of directories: {','.join(directories)}."
            self.args_schema = FixedDirectoryReadToolSchema
            self._generate_description()

    def _run_each(
        self,
        **kwargs: Any,
    ) -> Any:
        directory: str | None = kwargs.get("directory", None)
        if directory is None:
            raise ValueError("Directory must be provided.")

        if directory[-1] == "/":
            directory = directory[:-1]

        files_list = [
            f"{directory}/{(os.path.join(root, filename).replace(directory, '').lstrip(os.path.sep))}"
            for root, dirs, files in os.walk(directory)
            for filename in files
        ]
        files = "\n- ".join(files_list)
        return files

    def _run(
        self,
        **kwargs: Any,
    ) -> Any:
        directories: List[str] | None = kwargs.get("directories", self.directories)
        if directories is None:
            raise ValueError("Directory must be provided.")

        files = "\n".join([ self._run_each(directory=dir) for dir in directories ])
        return f"File paths: \n{files}"
