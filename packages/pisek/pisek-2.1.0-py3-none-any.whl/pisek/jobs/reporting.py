# pisek  - Tool for developing tasks for programming competitions.
#
# Copyright (c)   2025        Daniel Skýpala <daniel@honza.info>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from abc import ABC, abstractmethod
from colorama import Cursor, ansi
from functools import wraps
from math import ceil
import re
import sys
import time
from typing import Callable, Concatenate, ParamSpec

from pisek.utils.text import tab
from pisek.utils.terminal import terminal_width, terminal_height, LINE_SEPARATOR

from pisek.jobs.jobs import State, PipelineItem, Job, JobManager
from pisek.env.env import Env

P = ParamSpec("P")


class Reporter(ABC):
    def __init__(self, env: Env, job_managers: list[JobManager]) -> None:
        self._env = env
        self._job_managers = job_managers

    @abstractmethod
    def update(self) -> None:
        pass

    @abstractmethod
    def report_job(self, job: Job) -> None:
        pass

    @abstractmethod
    def report_manager(self, job_manager: JobManager) -> None:
        pass

    @abstractmethod
    def refresh(self, active_jobs: list[Job]) -> None:
        pass


class CommandLineReporter(Reporter):
    def __init__(self, env: Env, job_managers: list[JobManager]) -> None:
        self._finished_jm = 0
        self._tmp_lines = 0
        self._dirty_lines = 0
        self._manager_tmp_lines = 0
        super().__init__(env, job_managers)

    def update(self) -> None:
        self._reset_tmp_lines()
        self._manager_tmp_lines = 0
        for i in range(self._finished_jm, len(self._job_managers)):
            job_man = self._job_managers[i]

            if i == self._finished_jm and job_man.state.finished():
                self._finished_jm += 1
                self._print(job_man.get_status())
                if job_man.state != State.cancelled:
                    self._report_manager(job_man)
                if job_man.state == State.failed and not self._env.full:
                    break
            elif job_man.state == State.running:
                msg = job_man.get_status()
                self._print_tmp(msg)
                self._manager_tmp_lines = self._lines(msg)
                break

    def report_job(self, job: Job) -> None:
        pass

    def report_manager(self, job_manager: JobManager) -> None:
        # If the conditions are met, we need to report it now as we won't have another chance
        # Otherwise we'll just do it later
        if (
            self._finished_jm <= self._job_managers.index(job_manager)
            and job_manager.any_failed()
            and not self._env.full
        ):
            self._print(job_manager.get_status())
            self._report_manager(job_manager)

    def _report_manager(self, job_manager: JobManager) -> None:
        self._clear_lines(self._dirty_lines)
        report_about: list[PipelineItem] = job_manager.jobs + [job_manager]

        # Prints and warnings
        for item in report_about:
            for msg, is_stderr in item.terminal_output:
                self._print(msg, end="", file=sys.stderr if is_stderr else sys.stdout)

        # Fails
        fails: list[str] = []
        for item in report_about:
            if item.state == State.failed and item.fail_msg:
                fails.append(self._fail_message(item))

        if fails:
            msg = self._colored(
                LINE_SEPARATOR + LINE_SEPARATOR.join(fails) + LINE_SEPARATOR, "red"
            )
            self._print(msg, end="")

    def refresh(self, active_jobs: list[Job]) -> None:
        self._reset_tmp_lines(leave=self._manager_tmp_lines)
        now = time.time()

        if terminal_height <= self._env.jobs + 5:  # Some extra safety margin
            if active_jobs:
                self._print_tmp(
                    f"{len(active_jobs)} active job{'s' if len(active_jobs) >= 2 else ''}, longest running: {self._format_job(active_jobs[0], now)}"
                )
        else:
            if active_jobs:
                self._print_tmp("Active jobs:")

            for job in active_jobs:
                self._print_tmp("- " + self._format_job(job, now))

            self._clear_lines(self._dirty_lines)

    def _format_job(self, job: Job, now: float) -> str:
        run_time: float = 0 if job.started is None else max(0, now - job.started)
        return f"{job.name} ({run_time:.1f}s)"

    @staticmethod
    def _jumps(
        func: Callable[Concatenate["CommandLineReporter", P], None],
    ) -> Callable[Concatenate["CommandLineReporter", P], None]:
        @wraps(func)
        def g(self, *args: P.args, **kwargs: P.kwargs) -> None:
            if not self._env.no_jumps:
                func(self, *args, **kwargs)

        return g

    @_jumps
    def _reset_tmp_lines(self, leave: int = 0) -> None:
        up = max(0, self._tmp_lines - leave)
        print(Cursor.UP() * up, end="")
        self._dirty_lines += up
        self._tmp_lines -= up

    @_jumps
    def _print_tmp(self, msg, *args, **kwargs) -> None:
        """Prints a text to be rewritten latter."""
        lines = self._lines(msg)
        self._clear_lines(lines)
        self._tmp_lines += lines
        self._dirty_lines -= lines
        print(str(msg), *args, **kwargs)

    def _print(self, msg, *args, **kwargs) -> None:
        """Prints a text."""
        self._reset_tmp_lines()
        self._clear_lines(self._lines(msg))
        self._dirty_lines -= self._lines(msg)
        print(str(msg), *args, **kwargs)

    @_jumps
    def _clear_lines(self, count: int) -> None:
        if count >= self._dirty_lines:
            self._dirty_lines = 0
        print(f"{ansi.clear_line()}\n" * count + Cursor.UP() * count, end="")

    def _lines(self, text: str) -> int:
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return sum(
            max(ceil(len(re.sub(ansi_escape, "", line)) / terminal_width), 1)
            for line in text.split("\n")
        )

    def _colored(self, msg: str, color: str) -> str:
        return self._env.colored(msg, color)

    def _fail_message(self, pitem: PipelineItem) -> str:
        return f'"{pitem.name}" failed:\n{tab(pitem.fail_msg)}\n'
