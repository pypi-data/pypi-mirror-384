from c2d.config import Bag


class Packaging:
    def __init__(
        self, jobname: str, framework: str, simulator: str, custom: Bag = None
    ):
        if isinstance(framework, str) and framework.lower() == "none":
            framework = None

        # We will assume following our convention of framework:version
        # and our catch statement will alow None to go through, as well as
        # anything else that copava accepts but does not follow the convention.
        # Will most likely need coming back to
        try:
            self.framework, self.framework_version = framework.split(":", 1)
        except (AttributeError, ValueError):
            self.framework, self.framework_version = framework, None

        self.is_ros = self.__check_ros()
        self.simulator = simulator
        self.custom = custom

    def __check_ros(self):
        if self.framework is not None and "ros" in self.framework:
            return True
        else:
            return False

    def fix_pathing(self, commands: list) -> list:
        cleaned_commands = []
        for command in commands:
            # the space after ". " is necessary to avoid matching "./"
            if command.startswith(("source", ". ")):
                # The project will always be copied into "/ws/src", and so any pathing should not escape this space.
                # Paths should be relative to the project root, so clean up any prepending "/". Just sourcing for now.
                path = command.split(" ")[1].lstrip("/")
                cleaned_commands.append(f"source /ws/src/{path}")
            else:
                # Let it pass through, but need to think about what to allow
                cleaned_commands.append(command)

        return cleaned_commands

    def get_workdir(self) -> str:
        if self.is_ros:
            return "/ws"
        return "/ws/src"
