r"""
 ___           _
| _ \__ _ _  _| |___  ___ _ __
|  _/ _` | || | / _ \/ _ \ '_ \
|_| \__,_|\_, |_\___/\___/ .__/
          |__/           |_|AI             07312025 / optimus codex
"""

from payloop._config import Config
from payloop._network import Api
from payloop.api._invocation import Invocation


class Workflow(Api):
    def __init__(self, config: Config):
        super().__init__(config)

        self.invocation = Invocation(config)

    def update(self, uuid, label=None):
        return self.patch(f"workflow/{uuid}", {"label": label})


class Workflows(Api):
    def list(self):
        return self.get("workflows")
