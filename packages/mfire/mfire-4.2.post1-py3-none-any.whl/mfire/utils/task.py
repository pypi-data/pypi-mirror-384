from __future__ import annotations

import os
import time
import traceback
from enum import Enum
from multiprocessing import TimeoutError as MultiTimeoutError
from multiprocessing import get_context
from typing import Any, Callable, Iterable, List, Optional, Tuple

from mfire.settings import Settings
from mfire.settings.logger import Logger

LOGGER = Logger(name="utils.parallel")
error_callback = 0


class WrapCall:
    def __init__(self, name, func):
        self.func = func
        self.name = name

    def pre_call(self, *args, **kwargs):
        start = time.time()
        LOGGER.info(f"Task {self.name}: RUNNING")
        result = self.func(*args, **kwargs)
        LOGGER.info(f"Task {self.name}: DONE ({time.time() - start:.3f}s)")
        return result


class TaskStatus(str, Enum):
    """Possible status of a task"""

    NEW = ("NEW", False)
    PENDING = ("PENDING", False)
    RUNNING = ("RUNNING", False)
    FAILED = ("FAILED", True)
    TIMEOUT = ("TIMEOUT", True)
    DONE = ("DONE", False)

    is_error: bool

    def __new__(cls, value: str, is_error: bool) -> "TaskStatus":
        """Initialize a new TaskStatus object.

        Args:
            value: String value of the Task Status.
            is_error: Whether the given status is an error.

        Returns:
            TaskStatus: New TaskStatus object.
        """
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.is_error = is_error
        return obj


class Task:
    """Wrapping of a task containing a function to apply on given
    arguments and keyword arguments.
    """

    def __init__(
        self,
        func: Callable,
        args: Optional[Iterable] = None,
        callback: Optional[Callable] = None,
        name: Optional[str] = None,
    ):
        self.func = func
        self.args = list(args) if args is not None else []
        self.callback = callback if callback is not None else lambda x: None
        self.name = name if name is not None else "Task"
        self.status = TaskStatus.NEW
        self.async_result = None

    def change_status(self, new_status: TaskStatus, **kwargs):
        """Changes the task's status and notifies through the logger.

        Args:
            new_status: New status of the task.
            **kwargs: Keyword arguments for the logger.
        """
        if self.status != new_status:
            msg = f"Task {self.name}: {self.status.value} -> {new_status.value} "
            if new_status.is_error:
                LOGGER.error(msg, **kwargs)
            self.status = new_status

    def run(self) -> Any:
        try:
            self.change_status(TaskStatus.RUNNING)
            result = self.func(*self.args)
            self.callback(result)
            self.change_status(TaskStatus.DONE)
            return result
        except Exception as excpt:
            self.change_status(TaskStatus.FAILED)
            raise excpt

    def __repr__(self) -> str:
        return f"{self.name} (status={self.status.value})"

    def __str__(self) -> str:
        return repr(self)


