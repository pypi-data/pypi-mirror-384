# pisek  - Tool for developing tasks for programming competitions.
#
# Copyright (c)   2023        Daniel Skýpala <daniel@honza.info>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from abc import abstractmethod
from decimal import Decimal
import subprocess
from typing import Optional

from pisek.env.env import Env
from pisek.utils.paths import TaskPath, InputPath, OutputPath
from pisek.jobs.jobs import PipelineItemFailure
from pisek.utils.text import tab
from pisek.task_jobs.run_result import RunResult, RunResultKind
from pisek.task_jobs.solution.solution_result import (
    Verdict,
    SolutionResult,
    RelativeSolutionResult,
)
from pisek.task_jobs.checker.checker_base import RunBatchChecker


class RunJudgeLibChecker(RunBatchChecker):
    """Checks solution output and correct output using judgelib checker."""

    @abstractmethod
    def _get_flags(self) -> list[str]:
        pass

    def _check(self) -> SolutionResult:
        self._access_file(self.output)
        self._access_file(self.correct_output)

        executable = TaskPath.executable_path("_" + self.checker_name)

        checker = self._run_subprocess(
            [
                executable.path,
                *self._get_flags(),
                self.output.path,
                self.correct_output.path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        assert checker.stderr is not None
        stderr = checker.stderr.read().decode("utf-8")

        # XXX: Okay, it didn't finish in no time, but this is not meant to be used
        rr = RunResult(
            RunResultKind.OK,
            checker.returncode,
            0,
            0,
            status=(stderr.strip() or "Files are equivalent")
            + f": {self.output.col(self._env)} {self.correct_output.col(self._env)}",
        )

        if checker.returncode == 42:
            return RelativeSolutionResult(
                Verdict.ok, None, self._solution_run_res, rr, Decimal(1)
            )
        elif checker.returncode == 43:
            return RelativeSolutionResult(
                Verdict.wrong_answer, None, self._solution_run_res, rr, Decimal(0)
            )
        else:
            raise PipelineItemFailure(f"{self.checker_name} failed:\n{tab(stderr)}")


class RunTokenChecker(RunJudgeLibChecker):
    """Checks solution output and correct output using judge-token."""

    def __init__(
        self,
        env: Env,
        test: int,
        input_: InputPath,
        output: OutputPath,
        correct_output: OutputPath,
        expected_verdict: Optional[Verdict],
    ) -> None:
        super().__init__(
            env=env,
            checker_name="judge-token",
            test=test,
            input_=input_,
            output=output,
            correct_output=correct_output,
            expected_verdict=expected_verdict,
        )

    def _get_flags(self) -> list[str]:
        flags = ["-t"]
        if self._env.config.tests.tokens_ignore_newlines:
            flags.append("-n")
        if self._env.config.tests.tokens_ignore_case:
            flags.append("-i")
        if self._env.config.tests.tokens_float_rel_error != None:
            flags.extend(
                [
                    "-r",
                    "-e",
                    str(self._env.config.tests.tokens_float_rel_error),
                    "-E",
                    str(self._env.config.tests.tokens_float_abs_error),
                ]
            )
        return flags


class RunShuffleChecker(RunJudgeLibChecker):
    """Checks solution output and correct output using judge-shuffle."""

    def __init__(
        self,
        env: Env,
        test: int,
        input_: InputPath,
        output: OutputPath,
        correct_output: OutputPath,
        expected_verdict: Optional[Verdict],
    ) -> None:
        super().__init__(
            env=env,
            checker_name="judge-shuffle",
            test=test,
            input_=input_,
            output=output,
            correct_output=correct_output,
            expected_verdict=expected_verdict,
        )

    def _get_flags(self) -> list[str]:
        SHUFFLE_MODE_FLAGS = {
            "lines": "-l",
            "words": "-w",
            "lines_words": "-lw",
            "tokens": "-nw",
        }
        assert self._env.config.tests.shuffle_mode is not None
        flags = ["-e", SHUFFLE_MODE_FLAGS[self._env.config.tests.shuffle_mode]]
        if self._env.config.tests.shuffle_ignore_case:
            flags.append("-i")

        return flags
