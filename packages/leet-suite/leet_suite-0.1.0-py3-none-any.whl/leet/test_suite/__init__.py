import math
import time
from pprint import pprint
from typing import Callable, List, Optional

from ascii_graph import Pyasciigraph
from loguru import logger

LEET_STR = """
  _      ______ ______ ______ ______ ______ ______ ______ ______ ______ ______ _______
 | |    |  ____|  ____|  ____|  ____|  ____|  ____|  ____|  ____|  ____|  ____|__   __|
 | |    | |__  | |__  | |__  | |__  | |__  | |__  | |__  | |__  | |__  | |__     | |
 | |    |  __| |  __| |  __| |  __| |  __| |  __| |  __| |  __| |  __| |  __|    | |
 | |____| |____| |____| |____| |____| |____| |____| |____| |____| |____| |____   | |
 |______|______|______|______|______|______|______|______|______|______|______|  |_|


"""


class Case:
    def __init__(
        self,
        enabled: bool = True,
        disabled_from_here: bool = False,
        enabled_from_here: bool = False,
        **kwargs,
    ):
        self.input_args = kwargs
        self.enabled = enabled
        self.disabled_from_here = disabled_from_here
        self.enabled_from_here = enabled_from_here

        if "solution" in kwargs:
            self.solution = kwargs["solution"]
            self.input_args = {k: v for k, v in kwargs.items() if k != "solution"}
        else:
            raise ValueError("A 'solution' arg is needed.")

    def disable(self):
        self.enabled = False
        return self

    def enable(self):
        self.enabled = True
        return self

    def disable_from_here(self):
        self.disabled_from_here = True
        return self

    def enable_from_here(self):
        self.enabled_from_here = True
        return self


class Submission:
    def __init__(
        self,
        callable: Callable,
        cases: List[Case] = [],
        verbose: bool = False,
        inplace: bool = False,
        throw: bool = True,
    ):
        self.callable = callable
        self.cases = cases
        self.inplace = inplace
        self.throw = throw
        self.verbose = verbose

        if verbose:
            print(LEET_STR)

    def print_stats(self, overall_stats: dict = {}):
        skipped_percentage = 100
        correct_percentage = 0
        if len(self.cases) > overall_stats["skipped"]:
            skipped_percentage = overall_stats["skipped"] / len(self.cases) * 100
        if len(self.cases) - overall_stats["skipped"] > 0:
            correct_percentage = (
                (overall_stats["correct"])
                / (len(self.cases) - overall_stats["skipped"])
                * 100
            )
        logger.info(f"Overall runtime: {overall_stats['runtime']:.6f} seconds")
        logger.info(
            f"Skipped {overall_stats['skipped']} out of {len(self.cases)} cases ({skipped_percentage:.0f}%)"
        )
        corr_str = f"Found correct solution in {overall_stats['correct']} / {len(self.cases) - overall_stats['skipped']} non-skipped cases ({correct_percentage:.0f}%)"
        if int(correct_percentage) == 100:
            logger.success(corr_str)
        elif 0 < int(correct_percentage) < 100:
            logger.warning(corr_str)
        elif (
            int(correct_percentage) == 0
            and len(self.cases) - overall_stats["skipped"] > 0
        ):
            logger.error(corr_str)
        else:
            logger.info(corr_str)

    def display_runtime_graph(self, stats: list = [], logarithmic: bool = False):
        def transf(x):
            return x

        if logarithmic:

            def transf(x):
                return math.log(x, math.exp(1))

        run_times = [
            (f"case {stat['case']}", transf(stat["runtime"])) for stat in stats
        ]

        graph = Pyasciigraph(float_format="{0:.10f}")
        for line in graph.graph("Run times (s)", run_times):
            print(line)

    def run(
        self,
        comparator: Callable = lambda x, y: x == y,
        inplace_arg: Optional[str] = None,
    ):
        logger.info("Starting run.")
        if self.verbose and self.inplace and inplace_arg is not None:
            logger.info(
                f"Using inplace comparison of input arg '{inplace_arg}' to case.solution."
            )
        elif self.verbose and not self.inplace and inplace_arg is not None:
            logger.info(
                f"Not running inplace mode but 'inplace_arg' was set to {inplace_arg}. Ignoring."
            )

        if self.inplace and inplace_arg is None:
            raise ValueError(
                "Running inplace but 'inplace_arg' is None. Please set it or set inplace=False on init."
            )

        overall_stats = {"runtime": 0, "skipped": 0, "correct": 0}
        stats = []
        disabled_from_here = False
        enabled_from_here = False
        for i, case in enumerate(self.cases):
            if case.disabled_from_here:
                disabled_from_here = True
            if case.enabled_from_here:
                enabled_from_here = True
                disabled_from_here = False
            if not case.enabled and disabled_from_here:
                overall_stats["skipped"] += 1
                if self.verbose:
                    logger.info(f"Case {i + 1} not enabled. Skipping.")
                continue
            elif not case.enabled and not enabled_from_here:
                overall_stats["skipped"] += 1
                if self.verbose:
                    logger.info(f"Case {i + 1} not enabled. Skipping.")
                continue
            elif case.enabled and disabled_from_here:
                overall_stats["skipped"] += 1
                if self.verbose:
                    logger.info(f"Case {i + 1} not enabled. Skipping.")
                continue

            if self.verbose:
                print("~" * 100)
                logger.info(
                    f"Case {i + 1} / {len(self.cases)} ({(i + 1) / len(self.cases) * 100:.0f}%)"
                )
            s = time.time()
            sol = self.callable(**case.input_args)
            e = time.time() - s

            overall_stats["runtime"] += e

            if self.inplace:
                res = comparator(case.input_args[inplace_arg], case.solution)
                if self.verbose and not res:
                    if self.verbose:
                        logger.info("Actual solution:")
                        pprint(case.solution)
                        logger.info("Found solution")
                        pprint(case.input_args[inplace_arg])
                        if not isinstance(
                            case.input_args[inplace_arg], type(case.solution)
                        ):
                            logger.warning(
                                f"Type of actual solution ({type(case.solution)}) does not match type of found solution ({case.input_args[inplace_arg]}). Might be coding error."
                            )

                if self.throw and not res:
                    raise ValueError(f"Solution for case {i + 1} incorrect.")
                elif not self.throw and not res:
                    logger.error(f"Solution for case {i + 1} incorrect.")
                else:
                    logger.success(f"Solution for case {i + 1} correct.")
                    overall_stats["correct"] += 1
                    stats.append({"case": i + 1, "runtime": e})
                    if self.verbose:
                        logger.info(f"Took {e:.6f} seconds.")

            else:
                res = comparator(case.solution, sol)

                if self.verbose and not res:
                    logger.info("Actual solution:")
                    pprint(case.solution)
                    logger.info("Found solution")
                    pprint(sol)
                    if not isinstance(sol, type(case.solution)):
                        logger.warning(
                            f"Type of actual solution ({type(case.solution)}) does not match type of found solution ({type(sol)}). Might be coding error."
                        )

                if self.throw and not res:
                    raise ValueError(f"Solution for case {i + 1} incorrect.")
                elif not self.throw and not res:
                    logger.error(f"Solution for case {i + 1} incorrect.")
                else:
                    logger.success(f"Solution for case {i + 1} correct.")
                    overall_stats["correct"] += 1
                    stats.append({"case": i + 1, "runtime": e})
                    if self.verbose:
                        logger.info(f"Took {e:.6f} seconds.")

            if self.verbose:
                print("^" * 100)
        if self.verbose:
            self.print_stats(overall_stats=overall_stats)
            self.display_runtime_graph(stats=stats)
