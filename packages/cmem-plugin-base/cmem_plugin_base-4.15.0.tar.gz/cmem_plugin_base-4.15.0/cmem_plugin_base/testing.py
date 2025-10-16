"""Module provides context classes for testing purposes in the CMEM plugin environment.

Classes included in this module:
- TestUserContext: testing user context with token management
- TestPluginContext: testing plugin context
- TestTaskContext: testing task context
- TestExecutionContext: testing execution context with task and user linkage
- TestSystemContext: testing system context with encryption/decryption placeholders
- TestWorkflowContext: testing workflow context with workflow ID and status

These classes are intended for use in unit tests and other testing scenarios where real
context objects are unavailable or unnecessary.
"""

from typing import ClassVar, Literal

from cmem.cmempy.api import get_token
from cmem.cmempy.config import get_oauth_default_credentials

from cmem_plugin_base.dataintegration.context import (
    ExecutionContext,
    PluginContext,
    ReportContext,
    SystemContext,
    TaskContext,
    UserContext,
    WorkflowContext,
)


class TestUserContext(UserContext):
    """Testing user context"""

    __test__ = False
    default_credential: ClassVar[dict] = {}

    def __init__(self):
        if not TestUserContext.default_credential:
            TestUserContext.default_credential = get_oauth_default_credentials()
        self.access_token = get_token(_oauth_credentials=TestUserContext.default_credential)[
            "access_token"
        ]

    def token(self) -> str:
        """Get an access token"""
        return f"{self.access_token}"


class TestPluginContext(PluginContext):
    """Testing plugin context"""

    __test__ = False

    def __init__(self, project_id: str = "TestProject"):
        self.project_id = project_id
        self.user = TestUserContext()


class TestTaskContext(TaskContext):
    """Testing task context"""

    __test__ = False

    def __init__(self, project_id: str = "TestProject", task_id: str = "TestTask"):
        self._project_id = project_id
        self._task_id = task_id

    def project_id(self) -> str:
        """Get the project ID."""
        return self._project_id

    def task_id(self) -> str:
        """Get the task ID."""
        return self._task_id


class TestExecutionContext(ExecutionContext):
    """Testing execution context"""

    __test__ = False

    def __init__(
        self,
        project_id: str = "TestProject",
        task_id: str = "TestTask",
        workflow_id: str = "TestWorkflow",
    ):
        self.system = TestSystemContext()
        self.report = ReportContext()
        self.task = TestTaskContext(project_id=project_id, task_id=task_id)
        self.user = TestUserContext()
        self.workflow = TestWorkflowContext(workflow_id=workflow_id)


class TestSystemContext(SystemContext):
    """Testing system context"""

    __test__ = False

    def __init__(self) -> None:
        self._version: str = "1.0.0"

    def di_version(self) -> str:
        """Get data integration version."""
        return self._version

    def encrypt(self, value: str) -> str:
        """Encrypt a value."""
        return value

    def decrypt(self, value: str) -> str:
        """Decrypt a value."""
        return value


class TestWorkflowContext(WorkflowContext):
    """Testing workflow context"""

    __test__ = False

    def __init__(
        self,
        workflow_id: str = "TestWorkflow",
        status: Literal["Idle", "Waiting", "Running", "Canceling", "Finished"] = "Running",
    ):
        self._workflow_id = workflow_id
        self._status = status

    def workflow_id(self) -> str:
        """Get the workflow ID."""
        return self._workflow_id

    def status(self) -> Literal["Idle", "Waiting", "Running", "Canceling", "Finished"]:
        """Get the workflow status."""
        return self._status
