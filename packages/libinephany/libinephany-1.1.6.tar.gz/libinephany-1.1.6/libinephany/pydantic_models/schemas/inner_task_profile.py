# ======================================================================================================================
#
# IMPORTS
#
# ======================================================================================================================

import math
from typing import Any, Callable

from pydantic import BaseModel

# ======================================================================================================================
#
# CONSTANTS
#
# ======================================================================================================================

VRAM_USAGES_KEY = "vram_usages"

# ======================================================================================================================
#
# CLASSES
#
# ======================================================================================================================


class InnerTaskProfile(BaseModel):

    inner_task_name: str

    number_of_agents: int
    number_of_layers: int
    number_of_parameters: int

    observation_space_sizes: dict[str, int]
    action_space_sizes: dict[str, int]

    vram_usages: dict[int, tuple[float, float]] | None = None
    expected_vram_usage: float | None = None
    expected_idle_vram_usage: float | None = None
    max_batch_size_override: int | None = None

    @property
    def vram_usage(self) -> float:
        """
        :return: VRAM usage at the max batch size.
        """

        if self.expected_vram_usage is None:
            return float("nan")

        return self.expected_vram_usage

    @property
    def idle_vram_usage(self) -> float:
        """
        :return: Idle VRAM usage at the max batch size.
        """

        if self.expected_idle_vram_usage is None:
            return float("nan")

        return self.expected_idle_vram_usage

    @property
    def failed_to_profile(self) -> bool:
        """
        :return: Whether the corresponding task is completely invalid since it could not be profiled.
        """

        return math.isnan(self.vram_usage)

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """
        :param kwargs: Standard Pydantic model dump kwargs.
        :return: Dump result of the superclass' method.
        """

        super_dump = super().model_dump(**kwargs)

        if self.vram_usages is not None:
            super_dump[VRAM_USAGES_KEY] = {k: list(v) for k, v in self.vram_usages.items()}

        return super_dump


