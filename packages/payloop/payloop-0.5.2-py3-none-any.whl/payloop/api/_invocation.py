r"""
 ___           _
| _ \__ _ _  _| |___  ___ _ __
|  _/ _` | || | / _ \/ _ \ '_ \
|_| \__,_|\_, |_\___/\___/ .__/
          |__/           |_|AI             07312025 / optimus codex
"""

from payloop._config import Config
from payloop._network import Api


class Invocation(Api):
    def __init__(self, config: Config):
        super().__init__(config)

        self.__attribution = {"parent": None, "subsidiary": None}

    def attribution(
        self, parent_id, parent_name=None, subsidiary_id=None, subsidiary_name=None
    ):
        self.__attribution = {
            "parent": {"id": parent_id, "name": parent_name},
            "subsidiary": {"id": subsidiary_id, "name": subsidiary_name},
        }

        return self

    def summary(self, uuid, date_start, date_end=None):
        return self.post(
            f"workflow/{uuid}/invocation/summary",
            json={
                "attribution": self.__attribution,
                "date": {
                    "end": str(date_end) if date_end is not None else None,
                    "start": str(date_start),
                },
            },
        )
