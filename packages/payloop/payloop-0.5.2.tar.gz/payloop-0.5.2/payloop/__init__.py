r"""
 ___           _
| _ \__ _ _  _| |___  ___ _ __
|  _/ _` | || | / _ \/ _ \ '_ \
|_| \__,_|\_, |_\___/\___/ .__/
          |__/           |_|AI             07312025 / optimus codex
"""

import os
from uuid import uuid4

from payloop._config import Config
from payloop._providers import Anthropic as LlmProviderAnthropic
from payloop._providers import Google as LlmProviderGoogle
from payloop._providers import LangChain as LlmProviderLangChain
from payloop._providers import OpenAi as LlmProviderOpenAi
from payloop._providers import PydanticAi as LlmProviderPydanticAi
from payloop.api._workflow import Workflow, Workflows

__all__ = ["Payloop"]


class Payloop:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.environ.get("PAYLOOP_API_KEY", None)

        if api_key is None:
            raise RuntimeError(
                "API key is missing. Either set the PAYLOOP_API_KEY environment "
                + "variable or set the api_key parameter when instantiating Payloop."
            )

        self.config = Config()
        self.config.api_key = api_key
        self.config.tx_uuid = uuid4()

        self.anthropic = LlmProviderAnthropic(self)
        self.google = LlmProviderGoogle(self)
        self.langchain = LlmProviderLangChain(self)
        self.openai = LlmProviderOpenAi(self)
        self.pydantic_ai = LlmProviderPydanticAi(self)

        self.workflow = Workflow(self.config)
        self.workflows = Workflows(self.config)

    def attribution(
        self,
        parent_id=None,
        parent_name=None,
        subsidiary_id=None,
        subsidiary_name=None,
        # -- Deprecated parameters! They are here for backwards compatibility only.
        parent_uuid=None,
        subsidiary_uuid=None,
    ):
        if parent_id is None:
            raise RuntimeError("a string parent_id is required")

        parent_id = str(parent_id)

        if len(parent_id) > 100:
            raise RuntimeError("parent_id cannot be greater than 100 characters")

        if parent_name is not None and len(parent_name) > 100:
            raise RuntimeError("parent_name cannot be greater than 100 characters")

        if subsidiary_name is not None and subsidiary_id is None:
            raise RuntimeError(
                "a string subsidiary_id is required if a subsidiary_name is provided"
            )

        if subsidiary_id is not None:
            subsidiary_id = str(subsidiary_id)

            if len(subsidiary_id) > 100:
                raise RuntimeError(
                    "subsidiary_id cannot be greater than 100 characters"
                )

        if subsidiary_name is not None and len(subsidiary_name) > 100:
            raise RuntimeError("subsidiary_name cannot be greater than 100 characters")

        subsidiary = None
        if subsidiary_id is not None:
            subsidiary = {"id": subsidiary_id, "name": subsidiary_name}

        self.config.attribution = {
            "parent": {"id": parent_id, "name": parent_name},
            "subsidiary": subsidiary,
        }

        return self

    def new_transaction(self):
        self.config.tx_uuid = uuid4()
        return self
