"""
Test suite for context truncation and overlap detection in generative models.
Tests real-world scenarios with chat history, tool outputs, and prompts.
"""

import asyncio
import re


class MockLLM:
    """Mock LLM for testing truncation logic without API calls"""
    def __init__(self):
        self.chat_history = []

    def _extract_tool_output_from_prompt(self, prompt: str) -> str:
        """Extract tool output content from prompt's tags"""
        import re
        pattern = r'<PREVIOUS TOOL OUTPUT START>\n(.*?)\n<PREVIOUS TOOL OUTPUT END>'
        match = re.search(pattern, prompt, re.DOTALL)
        return match.group(1).strip() if match else ''

    def _check_overlap(self, text1: str, text2: str, min_chunk_words: int = 20) -> bool:
        """Check if two texts have significant overlap"""
        if not text1 or not text2:
            return False

        words1 = text1.split()
        words2 = text2.split()

        if len(words1) < min_chunk_words or len(words2) < min_chunk_words:
            shorter = text1 if len(words1) < len(words2) else text2
            longer = text2 if len(words1) < len(words2) else text1
            return shorter in longer

        # Check if any chunk appears in text2
        for i in range(len(words1) - min_chunk_words + 1):
            chunk = ' '.join(words1[i:i + min_chunk_words])
            if chunk in text2:
                return True

        return False

    def _truncate_overlapping_tool_output(self, content: str, tool_output_reference: str, max_words: int = 30) -> str:
        """Truncate tool output in content if it overlaps with reference"""
        if not content or not isinstance(content, str) or not tool_output_reference:
            return content or ''

        import re

        reference_clean = tool_output_reference.rstrip('.')
        pattern = r'<PREVIOUS TOOL OUTPUT START>\n(.*?)\n<PREVIOUS TOOL OUTPUT END>'

        def truncate_if_overlapping(match):
            tool_output = match.group(1).strip()

            if tool_output.endswith('...'):
                return match.group(0)

            tool_output_clean = tool_output.rstrip('.')

            # Check overlap in BOTH directions
            has_overlap = (self._check_overlap(tool_output_clean, reference_clean) or
                          self._check_overlap(reference_clean, tool_output_clean))

            if has_overlap:
                words = tool_output.split()
                if len(words) <= max_words:
                    return match.group(0)

                truncated = ' '.join(words[:max_words])
                return f'<PREVIOUS TOOL OUTPUT START>\n{truncated}...\n<PREVIOUS TOOL OUTPUT END>'

            return match.group(0)

        # Handle tagged outputs
        modified_content = re.sub(pattern, truncate_if_overlapping, content, flags=re.DOTALL)

        # Handle untagged content
        if modified_content == content and '<PREVIOUS TOOL OUTPUT' not in content:
            content_clean = content.rstrip('.')
            if self._check_overlap(content_clean, reference_clean, min_chunk_words=30):
                words = content.split()
                if len(words) > max_words:
                    truncated = ' '.join(words[:max_words])
                    return f'{truncated}... [truncated - overlaps with tool output]'

        return modified_content

    async def _update_component_context(self, component_context, role, prompt):
        """Update component context with truncation logic"""
        import time
        start_time = time.time()

        # Extract tool output from current prompt once
        tool_output_in_prompt = self._extract_tool_output_from_prompt(prompt)

        if tool_output_in_prompt:
            # Truncate overlapping tool outputs in component context messages
            if component_context:
                truncated_context = []
                for message in component_context:
                    if not isinstance(message, dict) or 'content' not in message:
                        truncated_context.append(message)
                        continue

                    content = message.get('content', '')
                    if content is None:
                        content = ''

                    truncated_message = message.copy()
                    truncated_message['content'] = self._truncate_overlapping_tool_output(content, tool_output_in_prompt)
                    truncated_context.append(truncated_message)
                component_context = truncated_context

            # Also truncate tool outputs in existing chat_history (both tagged and untagged)
            history_truncate_start = time.time()
            self.chat_history = [
                {'role': msg.get('role', ''), 'content': self._truncate_overlapping_tool_output(msg.get('content', '') or '', tool_output_in_prompt)}
                if isinstance(msg, dict) else msg
                for msg in self.chat_history
            ]

            print(f"⏱️ CONTEXT FILTERING TIME: Total={time.time()-start_time:.4f}s | Component={len(component_context or [])} msgs | History={len(self.chat_history)} msgs | Time={time.time()-history_truncate_start:.4f}s")

        if component_context:
            self.chat_history.extend(component_context)


