from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any, Literal

import itkdb
from itkdb.models.component import Component as ITkDBComponent

from module_qc_database_tools.typing_compat import Dict

log = logging.getLogger(__name__)


def tests(self: ITkDBComponent) -> list[Dict[str, Any]]:
    """
    List of the tests on the component grouped by test type.
    """
    return self._data.get("tests", [])  # pylint: disable=protected-access


def test_runs(self: ITkDBComponent) -> list[Dict[str, Any]]:
    """
    List of the test runs on the component.
    """
    return [testRun for test in self.tests for testRun in test.get("testRuns", [])]


def current_stage(self: ITkDBComponent) -> str | None:
    """
    Current stage code of the component.
    """
    return self._data.get("currentStage", {}).get("code")  # pylint: disable=protected-access


def component_type(self: ITkDBComponent) -> str | None:
    """
    Component type code of the component.
    """
    return self._data.get("componentType", {}).get("code")  # pylint: disable=protected-access


def attachments(self: ITkDBComponent) -> list[ITkDBAttachment]:
    """
    List of attachments on the component.
    """
    return [
        ITkDBComponentAttachment(self._client, attachment, identifier=self.id)  # pylint: disable=protected-access
        for attachment in self._data.get("attachments", {})  # pylint: disable=protected-access
    ]


def inject_tests(self: ITkDBComponent):
    """
    Call this function to query the production database to expand the test information stored on the component for every test.
    """
    for test in self.tests:
        log.debug("fetching %s tests for %s", test["code"], self.serial_number)
        test["testRuns"] = [
            ITkDBTestRun(self._client, test_run)  # pylint: disable=protected-access
            for test_run in self._client.get(  # pylint: disable=protected-access
                "getTestRunBulk",
                json={
                    "testRun": [
                        test_run["id"]
                        for test_run in test.get("testRuns", [])
                        if test_run.get("state") == "ready"
                    ]
                },
            )
        ]


def relationships(self: ITkDBComponent) -> Iterable[ITkDBComponent, ITkDBComponent]:
    """
    Generator that yields (parent, child) pairs for all (sub)components from the top-level component.
    """
    for child in self.children:
        yield (self, child)
        yield from child.relationships


def children_flattened(self: ITkDBComponent) -> Iterable[ITkDBComponent]:
    """
    Generator that yields all children on this component, not including the top-level component.
    """
    for child in self.children:
        yield child
        yield from child.children_flattened


_old_walk = ITkDBComponent.walk


def walk(self: ITkDBComponent, recurse: bool = True) -> None:
    """
    Updated Component.walk() functionality that also injects test runs on the component as it walks through.
    """
    _old_walk(self, recurse=recurse)
    self.inject_tests()


def to_str(self: ITkDBComponent) -> str:
    """
    Update the Component.__str__ representation.
    """
    return f"{self.serial_number} ([bright_black]{self.component_type}[/])"


ITkDBComponent.tests = property(tests)
ITkDBComponent.test_runs = property(test_runs)
ITkDBComponent.current_stage = property(current_stage)
ITkDBComponent.component_type = property(component_type)
ITkDBComponent.attachments = property(attachments)
ITkDBComponent.relationships = property(relationships)
ITkDBComponent.children_flattened = property(children_flattened)
ITkDBComponent.inject_tests = inject_tests
ITkDBComponent.walk = walk
ITkDBComponent.__rich__ = to_str
ITkDBComponent.__str__ = to_str


class ITkDBTestRunComponent(ITkDBComponent):
    """
    Similar to ITkDBComponent, but with additional accessors specifically for the testRun components field.
    """

    @property
    def tested_at_stage(self: ITkDBComponent) -> str | None:
        """
        Tested At Stage for component test run.
        """
        return self._data.get("testedAtStage", {}).get("code")  # pylint: disable=protected-access


