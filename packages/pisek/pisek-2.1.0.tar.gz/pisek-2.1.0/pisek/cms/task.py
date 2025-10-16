# pisek cms - Tool for importing tasks from Pisek into CMS.
#
# Copyright (c)   2024        Benjamin Swart <benjaminswart@email.cz>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from datetime import timedelta
from typing import Optional
from cms.db.task import Task
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from pisek.cms.dataset import create_dataset
from pisek.env.env import Env
from pisek.config.task_config import TaskConfig
from pisek.utils.paths import InputPath


def create_task(
    session: Session,
    env: Env,
    testcases: list[InputPath],
    description: str,
    time_limit: Optional[float],
) -> Task:
    config = env.config

    task = Task(name=config.cms.name, title=config.cms.title)
    set_task_settings(task, config)

    dataset = create_dataset(session, env, task, testcases, description, time_limit)

    task.active_dataset = dataset

    session.add(task)
    return task


def set_task_settings(task: Task, config: TaskConfig):
    task.title = config.cms.title
    task.submission_format = config.cms.submission_format
    task.max_submission_number = config.cms.max_submissions
    task.min_submission_interval = (
        timedelta(seconds=config.cms.min_submission_interval)
        if config.cms.min_submission_interval > 0
        else None
    )
    task.score_precision = config.task.score_precision
    task.score_mode = config.cms.score_mode
    task.feedback_level = config.cms.feedback_level


def get_task(session: Session, config: TaskConfig):
    try:
        return session.query(Task).filter(Task.name == config.cms.name).one()
    except NoResultFound as e:
        raise RuntimeError("This task has not been imported into CMS yet") from e
