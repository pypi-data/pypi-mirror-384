"""
Test Enhanced Streaming Functionality

This test script verifies that the enhanced streaming system works correctly:
1. Streaming events are emitted properly
2. Event callbacks work
3. Tool emit functions work
4. Simple vs Enhanced handlers behave correctly
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from masai.Tools.utilities.streaming_events import (
    StreamingEvent,
    emit_tool_call,
    emit_tool_output,
    emit_custom_event,
    set_streaming_callback,
    clear_streaming_callback,
    get_streaming_callback
)


# ============================================================================
# TEST 1: Basic Event Creation and Formatting
# ============================================================================

def test_event_creation():
    """Test that StreamingEvent can be created and formatted."""
    print("\n" + "="*70)
    print("TEST 1: Event Creation and Formatting")
    print("="*70)
    
    # Test tool_call event
    event = StreamingEvent(
        event_type="tool_call",
        data={"tool_name": "search_db", "tool_input": {"query": "test"}},
        metadata={"node": "execute_tool"}
    )
    
    print("\n✅ Created tool_call event:")
    print(f"   Type: {event.event_type}")
    print(f"   Data: {event.data}")
    print(f"   Metadata: {event.metadata}")
    
    # Test SSE formatting
    sse_output = event.to_openai_sse("test-model")
    print("\n✅ SSE Format:")
    print(f"   {sse_output[:200]}...")
    
    # Verify it's valid JSON
    import json
    try:
        json_data = json.loads(sse_output.split("data: ")[1].strip())
        print(f"\n✅ Valid JSON: {json_data['event_type']}")
        print(f"   Model: {json_data['model']}")
        print(f"   Has choices: {len(json_data['choices']) > 0}")
    except Exception as e:
        print(f"\n❌ JSON parsing failed: {e}")
        return False
    
    print("\n✅ TEST 1 PASSED")
    return True


# ============================================================================
# TEST 2: Callback System
# ============================================================================

async def test_callback_system():
    """Test that callback system works correctly."""
    print("\n" + "="*70)
    print("TEST 2: Callback System")
    print("="*70)
    
    received_events = []
    
    async def test_callback(event: StreamingEvent):
        """Test callback that collects events."""
        received_events.append(event)
        print(f"\n✅ Callback received: {event.event_type}")
        print(f"   Data: {event.data}")
    
    # Test 1: No callback set
    print("\n📊 Test 2.1: No callback set")
    callback = get_streaming_callback()
    print(f"   Callback: {callback}")
    assert callback is None, "Callback should be None initially"
    print("   ✅ Correct: No callback set")
    
    # Test 2: Set callback
    print("\n📊 Test 2.2: Set callback")
    set_streaming_callback(test_callback)
    callback = get_streaming_callback()
    print(f"   Callback: {callback}")
    assert callback is not None, "Callback should be set"
    print("   ✅ Correct: Callback is set")
    
    # Test 3: Emit events with callback
    print("\n📊 Test 2.3: Emit events with callback")
    await emit_tool_call("test_tool", {"arg": "value"}, "test_node")
    await emit_tool_output("test_tool", "test output", "test_node")
    await emit_custom_event("Custom message", {"progress": 0.5})
    
    print(f"\n   Received {len(received_events)} events")
    assert len(received_events) == 3, f"Should receive 3 events, got {len(received_events)}"
    print("   ✅ Correct: All 3 events received")
    
    # Verify event types
    event_types = [e.event_type for e in received_events]
    print(f"\n   Event types: {event_types}")
    assert "tool_call" in event_types, "Should have tool_call event"
    assert "tool_output" in event_types, "Should have tool_output event"
    assert "custom" in event_types, "Should have custom event"
    print("   ✅ Correct: All event types present")
    
    # Test 4: Clear callback
    print("\n📊 Test 2.4: Clear callback")
    clear_streaming_callback()
    callback = get_streaming_callback()
    print(f"   Callback: {callback}")
    assert callback is None, "Callback should be None after clear"
    print("   ✅ Correct: Callback cleared")
    
    # Test 5: Emit without callback (should not error)
    print("\n📊 Test 2.5: Emit without callback (should be no-op)")
    initial_count = len(received_events)
    await emit_tool_call("test_tool_2", {"arg": "value2"}, "test_node")
    print(f"   Events before: {initial_count}, after: {len(received_events)}")
    assert len(received_events) == initial_count, "Should not receive events without callback"
    print("   ✅ Correct: No events received (callback not set)")
    
    print("\n✅ TEST 2 PASSED")
    return True


# ============================================================================
# TEST 3: Tool Emit Functions
# ============================================================================

async def test_tool_emit_functions():
    """Test that tool emit functions work correctly."""
    print("\n" + "="*70)
    print("TEST 3: Tool Emit Functions")
    print("="*70)
    
    from langchain.tools import tool
    
    @tool("test_tool_with_emits")
    async def test_tool_with_emits(query: str) -> str:
        """Test tool that emits custom events."""
        # Emit start
        await emit_custom_event(
            content=f"Starting search for: {query}",
            custom_data={"stage": "start", "progress": 0.0}
        )
        
        # Simulate work
        await asyncio.sleep(0.1)
        
        # Emit progress
        await emit_custom_event(
            content="Processing...",
            custom_data={"stage": "processing", "progress": 0.5}
        )
        
        # Simulate more work
        await asyncio.sleep(0.1)
        
        # Emit completion
        await emit_custom_event(
            content="Complete!",
            custom_data={"stage": "complete", "progress": 1.0}
        )
        
        return f"Results for: {query}"
    
    # Set up callback to collect events
    received_events = []
    
    async def collect_callback(event: StreamingEvent):
        received_events.append(event)
        print(f"\n✅ Event: {event.event_type} - {event.data.get('content', event.data)}")
    
    set_streaming_callback(collect_callback)
    
    # Execute tool
    print("\n📊 Executing tool with emit functions...")
    result = await test_tool_with_emits.ainvoke({"query": "test query"})
    
    print(f"\n   Tool result: {result}")
    print(f"   Events received: {len(received_events)}")
    
    # Verify events
    assert len(received_events) == 3, f"Should receive 3 events, got {len(received_events)}"
    print("   ✅ Correct: All 3 custom events received")
    
    # Verify event data
    stages = [e.data.get("custom_data", {}).get("stage") for e in received_events]
    print(f"\n   Stages: {stages}")
    assert stages == ["start", "processing", "complete"], f"Wrong stages: {stages}"
    print("   ✅ Correct: Event stages in order")
    
    # Verify progress values
    progress_values = [e.data.get("custom_data", {}).get("progress") for e in received_events]
    print(f"   Progress: {progress_values}")
    assert progress_values == [0.0, 0.5, 1.0], f"Wrong progress: {progress_values}"
    print("   ✅ Correct: Progress values correct")
    
    clear_streaming_callback()
    
    print("\n✅ TEST 3 PASSED")
    return True


# ============================================================================
# TEST 4: Simple Streaming (No Callback)
# ============================================================================

async def test_simple_streaming_no_callback():
    """Test that emit functions don't break when no callback is set."""
    print("\n" + "="*70)
    print("TEST 4: Simple Streaming (No Callback)")
    print("="*70)
    
    from langchain.tools import tool
    
    @tool("test_tool_simple")
    async def test_tool_simple(query: str) -> str:
        """Tool with emit calls but no callback set."""
        # These should be no-ops
        await emit_custom_event("Event 1", {"data": "test"})
        await emit_tool_call("some_tool", {"arg": "value"})
        await emit_tool_output("some_tool", "output")
        
        return f"Result: {query}"
    
    # Make sure no callback is set
    clear_streaming_callback()
    callback = get_streaming_callback()
    print(f"\n   Callback: {callback}")
    assert callback is None, "Callback should be None"
    
    # Execute tool - should not error
    print("\n📊 Executing tool without callback...")
    try:
        result = await test_tool_simple.ainvoke({"query": "test"})
        print(f"   ✅ Tool executed successfully: {result}")
        print("   ✅ No errors with emit calls (they were no-ops)")
    except Exception as e:
        print(f"   ❌ Tool execution failed: {e}")
        return False
    
    print("\n✅ TEST 4 PASSED")
    return True


