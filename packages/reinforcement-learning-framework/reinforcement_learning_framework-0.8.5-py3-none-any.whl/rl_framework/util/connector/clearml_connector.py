import logging
import os
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, SupportsFloat, Text

import gymnasium as gym
import stable_baselines3
from clearml import Task
from clearml.model import InputModel

from rl_framework.util.video_recording import record_video

from .base_connector import Connector, DownloadConfig, UploadConfig


@dataclass
class ClearMLUploadConfig(UploadConfig):
    """
    task_name (Optional[str]): The name of the task, None uses the script name.
    task_tags (list[str]): The default tags associated with the task.
    model_tags (list[str]): The default tags associated with the output model.
    """

    task_name: Optional[str] = None
    task_tags: list[str] = ()
    model_tags: list[str] = ()


@dataclass
class ClearMLDownloadConfig(DownloadConfig):
    """
    file_name (Optional[str]): The name of the output model and save file, used when a task_id is specified.
    task_id (str): A ClearML task id.
    If no file_name is provided, it will use the last added output model.
    model_id (str): ID of the existing ClearML model to download the agent from, preferred over task_id and file_name.
    """

    file_name: Optional[str] = None
    task_id: Optional[str] = None
    model_id: Optional[str] = None


class ClearMLConnector(Connector):
    def __init__(self, upload_config: ClearMLUploadConfig, download_config: ClearMLDownloadConfig, task: Task):
        """
        Initialize the connector and pass a ClearML Task object for tracking parameters/artifacts/results.

        Args:
            task (Task): Active task object to track parameters/artifacts/results in the experiment run(s).
                See https://clear.ml/docs/latest/docs/clearml_sdk/task_sdk/ on how to use tasks for your purposes.
        """
        super().__init__(upload_config, download_config)
        self.task = task

        if self.upload_config.task_name:
            self.task.set_name(self.upload_config.task_name)

        self.task.add_tags(list(self.upload_config.task_tags))

    def log_value_with_timestep(self, timestep: int, value_scalar: SupportsFloat, value_name: Text) -> None:
        """
        Log scalar value to create a sequence of values over time steps.
        Will appear in the "Scalar" section of the ClearML experiment page as a graph.

        Args:
            timestep: Time step which the scalar value corresponds to (x-value)
            value_scalar: Scalar value which should be logged (y-value)
            value_name: Name of scalar value (e.g., "avg. sum of reward")
        """
        super().log_value_with_timestep(timestep, value_scalar, value_name)
        self.task.get_logger().report_scalar(
            title=value_name, series=value_name, value=float(value_scalar), iteration=timestep
        )

    def log_value(self, metric_scalar: SupportsFloat, metric_name: Text) -> None:
        """
        Log one value with a certain metric name (once).
        Will appear in the "Scalar" section of the ClearML experiment page in a "Summary" window.

        Args:
            metric_scalar: Value which should be logged
            metric_name: Name of value (e.g., "mean_episode_reward")
        """
        super().log_value(metric_scalar, metric_name)
        self.task.logger.report_single_value(metric_name, round(float(metric_scalar), 2))

    def upload(
        self,
        agent,
        video_recording_environment: Optional[gym.Env] = None,
        checkpoint_id: Optional[int] = None,
        *args,
        **kwargs,
    ) -> None:
        """Evaluate the agent on the evaluation environment and generate a video.
         Afterward, upload the artifacts and the agent itself to a ClearML task.

        Args:
            agent (Agent): Agent (and its .algorithm attribute) to be uploaded.
            video_recording_environment (Environment): Environment used for clip creation before upload.
                If not provided, no video will be created.
            checkpoint_id (int): If specified, we do not perform a final upload with video generation and
                scalar logging but instead upload only a model checkpoint to ClearML.
        """
        file_name = self.upload_config.file_name
        video_length = self.upload_config.video_length

        assert file_name

        # Step 1: Save agent to temporary file and upload to ClearML
        file_literal, file_ending = str.split(file_name, ".")
        checkpoint_suffix = f"-{checkpoint_id}" if checkpoint_id else ""
        file_name = f"{file_literal}{checkpoint_suffix}"

        # Save agent to file
        agent_save_path = Path(tempfile.gettempdir(), f"{str(uuid.uuid1())}-{file_name}.{file_ending}")
        logging.debug(f"Saving agent to .zip file at {agent_save_path} and uploading artifact ...")
        agent.save_to_file(agent_save_path)
        while not os.path.exists(agent_save_path):
            time.sleep(1)

        # Upload to ClearML
        self.task.update_output_model(
            name=file_name,
            model_name=file_name,
            model_path=str(agent_save_path),
            tags=["final"] + list(self.upload_config.model_tags) if checkpoint_id is None else ["checkpoint"],
        )

        if not checkpoint_id:
            logging.info(
                "This function will evaluate the performance of your agent and log the model as well as the experiment "
                "results as artifacts to ClearML. Also, a video of the agent's performance on the evaluation "
                "environment will be generated and uploaded to the 'Debug Sample' section of the ClearML experiment."
            )

            # Step 2: Create a system info dictionary and upload it
            logging.debug("Uploading system meta information ...")
            system_info, _ = stable_baselines3.get_system_info()
            self.task.upload_artifact(name="system_info", artifact_object=system_info)

            # Step 3: Record a video and log local video file
            if video_recording_environment and video_length > 0:
                temp_path = tempfile.mkdtemp()
                logging.debug(f"Recording video to {temp_path} and uploading as debug sample ...")
                video_path = Path(temp_path) / "replay.mp4"
                record_video(
                    agent=agent,
                    video_recording_environment=video_recording_environment,
                    file_path=video_path,
                    fps=1,
                    video_length=video_length,
                )
                self.task.get_logger().report_media(
                    "video ", "agent-in-environment recording", iteration=1, local_path=video_path
                )

            # TODO: Save README.md

    def download(self, *args, **kwargs) -> Path:
        task_id = self.download_config.task_id
        model_id = self.download_config.model_id
        file_name = self.download_config.file_name

        # Search the model in the given task
        if task_id and not model_id:
            container = Task.get_task(task_id=task_id)
            if file_name:
                model_id = container.models["output"][file_name[:-4]].id
            else:
                model = container.models["output"][-1]
                model_id = model.id

        assert model_id, "Neither model_id nor task_id with optional file_name defined!"

        model = InputModel(model_id)
        model.connect(self.task, name=model.name)

        file_path = model.get_local_copy(raise_on_error=True)

        # If it's a directory, then it is a legacy model
        if Path(file_path).is_dir():
            logging.info(
                "Legacy model downloaded, make sure %s is the correct file name for the model file within.", file_path
            )
            return Path(file_path, file_name)

        return Path(file_path)
