import importlib.util
import logging
from typing import Optional, Union


DOCKER_PACKAGE_NAME = "docker"
PODMAN_PACKAGE_NAME = "podman"


if importlib.util.find_spec(DOCKER_PACKAGE_NAME) is not None:
    DOCKER_AVAILABLE = True
    from .docker_runtime import DockerRuntime
else:
    DOCKER_AVAILABLE = False


if importlib.util.find_spec(PODMAN_PACKAGE_NAME) is not None:
    PODMAN_AVAILABLE = True
    from .podman_runtime import PodmanRuntime
else:
    PODMAN_AVAILABLE = False


LOGGER = logging.getLogger(__name__)


def runtime_factory(runtime: Optional[str] = None) -> tuple[Union["DockerRuntime", "PodmanRuntime"], str]:
    if runtime is None:
        if DOCKER_AVAILABLE:
            LOGGER.info("Docker SDK for Python found. Defaulting container runtime to Docker.")
            return DockerRuntime, DOCKER_PACKAGE_NAME
        if PODMAN_AVAILABLE:
            LOGGER.info("Podman SDK for Python found. Defaulting container runtime to Podman.")
            return PodmanRuntime, PODMAN_PACKAGE_NAME
        raise ImportError("Docker/Podman SDK for Python is not installed. Please install one of them.")
    if runtime == DOCKER_PACKAGE_NAME:
        if not DOCKER_AVAILABLE:
            raise ImportError("Docker SDK for Python is not installed. Please install it to use Docker runtime.")
        return DockerRuntime, DOCKER_PACKAGE_NAME
    elif runtime == PODMAN_PACKAGE_NAME:
        if not PODMAN_AVAILABLE:
            raise ImportError("Podman SDK for Python is not installed. Please install it to use Podman runtime.")
        return PodmanRuntime, PODMAN_PACKAGE_NAME
    else:
        raise ValueError(f"Unsupported runtime: {runtime}")
