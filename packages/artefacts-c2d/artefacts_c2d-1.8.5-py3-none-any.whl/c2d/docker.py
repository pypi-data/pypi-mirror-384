from collections import namedtuple
from typing import Optional

DockerLine = namedtuple(
    "DockerLine",
    [
        "cmd",
        "value",
    ],
)


class WarpBase:
    def __init__(self, job_name: Optional[str] = None, default_commands: bool = False):
        """
        Base image and instrumentation.

        At this point, just a base image.
        """
        self.job_name = job_name
        if default_commands:
            self.commands = [
                DockerLine(
                    cmd="from",
                    value="ubuntu:focal",
                ),
                DockerLine(cmd="cmd", value=["echo", "todo"]),
            ]
            self.base_os = "ubuntu:focal"
        else:
            self.commands = []
            self.base_os = None

    def __eq__(self, alter):
        return (
            alter.job_name == self.job_name
            and len(alter.commands) == len(self.commands)
            and all(
                [
                    alter.commands[i] == self.commands[i]
                    for i in range(len(self.commands))
                ]
            )
        )

    def __ne__(self, alter):
        return not self.__eq__(alter)

    def __repr__(self):
        pieces = []
        current = None
        for cmd in self.commands:
            if current is None or cmd.cmd != current:
                if current is not None:
                    pieces.append("")
                current = cmd.cmd
            if current == "cmd":
                value = str(cmd.value).replace("'", '"')
            else:
                value = cmd.value
            pieces.append(f"{cmd.cmd.upper()} {value}")
        return "\n".join(pieces)

    def clear(self):
        self.commands = []

    def add(self, cmd: str, value: str):
        if "from" in cmd.lower():
            self.base_os = value
        self.commands.append(DockerLine(cmd=cmd, value=value))

    def dump(self, path: str) -> None:
        with open(path, "w") as f:
            content = self.__repr__()
            f.write(content)
