from shell import ShellExecutor
from tools.Tools import Tools


class BashTools(Tools):
    def __init__(self):
        self.name = "Bash"
        self.description = "Run shell command"
        self.input_schema = {
          "type": "object",
          "properties": {
              "command": {
                  "type": "string",
                  "description": "shell command",
              }
          },
          "required": ["command"],
      }
        self.execute = self.runshell
        self.is_readonly = self.checkReadOnlyConstraints


    async def runshell(self,cmd,shell:ShellExecutor) -> str:

        shell_result = await shell.exec(cmd)
        print(shell_result)
        return shell_result.stdout

    def checkReadOnlyConstraints(self,cmd) -> bool:
        return False

