"""Simple test for truncation logic"""
import asyncio
import re


class MockLLM:
    """Mock LLM for testing"""
    def __init__(self):
        self.chat_history = []
    
    def _extract_tool_output_from_prompt(self, prompt: str) -> str:
        """Extract tool output from prompt"""
        pattern = r'<PREVIOUS TOOL OUTPUT START>\n(.*?)\n<PREVIOUS TOOL OUTPUT END>'
        match = re.search(pattern, prompt, re.DOTALL)
        result = match.group(1).strip() if match else ''
        print(f"[EXTRACT] Found {len(result)} chars in prompt")
        return result
    
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
        """Truncate if overlap found"""
        if not content or not isinstance(content, str) or not tool_output_reference:
            return content or ''

        reference_clean = tool_output_reference.rstrip('.')
        pattern = r'<PREVIOUS TOOL OUTPUT START>\n(.*?)\n<PREVIOUS TOOL OUTPUT END>'

        def truncate_if_overlapping(match):
            tool_output = match.group(1).strip()

            if tool_output.endswith('...'):
                print(f"  [SKIP] Already truncated")
                return match.group(0)

            tool_output_clean = tool_output.rstrip('.')

            # Check overlap in BOTH directions
            has_overlap = (self._check_overlap(tool_output_clean, reference_clean) or
                          self._check_overlap(reference_clean, tool_output_clean))

            print(f"  [OVERLAP] Has overlap: {has_overlap}")
            print(f"  [WORDS] Tool: {len(tool_output.split())}, Ref: {len(tool_output_reference.split())}")

            if has_overlap:
                words = tool_output.split()
                if len(words) <= max_words:
                    print(f"  [SKIP] Already short enough")
                    return match.group(0)

                truncated = ' '.join(words[:max_words])
                print(f"  [TRUNCATE] {len(words)} -> {max_words} words")
                return f'<PREVIOUS TOOL OUTPUT START>\n{truncated}...\n<PREVIOUS TOOL OUTPUT END>'

            print(f"  [SKIP] No overlap")
            return match.group(0)

        # Handle tagged outputs
        modified_content = re.sub(pattern, truncate_if_overlapping, content, flags=re.DOTALL)

        # Handle untagged content (only if no tags were found)
        if modified_content == content and '<PREVIOUS TOOL OUTPUT' not in content:
            content_clean = content.rstrip('.')
            print(f"  [CHECK UNTAGGED] Checking untagged content...")
            if self._check_overlap(content_clean, reference_clean, min_chunk_words=30):
                words = content.split()
                if len(words) > max_words:
                    truncated = ' '.join(words[:max_words])
                    print(f"  [TRUNCATE UNTAGGED] {len(words)} -> {max_words} words")
                    return f'{truncated}... [truncated - overlaps with tool output]'
                else:
                    print(f"  [SKIP UNTAGGED] Already short enough")
            else:
                print(f"  [SKIP UNTAGGED] No overlap")

        return modified_content
    
    async def _update_component_context(self, component_context, role, prompt):
        """Update with truncation"""
        tool_output_in_prompt = self._extract_tool_output_from_prompt(prompt)

        if tool_output_in_prompt:
            print(f"\n[PROCESS] Processing {len(self.chat_history)} history + {len(component_context or [])} component messages")

            # Truncate component context
            if component_context:
                truncated_context = []
                for i, message in enumerate(component_context):
                    if not isinstance(message, dict) or 'content' not in message:
                        truncated_context.append(message)
                        continue

                    content = message.get('content', '') or ''
                    print(f"\n[COMPONENT {i}] Processing...")
                    truncated_message = message.copy()
                    truncated_message['content'] = self._truncate_overlapping_tool_output(content, tool_output_in_prompt)
                    truncated_context.append(truncated_message)
                component_context = truncated_context

            # Truncate chat history (both tagged and untagged)
            for i, msg in enumerate(self.chat_history):
                if isinstance(msg, dict):
                    content = msg.get('content', '') or ''
                    if content:  # Process all non-empty content
                        print(f"\n[HISTORY {i}] Processing...")
                        msg['content'] = self._truncate_overlapping_tool_output(content, tool_output_in_prompt)

        if component_context:
            self.chat_history.extend(component_context)


