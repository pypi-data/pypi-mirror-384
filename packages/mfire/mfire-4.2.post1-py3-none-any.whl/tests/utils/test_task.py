import time

import pytest

from mfire.settings import Settings
from mfire.utils.task import Task, Tasks, TaskStatus


def func(arg: str) -> str:
    if arg == "error":
        raise ValueError("error")
    if arg == "timeout":
        time.sleep(6)
        return "timeout"
    return arg


class TestTask:
    def test_default_init(self):
        task = Task(func=func)
        assert str(task) == "Task (status=NEW)"

    def test_change_status(self):
        task = Task(func=func)
        assert task.status == TaskStatus.NEW

        task.change_status(TaskStatus.PENDING)
        assert task.status == TaskStatus.PENDING

        task.change_status(TaskStatus.FAILED)
        assert task.status == TaskStatus.FAILED

    def test_run(self):
        task = Task(func=func, args=("success",))
        result = task.run()
        assert task.status == TaskStatus.DONE
        assert result == "success"

        task = Task(func=func, args=("error",))
        with pytest.raises(ValueError, match="error"):
            task.run()
        assert task.status == TaskStatus.FAILED


class TestTasks:
    def test_append(self):
        tasks = Tasks()
        tasks.append(func, task_name="task1")
        tasks.append(func, task_name="task2")

        assert len(tasks._tasks) == 2
        assert tasks._tasks[0].name == "task1"
        assert tasks._tasks[1].name == "task2"

    def test_clean(self):
        p = Tasks()
        p.append(func, task_name="TestParallel")
        assert len(p) == 1

        p.clean()
        assert len(p) == 0

    def test_run_sync(self):
        tasks, res = Tasks(2), []
        for task in ["success", "error", "success", "timeout", "success", "error"]:
            tasks.append(
                func, task_name="TestSequential", args=(task,), callback=res.append
            )

        tasks.run_sync(timeout=5)
        assert res == ["success", "success", "timeout"]

        expected_statuses = [
            TaskStatus.DONE,
            TaskStatus.FAILED,
            TaskStatus.DONE,
            TaskStatus.DONE,
            TaskStatus.TIMEOUT,
            TaskStatus.TIMEOUT,
        ]
        for task, exp_status in zip(tasks, expected_statuses):
            assert task.status == exp_status

        assert str(tasks) == "Tasks(6 tasks: 1 FAILED; 2 TIMEOUT; 3 DONE)"

    def test_run_async(self):
        tasks, res = Tasks(2), []
        for task in ["success", "error", "success", "timeout", "success", "error"]:
            tasks.append(
                func, task_name="TestSequential", args=(task,), callback=res.append
            )

        tasks.run_async(timeout=5)
        assert res == ["success", "success"]

        expected_statuses = [
            TaskStatus.DONE,
            TaskStatus.FAILED,
            TaskStatus.DONE,
            TaskStatus.TIMEOUT,
            TaskStatus.TIMEOUT,
            TaskStatus.TIMEOUT,
        ]
        for task, exp_status in zip(tasks, expected_statuses):
            assert task.status == exp_status

        assert str(tasks) == "Tasks(6 tasks: 1 FAILED; 3 TIMEOUT; 2 DONE)"

    @pytest.mark.parametrize(
        "disable_parallel,expected",
        [(False, ["success", "success"]), (True, ["success", "success", "timeout"])],
    )
    def test_run(self, disable_parallel, expected):
        Settings().set(disable_parallel=disable_parallel)
        tasks, res = Tasks(2), []
        for task in ["success", "error", "success", "timeout", "success", "error"]:
            tasks.append(
                func, task_name="TestSequential", args=(task,), callback=res.append
            )
        tasks.run(timeout=5)

        assert res == expected
