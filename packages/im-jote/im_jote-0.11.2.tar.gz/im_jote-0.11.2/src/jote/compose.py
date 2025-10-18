"""The Job Tester 'compose' module.

This module is responsible for injecting a 'docker-compose.yml' file into the
repository of the Data Manager Job repository under test. It also
created project and instance directories, and executes 'docker-compose up'
to run the Job, and can remove the test directory.

This module is designed to simulate the actions of the Data Manager
and Job Operator that are running in the DM kubernetes deployment.
"""

import contextlib
import copy
import os
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# The 'simulated' instance directory,
# created by the Data Manager prior to launching the corresponding Job.
# Jobs know this directory because their container has this set via
# the environment variable 'DM_INSTANCE_DIRECTORY'.
INSTANCE_DIRECTORY: str = ".instance-88888888-8888-8888-8888-888888888888"

# A default test execution timeout (minutes)
DEFAULT_TEST_TIMEOUT_M: int = 10

# The docker-compose file template.
# A multi-line string with variable mapping,
# expanded and written to the test directory in 'create()'.
_COMPOSE_CONTENT: str = """---
# We use compose v2
# because we're relying on 'mem_limit' and 'cpus',
# which are ignored (moved to swarm) in v3.
version: '2.4'
networks:
  jote:
services:
  job:
    networks:
    - jote
    image: {image}
    container_name: {job}-{test}-jote
    user: '{uid}:{gid}'
    entrypoint: {command}
    command: []
    working_dir: {working_directory}
    volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - {test_path}:{project_directory}
    mem_limit: {memory_limit}
    cpus: {cpus}.0
    environment:
    - DM_INSTANCE_DIRECTORY={instance_directory}
{additional_environment}"""

_NF_CONFIG_CONTENT: str = """
docker.enabled = true
docker.runOptions = '-u $(id -u):$(id -g)'
"""


def _get_docker_compose_command() -> str:
    # Try 'docker compose' (v2) and then 'docker-compose' (v1)
    # we need one or the other.
    dc_command: str = ""
    try:
        _ = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            check=False,
            timeout=4,
        )
        dc_command = "docker compose"
    except FileNotFoundError:
        with contextlib.suppress(FileNotFoundError):
            _ = subprocess.run(
                ["docker-compose", "version"],
                capture_output=True,
                check=False,
                timeout=4,
            )
            dc_command = "docker-compose"
    if not dc_command:
        print("ERROR: Neither 'docker compose' nor 'docker-compose' has been found")
        print("One of these is required.")
        print("Please install one of them.")
        sys.exit(1)

    assert dc_command
    return dc_command


def _get_docker_compose_version() -> str:
    dc_command = _get_docker_compose_command()
    version_cmd: List[str] = dc_command.split() + ["version"]
    result = subprocess.run(version_cmd, capture_output=True, check=False, timeout=4)

    # stdout will contain the version on the first line: -
    # "docker-compose version v1.29.2, build unknown"
    # Ignore the first 23 characters of the first line...
    return str(result.stdout.decode("utf-8").split("\n")[0][23:])


def get_test_root() -> str:
    """Returns the root of the testing directory."""
    cwd: str = os.getcwd()
    return f"{cwd}/data-manager/jote"


