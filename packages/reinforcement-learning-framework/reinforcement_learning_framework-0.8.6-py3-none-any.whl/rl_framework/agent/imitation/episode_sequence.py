import uuid
from typing import Callable, Generator, Generic, List, Sequence, Tuple, TypeVar, cast

import d3rlpy
import datasets
import imitation
import imitation.data.types
import numpy as np
from imitation.data import serialize
from imitation.data.huggingface_utils import (
    TrajectoryDatasetSequence,
    trajectories_to_dataset,
    trajectories_to_dict,
)

from rl_framework.util import patch_datasets

patch_datasets()

GenericEpisode = List[Tuple[object, object, object, float, bool, bool, dict]]


class EpisodeSequence(Sequence):
    """
    Class to load, transform and access episodes, optimized for memory efficiency.
        - Using HuggingFace datasets for memory-efficient data management (using arrow datasets under the hood)
        - Using imitation.data.TrajectoryWithRew as the internal episode format (and as the format to load from)
        - Using converters for format changing transformations

    Each episode consists of a sequence, which has the following format:
        [
            (obs_t0, action_t0, next_obs_t0, reward_t0, terminated_t0, truncated_t0, info_t0),
            (obs_t1, action_t1, next_obs_t1, reward_t1, terminated_t1, truncated_t1, info_t1),
            ...
        ]
        Interpretation: Transition from obs to next_obs with action, receiving reward.
            Additional information returned about transition to next_obs: terminated, truncated and info.

    """

    def __init__(self):
        self._episodes: Sequence[imitation.data.types.TrajectoryWithRew] = []

    def __len__(self):
        return len(self._episodes)

    def __getitem__(self, index) -> imitation.data.types.TrajectoryWithRew:
        return self._episodes[index]

    @staticmethod
    def from_episode_generator(
        episode_generator: Generator[imitation.data.types.TrajectoryWithRew, None, None],
        n_episodes: int,
    ) -> "EpisodeSequence":
        """
        Initialize an EpisodeSequence based on a provided episode generator.

        Args:
            episode_generator (Generator): Custom episode generator generating episodes of type TrajectoryWithRew.
            n_episodes (int): Amount of episodes the generator will generate (to limit infinite generators).

        Returns:
            episode_sequence: Representation of episode sequence (this class).
        """

        # NOTE: This is a hack to make the generator pickleable (because of huggingface datasets caching requirements)
        #  https://github.com/huggingface/datasets/issues/6194#issuecomment-1708080653
        class TrajectoryGenerator:
            def __init__(self, generator, trajectories_to_generate):
                self.generator_id = str(uuid.uuid4())
                self.generator = generator
                self.trajectories_to_generate = trajectories_to_generate

            def __call__(self, *args, **kwargs):
                for _ in range(self.trajectories_to_generate):
                    imitation_trajectory = next(self.generator)
                    trajectory_dict = {
                        key: value[0] for key, value in trajectories_to_dict([imitation_trajectory]).items()
                    }
                    yield trajectory_dict

            def __reduce__(self):
                return raise_pickling_error, (self.generator_id,)

        def raise_pickling_error(*args, **kwargs):
            raise AssertionError("Cannot actually pickle TrajectoryGenerator!")

        episode_sequence = EpisodeSequence()
        trajectory_dataset = datasets.Dataset.from_generator(TrajectoryGenerator(episode_generator, n_episodes))
        trajectory_dataset_sequence = TrajectoryDatasetSequence(trajectory_dataset)
        episode_sequence._episodes = cast(Sequence[imitation.data.types.TrajectoryWithRew], trajectory_dataset_sequence)
        return episode_sequence

    @staticmethod
    def from_episodes(episodes: Sequence[imitation.data.types.TrajectoryWithRew]) -> "EpisodeSequence":
        """
        Initialize an EpisodeSequence based on a sequence of episode objects.

        Args:
            episodes (Sequence): Sequence of episodes of type TrajectoryWithRew.

        Returns:
            episode_sequence: Representation of episode sequence (this class).
        """

        episode_sequence = EpisodeSequence()
        trajectory_dataset = trajectories_to_dataset(episodes)
        trajectories_dataset_sequence = TrajectoryDatasetSequence(trajectory_dataset)
        episode_sequence._episodes = cast(
            Sequence[imitation.data.types.TrajectoryWithRew], trajectories_dataset_sequence
        )
        return episode_sequence

    @staticmethod
    def from_dataset(file_path: str) -> "EpisodeSequence":
        """
        Initialize an EpisodeSequence based on provided huggingface dataset path.

        Episode sequences are loaded from a provided file path in the agent section of the config.
        Files of recorded episode sequences are generated by saving a sequence of `imitation.TrajectoryWithRew` objects.
        https://imitation.readthedocs.io/en/latest/main-concepts/trajectories.html#storing-loading-trajectories

        Args:
            file_path (str): Path to huggingface dataset recording of episodes.

        Returns:
            episode_sequence: Representation of episode sequence (this class).
        """

        episode_sequence = EpisodeSequence()
        trajectories_dataset_sequence = serialize.load(file_path)
        episode_sequence._episodes = cast(
            Sequence[imitation.data.types.TrajectoryWithRew], trajectories_dataset_sequence
        )
        return episode_sequence

    def save(self, file_path):
        """
        Save episode sequence into a file, saved as HuggingFace dataset.
        To load these episodes again, you can call the `.from_dataset` method.

        Args:
            file_path: File path and file name to save episode sequence to.
        """
        serialize.save(file_path, self._episodes)

    def to_imitation_episodes(self) -> "EpisodeSequence[imitation.data.types.TrajectoryWithRew]":
        return self

    def to_d3rlpy_episodes(self) -> "WrappedEpisodeSequence[d3rlpy.dataset.components.Episode]":
        def generate_d3rlpy_episode_from_imitation_trajectory(
            trajectory: imitation.data.types.TrajectoryWithRew,
        ) -> d3rlpy.dataset.components.Episode:
            observations = np.array(trajectory.obs[:-1])

            rewards = np.expand_dims(np.array(trajectory.rews), axis=1)

            actions = np.array(trajectory.acts)
            actions = np.expand_dims(actions, axis=1) if actions.ndim == 1 else actions

            d3rlpy_episode = d3rlpy.dataset.components.Episode(
                observations=observations,
                actions=actions,
                rewards=rewards,
                terminated=trajectory.terminal,
            )
            return d3rlpy_episode

        episode_sequence = WrappedEpisodeSequence(
            self._episodes, conversion_function=generate_d3rlpy_episode_from_imitation_trajectory
        )
        return episode_sequence

    def to_generic_episodes(self) -> "WrappedEpisodeSequence[GenericEpisode]":
        def generate_generic_episode_from_imitation_trajectory(
            trajectory: imitation.data.types.TrajectoryWithRew,
        ) -> GenericEpisode:
            obs = trajectory.obs[:-1]
            acts = trajectory.acts
            rews = trajectory.rews
            next_obs = trajectory.obs[1:]
            terminations = np.zeros(len(trajectory.acts), dtype=bool)
            truncations = np.zeros(len(trajectory.acts), dtype=bool)
            terminations[-1] = trajectory.terminal
            truncations[-1] = not trajectory.terminal
            infos = np.array([{}] * len(trajectory)) if trajectory.infos is None else trajectory.infos
            episode: GenericEpisode = list(zip(*[obs, acts, next_obs, rews, terminations, truncations, infos]))
            return episode

        episode_sequence = WrappedEpisodeSequence(
            self._episodes, conversion_function=generate_generic_episode_from_imitation_trajectory
        )
        return episode_sequence


