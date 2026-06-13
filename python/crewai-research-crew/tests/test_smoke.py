"""Smoke tests for crewai-research-crew — offline, no gateway required."""
from __future__ import annotations

from uuid import uuid4

import pytest

from agent_assembly.adapters.langchain import AssemblyCallbackHandler
from agent_assembly.exceptions import ToolExecutionBlockedError

from src.policy import CrewPolicyEngine, MockApprover


@pytest.fixture
def policy() -> CrewPolicyEngine:
    return CrewPolicyEngine(approver=MockApprover(auto_approve=False), daily_budget_usd=2.00)


@pytest.fixture
def handler(policy: CrewPolicyEngine) -> AssemblyCallbackHandler:
    return AssemblyCallbackHandler(interceptor=policy)


def _call(handler: AssemblyCallbackHandler, tool: str, payload: str = "{}") -> None:
    handler.on_tool_start(
        serialized={"name": tool}, input_str=payload, run_id=uuid4()
    )


def test_researcher_tool_call_is_allowed(
    handler: AssemblyCallbackHandler, policy: CrewPolicyEngine
) -> None:
    policy.acting_as("researcher")
    _call(handler, "web_search", '{"query": "agent governance"}')
    assert policy.budget.spent == pytest.approx(0.05)


def test_file_write_requires_approval_and_is_rejected(
    handler: AssemblyCallbackHandler, policy: CrewPolicyEngine
) -> None:
    policy.acting_as("critic", parent="writer")
    with pytest.raises(ToolExecutionBlockedError, match="without sign-off"):
        _call(handler, "write_file", '{"path": "report.md"}')


def test_file_write_passes_when_approver_accepts() -> None:
    policy = CrewPolicyEngine(approver=MockApprover(auto_approve=True))
    handler = AssemblyCallbackHandler(interceptor=policy)
    policy.acting_as("critic", parent="writer")
    _call(handler, "write_file", '{"path": "report.md"}')
    assert policy.audit_events[-1].decision == "allow"


def test_delegation_chain_is_captured_in_call_stack(
    handler: AssemblyCallbackHandler, policy: CrewPolicyEngine
) -> None:
    policy.acting_as("critic", parent="writer")
    _call(handler, "review_text", '{"target": "summary"}')
    event = policy.audit_events[-1]
    assert event.agent_id == "critic"
    assert event.labels["delegated_by"] == "writer"
    # call_stack is parent → agent → tool
    parent_node = event.call_stack[0]
    assert parent_node.label == "writer"
    agent_node = parent_node.children[0]
    assert agent_node.label == "critic"
    assert agent_node.children[0].label == "review_text"


def test_shared_budget_is_enforced_across_agents(policy: CrewPolicyEngine) -> None:
    handler = AssemblyCallbackHandler(interceptor=policy)
    blocked = False
    agents = ("researcher", "writer", "critic")
    for i in range(100):
        policy.acting_as(agents[i % len(agents)])
        try:
            _call(handler, "web_search", '{"query": "x"}')
        except ToolExecutionBlockedError as exc:
            assert "crew daily budget is exhausted" in str(exc)
            blocked = True
            break
    assert blocked, "expected the shared crew budget to block a call"


def test_init_assembly_sdk_only_requires_no_gateway() -> None:
    from unittest.mock import patch

    from agent_assembly import init_assembly
    from agent_assembly.core import assembly as _core

    with patch.object(_core, "_register_adapters", return_value=[]):
        with patch.object(
            _core, "_start_network_layer", return_value=("sdk-only", lambda: None)
        ):
            ctx = init_assembly(
                gateway_url="http://localhost:8080",
                agent_id="test-crew",
                mode="sdk-only",
            )
            try:
                assert ctx.client.agent_id == "test-crew"
                assert ctx.network_mode == "sdk-only"
            finally:
                ctx.shutdown()
