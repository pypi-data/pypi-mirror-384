import logging
from typing import Dict, Union

from c2d.config import Config
from c2d.docker import WarpBase
from c2d.packaging import Packaging
from c2d import commands


logging.basicConfig()
logging.getLogger().setLevel("INFO")


class Converter:
    def __init__(self):
        pass

    def process(
        self, configo: Union[str, Dict], as_text: bool = True
    ) -> Dict[str, Config]:
        """
        Build a dictionary of Dockerfile strings.

        Each key is a job name found in the configuration argument,
          and the value is the Warp Dockerfile for this job,
          as a Config object.
        """

        # TODO Move to Copava, as there is duplication and we want Copava to be the reference.
        #      Already a problem: runtime block is not optional, yet the Config here does
        #      not know it. Copava does.
        config = Config(configo)
        dockerfiles = {}
        if "jobs" in config.map:
            for name, job in config.jobs:
                result = self._process_one(name, job)
                if as_text:
                    dockerfiles[name] = str(result)
                else:
                    dockerfiles[name] = result
        else:
            # Assuming processing for a single job
            name = list(config.map.keys())[0]
            result = WarpBase(job_name=name)
            job = getattr(config, name)
            result = self._process_one(name, job)
            if as_text:
                dockerfiles[name] = str(result)
            else:
                dockerfiles[name] = result
        return dockerfiles

    def _process_one(self, name: str, specs: Config) -> WarpBase:
        result = WarpBase(job_name=name)
        if not hasattr(specs.runtime, "framework"):
            specs.runtime.framework = None

        require_c2d_dockerfile = True
        if hasattr(specs, "package"):
            if hasattr(specs.package, "custom"):
                # auto-generate dockerfile with overrides / additions
                packaging = Packaging(
                    name,
                    specs.runtime.framework,
                    specs.runtime.simulator,
                    specs.package.custom,
                )
            if hasattr(specs.package, "docker"):
                require_c2d_dockerfile = False
        else:
            # auto-generate dockerfile
            packaging = Packaging(
                name, specs.runtime.framework, specs.runtime.simulator
            )

        if require_c2d_dockerfile:
            self._process_package(name, packaging, result)
            self._process_runtime(name, result, packaging)
        else:
            self._process_docker_package(specs.package.docker, result)
            self._process_runtime(name, result)

        return result

    def _process_package(
        self, job_name: str, packaging: Packaging, result: WarpBase
    ) -> None:
        # For monitoring: Codebuild has env variable JOB_ID available to it
        echo_cmd_prefix = f"echo [{job_name}]"
        # Base Image
        result.add("from", commands.get_base_image(packaging))
        result.add("arg", "JOB_ID")
        result.add("env", "JOB_ID=$JOB_ID")
        result.add("env", f"ARTEFACTS_JOB_NAME={job_name}")
        # Copy Stage
        result.add("run", f"{echo_cmd_prefix} STAGE: Copy")
        for path in commands.get_include_in_container(packaging):
            result.add("copy", f"{path} /ws/src")

        result.add("workdir", packaging.get_workdir())
        # ROS dependencies if used.
        if packaging.is_ros and not packaging.simulator == "turtlesim":
            result.add(
                "run",
                f"{echo_cmd_prefix} STAGE: Ros Dependencies && apt update -y && rosdep install --from-paths src --ignore-src -r -y",
            )
        # Build Stage
        build_command = commands.get_build_command(packaging)
        if build_command is None:
            build_command = "Project has no Build Stage"
        else:
            build_command = f"&& {build_command}"
        result.add("run", f"{echo_cmd_prefix} STAGE: Build: {build_command}")

        if packaging.is_ros:
            result.add("workdir", "/ws/src")

    def _process_docker_package(self, specs: Config, result: WarpBase) -> None:
        try:
            if "image" in specs:
                result.add("from", f"{specs['image']} AS build")
                result.add("workdir", "/app")
                result.add("copy", ". .")
            elif "build" in specs:
                logging.info(
                    "No docker package image specification: Nothing to do. Assuming the job already has a Dockerfile"
                )
        except Exception as e:
            logging.error(
                f"Error raised from c2d. MESSAGE:Invalid docker package specifications: {e}"
            )
            raise Exception(f"Invalid docker package specifications: {e}")

    def _process_runtime(
        self,
        job_name: str,
        result: WarpBase,
        packaging: Packaging = None,
    ) -> None:
        if packaging is not None:
            runtime_instruction, runtime_arguments = commands.get_launch_command(
                packaging
            )
            result.add("run", f"echo [{job_name}] STAGE: Launch")
            result.add(runtime_instruction, runtime_arguments)
        else:
            result.add("copy", "--from=build /app /app")