T = TypeVar("T")
T_CHANGED = TypeVar("T_CHANGED")


class WrappedEpisodeSequence(EpisodeSequence, Generic[T]):
    """
    Wrapper for EpisodeSequence to convert imitation episodes to various other formats,
        while keeping the memory-efficient properties of EpisodeSequence
        (using huggingface.datasets implementation with pyarrow datasets).

    Functionality:
        - Modify __getitem__ method to convert imitation episodes to any other format.
    """

    def __init__(
        self,
        episodes: Sequence[imitation.data.types.TrajectoryWithRew],
        conversion_function: Callable[[imitation.data.types.TrajectoryWithRew], T],
    ):
        super().__init__()
        self._episodes: Sequence[imitation.data.types.TrajectoryWithRew] = episodes
        self._conversion_function = conversion_function

    def __getitem__(self, index) -> T:
        e = self._episodes[index]
        return self._conversion_function(e)

    def episode_sequence_from_additional_conversion(
        self, additional_conversion_function: Callable[[T], T_CHANGED]
    ) -> "WrappedEpisodeSequence[T_CHANGED]":
        """
        Wrap the current episode sequence with a new conversion function.

        Args:
            additional_conversion_function (Callable):
                Function to convert episodes (of type T) to another format (type T_CHANGED).

        Returns:
            WrappedEpisodeSequence: New episode sequence with the specified conversion function on top.
        """

        def new_conversion_function(episode: imitation.data.types.TrajectoryWithRew) -> T_CHANGED:
            episode_with_old_conversion: T = self._conversion_function(episode)
            episode_with_new_conversion: T_CHANGED = additional_conversion_function(episode_with_old_conversion)
            return episode_with_new_conversion

        return WrappedEpisodeSequence(self._episodes, new_conversion_function)