class Tasks(Iterable):
    """Class that wraps the usage of multiprocessing.pool.Pool.apply_async
    to make it safer by catching Exceptions and triggering timeouts.
    """

    def __init__(self, processes: Optional[int] = os.cpu_count()):
        self.processes = max(processes or 1, 1)
        self._tasks: List[Task] = []
        if not Settings().disable_parallel:
            processes = max(1, self.processes - 1) if self.processes is not None else 1
            self.pool = get_context("spawn").Pool(
                processes=processes, maxtasksperchild=20
            )
        global error_callback
        error_callback = 0

    def __iter__(self):
        return iter(self._tasks)

    def __len__(self) -> int:
        return len(self._tasks)

    def __repr__(self) -> str:
        status_counts = self.status_count
        status_str = "; ".join(
            f"{count} {status.value}" for status, count in status_counts if count > 0
        )
        return f"Tasks({len(self)} tasks: {status_str})"

    @property
    def status_count(self) -> List[Tuple[str, int]]:
        """Counts the number of tasks for each possible status.

        Returns:
            List[Tuple[str, int]]: A list containing each TaskStatus
                and the corresponding number of tasks with that status.
        """
        statuses = [task.status for task in self._tasks]
        return [(status, statuses.count(status)) for status in TaskStatus]

    def clean(self):
        """Cleans the tasks."""
        self._tasks = []
        global error_callback
        error_callback = 0

    @property
    def queue(self) -> List[Task]:
        """Tasks that are new or pending.

        Returns:
            List[Task]: A list of tasks in the queue.
        """
        return [
            t for t in self._tasks if t.status in (TaskStatus.NEW, TaskStatus.PENDING)
        ]

    def _error_callback(self, excpt: Exception):
        """Error callback method used during the "get" execution.
        It is used when a sub-process fails and logs the caught exception.

        Args:
            excpt: The exception to log.
        """
        try:
            trace = traceback.format_exception(type(excpt), excpt, excpt.__traceback__)
            LOGGER.error(f"An error has been caught: {repr(excpt)}.\n" + "".join(trace))
        finally:
            global error_callback
            error_callback += 1

    def append(
        self,
        func: Callable,
        task_name: str,
        args: Optional[Iterable] = None,
        callback: Optional[Callable] = None,
    ):
        """Appends a task into the queue following an "apply" schema, which means
        providing a function and its arguments and keyword arguments.

        Warning: This method doesn't trigger any processing. To run the
        loaded tasks, you must call self.run() after.

        Args:
            func: The function to apply.
            task_name: The name of the task (for logging purposes).
            args: The arguments to pass to the function. Defaults to None.
            callback: The function to call when the data is ready. Defaults to None.
        """
        self._tasks.append(
            Task(func=func, args=args, callback=callback, name=task_name)
        )

    def run(self, name: Optional[str] = "", timeout: Optional[float] = None):
        if Settings().disable_parallel:
            self.run_sync(name, timeout)
        else:
            self.run_async(name, timeout)

    def run_sync(self, name: Optional[str] = "", timeout: Optional[float] = None):
        """
        Executes tasks sequentially with optional timeout.

        Args:
            name: Task name, empty by default.
            timeout: Optional timeout in seconds. If specified, processing will stop
                after the timeout is reached, even if there are still tasks remaining.

        Logs:
            - Information about the start and end of processing, including the number
              of tasks processed and elapsed time.
            - Timeout message if a timeout occurs.
        """
        start = time.time()
        LOGGER.info(
            f"{name} Starting sequential processing:"
            f" {len(self.queue)} tasks to process."
        )
        num_successful_tasks = 0
        for idx, task in enumerate(self._tasks):
            # Handling of timeout
            if timeout is not None and time.time() - start > timeout:
                LOGGER.warning("Timeout reached, stopping processing.")
                for timeout_task in self._tasks[idx:]:
                    timeout_task.change_status(TaskStatus.TIMEOUT)
                break
            try:
                task.run()
                num_successful_tasks += 1
            except Exception as excpt:
                LOGGER.error(f"Task execution failed with exception: {excpt}")

        LOGGER.info(
            "{name} End of sequential processing."
            f"\t{num_successful_tasks -error_callback}/{len(self._tasks)} tasks done."
            f"\tElapsed time: {time.time() - start:.3f}s."
        )

    def run_async(self, name: Optional[str] = "", timeout: Optional[float] = None):
        """
        Launches asynchronous processing of the previously loaded tasks using a process
        pool.

        Args:
            name: Task name, empty by default.
            timeout: The maximum duration in seconds to run all the tasks. Defaults to
                None.
        """

        start = time.time()
        keep_running = True
        remaining_time = 1
        nbr_successful_tasks = 0

        LOGGER.info(
            f"{name} Starting parallel processing: {len(self.queue)} tasks to process."
        )
        while keep_running and remaining_time > 0:
            # Manage remaining time
            if timeout is not None:
                elapsed_time = time.time() - start
                remaining_time = max(timeout - elapsed_time, 0)
            keep_running, successful_task = self._run_async_loop()
            nbr_successful_tasks += successful_task

        for task in self.queue:
            try:
                task.async_result.get(timeout=0)
                task.change_status(TaskStatus.DONE)
                nbr_successful_tasks += 1
            except MultiTimeoutError:
                task.change_status(TaskStatus.TIMEOUT)
                LOGGER.warning(f"Timeout for task {task.name}")
            except Exception:
                task.change_status(TaskStatus.FAILED, exc_info=True)
                LOGGER.error(f"Task {task.name} failed")

        LOGGER.info(
            f"{name} End of parallel processing."
            f"\t{nbr_successful_tasks}/{len(self._tasks)} tasks done."
            f"\tElapsed time: {time.time() - start:.3f}s."
            f"\t(errors in callback {error_callback})."
        )

    def _run_async_loop(self) -> Tuple[bool, int]:
        keep_running, successful_task = False, 0
        for task in self.queue:
            if task.status == TaskStatus.NEW:
                task.async_result = self.pool.apply_async(
                    WrapCall(task.name, task.func).pre_call,
                    args=task.args,
                    callback=task.callback,
                    error_callback=self._error_callback,
                )
                task.change_status(TaskStatus.PENDING)
                time.sleep(0.001)  # To force the process to start
                keep_running = True
            elif task.async_result.ready():
                if task.async_result.successful():
                    task.change_status(TaskStatus.DONE)
                    successful_task += 1
                else:
                    task.change_status(TaskStatus.FAILED)
            else:
                keep_running = True

        time.sleep(0.5)  # To prevent main CPU hogging
        return keep_running, successful_task
