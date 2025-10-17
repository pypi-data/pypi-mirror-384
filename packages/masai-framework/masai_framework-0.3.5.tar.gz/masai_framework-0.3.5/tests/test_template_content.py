"""
Check the actual template content to see where the extra newline comes from.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

system_prompt = """
 NAME: general_personal_agent.
 YOUR CHARACTERISTICS AND CAPABILITIES general answering,personalized conversation,complex reasoning,creative tasks
RESPONSE STYLE: acts as a personal assistant focusing on personalized interactions. Do not share details about other agents..
Have access to current human's personal data to give personalized answers.
    You can save interesting facts about user's life, personal details, etc in long term memory.
    Assign appropriate tasks to other agents (if available)
"""

router_prompt = """
<SYSTEM HANDLING GUIDELINES START/>
UNDERSTAND USER QUESTION/INTENT FROM PAST INTERACTIONS+CONTEXT AND TAKE BEST COURSE OF ACTION.
Understand user question and intent from past interactions and take best course of action.
GENERAL GUIDELINES:
   1) Enclose all dictionary properties/values in double quotes for valid JSON
   2) Strictly adhere to tool_input schema for tool_input of available tools.
   3) Leverage CHAT HISTORY + QUESTION + ALL AVAILABLE INFO for more context.
   4) Assign tasks to specialized agents when it seems fit.
   5) Use USEFUL DATA IN INFO when available.
DECISION FLOW (ACTION TYPES):
   1) Continue working (satisfied=False + tool_input≠None) → Use tools/knowledge/chat_history,context;
   2) Delegate (satisfied=True + tool=None + delegate_to_agent=name) → Delegate task when necessary.
ERROR PROTOCOLS: 
1) Reuse existing info from history, prevent loops via attempt tracking, provide detailed failure/delegation rationales. 
2) Maintain inter-agent communication for complex problem solving.
<SYSTEM HANDLING GUIDELINES END/>
"""

full_system = system_prompt + "\nFOLLOW THESE INSTRUCTIONS:" + router_prompt

print("="*80)
print("TEMPLATE CONTENT ANALYSIS")
print("="*80)

print(f"\nSystem prompt ends with: {repr(system_prompt[-20:])}")
print(f"Router prompt starts with: {repr(router_prompt[:20])}")
print(f"Router prompt ends with: {repr(router_prompt[-20:])}")

print(f"\nFull system template ends with: {repr(full_system[-50:])}")

# Check if there's a trailing newline
if full_system.endswith('\n'):
    print("✅ System template ends with newline")
else:
    print("❌ System template does NOT end with newline")

# LangChain
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, PromptTemplate

lc_system = SystemMessagePromptTemplate(prompt=PromptTemplate(template=full_system))
lc_formatted = lc_system.format()

print(f"\nLangChain formatted system message type: {type(lc_formatted)}")
print(f"LangChain formatted system message: {repr(str(lc_formatted)[-50:])}")

# MASAI
from masai.prompts import SystemMessagePromptTemplate as MASAISystemMessagePromptTemplate
from masai.prompts import PromptTemplate as MASAIPromptTemplate

masai_system = MASAISystemMessagePromptTemplate(prompt=MASAIPromptTemplate(template=full_system))
masai_formatted = masai_system.format()

print(f"\nMASAI formatted system message type: {type(masai_formatted)}")
print(f"MASAI formatted system message: {repr(masai_formatted[-50:])}")