# ============================================================================
# TEST 5: Enhanced vs Simple Handler Behavior
# ============================================================================

async def test_handler_behavior():
    """Test that handlers behave correctly."""
    print("\n" + "="*70)
    print("TEST 5: Handler Behavior")
    print("="*70)
    
    from masai.Tools.utilities.enhanced_streaming import (
        EnhancedStreamHandler,
        SimpleStreamHandler
    )
    
    # Test 1: EnhancedStreamHandler configuration
    print("\n📊 Test 5.1: EnhancedStreamHandler configuration")
    handler = EnhancedStreamHandler(
        model="test-model",
        enable_tool_events=True,
        enable_custom_events=True,
        enable_node_transitions=False
    )
    
    print(f"   Model: {handler.model}")
    print(f"   Tool events: {handler.enable_tool_events}")
    print(f"   Custom events: {handler.enable_custom_events}")
    print(f"   Node transitions: {handler.enable_node_transitions}")
    
    assert handler.model == "test-model", "Model should be set"
    assert handler.enable_tool_events == True, "Tool events should be enabled"
    assert handler.enable_custom_events == True, "Custom events should be enabled"
    assert handler.enable_node_transitions == False, "Node transitions should be disabled"
    print("   ✅ Configuration correct")
    
    # Test 2: Event filtering
    print("\n📊 Test 5.2: Event filtering")
    
    # Create events
    tool_call_event = StreamingEvent("tool_call", {"tool": "test"})
    custom_event = StreamingEvent("custom", {"content": "test"})
    node_event = StreamingEvent("node_transition", {"from": "a", "to": "b"})
    
    # Test with all enabled
    handler_all = EnhancedStreamHandler(
        enable_tool_events=True,
        enable_custom_events=True,
        enable_node_transitions=True
    )
    
    assert handler_all._should_emit_event(tool_call_event) == True
    assert handler_all._should_emit_event(custom_event) == True
    assert handler_all._should_emit_event(node_event) == True
    print("   ✅ All events enabled: all pass")
    
    # Test with tool events disabled
    handler_no_tools = EnhancedStreamHandler(
        enable_tool_events=False,
        enable_custom_events=True,
        enable_node_transitions=True
    )
    
    assert handler_no_tools._should_emit_event(tool_call_event) == False
    assert handler_no_tools._should_emit_event(custom_event) == True
    assert handler_no_tools._should_emit_event(node_event) == True
    print("   ✅ Tool events disabled: tool_call filtered")
    
    # Test 3: SimpleStreamHandler
    print("\n📊 Test 5.3: SimpleStreamHandler")
    simple_handler = SimpleStreamHandler(model="simple-model")
    
    print(f"   Model: {simple_handler.model}")
    assert simple_handler.model == "simple-model", "Model should be set"
    print("   ✅ SimpleStreamHandler created")
    
    # Test SSE formatting
    sse = simple_handler._format_sse_event({"delta": {"content": "test"}})
    print(f"   SSE format: {sse[:100]}...")
    assert "data: " in sse, "Should have SSE format"
    assert "simple-model" in sse, "Should include model name"
    print("   ✅ SSE formatting works")
    
    print("\n✅ TEST 5 PASSED")
    return True


