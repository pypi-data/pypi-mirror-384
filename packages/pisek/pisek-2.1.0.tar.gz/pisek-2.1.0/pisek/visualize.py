# pisek  - Tool for developing tasks for programming competitions.
#
# Copyright (c)   2023        Daniel Skýpala <daniel@honza.info>
# Copyright (c)   2024        Antonín Maloň <git@tonyl.eu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from dataclasses import dataclass
from decimal import Decimal
import json
from math import ceil, inf
import os
from typing import Any, Optional

from pisek.utils.text import pad, tab, eprint
from pisek.utils.colors import ColorSettings
from pisek.utils.terminal import terminal_width
from pisek.config.config_types import TestPoints
from pisek.config.task_config import load_config, TaskConfig
from pisek.config.select_solutions import expand_solutions, UnknownSolutions
from pisek.task_jobs.solution.solution_result import Verdict
from pisek.task_jobs.solution.verdicts_eval import evaluate_verdicts


class MissingSolution(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"Missing solution {name} in testing log.")


@dataclass
class LoggedResult:
    verdict: Verdict
    relative_points: Optional[Decimal]
    absolute_points: Optional[Decimal]
    time: float
    test: str
    original_verdict: Verdict

    def points(self, test_points: TestPoints) -> Decimal:
        if test_points == "unscored":
            return Decimal("0")
        if self.relative_points is not None:
            return self.relative_points * test_points
        elif self.absolute_points is not None:
            return self.absolute_points
        else:
            raise ValueError("Relative and absolute points unset")

    def to_str(
        self,
        limit: float,
        segments: int,
        test_pad_length: int = 15,
    ) -> str:
        def get_bar() -> str:
            percentage = self.time / limit
            full = max(ceil(segments * percentage), 1)

            bounded = min(full, segments)
            overflown = max(0, full - segments)

            overflown_max_length = terminal_width - segments - test_pad_length - 40
            if cut := (overflown > overflown_max_length):
                overflown = overflown_max_length

            if abs(percentage - 1) < 0.1:
                color = "red"
            elif abs(percentage - 1) < 0.5:
                color = "yellow"
            else:
                color = "green"

            full_bar = ColorSettings.colored("━", color)

            return (
                f"[{full_bar*bounded}{('━' if ColorSettings.colors_on else ' ')*(segments-bounded)}|"
                f"{full_bar*overflown}{' '*(overflown_max_length - overflown)}{'⋯⋯' if cut else '  '}"
            )

        return (
            f"{pad(self.test, test_pad_length)}  "
            f"{self.original_verdict.mark()}->{self.verdict.mark()}  "
            f"{get_bar()}    {self.time:.2f} / {limit:.2f}s"
        )


def limit_result(result: LoggedResult, limit: float) -> LoggedResult:
    if result.time <= limit and result.verdict == Verdict.timeout:
        new_verdict = result.original_verdict
        if new_verdict == Verdict.timeout:
            new_verdict = Verdict.ok

        return LoggedResult(
            new_verdict,
            Decimal(1),
            None,
            result.time,
            result.test,
            result.original_verdict,
        )
    if result.time > limit:
        return LoggedResult(
            Verdict.timeout,
            Decimal(0),
            None,
            result.time,
            result.test,
            result.original_verdict,
        )
    return result


class SolutionResults:
    def __init__(
        self, name: str, config: TaskConfig, results: list[LoggedResult]
    ) -> None:
        self.name = name
        self._solution = config.solutions[name]
        self._config = config
        self._results = results

        self._results.sort(
            key=lambda r: (self._get_test(r), r.verdict.value, r.time, r.test)
        )

    def _get_test(self, result: LoggedResult) -> int:
        return min(
            i
            for i, sub in self._config.test_sections.items()
            if sub.new_in_test(result.test)
        )

    def _evaluate_results(
        self, results: list[LoggedResult], test_num: int
    ) -> tuple[bool, bool, Optional[LoggedResult]]:
        ok, definitive, breaker = evaluate_verdicts(
            self._config,
            list(map(lambda r: r.verdict, results)),
            self._solution.tests[test_num],
        )
        return ok, definitive, results[breaker] if breaker is not None else None

    @staticmethod
    def from_log(
        name: str, config: TaskConfig, testing_log, limit: float
    ) -> "SolutionResults":
        if name not in testing_log["solutions"]:
            raise MissingSolution(name)

        results = []
        for test_name, result in testing_log["solutions"][name]["results"].items():

            def load_decimal(result: dict[str, Any], key: str) -> Optional[Decimal]:
                return Decimal(result[key]) if key in result else None

            results.append(
                limit_result(
                    LoggedResult(
                        Verdict[result["result"]],
                        load_decimal(result, "relative_points"),
                        load_decimal(result, "absolute_points"),
                        result["time"],
                        test_name,
                        Verdict[result["result"]],
                    ),
                    limit,
                )
            )

        return SolutionResults(name, config, results)

    def get_all(self) -> list[LoggedResult]:
        return self._results

    def get_by_test(self) -> list[list[LoggedResult]]:
        by_test: list[list[LoggedResult]] = [
            [] for _ in range(self._config.tests_count)
        ]
        for res in self._results:
            for num, sub in self._config.test_sections.items():
                if sub.in_test(res.test):
                    by_test[num].append(res)

        return by_test

    def check_test(self, num: int) -> Optional[str]:
        results = self.get_by_test()

        expected = self._solution.tests[num]
        ok, _, breaker = self._evaluate_results(results[num], num)
        if not ok:
            failed_test = f" ({breaker.test})" if breaker else ""
            return f"{expected}{failed_test}"
        return None

    def check_points(self) -> Optional[str]:
        achieved = Decimal(0)
        results = self.get_by_test()
        for num, sub in self._config.test_sections.items():
            achieved += min(map(lambda r: r.points(sub.points), results[num]))

        points = self._solution.points
        points_min = self._solution.points_min
        points_max = self._solution.points_max

        if points is not None and points != achieved:
            return f"{points}p"
        if points_min is not None and not achieved >= points_min:
            return f"at least {points_min}p"
        if points_max is not None and not achieved <= points_max:
            return f"at most {points_max}p"

        return None

    def check_all(self) -> list[str]:
        fails = []
        for num in self._config.test_sections:
            if (err := self.check_test(num)) is not None:
                fails.append(f"{err} on {self._config.test_sections[num].name}")
        if (err := self.check_points()) is not None:
            fails.append(f"get {err}")

        return fails

    def get_time_limit_range(self, num: int) -> tuple[float, float]:
        results = self.get_by_test()[num]
        times = [0] + list(map(lambda r: r.time, results))
        times.sort()
        min_possible = len(times) - 1
        max_possible = 0
        for i, time in enumerate(times):
            ok, _, _ = self._evaluate_results(
                list(map(lambda r: limit_result(r, time), results)),
                num,
            )
            if ok:
                min_possible = min(i, min_possible)
                max_possible = max(i, max_possible)

        times.append(inf)
        return (times[min_possible], times[max_possible + 1])


