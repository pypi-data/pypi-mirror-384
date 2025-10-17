import logging
from c2d.packaging import Packaging
from c2d.constants import (
    CURRENT_ARTEFACTS_INFRA_VERSION,
    SUPPORTED_IMAGE_TAGS,
    LEGACY_FRAMEWORK_LAST_SUPPORTED,
)

logging.basicConfig()
logging.getLogger().setLevel("INFO")

build_dict = {
    "ros1": "catkin config --init && catkin build",
    # The makeflags will force colcon to use 1 core, and each directory will be built sequentially to avoid codebuild from crashing
    "ros2": 'MAKEFLAGS="-j1 -l1" colcon build --symlink-install --executor sequential',
    "maniskill": "pip install -e .",
}

# Reminder. These are all hardcoded at the moment, but fundamentally if a project
# contains a build stage, the source is the workspace, i,e "ws/install" for ros2 and "ws/devel" for ros1.
# Without a build stage, the source is the framework itself, i.e "/opt/ros/"
launch_dict = {
    # Key: QT_QPA_PLATFORM=offscreen is required when the simulator does not have a "headless" mode
    # Key: Xvfb is used when the simulator's "headless" mode doesn't allow any rendering (such as cameras)
    # LEGACY: 0.7.0
    "noetic": {
        "turtlesim": "source /ws/devel/setup.bash --extend && QT_QPA_PLATFORM=offscreen",
        "gazebo:11": "Xvfb :0 -screen 0 10x14x24  & source /ws/devel/setup.bash --extend &&",
    },
    # LEGACY: 0.7.0
    "galactic": {
        "turtlesim": "source /opt/ros/galactic/setup.bash && QT_QPA_PLATFORM=offscreen",
        "gazebo:fortress": "source /ws/install/setup.bash &&",
    },
    "humble": {
        "turtlesim": "source /opt/ros/humble/setup.bash && QT_QPA_PLATFORM=offscreen",
        "gazebo:fortress": "source /ws/install/setup.bash &&",
    },
}


def _generate_docker_tag(base_tag, simulator, gpu=True):
    gpu_tag = "-gpu" if gpu else ""
    if base_tag in LEGACY_FRAMEWORK_LAST_SUPPORTED:
        artefacts_version = LEGACY_FRAMEWORK_LAST_SUPPORTED[base_tag]
        logging.warning(
            f"DEPRECATION WARNING: {base_tag} is not supported by recent versions of artefacts. Falling back to version {LEGACY_FRAMEWORK_LAST_SUPPORTED[base_tag]}. Some features may not work as expected."
        )
    else:
        artefacts_version = CURRENT_ARTEFACTS_INFRA_VERSION

    return f"{base_tag}-{simulator}{gpu_tag}-{artefacts_version}"


def get_base_image(packaging: Packaging) -> str:
    registry = "public.ecr.aws/artefacts"
    repo = packaging.framework
    tag = packaging.framework_version
    fallback_base_img = "public.ecr.aws/docker/library/ubuntu:22.04 AS build"

    # User Specified
    if hasattr(packaging.custom, "os"):
        return packaging.custom.os + " AS build"
    # Fallback if framework not provided.
    if packaging.framework is None:
        return fallback_base_img
    # Default: use our base images
    try:
        simulator_version = packaging.simulator.split(":")[1]
        # E.g. "11" is too general for gazebo:11, so we want gazebo11
        if simulator_version.isnumeric():
            simulator_version = packaging.simulator.replace(":", "")

        tag = _generate_docker_tag(tag, simulator_version)
    except IndexError:
        tag = _generate_docker_tag(tag, packaging.simulator, gpu=False)
        logging.warning(
            f"Simulator version not provided, attempting to find base image: {tag}"
        )

    if tag in SUPPORTED_IMAGE_TAGS:
        return f"{registry}/{repo}:{tag}"
    else:
        logging.warning(
            f"No Artefacts base image for {tag}, no dockerfile provided, no package['custom']['os'] block. Attempting with Ubuntu22."
        )
        return fallback_base_img


def get_include_in_container(packaging: Packaging) -> list:
    # Presumption is user tells us what they wanted copied over,
    # rather than the whole repo
    if hasattr(packaging.custom, "include"):
        return packaging.custom.include
    # otherwise, copy over the whole repo
    return ["."]


def get_build_command(packaging: Packaging) -> str:
    use_build_dict = False

    if packaging.framework in build_dict:
        use_build_dict = True
    # Temporary -> Current ros2 turtlesim demo has no build stage.
    # TODO: Parse config file / project repo to determine if project build is required.
    if packaging.framework == "ros2" and packaging.simulator == "turtlesim":
        use_build_dict = False

    build_command = ""
    if hasattr(packaging.custom, "commands"):
        custom_commands = packaging.fix_pathing(packaging.custom.commands)
        for custom_command in custom_commands:
            build_command += custom_command + " && "

    # Return Logic, explicit to show different combinations:

    # Nothing
    if not use_build_dict and not hasattr(packaging.custom, "commands"):
        return None

    # Just user provided commands, dont need the final &&
    if not use_build_dict and hasattr(packaging.custom, "commands"):
        return build_command[:-4]

    # User provided commands (if any) plus c2d's generated build command for ros projects.
    if packaging.is_ros:
        return (
            build_command
            + f"source /opt/ros/{packaging.framework_version}/setup.bash --extend && "
            + build_dict[packaging.framework]
        )
    # User provided commands (if any) plus c2d's generated build command for non-ros projects.
    # TODO: Requires test after Maniskill implementation
    return build_command + build_dict.get(packaging.framework, "")


def get_launch_command(packaging: Packaging) -> str:
    if packaging.framework is None:
        return "copy", "--from=build /ws/src /ws/src"

    try:
        pre_launch_cmds = (
            launch_dict[packaging.framework_version][packaging.simulator] + " "
        )
    except KeyError:
        pre_launch_cmds = ""
    return (
        "cmd",
        pre_launch_cmds + "artefacts run $ARTEFACTS_JOB_NAME",
    )
