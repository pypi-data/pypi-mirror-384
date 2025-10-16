# Copyright 2025 t54 labs
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import Any, Dict

import asyncio
import os
from .headers import build_payment_secure_header, start_client_span
from .risk import RiskClient
from .buyer import BuyerClient


async def store_agent_trace(
    *,
    risk: RiskClient,
    sid: str,
    task: str,
    params: Dict[str, Any],
    environment: Dict[str, Any],
    events: list[Dict[str, Any]],
    model_config: Optional[Dict[str, Any]] = None,
    session_context: Optional[Dict[str, Any]] = None,
) -> str:
    import time
    import hashlib
    
    agent_trace: Dict[str, Any] = {
        "task": task,
        "parameters": params,
        "environment": environment,
        "events": events,
    }
    
    # Add model configuration if provided
    if model_config:
        agent_trace["model_config"] = model_config
    
    # Add session context if provided
    if session_context:
        agent_trace["session_context"] = session_context
    
    # Add timestamps
    agent_trace["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    # Print agent trace context before uploading
    print("\n" + "="*80)
    print("📊 AGENT TRACE CONTEXT (before upload)")
    print("="*80)
    print(f"🎯 Task: {task}")
    print(f"📝 Parameters: {params}")
    print(f"🌍 Environment: {environment}")
    if model_config:
        print(f"🤖 Model Config:")
        print(f"   Provider: {model_config.get('provider', 'N/A')}")
        print(f"   Model: {model_config.get('model', 'N/A')}")
        print(f"   Tools: {', '.join(model_config.get('tools_enabled', []))}")
    if session_context:
        print(f"🔐 Session Context:")
        print(f"   Session ID: {session_context.get('session_id', 'N/A')}")
        print(f"   Request ID: {session_context.get('request_id', 'N/A')}")
        if 'client_ip_hash' in session_context:
            print(f"   Client IP (hashed): {session_context['client_ip_hash'][:16]}...")
    print(f"📋 Events: {len(events)} total")
    
    # Show user inputs
    user_inputs = [e for e in events if e.get('type') == 'user_input']
    if user_inputs:
        print(f"\n   👤 User Inputs ({len(user_inputs)} items):")
        for i, evt in enumerate(user_inputs, 1):
            content = evt.get('content', '')
            print(f"      {i}. {content[:80]}{'...' if len(content) > 80 else ''}")
    
    # Show agent outputs
    agent_outputs = [e for e in events if e.get('type') == 'agent_output']
    if agent_outputs:
        print(f"\n   🤖 Agent Outputs ({len(agent_outputs)} items):")
        for i, evt in enumerate(agent_outputs, 1):
            content = evt.get('content', '')
            print(f"      {i}. {content[:80]}{'...' if len(content) > 80 else ''}")
    
    # Show last few events
    if events:
        print("\n   Recent events:")
        for i, evt in enumerate(events[-5:], 1):
            evt_type = evt.get('type', 'unknown')
            evt_name = evt.get('name', 'N/A')
            print(f"      {i}. {evt_type}: {evt_name}")
    print("="*80 + "\n")
    
    tid = (await risk.create_trace(sid=sid, agent_trace=agent_trace))["tid"]
    print(f"✅ Agent trace uploaded, tid: {tid}\n")
    return tid


async def execute_payment_with_tid(
    *,
    buyer: BuyerClient,
    endpoint: str,
    task: str,
    params: Dict[str, Any],
    sid: str,
    tid: str,
) -> Any:
    with start_client_span("buyer.payment"):
        xps = build_payment_secure_header(agent_trace_context={"tid": tid})
        return await buyer.execute_paid_request(
            endpoint,
            task=task,
            params=params,
            risk_sid=sid,
            extra_headers=xps,
        )

def _resolve_handlers_from_defs(tool_defs: list, tracer, explicit: dict | None) -> dict:
    if explicit:
        return {name: tracer.tool(fn) for name, fn in explicit.items()}
    resolved: dict = {}
    ns = os.getenv("X402_AGENT_TOOL_NS")
    import importlib

    for td in tool_defs or []:
        try:
            f = td.get("function") if isinstance(td, dict) else getattr(td, "function", None)
        except Exception:
            f = None
        if not f:
            continue
        name = f.get("name") if isinstance(f, dict) else getattr(f, "name", None)
        if not name:
            continue
        xp = (f.get("x-python") or f.get("x_python")) if isinstance(f, dict) else None
        fn = None
        if xp:
            mod, attr = xp.split(":", 1)
            fn = getattr(importlib.import_module(mod), attr, None)
        elif ns:
            mod = importlib.import_module(ns)
            fn = getattr(mod, name, None)
        if fn is not None:
            resolved[name] = tracer.tool(fn)
    if not resolved:
        raise RuntimeError("No tool handlers resolvable; pass tools mapping, set X402_AGENT_TOOL_NS, or add x-python to tool_defs")
    return resolved


async def run_agent_payment(
    *,
    buyer: BuyerClient,
    gateway_url: str,
    messages: list[dict],
    tools: dict[str, callable] | None,
    tool_defs: list,
    task: str,
    environment: dict,
    model: str | None = None,
    plan_key: str = "prepare_payment",
) -> any:
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:  # pragma: no cover - soft import for examples
        raise RuntimeError("OpenAI package not installed. pip install openai") from e

    from .tracing import OpenAITraceCollector

    tracer = OpenAITraceCollector()
    wrapped_tools = _resolve_handlers_from_defs(tool_defs, tracer, tools)

    client = OpenAI()
    with client.responses.stream(
        model=model or os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        input=messages,
        tools=tool_defs,
        reasoning={"effort": "low", "summary": "auto"},
    ) as stream:
        result = asyncio.get_event_loop().run_until_complete(
            tracer.process_stream(stream, tools=wrapped_tools)
        )
    tool_results = result.get("tool_results") or {}
    plan = tool_results.get(plan_key)
    if not plan or plan.get("error"):
        raise RuntimeError("agent did not produce a valid payment plan")

    # Create session + store trace
    rc = RiskClient(gateway_url)
    # TODO: When integrating with EIP-8004, pass did:eip8004:{chain_id}:{contract}:{token_id}
    sid = (await rc.create_session(agent_did=buyer.address, app_id=None, device={"ua": "x402-agent"}))[
        "sid"
    ]
    tid = await store_agent_trace(
        risk=rc,
        sid=sid,
        task=task,
        params=plan.get("params") or {},
        environment=environment,
        events=tracer.events,
    )

    # Execute payment
    endpoint = plan.get("endpoint")
    if not endpoint:
        raise RuntimeError("payment plan missing endpoint")
    return await execute_payment_with_tid(
        buyer=buyer,
        endpoint=endpoint,
        task=task,
        params=plan.get("params") or {},
        sid=sid,
        tid=tid,
    )