def show_all(results: list[LoggedResult]) -> list[LoggedResult]:
    return results


def show_slowest(results: list[LoggedResult]) -> list[LoggedResult]:
    return [max(results, key=lambda r: (r.verdict.value, r.time))]


def visualize(
    path: str,
    filter: str,
    bundle: bool,
    solutions: Optional[list[str]],
    limit: Optional[float],
    filename: str,
    segments: Optional[int],
    pisek_dir: Optional[str],
    config_filename: str,
    **_,
) -> int:
    config = load_config(path, pisek_dir, config_filename)
    if config is None:
        return 2

    log_path = os.path.join(path, filename)
    try:
        with open(log_path) as log_file:
            testing_log = json.load(log_file)
    except FileNotFoundError:
        eprint(
            ColorSettings.colored(
                f"File {log_path} not found. Test with --testing-log to create a log.",
                "red",
            )
        )
        return 2

    if testing_log["source"] == "cms":
        limit_default = config.cms.time_limit
    else:
        limit_default = config.solution_time_limit
    time_limit = limit_default if limit is None else limit

    filter_fn = show_all if filter == "all" else show_slowest

    segment_cnt = terminal_width // 8 if segments is None else segments

    try:
        expanded_solutions = expand_solutions(config, solutions)
    except UnknownSolutions as err:
        eprint(ColorSettings.colored(str(err), "red"))
        return 2

    results: dict[str, SolutionResults] = {}
    max_test_length = 0
    for sol in expanded_solutions:
        try:
            results[sol] = SolutionResults.from_log(
                sol, config, testing_log, time_limit
            )
            max_test_length = max(
                max_test_length, max(map(lambda r: len(r.test), results[sol].get_all()))
            )
        except MissingSolution as err:
            eprint(ColorSettings.colored(str(err), "yellow"))

    wrong_solutions = {}
    for sol, sol_res in results.items():
        if not bundle:
            sol_err = sol_res.check_points()
            err_msg = ""
            if sol_err is not None:
                err_msg = ColorSettings.colored(f" should get {sol_err}", "red")
                wrong_solutions[sol] = True
            print(f"{sol}{err_msg}")

            for num, group_res in enumerate(sol_res.get_by_test()):
                test_err = sol_res.check_test(num)
                err_msg = ""
                if test_err is not None:
                    err_msg = ColorSettings.colored(f" should result {test_err}", "red")
                    wrong_solutions[sol] = True

                print(tab(f"{config.test_sections[num].name}{err_msg}"))
                for res in filter_fn(group_res):
                    print(
                        tab(tab(res.to_str(time_limit, segment_cnt, max_test_length)))
                    )

        else:
            sol_errs = sol_res.check_all()
            err_msg = ""
            if sol_errs:
                err_msg = ColorSettings.colored(f" should {', '.join(sol_errs)}", "red")
                wrong_solutions[sol] = True
            print(f"{sol}{err_msg}")

            for res in filter_fn(sol_res.get_all()):
                print(tab(tab(res.to_str(time_limit, segment_cnt, max_test_length))))

    print()
    if wrong_solutions:
        print(
            ColorSettings.colored(
                f"Solutions {', '.join(wrong_solutions.keys())} should result differently.",
                "red",
            )
        )

    min_possible = 0.0
    max_possible = inf
    for sol, sol_res in results.items():
        for num in config.test_sections:
            a, b = sol_res.get_time_limit_range(num)
            min_possible = max(a, min_possible)
            max_possible = min(b, max_possible)

    if min_possible <= max_possible:
        limit_msg = f"Valid time limit between {min_possible:.2f}, {max_possible:.2f}."
    else:
        limit_msg = "No valid time limit found."
    print(ColorSettings.colored(limit_msg, "cyan"))

    return 0
