"""
Debug format_messages() method.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# LangChain
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate, SystemMessagePromptTemplate

lc_system = SystemMessagePromptTemplate(prompt=PromptTemplate(template="You are a helpful assistant."))
lc_human = HumanMessagePromptTemplate(prompt=PromptTemplate(template="Hello {name}!"))
lc_prompt = ChatPromptTemplate.from_messages([lc_system, lc_human])

lc_format_result = lc_prompt.format(name="Alice")
lc_format_messages_result = lc_prompt.format_messages(name="Alice")

print("="*80)
print("LANGCHAIN")
print("="*80)
print(f"\n.format() type: {type(lc_format_result)}")
print(f".format() result: {repr(lc_format_result)}")
print(f"\n.format_messages() type: {type(lc_format_messages_result)}")
print(f".format_messages() length: {len(lc_format_messages_result)}")
print(f".format_messages() result: {lc_format_messages_result}")

# MASAI
from masai.prompts import ChatPromptTemplate as MASAIChatPromptTemplate
from masai.prompts import HumanMessagePromptTemplate as MASAIHumanMessagePromptTemplate
from masai.prompts import PromptTemplate as MASAIPromptTemplate
from masai.prompts import SystemMessagePromptTemplate as MASAISystemMessagePromptTemplate

masai_system = MASAISystemMessagePromptTemplate(prompt=MASAIPromptTemplate(template="You are a helpful assistant."))
masai_human = MASAIHumanMessagePromptTemplate(prompt=MASAIPromptTemplate(template="Hello {name}!"))
masai_prompt = MASAIChatPromptTemplate.from_messages([masai_system, masai_human])

masai_format_result = masai_prompt.format(name="Alice")
masai_format_messages_result = masai_prompt.format_messages(name="Alice")

print("\n" + "="*80)
print("MASAI")
print("="*80)
print(f"\n.format() type: {type(masai_format_result)}")
print(f".format() result: {repr(masai_format_result)}")
print(f"\n.format_messages() type: {type(masai_format_messages_result)}")
print(f".format_messages() length: {len(masai_format_messages_result)}")
print(f".format_messages() result: {masai_format_messages_result}")

print("\n" + "="*80)
print("COMPARISON")
print("="*80)
print(f"\n.format() match: {type(lc_format_result) == type(masai_format_result)}")
print(f".format_messages() match: {type(lc_format_messages_result) == type(masai_format_messages_result)}")
print(f".format_messages() length match: {len(lc_format_messages_result) == len(masai_format_messages_result)}")