class ITkDBTestRun:
    """TestRun model"""

    def __init__(self: ITkDBTestRun, client: itkdb.Client, data: Dict[str, Any]):
        self._client = client
        self._data = data

    @property
    def test_type(self: ITkDBTestRun) -> str:
        """test type code of test run"""
        return self._data.get("testType", {}).get("code") or ""

    @property
    def id(self: ITkDBTestRun) -> str:  # pylint: disable=invalid-name
        """unique identifier of component"""
        return str(self._data["id"])

    @property
    def run_number(self: ITkDBTestRun) -> str:
        """run number of test run"""
        return self._data["runNumber"]

    @property
    def properties(self: ITkDBTestRun) -> Dict[str, Any]:
        """
        Get the properties for this test run.
        """
        return {
            item["code"]: item["value"]
            for item in sorted(
                self._data.get("properties", []), key=lambda x: x["code"]
            )
        }

    @property
    def parameters(self: ITkDBTestRun) -> Dict[str, Any]:
        """
        Get the parameters for this test run.
        """
        return {
            item["code"]: item["value"]
            for item in sorted(
                self._data.get("parameters", []), key=lambda x: x["code"]
            )
        }

    @property
    def results(self: ITkDBTestRun) -> Dict[str, Any]:
        """
        Get the results for this test run.
        """
        return {
            item["code"]: item["value"]
            for item in sorted(self._data.get("results", []), key=lambda x: x["code"])
        }

    @property
    def components(self) -> list[ITkDBTestRunComponent]:
        """
        Get the components associated with this test run.
        """
        return [
            ITkDBTestRunComponent(self._client, component)
            for component in (self._data.get("components") or [])
        ]

    @property
    def attachments(self: ITkDBTestRun) -> list[ITkDBAttachment]:
        """
        List of attachments on the test run.
        """
        return [
            ITkDBTestRunAttachment(self._client, attachment, identifier=self.id)
            for attachment in self._data.get("attachments", {})  # pylint: disable=protected-access
        ]

    @property
    def stage(self: ITkDBComponent) -> str | None:
        """
        Stage this test run was tested at.
        """
        if self.components:
            return self.components[0].tested_at_stage

        return None

    @property
    def institution(self: ITkDBComponent) -> str | None:
        """
        Institution this test run was tested at.
        """
        return self._data.get("institution", {}).get("code")

    def __str__(self: ITkDBTestRun) -> str:
        """
        Define the ITkDBTestRun.__str__ representation.
        """
        return f"{self.id} ([bright_black]{self.test_type} @ {self.stage}[/])"

    def __rich__(self: ITkDBTestRun) -> str:
        return str(self)

    def __repr__(self: ITkDBTestRun) -> str:
        module = type(self).__module__
        qualname = type(self).__qualname__
        return f"<{module}.{qualname} object '{self.test_type}' at {hex(id(self))}>"


class ITkDBAttachment:
    """Attachment model"""

    __kind__: Literal["", "component", "testRun", "shipment", "batch"] = ""
    __endpoint__: Literal[
        "",
        "getComponentAttachment",
        "getTestRunAttachment",
        "getShipmentAttachment",
        "getBatchAttachment",
    ] = ""

    def __init__(
        self: ITkDBAttachment,
        client: itkdb.Client,
        data: Dict[str, Any],
        *,
        identifier: str,
    ):
        self._client = client
        self._data = data
        self._identifier = identifier

    @property
    def type(self: ITkDBAttachment) -> str:
        """type of attachment"""
        return self._data.get("type") or ""

    @property
    def code(self: ITkDBAttachment) -> str:
        """code of attachment"""
        return self._data.get("code") or ""

    @property
    def title(self: ITkDBAttachment) -> str:
        """title of attachment"""
        return self._data.get("title") or ""

    @property
    def description(self: ITkDBAttachment) -> str:
        """description of attachment"""
        return self._data.get("description") or ""

    @property
    def filename(self: ITkDBAttachment) -> str:
        """filename of attachment"""
        return self._data.get("filename") or ""

    @property
    def url(self: ITkDBAttachment) -> str:
        """url of attachment"""
        return self._data.get("url")

    @property
    def kind(self: ITkDBAttachment) -> str:
        """
        The kind of object the attachment is associated with.
        """
        if self.__kind__ is None:
            msg = "Should be using an inherited class"
            raise RuntimeError(msg)
        return self.__kind__

    @property
    def endpoint(self: ITkDBAttachment) -> str:
        """
        The endpoint to use for downloading the attachment from production database.
        """
        if self.__endpoint__ is None:
            msg = "Should be using an inherited class"
            raise RuntimeError(msg)
        return self.__endpoint__

    def download(self: ITkDBAttachment) -> itkdb.models.file.BinaryFile:
        """
        Download this attachment from either Production Database or EOS.
        """
        if self.type == "eos":
            return self._client.get(self.url)  # pylint: disable=protected-access

        return self._client.get(  # pylint: disable=protected-access
            self.endpoint,
            json={self.kind: self._identifier, "code": self.code},  # pylint: disable=protected-access
        )

    def __str__(self: ITkDBAttachment) -> str:
        """
        Define the ITkDBAttachment.__str__ representation.
        """
        return f"{self.title} ([bright_black]{self.filename}[/])"

    def __rich__(self: ITkDBAttachment) -> str:
        return str(self)

    def __repr__(self: ITkDBAttachment) -> str:
        module = type(self).__module__
        qualname = type(self).__qualname__
        return f"<{module}.{qualname} object '{self.title}' at {hex(id(self))}>"


class ITkDBComponentAttachment(ITkDBAttachment):
    """
    Model for attachments on components.
    """

    __kind__ = "component"
    __endpoint__ = "getComponentAttachment"


class ITkDBTestRunAttachment(ITkDBAttachment):
    """
    Model for attachments on test runs.
    """

    __kind__ = "testRun"
    __endpoint__ = "getTestRunAttachment"


class ITkDBShipmentAttachment(ITkDBAttachment):
    """
    Model for attachments on shipments.
    """

    __kind__ = "shipment"
    __endpoint__ = "getShipmentAttachment"


class ITkDBBatchAttachment(ITkDBAttachment):
    """
    Model for attachments on batches.
    """

    __kind__ = "batch"
    __endpoint__ = "getBatchAttachment"


__all__ = ("ITkDBAttachment", "ITkDBComponent", "ITkDBTestRun")