# ============================================================================
# TEST 6: Integration Test (Simulated Agent Execution)
# ============================================================================

async def test_integration():
    """Test integration with simulated agent execution."""
    print("\n" + "="*70)
    print("TEST 6: Integration Test")
    print("="*70)
    
    from langchain.tools import tool
    
    @tool("integration_test_tool")
    async def integration_test_tool(query: str) -> str:
        """Tool for integration testing."""
        await emit_custom_event("Tool started", {"stage": "start"})
        await asyncio.sleep(0.1)
        await emit_custom_event("Tool processing", {"stage": "processing"})
        await asyncio.sleep(0.1)
        await emit_custom_event("Tool complete", {"stage": "complete"})
        return f"Processed: {query}"
    
    # Simulate agent execution with streaming
    collected_events = []
    
    async def integration_callback(event: StreamingEvent):
        collected_events.append(event)
    
    set_streaming_callback(integration_callback)
    
    print("\n📊 Simulating agent execution...")
    
    # Simulate tool call
    await emit_tool_call("integration_test_tool", {"query": "test"}, "execute_tool")
    
    # Execute tool
    result = await integration_test_tool.ainvoke({"query": "test"})
    
    # Simulate tool output
    await emit_tool_output("integration_test_tool", result, "execute_tool")
    
    print(f"\n   Tool result: {result}")
    print(f"   Total events: {len(collected_events)}")
    
    # Verify events
    event_types = [e.event_type for e in collected_events]
    print(f"   Event types: {event_types}")
    
    # Should have: tool_call, 3x custom, tool_output
    assert "tool_call" in event_types, "Should have tool_call"
    assert "tool_output" in event_types, "Should have tool_output"
    assert event_types.count("custom") == 3, f"Should have 3 custom events, got {event_types.count('custom')}"
    
    print("   ✅ All events received in correct order")
    
    clear_streaming_callback()
    
    print("\n✅ TEST 6 PASSED")
    return True


# ============================================================================
# RUN ALL TESTS
# ============================================================================

async def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("ENHANCED STREAMING TEST SUITE")
    print("="*70)
    
    results = []
    
    # Test 1: Event creation
    try:
        result = test_event_creation()
        results.append(("Event Creation", result))
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        results.append(("Event Creation", False))
    
    # Test 2: Callback system
    try:
        result = await test_callback_system()
        results.append(("Callback System", result))
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        results.append(("Callback System", False))
    
    # Test 3: Tool emit functions
    try:
        result = await test_tool_emit_functions()
        results.append(("Tool Emit Functions", result))
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        results.append(("Tool Emit Functions", False))
    
    # Test 4: Simple streaming (no callback)
    try:
        result = await test_simple_streaming_no_callback()
        results.append(("Simple Streaming", result))
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        results.append(("Simple Streaming", False))
    
    # Test 5: Handler behavior
    try:
        result = await test_handler_behavior()
        results.append(("Handler Behavior", result))
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        results.append(("Handler Behavior", False))
    
    # Test 6: Integration
    try:
        result = await test_integration()
        results.append(("Integration", result))
    except Exception as e:
        print(f"\n❌ TEST 6 FAILED: {e}")
        results.append(("Integration", False))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30s} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("\n" + "="*70)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("="*70)
    
    return all(p for _, p in results)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