class InnerTaskProfiles(BaseModel):

    profiles: dict[str, InnerTaskProfile] = {}
    rejected_tasks: list[str] = []

    @property
    def max_agents(self) -> int:
        """
        :return: Maximum number of agents active in any one environment.
        """

        return max(profile.number_of_agents for profile in self.profiles.values())

    @property
    def max_layers(self) -> int:
        """
        :return: Maximum number of inner model layers in any one environment.
        """

        return max(profile.number_of_layers for profile in self.profiles.values())

    @property
    def min_layers(self) -> int:
        """
        :return: Minimum number of inner model layers in any one environment.
        """

        return min(profile.number_of_layers for profile in self.profiles.values())

    @property
    def possible_agents(self) -> list[str]:
        """
        :return: A list of names of the possible agents across inner tasks.
        """

        return list(self.compiled_observation_sizes.keys())

    @property
    def compiled_observation_sizes(self) -> dict[str, int]:
        """
        :return: The observation size of each possible agent.
        """

        spaces = {
            inner_task_name: inner_task_profile.observation_space_sizes
            for inner_task_name, inner_task_profile in self.profiles.items()
        }
        return self._compile_gym_space_sizes(spaces=spaces)

    @property
    def compiled_action_sizes(self) -> dict[str, int]:
        """
        :return: The action size of each possible agent.
        """

        spaces = {
            inner_task_name: inner_task_profile.action_space_sizes
            for inner_task_name, inner_task_profile in self.profiles.items()
        }
        return self._compile_gym_space_sizes(spaces=spaces)

    @property
    def total_observation_size(self) -> int:
        """
        :return: Total observation size summed across all agents.
        """

        return sum(self.compiled_observation_sizes.values())

    @property
    def total_action_size(self) -> int:
        """
        :return: Total action size summed across all agents.
        """

        return sum(self.compiled_action_sizes.values())

    @property
    def max_total_observation_size(self) -> int:
        """
        :return: The summed observation size of all agents with the task that has the most layers.
        """

        if not self.profiles:
            raise ValueError(
                "No profiles to calculate max total observation size. Ensure profiles have been "
                "added before executing the training loop"
            )

        largest_task_name = max(self.profiles, key=lambda k: self.profiles[k].number_of_layers)
        largest_task = self.profiles[largest_task_name]

        return sum(largest_task.observation_space_sizes.values())

    @property
    def max_total_action_size(self) -> int:
        """
        :return: The summed action size of all agents with the task that has the most layers.
        """

        if not self.profiles:
            raise ValueError(
                "No profiles to calculate max total action size. Ensure profiles have been "
                "added before executing the training loop"
            )

        largest_task_name = max(self.profiles, key=lambda k: self.profiles[k].number_of_layers)
        largest_task = self.profiles[largest_task_name]

        return sum(largest_task.action_space_sizes.values())

    @staticmethod
    def _compile_gym_space_sizes(spaces: dict[str, dict[str, int]]) -> dict[str, int]:
        """
        :param spaces: Dictionary mapping inner task names to a dictionary mapping agent IDs to observation/action
        space sizes.
        :return: Dictionary mapping agent IDs to observation/action space sizes.
        """

        compiled_spaces: dict[str, int] = {}

        for inner_task_spaces in spaces.values():
            for agent_id, agent_space in inner_task_spaces.items():
                if agent_id not in compiled_spaces:
                    compiled_spaces[agent_id] = agent_space

                elif agent_space != compiled_spaces[agent_id]:
                    raise ValueError(
                        f"Gym space size for agent {agent_id} differs between environments. "
                        f"Expected {compiled_spaces[agent_id]}, Got {agent_space}."
                    )

        return compiled_spaces

    @staticmethod
    def validate_size(
        policy_mapping_function: Callable[[str, Any, Any], str],
        size_dictionary: dict[str, int],
        expected_sizes: dict[str, int],
        task_name: str,
    ) -> dict[str, int]:
        """
        :param policy_mapping_function: Function which maps agent IDs to policy IDs.
        :param size_dictionary: Dictionary mapping agent IDs to observation/action space sizes.
        :param expected_sizes: Dictionary mapping policy IDs to expected observation/action space sizes.
        :param task_name: Name of the task being validated.
        :return: Updated expected_sizes dictionary.
        """

        for agent_id, size in size_dictionary.items():
            policy_id = policy_mapping_function(agent_id)  # type: ignore

            if policy_id not in expected_sizes:
                expected_sizes[policy_id] = size

            elif expected_sizes[policy_id] != size:
                raise ValueError(
                    f"The observation space size of agent {agent_id} for task {task_name} does not match the "
                    f"expected size {size}."
                )

        return expected_sizes

    def profile_exists(self, inner_task_name: str) -> bool:
        """
        :param inner_task_name: Name of the inner task to check whether the profile exists.
        :return: Whether the profile of the given inner task exists.
        """

        return inner_task_name in self.profiles

    def validate_task_profiles(self, policy_mapping_function: Callable[[str, Any, Any], str]) -> None:
        """
        :param policy_mapping_function: Function which maps agent IDs to policy IDs.
        """

        expected_observation_sizes: dict[str, int] = {}
        expected_action_sizes: dict[str, int] = {}

        for task_name, task_profile in self.profiles.items():
            expected_observation_sizes = self.validate_size(
                policy_mapping_function=policy_mapping_function,
                size_dictionary=task_profile.observation_space_sizes,
                expected_sizes=expected_observation_sizes,
                task_name=task_name,
            )
            expected_action_sizes = self.validate_size(
                policy_mapping_function=policy_mapping_function,
                size_dictionary=task_profile.action_space_sizes,
                expected_sizes=expected_action_sizes,
                task_name=task_name,
            )

    def reject_task(self, task: str) -> None:
        """
        :param task: Task being rejected due to excessive VRAM consumption.
        """

        if task not in self.rejected_tasks:
            self.rejected_tasks.append(task)

    def get_valid_profiles(self, force_tasks: str | list[str] | None = None) -> dict[str, InnerTaskProfile]:
        """
        :param force_tasks: Specific task or list of tasks to always include in valid profiles or None.
        :return: Dictionary mapping inner task names to profiles of the tasks with all tasks that failed to be profiled
        or were rejected removed.
        """

        force_tasks = [force_tasks] if isinstance(force_tasks, str) else force_tasks
        force_tasks = [] if force_tasks is None else force_tasks

        return {
            task: profile
            for task, profile in self.profiles.items()
            if task in force_tasks or (not profile.failed_to_profile and task not in self.rejected_tasks)
        }

    def get_vram_usages_of_valid_tasks(self) -> dict[str, float]:
        """
        :return: Dictionary mapping inner task names to the VRAM usage that task.
        """

        return {task: profile.vram_usage for task, profile in self.get_valid_profiles().items()}