def test_basic():
    """Test basic truncation"""
    print("\n" + "="*80)
    print("TEST: Full in History, Truncated in Prompt")
    print("="*80)
    
    llm = MockLLM()
    
    # Full output (500 words)
    full_output = " ".join([f"word{i}" for i in range(500)])
    
    # Truncated output (30 words)
    truncated_output = " ".join([f"word{i}" for i in range(30)]) + "..."
    
    # History with full output
    llm.chat_history = [
        {'role': 'user', 'content': 'Search for Python'},
        {'role': 'tool', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{full_output}\n<PREVIOUS TOOL OUTPUT END>'}
    ]
    
    # Component context with full output
    component_context = [
        {'role': 'tool', 'content': f'<PREVIOUS TOOL OUTPUT START>\n{full_output}\n<PREVIOUS TOOL OUTPUT END>'}
    ]
    
    # Prompt with truncated output
    prompt = f"""
<PREVIOUS TOOL OUTPUT START>
{truncated_output}
<PREVIOUS TOOL OUTPUT END>
"""
    
    print(f"\nBefore: History has {len(llm.chat_history)} messages")
    
    asyncio.run(llm._update_component_context(component_context, 'user', prompt))
    
    print(f"\nAfter: History has {len(llm.chat_history)} messages")
    
    # Check results
    for i, msg in enumerate(llm.chat_history):
        content = msg.get('content', '')
        if '<PREVIOUS TOOL OUTPUT' in content:
            if '...' in content:
                match = re.search(r'<PREVIOUS TOOL OUTPUT START>\n(.*?)\n<PREVIOUS TOOL OUTPUT END>', content, re.DOTALL)
                if match:
                    words = match.group(1).split()
                    print(f"\nMessage {i}: TRUNCATED ({len(words)} words)")
            else:
                match = re.search(r'<PREVIOUS TOOL OUTPUT START>\n(.*?)\n<PREVIOUS TOOL OUTPUT END>', content, re.DOTALL)
                if match:
                    words = match.group(1).split()
                    print(f"\nMessage {i}: NOT TRUNCATED ({len(words)} words)")


def test_untagged_content():
    """Test truncation of untagged content that overlaps with tool output"""
    print("\n" + "="*80)
    print("TEST: Untagged Content with Tool Output Overlap")
    print("="*80)

    llm = MockLLM()

    # Tool output in prompt (30 words)
    tool_output = " ".join([f"result{i}" for i in range(30)])

    # LLM response that directly outputs the tool result (100 words)
    llm_response = " ".join([f"result{i}" for i in range(100)])

    # History with untagged LLM response
    llm.chat_history = [
        {'role': 'user', 'content': 'Get results'},
        {'role': 'assistant', 'content': llm_response}  # No tags!
    ]

    component_context = []

    # Prompt with tagged tool output
    prompt = f"""
<PREVIOUS TOOL OUTPUT START>
{tool_output}
<PREVIOUS TOOL OUTPUT END>
"""

    print(f"\nBefore: History message 1 has {len(llm.chat_history[1]['content'].split())} words (untagged)")

    asyncio.run(llm._update_component_context(component_context, 'user', prompt))

    print(f"\nAfter: History message 1 content:")
    content = llm.chat_history[1]['content']
    print(f"  Length: {len(content.split())} words")
    print(f"  Truncated: {'[truncated' in content}")

    if '[truncated' in content:
        print("\n✅ PASS: Untagged content was truncated")
    else:
        print("\n❌ FAIL: Untagged content was NOT truncated")


if __name__ == "__main__":
    test_basic()
    test_untagged_content()