class TestContextTruncation:
    """Test context truncation with realistic scenarios"""

    def setup_llm(self):
        """Create a mock LLM instance for testing"""
        return MockLLM()
    
    def test_scenario_1_full_in_history_truncated_in_prompt(self):
        """
        Scenario 1: Full tool output in chat history, truncated version in current prompt
        Expected: History should be truncated to match prompt's truncation
        """
        print("\n" + "="*80)
        print("TEST 1: Full in History, Truncated in Prompt")
        print("="*80)
        
        llm = self.setup_llm()
        
        # Simulate full tool output (500 words)
        full_tool_output = " ".join([f"word{i}" for i in range(500)])
        
        # Simulate truncated tool output in prompt (30 words)
        truncated_tool_output = " ".join([f"word{i}" for i in range(30)]) + "..."
        
        # Chat history with full tool output
        llm.chat_history = [
            {'role': 'user', 'content': 'Search for Python tutorials'},
            {'role': 'assistant', 'content': 'I will search for that.'},
            {'role': 'tool', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{full_tool_output}\n<PREVIOUS TOOL OUTPUT END>'}
        ]
        
        # Component context also has full output
        component_context = [
            {'role': 'assistant', 'content': 'Let me analyze the results.'},
            {'role': 'tool', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{full_tool_output}\n<PREVIOUS TOOL OUTPUT END>'}
        ]
        
        # Current prompt with truncated output
        current_prompt = f"""
        === CONTEXT ===
        ORIGINAL QUESTION: Search for Python tutorials
        
        <PREVIOUS TOOL OUTPUT START>
        {truncated_tool_output}
        <PREVIOUS TOOL OUTPUT END>
        === END CONTEXT ===
        """
        
        # Run the update
        asyncio.run(llm._update_component_context(component_context, 'user', current_prompt))
        
        # Verify truncation happened
        print(f"\n📊 Results:")
        print(f"Original history length: 3 messages")
        print(f"Final history length: {len(llm.chat_history)} messages")
        
        # Check if tool output in history is truncated
        for i, msg in enumerate(llm.chat_history):
            if 'PREVIOUS TOOL OUTPUT' in msg.get('content', ''):
                content = msg['content']
                if '...' in content:
                    print(f"✅ Message {i}: Tool output TRUNCATED")
                    # Extract and show word count
                    import re
                    match = re.search(r'<PREVIOUS TOOL OUTPUT START>\n(.*?)\n<PREVIOUS TOOL OUTPUT END>', content, re.DOTALL)
                    if match:
                        words = match.group(1).split()
                        print(f"   Word count: {len(words)} words")
                else:
                    print(f"❌ Message {i}: Tool output NOT truncated")
                    import re
                    match = re.search(r'<PREVIOUS TOOL OUTPUT START>\n(.*?)\n<PREVIOUS TOOL OUTPUT END>', content, re.DOTALL)
                    if match:
                        words = match.group(1).split()
                        print(f"   Word count: {len(words)} words")
        
        print("\n" + "="*80 + "\n")
    
    def test_scenario_2_already_truncated(self):
        """
        Scenario 2: Tool output already truncated in history
        Expected: Should NOT truncate again (no double truncation)
        """
        print("\n" + "="*80)
        print("TEST 2: Already Truncated - No Double Truncation")
        print("="*80)
        
        llm = self.setup_llm()
        
        # Already truncated output
        truncated_output = " ".join([f"word{i}" for i in range(30)]) + "..."
        
        llm.chat_history = [
            {'role': 'user', 'content': 'Search for Python tutorials'},
            {'role': 'tool', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{truncated_output}\n<PREVIOUS TOOL OUTPUT END>'}
        ]
        
        component_context = []
        
        current_prompt = f"""
        <PREVIOUS TOOL OUTPUT START>
        {truncated_output}
        <PREVIOUS TOOL OUTPUT END>
        """
        
        # Store original for comparison
        original_content = llm.chat_history[1]['content']
        
        asyncio.run(llm._update_component_context(component_context, 'user', current_prompt))
        
        # Verify no change
        final_content = llm.chat_history[1]['content']
        
        print(f"\n📊 Results:")
        print(f"Original content == Final content: {original_content == final_content}")
        
        if original_content == final_content:
            print("✅ PASS: Content unchanged (no double truncation)")
        else:
            print("❌ FAIL: Content was modified")
            print(f"Original: {original_content[:100]}...")
            print(f"Final: {final_content[:100]}...")
        
        print("\n" + "="*80 + "\n")
    
    def test_scenario_3_different_tool_outputs(self):
        """
        Scenario 3: Different tool outputs (no overlap)
        Expected: Should NOT truncate (different content)
        """
        print("\n" + "="*80)
        print("TEST 3: Different Tool Outputs - No Truncation")
        print("="*80)
        
        llm = self.setup_llm()
        
        # Different tool outputs
        tool_output_1 = "Search results for Python: " + " ".join([f"python{i}" for i in range(100)])
        tool_output_2 = "Search results for JavaScript: " + " ".join([f"javascript{i}" for i in range(100)])
        
        llm.chat_history = [
            {'role': 'user', 'content': 'Search for Python'},
            {'role': 'tool', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{tool_output_1}\n<PREVIOUS TOOL OUTPUT END>'}
        ]
        
        component_context = []
        
        # Current prompt has different tool output
        current_prompt = f"""
        <PREVIOUS TOOL OUTPUT START>
        {tool_output_2}
        <PREVIOUS TOOL OUTPUT END>
        """
        
        original_content = llm.chat_history[1]['content']
        
        asyncio.run(llm._update_component_context(component_context, 'user', current_prompt))
        
        final_content = llm.chat_history[1]['content']
        
        print(f"\n📊 Results:")
        print(f"Original content == Final content: {original_content == final_content}")
        
        if original_content == final_content:
            print("✅ PASS: Content unchanged (different tool outputs)")
        else:
            print("❌ FAIL: Content was modified despite different outputs")
        
        print("\n" + "="*80 + "\n")
    
    def test_scenario_4_multiple_tool_outputs(self):
        """
        Scenario 4: Multiple tool outputs in history, only one overlaps
        Expected: Only truncate the overlapping one
        """
        print("\n" + "="*80)
        print("TEST 4: Multiple Tool Outputs - Selective Truncation")
        print("="*80)
        
        llm = self.setup_llm()
        
        # Two different tool outputs
        tool_output_search = "Search results: " + " ".join([f"result{i}" for i in range(100)])
        tool_output_calc = "Calculation result: " + " ".join([f"calc{i}" for i in range(100)])
        
        llm.chat_history = [
            {'role': 'user', 'content': 'Search for data'},
            {'role': 'tool', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{tool_output_search}\n<PREVIOUS TOOL OUTPUT END>'},
            {'role': 'user', 'content': 'Calculate something'},
            {'role': 'tool', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{tool_output_calc}\n<PREVIOUS TOOL OUTPUT END>'}
        ]
        
        component_context = []
        
        # Current prompt only has search output (truncated)
        truncated_search = "Search results: " + " ".join([f"result{i}" for i in range(30)]) + "..."
        current_prompt = f"""
        <PREVIOUS TOOL OUTPUT START>
        {truncated_search}
        <PREVIOUS TOOL OUTPUT END>
        """
        
        asyncio.run(llm._update_component_context(component_context, 'user', current_prompt))
        
        print(f"\n📊 Results:")
        
        # Check message 1 (search - should be truncated)
        msg1 = llm.chat_history[1]['content']
        if '...' in msg1 and 'result' in msg1:
            print("✅ Message 1 (search): TRUNCATED (correct)")
        else:
            print("❌ Message 1 (search): NOT truncated (incorrect)")
        
        # Check message 3 (calc - should NOT be truncated)
        msg3 = llm.chat_history[3]['content']
        if '...' not in msg3 and 'calc' in msg3:
            print("✅ Message 3 (calc): NOT truncated (correct)")
        else:
            print("❌ Message 3 (calc): Incorrectly truncated")
        
        print("\n" + "="*80 + "\n")
    
    def test_scenario_5_component_context_extension(self):
        """
        Scenario 5: Component context with overlapping tool output gets truncated before extending
        Expected: Extended messages should have truncated tool output
        """
        print("\n" + "="*80)
        print("TEST 5: Component Context Extension with Truncation")
        print("="*80)
        
        llm = self.setup_llm()
        
        full_output = " ".join([f"data{i}" for i in range(200)])
        truncated_output = " ".join([f"data{i}" for i in range(30)]) + "..."
        
        llm.chat_history = [
            {'role': 'user', 'content': 'Initial query'}
        ]
        
        # Component context has full output
        component_context = [
            {'role': 'assistant', 'content': 'Processing...'},
            {'role': 'tool', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{full_output}\n<PREVIOUS TOOL OUTPUT END>'}
        ]
        
        current_prompt = f"""
        <PREVIOUS TOOL OUTPUT START>
        {truncated_output}
        <PREVIOUS TOOL OUTPUT END>
        """
        
        initial_length = len(llm.chat_history)
        
        asyncio.run(llm._update_component_context(component_context, 'user', current_prompt))
        
        final_length = len(llm.chat_history)
        
        print(f"\n📊 Results:")
        print(f"Initial history length: {initial_length}")
        print(f"Final history length: {final_length}")
        print(f"Messages added: {final_length - initial_length}")
        
        # Check if the extended message has truncated output
        last_msg = llm.chat_history[-1]['content']
        if '...' in last_msg:
            print("✅ Extended message has TRUNCATED tool output")
            import re
            match = re.search(r'<PREVIOUS TOOL OUTPUT START>\n(.*?)\n<PREVIOUS TOOL OUTPUT END>', last_msg, re.DOTALL)
            if match:
                words = match.group(1).split()
                print(f"   Word count: {len(words)} words")
        else:
            print("❌ Extended message does NOT have truncated output")
        
        print("\n" + "="*80 + "\n")
    
    def test_scenario_6_realistic_conversation_flow(self):
        """
        Scenario 6: Realistic multi-turn conversation with tool usage
        Expected: All overlapping tool outputs truncated, history manageable
        """
        print("\n" + "="*80)
        print("TEST 6: Realistic Conversation Flow")
        print("="*80)
        
        llm = self.setup_llm()
        
        # Simulate realistic conversation
        search_output = "Search results for Python tutorials:\n" + "\n".join([f"Tutorial {i}: Learn Python basics with examples and exercises" for i in range(50)])
        
        llm.chat_history = [
            {'role': 'user', 'content': 'Find Python tutorials'},
            {'role': 'assistant', 'content': 'I will search for Python tutorials.'},
            {'role': 'tool', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{search_output}\n<PREVIOUS TOOL OUTPUT END>'},
            {'role': 'assistant', 'content': 'I found several tutorials. Let me analyze them.'},
        ]
        
        # Component context from evaluator
        component_context = [
            {'role': 'assistant', 'content': 'Analyzing search results...'},
            {'role': 'tool', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{search_output}\n<PREVIOUS TOOL OUTPUT END>'}
        ]
        
        # Current prompt (truncated)
        truncated_search = "Search results for Python tutorials:\n" + "\n".join([f"Tutorial {i}: Learn Python basics with examples and exercises" for i in range(5)]) + "..."
        
        current_prompt = f"""
        === CONTEXT ===
        ORIGINAL QUESTION: Find Python tutorials
        
        <PREVIOUS TOOL OUTPUT START>
        {truncated_search}
        <PREVIOUS TOOL OUTPUT END>
        === END CONTEXT ===
        """
        
        print(f"\n📊 Before Update:")
        print(f"Chat history: {len(llm.chat_history)} messages")
        print(f"Component context: {len(component_context)} messages")
        
        # Calculate total characters before
        total_chars_before = sum(len(msg.get('content', '')) for msg in llm.chat_history)
        
        asyncio.run(llm._update_component_context(component_context, 'user', current_prompt))
        
        # Calculate total characters after
        total_chars_after = sum(len(msg.get('content', '')) for msg in llm.chat_history)
        
        print(f"\n📊 After Update:")
        print(f"Chat history: {len(llm.chat_history)} messages")
        print(f"Total characters before: {total_chars_before}")
        print(f"Total characters after: {total_chars_after}")
        print(f"Character reduction: {total_chars_before - total_chars_after} ({((total_chars_before - total_chars_after) / total_chars_before * 100):.1f}%)")
        
        # Count truncated messages
        truncated_count = sum(1 for msg in llm.chat_history if '...' in msg.get('content', ''))
        print(f"Messages with truncated tool output: {truncated_count}")
        
        if total_chars_after < total_chars_before:
            print("✅ PASS: Context size reduced through truncation")
        else:
            print("⚠️  WARNING: Context size not reduced")
        
        print("\n" + "="*80 + "\n")


def run_all_tests():
    """Run all test scenarios"""
    print("\n" + "🧪 " * 40)
    print("CONTEXT TRUNCATION TEST SUITE")
    print("🧪 " * 40)
    
    tester = TestContextTruncation()
    
    try:
        tester.test_scenario_1_full_in_history_truncated_in_prompt()
        tester.test_scenario_2_already_truncated()
        tester.test_scenario_3_different_tool_outputs()
        tester.test_scenario_4_multiple_tool_outputs()
        tester.test_scenario_5_component_context_extension()
        tester.test_scenario_6_realistic_conversation_flow()
        
        print("\n" + "✅ " * 40)
        print("ALL TESTS COMPLETED")
        print("✅ " * 40 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()

