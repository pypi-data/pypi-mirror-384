import click
import click.shell_completion
from chattool.const import CHATTOOL_CONFIG_DIR,  CHATTOOL_ENV_DIR

# Autocompletion
# environment name completion
class EnvNameCompletionType(click.ParamType):
    name = "envname"
    def shell_complete(self, ctx, param, incomplete):
        return [
            click.shell_completion.CompletionItem(path.stem) for path in CHATTOOL_ENV_DIR.glob(f"{incomplete}*.env")
        ]
# chat file completion
class ChatFileCompletionType(click.ParamType):
    name = "chatfile"
    def shell_complete(self, ctx, param, incomplete):
        return [
            click.shell_completion.CompletionItem(path.stem) for path in CHATTOOL_CONFIG_DIR.glob(f"{incomplete}*.json")
            if not path.name.startswith("_")
        ]