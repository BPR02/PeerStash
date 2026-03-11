from datetime import datetime

import pytest
from pytest_mock import MockerFixture


class MockTask:
    """A simple class to represent a Task DB record."""

    def __init__(
        self,
        name,
        include,
        exclude,
        hostname,
        schedule,
        retention,
        prune_schedule="0 4 * * 0",
        status="idle",
    ):
        self.name = name
        self.include = include
        self.exclude = exclude
        self.hostname = hostname
        self.schedule = schedule
        self.retention = retention
        self.prune_schedule = prune_schedule
        self.status = status
        self.last_run = datetime.now()
        self.last_exit_code = 0


@pytest.fixture
def mock_db(mocker: MockerFixture):
    """
    Mocks the database layer using an in-memory dictionary.
    This allows state to persist across mock function calls within a single test.
    """
    db_state = {
        "tasks": {},
        "users": {"mockuser": True},
        "hosts": {"peerstash-node1": True},
    }

    # DB Helper Mocks
    mocker.patch("peerstash.core.db.db_get_user", return_value="mockuser")
    mocker.patch(
        "peerstash.core.db.db_host_exists", side_effect=lambda h: h in db_state["hosts"]
    )

    # Task Mocks
    def mock_get_task(name):
        return db_state["tasks"].get(name)

    def mock_task_exists(name):
        return name in db_state["tasks"]

    def mock_add_task(
        name, include, exclude, hostname, schedule, retention, prune_schedule
    ):
        db_state["tasks"][name] = MockTask(
            name, include, exclude, hostname, schedule, retention, prune_schedule
        )

    def mock_update_task(name, task_update):
        if name in db_state["tasks"]:
            task = db_state["tasks"][name]
            for key, value in task_update.__dict__.items():
                if value is not None:
                    setattr(task, key, value)

    def mock_delete_task(name):
        if name in db_state["tasks"]:
            del db_state["tasks"][name]
            return True
        return False

    mocker.patch("peerstash.core.db.db_get_task", side_effect=mock_get_task)
    mocker.patch("peerstash.core.db.db_task_exists", side_effect=mock_task_exists)
    mocker.patch("peerstash.core.db.db_add_task", side_effect=mock_add_task)
    mocker.patch("peerstash.core.db.db_update_task", side_effect=mock_update_task)
    mocker.patch("peerstash.core.db.db_delete_task", side_effect=mock_delete_task)

    # Return the state dict so tests can inspect or prepopulate it if needed
    return db_state
