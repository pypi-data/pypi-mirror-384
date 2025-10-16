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

from typing import Optional, Any
from cms.db.task import Dataset
from cms.db.submission import SubmissionResult, Evaluation
from cms.db.filecacher import FileCacher
from sqlalchemy.orm import Session
import json

from pisek.cms.submission import get_submission
from pisek.utils.colors import ColorSettings
from pisek.env.env import Env
from pisek.task_jobs.testing_log import TESTING_LOG
from pisek.task_jobs.solution.solution_result import Verdict
from pisek.config.task_config import SolutionSection, TestSection
from pisek.utils.text import eprint, tab

RUNTIME_ERROR_MESSAGES = [
    "Evaluation didn't produce file %s",
    "Execution killed (could be triggered by violating memory limits)",
    "Execution failed because the return code was nonzero",
]

TIME_LIMIT_MESSAGES = [
    "Execution timed out",
    "Execution timed out (wall clock limit exceeded)",
]


def create_testing_log(session: Session, env: Env, dataset: Dataset) -> bool:
    config = env.config
    files = FileCacher()

    payload: dict[str, Any] = {"source": "cms", "solutions": {}}
    success = True

    for name, solution in config.solutions.items():
        results: dict[str, Any] = {}
        payload["solutions"][name] = {"results": results}

        try:
            result = get_submission_result(session, files, env, solution, dataset)
        except SubmissionResultError as e:
            eprint(ColorSettings.colored(f"Skipping {name}: {e}", "yellow"))
            success = False
            continue

        evaluation: Evaluation
        for evaluation in result.evaluations:
            points: str | float
            result_type: str

            try:
                points = float(evaluation.outcome)

                if points >= 1:
                    result_type = Verdict.ok.name
                elif points <= 0:
                    if evaluation.text[0] in TIME_LIMIT_MESSAGES:
                        result_type = Verdict.timeout.name
                    elif evaluation.text[0] in RUNTIME_ERROR_MESSAGES:
                        result_type = Verdict.error.name
                    else:
                        result_type = Verdict.wrong_answer.name
                else:
                    result_type = Verdict.partial_ok.name
            except ValueError:
                points = evaluation.outcome
                result_type = "indeterminate"

            result = {
                "time": evaluation.execution_time,
                "wall_clock_time": evaluation.execution_wall_clock_time,
                "memory": (
                    evaluation.execution_memory / (1024 * 1024)
                    if evaluation.execution_memory is not None
                    else None
                ),
                "relative_points": points,
                "result": result_type,
            }

            result = dict(filter(lambda p: p[1] is not None, result.items()))

            results[f"{evaluation.codename}.in"] = result

    with open(TESTING_LOG, "w") as file:
        json.dump(payload, file, indent=4)

    return success


def check_results(session: Session, env: Env, dataset: Dataset) -> bool:
    config = env.config
    files = FileCacher()

    success = True

    solution: SolutionSection
    for name, solution in config.solutions.items():
        try:
            result = get_submission_result(session, files, env, solution, dataset)

            if not result.scored():
                raise SubmissionResultError("This submission has not been scored yet")
        except SubmissionResultError as e:
            print(ColorSettings.colored(f"Skipping {name}: {e}", "yellow"))
            success = False
            continue

        score = result.score

        score_missed_target = None

        if solution.points is not None and score != solution.points:
            score_missed_target = f"{solution.points}"
        elif solution.points_min is not None and score < solution.points_min:
            score_missed_target = f"above {solution.points_min}"
        elif solution.points_max is not None and score > solution.points_max:
            score_missed_target = f"below {solution.points_max}"

        message = f"{name}: {score} points"

        if score_missed_target is not None:
            message += f" (should be {score_missed_target})"
            message = ColorSettings.colored(message, "red")
            success = False

        print(message)

        subtasks: list[tuple[int, TestSection]] = list(config.test_sections.items())
        fractions = get_subtask_score_fractions(result.score_details)

        if fractions is None or len(fractions) != len(subtasks):
            message = "The task seems to use an unsupported score type, skipping checking subtasks"
            print(tab(ColorSettings.colored(message, "red")))

            success = False
            continue

        target: str
        for (num, subtask), fraction, target in zip(
            subtasks, fractions, solution.tests
        ):
            name = subtask.name or f"Subtask {num}"

            if target == "X":
                correct = True
            elif target == "1":
                target_name = "correct"
                correct = fraction == 1.0
            elif target == "P":
                target_name = "partially correct"
                correct = 0.0 < fraction < 1.0
            else:
                assert target in (
                    "0",
                    "W",
                    "T",
                    "!",
                ), f"Unknown expected result '{target}'"

                target_name = "wrong"
                correct = fraction == 0.0

            message = f"{name}: {fraction}"

            if not correct:
                message += f" (should be {target_name})"
                message = ColorSettings.colored(message, "red")
                success = False

            print(tab(message))

    return success


def get_subtask_score_fractions(score_details: Any) -> Optional[list[float]]:
    if not isinstance(score_details, list):
        return None

    results = []

    for subtask in score_details:
        if not isinstance(subtask, dict):
            return None

        if "score_fraction" not in subtask:
            return None

        fraction = subtask["score_fraction"]

        if not isinstance(fraction, float):
            return None

        results.append(fraction)

    return results


def get_submission_result(
    session: Session,
    files: FileCacher,
    env: Env,
    solution: SolutionSection,
    dataset: Dataset,
) -> SubmissionResult:
    submission = get_submission(session, files, env, solution, dataset.task)

    if submission is None:
        raise SubmissionResultError("This solution has not been submitted yet")

    result: Optional[SubmissionResult] = (
        session.query(SubmissionResult)
        .filter(SubmissionResult.submission == submission)
        .filter(SubmissionResult.dataset == dataset)
        .one_or_none()
    )

    if result is None:
        raise SubmissionResultError(
            "The latest submission hasn't started evaluating on this dataset"
        )

    if result.compilation_failed():
        raise SubmissionResultError("The submission failed to compile")

    if not result.evaluated():
        raise SubmissionResultError("The submission is still being evaluated")

    return result


class SubmissionResultError(Exception):
    pass
