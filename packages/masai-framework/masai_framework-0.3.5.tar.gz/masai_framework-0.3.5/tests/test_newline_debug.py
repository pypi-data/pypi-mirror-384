"""
Debug newline issue between LangChain and MASAI.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

system_prompt = "System message"
human_prompt = "Human message"

# LangChain
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate, SystemMessagePromptTemplate

lc_system = SystemMessagePromptTemplate(prompt=PromptTemplate(template=system_prompt))
lc_human = HumanMessagePromptTemplate(prompt=PromptTemplate(template=human_prompt))
lc_prompt = ChatPromptTemplate.from_messages([lc_system, lc_human])
lc_result = lc_prompt.format()

# MASAI
from masai.prompts import ChatPromptTemplate as MASAIChatPromptTemplate
from masai.prompts import HumanMessagePromptTemplate as MASAIHumanMessagePromptTemplate
from masai.prompts import PromptTemplate as MASAIPromptTemplate
from masai.prompts import SystemMessagePromptTemplate as MASAISystemMessagePromptTemplate

masai_system = MASAISystemMessagePromptTemplate(prompt=MASAIPromptTemplate(template=system_prompt))
masai_human = MASAIHumanMessagePromptTemplate(prompt=MASAIPromptTemplate(template=human_prompt))
masai_prompt = MASAIChatPromptTemplate.from_messages([masai_system, masai_human])
masai_result = masai_prompt.format()

print("="*80)
print("NEWLINE DEBUG")
print("="*80)

print(f"\nLangChain result:")
print(repr(lc_result))
print(f"Length: {len(lc_result)}")

print(f"\nMASAI result:")
print(repr(masai_result))
print(f"Length: {len(masai_result)}")

print(f"\n✅ Match: {lc_result == masai_result}")

# Check individual message formatting
print("\n" + "="*80)
print("INDIVIDUAL MESSAGE CHECK")
print("="*80)

print(f"\nLangChain system message format:")
print(repr(lc_system.format()))

print(f"\nMASAI system message format:")
print(repr(masai_system.format()))

print(f"\nLangChain human message format:")
print(repr(lc_human.format()))

print(f"\nMASAI human message format:")
print(repr(masai_human.format()))