class Compose:
    """A class handling the execution of 'docker compose'
    for an individual test.
    """

    # The docker-compose command (for the first test)
    _COMPOSE_COMMAND: str = ""
    # The docker-compose version (for the first test)
    _COMPOSE_VERSION: str = ""

    def __init__(
        self,
        collection: str,
        job: str,
        test: str,
        image: str,
        image_type: str,
        memory: str,
        cores: int,
        project_directory: str,
        working_directory: str,
        command: str,
        test_environment: Dict[str, str],
        user_id: Optional[int] = None,
        group_id: Optional[int] = None,
    ):
        # Memory must have a Mi or Gi suffix.
        # For docker-compose we translate to 'm' and 'g'
        self._memory: str = "1g"
        if memory.endswith("Mi"):
            self._memory = f"{memory[:-2]}m"
        elif memory.endswith("Gi"):
            self._memory = f"{memory[:-2]}g"
        assert self._memory

        self._collection: str = collection
        self._job: str = job
        self._test: str = test
        self._image: str = image
        self._image_type: str = image_type
        self._cores: int = cores
        self._project_directory: str = project_directory
        self._working_directory: str = working_directory
        self._command: str = command
        self._test_environment = copy.deepcopy(test_environment)
        self._user_id: Optional[int] = user_id
        self._group_id: Optional[int] = group_id

        assert Compose.try_to_set_compose_command()

    def get_test_path(self) -> str:
        """Returns the path to the root directory for a given test."""
        root: str = get_test_root()
        return f"{root}/{self._collection}.{self._job}.{self._test}"

    def get_test_project_path(self) -> str:
        """Returns the path to the root directory for a given test."""
        test_path: str = self.get_test_path()
        return f"{test_path}/project"

    def create(self) -> str:
        """Writes a docker-compose file
        and creates the test directory structure returning the
        full path to the test (project) directory.
        """

        print("# Compose: Creating test environment...")

        # First, delete
        test_path: str = self.get_test_path()
        if os.path.exists(test_path):
            shutil.rmtree(test_path)

        # Make the test directory
        # (where the test is launched from)
        # and the project directory (a /project sud-directory of test)
        test_path = self.get_test_path()
        project_path: str = self.get_test_project_path()
        inst_path: str = f"{project_path}/{INSTANCE_DIRECTORY}"
        if not os.path.exists(inst_path):
            os.makedirs(inst_path)

        # Run as a specific user/group ID?
        user_id = self._user_id if self._user_id is not None else os.getuid()
        group_id = self._group_id if self._group_id is not None else os.getgid()
        # Write the Docker compose content to a file in the test directory
        additional_environment: str = ""
        if self._test_environment:
            for e_name, e_value in self._test_environment.items():
                additional_environment += f"    - {e_name}={e_value}\n"
        variables: Dict[str, Any] = {
            "command": self._command,
            "test_path": project_path,
            "job": self._job,
            "test": self._test,
            "image": self._image,
            "memory_limit": self._memory,
            "cpus": self._cores,
            "uid": user_id,
            "gid": group_id,
            "project_directory": self._project_directory,
            "working_directory": self._working_directory,
            "instance_directory": INSTANCE_DIRECTORY,
            "additional_environment": additional_environment,
        }
        compose_content: str = _COMPOSE_CONTENT.format(**variables)
        compose_path: str = f"{test_path}/docker-compose.yml"
        with open(compose_path, "wt", encoding="UTF-8") as compose_file:
            compose_file.write(compose_content)

        # nextflow config?
        if self._image_type == "nextflow":
            # Write a nextflow config to the project path
            # (this is where the non-container-based nextflow is executed)
            # and where nextflow will, by default, look for the config.
            nf_cfg_path: str = f"{project_path}/nextflow.config"
            with open(nf_cfg_path, "wt", encoding="UTF-8") as nf_cfg_file:
                nf_cfg_file.write(_NF_CONFIG_CONTENT)

        print("# Compose: Created")

        return project_path

    def run(
        self, timeout_minutes: int = DEFAULT_TEST_TIMEOUT_M
    ) -> Tuple[int, str, str]:
        """Runs the container for the test, expecting the docker-compose file
        written by the 'create()'. The container exit code is returned to the
        caller along with the stdout and stderr content.
        A non-zero exit code does not necessarily mean the test has failed.
        """
        assert Compose.try_to_set_compose_command()

        execution_directory: str = self.get_test_path()

        print(f'# Compose: Executing the test ("{Compose._COMPOSE_COMMAND} up")...')
        print(f'# Compose: Execution directory is "{execution_directory}"')

        cwd = os.getcwd()
        os.chdir(execution_directory)

        timeout: bool = False
        try:
            # Run the container, and then cleanup.
            # If a test environment is set then we pass in these values to the
            # process as we run it - but it also needs to have a copy of the
            # exiting environment.
            env: Optional[Dict[str, Any]] = None
            if self._test_environment:
                env = os.environ.copy()
                env.update(self._test_environment)

            # By using '-p' ('--project-name')
            # we set the prefix for the network name and can use compose files
            # from different directories. Without this the network name
            # is prefixed by the directory the compose file is in.
            up_cmd: List[str] = Compose._COMPOSE_COMMAND.split() + [
                "-p",
                "data-manager",
                "up",
                "--exit-code-from",
                "job",
                "--abort-on-container-exit",
            ]
            test = subprocess.run(
                up_cmd,
                capture_output=True,
                timeout=timeout_minutes * 60,
                check=False,
                env=env,
            )
            down_cmd: List[str] = Compose._COMPOSE_COMMAND.split() + ["down"]
            _ = subprocess.run(
                down_cmd,
                capture_output=True,
                timeout=240,
                check=False,
            )
        except:  # pylint: disable=bare-except
            timeout = True
        finally:
            os.chdir(cwd)

        if timeout:
            print("# Compose: ERROR - Test timeout")
            return_code: int = -911
            test_stdout: str = ""
            test_stderr: str = ""
        else:
            print(f"# Compose: Executed (exit code {test.returncode})")
            return_code = test.returncode
            test_stdout = test.stdout.decode("utf-8")
            test_stderr = test.stderr.decode("utf-8")

        return return_code, test_stdout, test_stderr

    def delete(self) -> None:
        """Deletes a test directory created by 'create()'."""
        print("# Compose: Deleting the test...")

        test_path: str = self.get_test_path()
        if os.path.exists(test_path):
            shutil.rmtree(test_path)

        print("# Compose: Deleted")

    @staticmethod
    def try_to_set_compose_command() -> bool:
        """Tries to find the docker-compose command,
        setting Compose._COMPOSE_COMMAND when found"""
        # Do we have the 'docker compose' command?
        if not Compose._COMPOSE_COMMAND:
            Compose._COMPOSE_COMMAND = _get_docker_compose_command()
            print(f"# Compose command: {Compose._COMPOSE_COMMAND}")
        # Do we have the 'docker-compose' command?
        if not Compose._COMPOSE_VERSION:
            Compose._COMPOSE_VERSION = _get_docker_compose_version()
            print(f"# Compose version: {Compose._COMPOSE_VERSION}")

        if Compose._COMPOSE_COMMAND and Compose._COMPOSE_VERSION:
            return True
        return False

    @staticmethod
    def run_group_compose_file(compose_file: str, delay_seconds: int = 0) -> bool:
        """Starts a group compose file in a detached state.
        The file is expected to be a compose file in the 'data-manager' directory.
        We pull the container image to reduce the 'docker-compose up' time
        and then optionally wait for a period of seconds.
        """
        assert Compose.try_to_set_compose_command()

        print("# Compose: Starting test group containers...")

        # Runs a group compose file in a detached state.
        # The file is expected to be resident in the 'data-manager' directory.
        try:
            # Pre-pull the docker-compose images.
            # This saves start-up execution time.
            pull_cmd: List[str] = Compose._COMPOSE_COMMAND.split() + [
                "-f",
                os.path.join("data-manager", compose_file),
                "pull",
            ]
            _ = subprocess.run(
                pull_cmd,
                capture_output=False,
                check=False,
            )

            # Bring the group-test compose file up.
            # By using '-p' ('--project-name')
            # we set the prefix for the network name and services from this container
            # are visible to the test container. Without this the network name
            # is prefixed by the directory the compose file is in.
            up_cmd: List[str] = Compose._COMPOSE_COMMAND.split() + [
                "-f",
                os.path.join("data-manager", compose_file),
                "-p",
                "data-manager",
                "up",
                "-d",
            ]
            _ = subprocess.run(
                up_cmd,
                capture_output=False,
                check=False,
            )
        except:  # pylint: disable=bare-except
            return False

        # Wait for a period of seconds after launching?
        if delay_seconds:
            print(f"# Compose: Post-bring-up test group sleep ({delay_seconds})...")
            time.sleep(delay_seconds)

        print("# Compose: Started test group containers")
        return True

    @staticmethod
    def stop_group_compose_file(compose_file: str) -> bool:
        """Stops a group compose file.
        The file is expected to be a compose file in the 'data-manager' directory.
        """
        assert Compose.try_to_set_compose_command()

        print("# Compose: Stopping test group containers...")

        try:
            # Bring the compose file down...
            down_cmd: List[str] = Compose._COMPOSE_COMMAND.split() + [
                "-f",
                os.path.join("data-manager", compose_file),
                "down",
                "--remove-orphans",
            ]
            _ = subprocess.run(
                down_cmd,
                capture_output=False,
                timeout=240,
                check=False,
            )
        except:  # pylint: disable=bare-except
            return False

        print("# Compose: Stopped test group containers")

        return True
