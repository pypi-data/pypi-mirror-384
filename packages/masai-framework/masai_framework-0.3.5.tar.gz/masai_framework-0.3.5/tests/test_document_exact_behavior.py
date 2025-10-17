"""
Test Document class for exact LangChain behavior match.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print("="*80)
print("DOCUMENT CLASS EXACT BEHAVIOR TEST")
print("="*80)

# LangChain Document
from langchain_core.documents import Document as LangChainDocument

# MASAI Document
from masai.schema import Document as MASAIDocument

# Test 1: Basic creation
print("\n" + "="*80)
print("TEST 1: Basic Document Creation")
print("="*80)

lc_doc = LangChainDocument(page_content="Test content", metadata={"source": "test.txt"})
masai_doc = MASAIDocument(page_content="Test content", metadata={"source": "test.txt"})

print(f"\nLangChain Document:")
print(f"  Type: {type(lc_doc)}")
print(f"  page_content: {lc_doc.page_content}")
print(f"  metadata: {lc_doc.metadata}")
print(f"  Has dict() method: {hasattr(lc_doc, 'dict')}")
print(f"  Has model_dump() method: {hasattr(lc_doc, 'model_dump')}")

print(f"\nMASAI Document:")
print(f"  Type: {type(masai_doc)}")
print(f"  page_content: {masai_doc.page_content}")
print(f"  metadata: {masai_doc.metadata}")
print(f"  Has dict() method: {hasattr(masai_doc, 'dict')}")
print(f"  Has model_dump() method: {hasattr(masai_doc, 'model_dump')}")
print(f"  Has to_dict() method: {hasattr(masai_doc, 'to_dict')}")

# Test 2: Dict conversion
print("\n" + "="*80)
print("TEST 2: Dict Conversion")
print("="*80)

# LangChain uses model_dump() in Pydantic v2
if hasattr(lc_doc, 'model_dump'):
    lc_dict = lc_doc.model_dump()
    print(f"\nLangChain model_dump(): {lc_dict}")
elif hasattr(lc_doc, 'dict'):
    lc_dict = lc_doc.dict()
    print(f"\nLangChain dict(): {lc_dict}")

# MASAI
masai_dict = masai_doc.to_dict()
print(f"MASAI to_dict(): {masai_dict}")

if hasattr(masai_doc, 'model_dump'):
    masai_model_dump = masai_doc.model_dump()
    print(f"MASAI model_dump(): {masai_model_dump}")

# Test 3: String representation
print("\n" + "="*80)
print("TEST 3: String Representation")
print("="*80)

print(f"\nLangChain str(): {str(lc_doc)}")
print(f"LangChain repr(): {repr(lc_doc)}")

print(f"\nMASAI str(): {str(masai_doc)}")
print(f"MASAI repr(): {repr(masai_doc)}")

# Test 4: Attribute access
print("\n" + "="*80)
print("TEST 4: Attribute Access")
print("="*80)

print(f"\nLangChain attributes: {dir(lc_doc)}")
print(f"\nMASAI attributes: {dir(masai_doc)}")

# Test 5: Equality
print("\n" + "="*80)
print("TEST 5: Equality Check")
print("="*80)

lc_doc2 = LangChainDocument(page_content="Test content", metadata={"source": "test.txt"})
masai_doc2 = MASAIDocument(page_content="Test content", metadata={"source": "test.txt"})

print(f"\nLangChain doc1 == doc2: {lc_doc == lc_doc2}")
print(f"MASAI doc1 == doc2: {masai_doc == masai_doc2}")

# Test 6: Metadata modification
print("\n" + "="*80)
print("TEST 6: Metadata Modification")
print("="*80)

lc_doc3 = LangChainDocument(page_content="Test", metadata={"key": "value"})
lc_doc3.metadata["new_key"] = "new_value"
print(f"\nLangChain after metadata modification: {lc_doc3.metadata}")

masai_doc3 = MASAIDocument(page_content="Test", metadata={"key": "value"})
masai_doc3.metadata["new_key"] = "new_value"
print(f"MASAI after metadata modification: {masai_doc3.metadata}")

# Test 7: Empty metadata
print("\n" + "="*80)
print("TEST 7: Empty Metadata")
print("="*80)

lc_doc4 = LangChainDocument(page_content="Test")
masai_doc4 = MASAIDocument(page_content="Test")

print(f"\nLangChain empty metadata: {lc_doc4.metadata}")
print(f"LangChain metadata type: {type(lc_doc4.metadata)}")

print(f"\nMASAI empty metadata: {masai_doc4.metadata}")
print(f"MASAI metadata type: {type(masai_doc4.metadata)}")

# Test 8: Serialization/Deserialization
print("\n" + "="*80)
print("TEST 8: Serialization/Deserialization")
print("="*80)

test_dict = {"page_content": "Serialized content", "metadata": {"source": "serialized.txt"}}

# LangChain
if hasattr(LangChainDocument, 'parse_obj'):
    lc_from_dict = LangChainDocument.parse_obj(test_dict)
    print(f"\nLangChain parse_obj(): {lc_from_dict}")
elif hasattr(LangChainDocument, 'model_validate'):
    lc_from_dict = LangChainDocument.model_validate(test_dict)
    print(f"\nLangChain model_validate(): {lc_from_dict}")
else:
    lc_from_dict = LangChainDocument(**test_dict)
    print(f"\nLangChain from dict: {lc_from_dict}")

# MASAI
masai_from_dict = MASAIDocument.from_dict(test_dict)
print(f"MASAI from_dict(): {masai_from_dict}")

# Test 9: JSON serialization
print("\n" + "="*80)
print("TEST 9: JSON Serialization")
print("="*80)

import json

# LangChain
if hasattr(lc_doc, 'model_dump'):
    lc_json = json.dumps(lc_doc.model_dump())
elif hasattr(lc_doc, 'dict'):
    lc_json = json.dumps(lc_doc.dict())
print(f"\nLangChain JSON: {lc_json}")

# MASAI
masai_json = json.dumps(masai_doc.to_dict())
print(f"MASAI JSON: {masai_json}")

print(f"\nJSON match: {lc_json == masai_json}")

# Test 10: Usage in InMemoryStore pattern
print("\n" + "="*80)
print("TEST 10: InMemoryStore Usage Pattern")
print("="*80)

# Simulate InMemoryStore usage
def store_document(doc):
    """Simulate storing a document."""
    if isinstance(doc, dict):
        return doc
    elif hasattr(doc, 'to_dict'):
        return doc.to_dict()
    elif hasattr(doc, 'model_dump'):
        return doc.model_dump()
    elif hasattr(doc, 'dict'):
        return doc.dict()
    else:
        return {"page_content": str(doc), "metadata": {}}

lc_stored = store_document(lc_doc)
masai_stored = store_document(masai_doc)

print(f"\nLangChain stored: {lc_stored}")
print(f"MASAI stored: {masai_stored}")
print(f"Storage match: {lc_stored == masai_stored}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print("\n✅ All Document behavior tests completed!")
print("Review the output above to identify any differences.")

