from enum import Enum


class RunCommandHerokuTaskParamsTaskType(str, Enum):
    RUN_COMMAND_HEROKU = "run_command_heroku"

    def __str__(self) -> str:
        return str(self.value)
