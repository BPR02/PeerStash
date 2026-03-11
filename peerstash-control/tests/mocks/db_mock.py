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

    # Helper function to patch multiple modules at once to avoid "from X import Y" reference bugs.
    def multi_patch(func_name, target_modules, side_effect=None, return_value=None):
        for mod in target_modules:
            patch_target = f"{mod}.{func_name}"
            if side_effect is not None:
                mocker.patch(patch_target, side_effect=side_effect, create=True)
            else:
                mocker.patch(patch_target, return_value=return_value, create=True)

    # DB Helper Mocks
    multi_patch(
        "db_get_user",
        ["peerstash.core.db", "peerstash.core.backup", "peerstash.core.identity"],
        return_value="mockuser",
    )

    multi_patch(
        "db_host_exists",
        ["peerstash.core.db", "peerstash.core.backup", "peerstash.core.registration"],
        side_effect=lambda h: h in db_state["hosts"],
    )

    multi_patch(
        "db_get_invite_code",
        ["peerstash.core.db", "peerstash.core.identity"],
        return_value="invite_xyz",
    )

    multi_patch(
        "db_add_host",
        ["peerstash.core.db", "peerstash.core.registration"],
        side_effect=lambda h, k: db_state["hosts"].update({h: True}),
    )

    multi_patch("db_update_host", ["peerstash.core.db", "peerstash.core.registration"])

    multi_patch(
        "db_delete_host",
        ["peerstash.core.db", "peerstash.core.registration"],
        side_effect=lambda h: db_state["hosts"].pop(h, None),
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

    multi_patch(
        "db_get_task",
        ["peerstash.core.db", "peerstash.core.backup"],
        side_effect=mock_get_task,
    )

    multi_patch(
        "db_task_exists",
        ["peerstash.core.db", "peerstash.core.backup"],
        side_effect=mock_task_exists,
    )

    multi_patch(
        "db_add_task",
        ["peerstash.core.db", "peerstash.core.backup"],
        side_effect=mock_add_task,
    )

    multi_patch(
        "db_update_task",
        ["peerstash.core.db", "peerstash.core.backup"],
        side_effect=mock_update_task,
    )

    multi_patch(
        "db_delete_task",
        ["peerstash.core.db", "peerstash.core.backup"],
        side_effect=mock_delete_task,
    )

    return db_state
