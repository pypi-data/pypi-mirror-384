import cProfile
import functools
import io
import logging
import pstats
import time
from logging.handlers import RotatingFileHandler

from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext


def profile_and_timeit(func):
    """
    Decorator to profile and time the execution of the decorated function.
    - Profiles the function using cProfile and logs the profiling report.
    - Measures and logs the total execution time.
    - Logs are written to a rotating file in the .logs directory under the project root.
    Ensures .logs is gitignored.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Ensure the .logs directory exists
        logs_dir = settings.ROOT_DIR / ".logs"
        logs_dir.mkdir(exist_ok=True)

        # Ensure .logs is gitignored
        gitignore_path = logs_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, "w") as f:
                f.write(".logs/\n")
        else:
            with open(gitignore_path, "r+") as f:
                lines = f.readlines()
                if ".logs/\n" not in lines and ".logs/" not in [
                    line.strip() for line in lines
                ]:
                    f.write(".logs/\n")

        # Setup logger for this function's profiling and timing
        log_file = logs_dir / f"{func.__qualname__}.log"
        logger = logging.getLogger(f"profile_and_timeit.{func.__qualname__}")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=3)
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        logger.info("Starting profiling and timing for %s", func.__qualname__)

        # Start profiling and timing
        pr = cProfile.Profile()
        pr.enable()
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        pr.disable()

        # Prepare profiling report
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        ps.print_stats()
        profile_report = s.getvalue()
        time_report = (
            f"[TIMEIT] {func.__qualname__} executed in {end - start:.6f} seconds"
        )

        logger.info("[PROFILE REPORT for %s]\n%s", func.__qualname__, profile_report)
        logger.info(time_report)
        logger.info("Finished profiling and timing for %s", func.__qualname__)

        return result

    return wrapper


# Example usage:
# @profile_and_timeit
# def my_function():
#     ...

# class MyClass:
#     @profile_and_timeit
#     def my_method(self):
#         ...


def log_queries_and_timeit(func):
    """
    Decorator to log all SQL queries executed by the decorated function,
    along with their execution times and the total function execution time.
    Logs are written to a rotating file in the .logs directory under the project root.
    Ensures .logs is gitignored.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Ensure the .logs directory exists
        logs_dir = settings.ROOT_DIR / ".logs"
        logs_dir.mkdir(exist_ok=True)

        # Ensure .logs is gitignored
        gitignore_path = logs_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, "w") as f:
                f.write(".logs/\n")
        else:
            with open(gitignore_path, "r+") as f:
                lines = f.readlines()
                if ".logs/\n" not in lines and ".logs/" not in [
                    line.strip() for line in lines
                ]:
                    f.write(".logs/\n")

        # Setup logger for this function's queries
        log_file = logs_dir / f"{func.__qualname__}_queries.log"
        logger = logging.getLogger(f"log_queries_and_timeit.{func.__qualname__}")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=3)
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        logger.info("Starting execution of %s", func.__qualname__)
        with CaptureQueriesContext(connection) as queries:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()

        # Prepare queries report
        if queries.captured_queries:
            queries_report = "\n".join(
                f"[{i+1}] {q['sql']} ({q['time']}s)"
                for i, q in enumerate(queries.captured_queries)
            )
            logger.info(
                "[QUERIES REPORT for %s]\n%s",
                func.__qualname__,
                queries_report,
            )
            logger.info("Total queries executed: %d", len(queries.captured_queries))
        else:
            logger.info("No SQL queries executed in %s", func.__qualname__)

        # Log total execution time
        time_report = (
            f"[TIMEIT] {func.__qualname__} executed in {end - start:.6f} seconds"
        )
        logger.info(time_report)
        logger.info("Finished execution of %s", func.__qualname__)

        return result

    return wrapper
