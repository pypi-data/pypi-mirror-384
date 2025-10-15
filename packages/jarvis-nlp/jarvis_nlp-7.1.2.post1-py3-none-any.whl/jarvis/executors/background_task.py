import os
import warnings
from collections import OrderedDict
from collections.abc import Generator

import yaml
from pydantic import ValidationError

from jarvis.modules.audio import speaker
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.models.classes import BackgroundTask
from jarvis.modules.utils import support, util


def background_task_handler(phrase: str) -> None:
    """Handles background tasks file resets by renaming it to tmp if requested to disable.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if "enable" in phrase.lower():
        if os.path.isfile(models.fileio.tmp_background_tasks):
            os.rename(
                src=models.fileio.tmp_background_tasks,
                dst=models.fileio.background_tasks,
            )
            speaker.speak(
                text=f"Background tasks have been enabled {models.env.title}!"
            )
        elif os.path.isfile(models.fileio.background_tasks):
            speaker.speak(
                text=f"Background tasks were never disabled {models.env.title}!"
            )
        else:
            speaker.speak(
                text=f"I couldn't not find the source file to enable background tasks {models.env.title}!"
            )
    elif "disable" in phrase.lower():
        if os.path.isfile(models.fileio.background_tasks):
            os.rename(
                src=models.fileio.background_tasks,
                dst=models.fileio.tmp_background_tasks,
            )
            speaker.speak(
                text=f"Background tasks have been disabled {models.env.title}!"
            )
        elif os.path.isfile(models.fileio.tmp_background_tasks):
            speaker.speak(
                text=f"Background tasks were never enabled {models.env.title}!"
            )
        else:
            speaker.speak(
                text=f"I couldn't not find the source file to disable background tasks {models.env.title}!"
            )
    else:
        speaker.speak(
            text="Please specify whether you'd like to enable or disable background tasks."
        )


def compare_tasks(dict1: dict, dict2: dict) -> bool:
    """Compares tasks currently in background tasks yaml file and the tasks already loaded.

    Args:
        dict1: Takes either the task in yaml file or loaded task as an argument.
        dict2: Takes either the task in yaml file or loaded task as an argument.

    Returns:
        bool:
        A boolean flag to if both the dictionaries are similar.
    """
    if (
        "ignore_hours" in dict1
        and dict1["ignore_hours"] == []
        and "ignore_hours" not in dict2
    ):
        dict1.pop("ignore_hours")
    if (
        "ignore_hours" in dict2
        and dict2["ignore_hours"] == []
        and "ignore_hours" not in dict1
    ):
        dict2.pop("ignore_hours")
    if OrderedDict(sorted(dict1.items())) == OrderedDict(sorted(dict2.items())):
        return True


def remove_corrupted(task: BackgroundTask | dict) -> None:
    """Removes a corrupted task from the background tasks feed file.

    Args:
        task: Takes a background task object as an argument.
    """
    with open(models.fileio.background_tasks) as read_file:
        existing_data = yaml.load(stream=read_file, Loader=yaml.FullLoader)
    for task_ in existing_data:
        if (isinstance(task, dict) and compare_tasks(task_, task)) or (
            isinstance(task, BackgroundTask) and compare_tasks(task_, task.__dict__)
        ):
            logger.info("Removing corrupted task: %s", task_)
            existing_data.remove(task_)
    with open(models.fileio.background_tasks, "w") as write_file:
        yaml.dump(data=existing_data, stream=write_file)


def validate_tasks(log: bool = True) -> Generator[BackgroundTask]:
    """Validates each of the background tasks.

    Args:
        log: Takes a boolean flag to suppress info level logging.

    Yields:
        BackgroundTask:
        BackgroundTask object.
    """
    if os.path.isfile(models.fileio.background_tasks):
        task_info = []
        with open(models.fileio.background_tasks) as file:
            try:
                task_info = yaml.load(stream=file, Loader=yaml.FullLoader) or []
            except yaml.YAMLError as error:
                logger.error(error)
                warnings.warn("BACKGROUND TASKS :: Invalid file format.")
                logger.error(
                    "Invalid file format. Logging background tasks and renaming the file to avoid repeated "
                    "errors in a loop.\n%s\n\n%s\n\n%s"
                    % (
                        "".join(["*" for _ in range(120)]),
                        file.read(),
                        "".join(["*" for _ in range(120)]),
                    )
                )
                os.rename(
                    src=models.fileio.background_tasks,
                    dst=models.fileio.tmp_background_tasks,
                )
        if task_info:
            logger.info("Background tasks: %d", len(task_info)) if log else None
        else:
            return
        for t in task_info:
            try:
                task = BackgroundTask(
                    seconds=t.get("seconds"),
                    task=t.get("task"),
                    ignore_hours=t.get("ignore_hours"),
                )
            except ValidationError as error:
                logger.error(error)
                remove_corrupted(t)
                continue
            if "restart" in task.task.lower():
                logger.warning(
                    "Unsupervised restarts are not allowed via background tasks. Use automation instead."
                )
                warnings.warn(
                    "Unsupervised restarts are not allowed via background tasks. Use automation instead."
                )
                continue
            if log:
                msg = f"{task.task!r} will be executed every {support.time_converter(second=task.seconds)!r}"
                if task.ignore_hours:
                    msg += f" except for the hours {util.comma_separator(list(map(str, task.ignore_hours)))}"
                logger.info(msg)
            yield task
