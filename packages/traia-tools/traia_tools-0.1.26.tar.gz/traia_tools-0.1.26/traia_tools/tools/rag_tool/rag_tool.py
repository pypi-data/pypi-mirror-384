from abc import ABC, abstractmethod
from typing import Any
from embedchain import App

from crewai.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Adapter(BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abstractmethod
    def query(self, question: str) -> str:
        """Query the knowledge base with a question and return the answer."""

    @abstractmethod
    def add(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Add content to the knowledge base."""

class EmbedchainAdapter(Adapter):
    embedchain_app: App
    summarize: bool = False

    def query(self, question: str) -> str:
        result, sources = self.embedchain_app.query(
            question, citations=True, dry_run=(not self.summarize)
        )
        if self.summarize:
            return result
        return "\n\n".join([source[0] for source in sources])

    def add(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.embedchain_app.add(*args, **kwargs)

class RagTool(BaseTool):
    class _AdapterPlaceholder(Adapter):
        def query(self, question: str) -> str:
            raise NotImplementedError

        def add(self, *args: Any, **kwargs: Any) -> None:
            raise NotImplementedError

    name: str = "Knowledge base"
    description: str = "A knowledge base that can be used to answer questions."
    summarize: bool = False
    adapter: Adapter = Field(default_factory=_AdapterPlaceholder)
    config: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _set_default_adapter(self):
        if isinstance(self.adapter, RagTool._AdapterPlaceholder):
            from embedchain import App
           
            app = App.from_config(config=self.config) if self.config else App()
            self.adapter = EmbedchainAdapter(
                embedchain_app=app, summarize=self.summarize
            )

        return self

    def add(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.adapter.add(*args, **kwargs)

    def _run(
        self,
        query: str,
        **kwargs: Any,
    ) -> Any:
        self._before_run(query, **kwargs)

        return f"Relevant Content:\n{self.adapter.query(query)}"

    def _before_run(self, query, **kwargs):
        pass


if __name__ == "__main__":
    # Test the tool
    tool = RagTool()
    tool.add("This is a test document about Bitcoin.")
    result = tool.run("What is Bitcoin?")
    print(result) 