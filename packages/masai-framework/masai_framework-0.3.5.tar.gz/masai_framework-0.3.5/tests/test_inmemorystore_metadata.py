"""
Test InMemoryStore metadata preservation.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from masai.Memory.InMemoryStore import InMemoryDocStore
from masai.schema import Document

print("="*80)
print("INMEMORYSTORE METADATA PRESERVATION TEST")
print("="*80)

# Test 1: String document
print("\n" + "="*80)
print("TEST 1: String Document")
print("="*80)

store1 = InMemoryDocStore(documents=["Test content"], embedding_model=None)
doc1 = store1.get_document("0")
print(f"Stored document: {doc1}")
print(f"Has metadata: {'metadata' in doc1}")
print(f"Metadata value: {doc1.get('metadata', 'NOT FOUND')}")

# Test 2: Dict document with metadata
print("\n" + "="*80)
print("TEST 2: Dict Document with Metadata")
print("="*80)

store2 = InMemoryDocStore(
    documents=[{"page_content": "Test content", "metadata": {"source": "test.txt", "page": 1}}],
    embedding_model=None
)
doc2 = store2.get_document("0")
print(f"Stored document: {doc2}")
print(f"Has metadata: {'metadata' in doc2}")
print(f"Metadata value: {doc2.get('metadata', 'NOT FOUND')}")

# Test 3: Document object with metadata
print("\n" + "="*80)
print("TEST 3: Document Object with Metadata")
print("="*80)

doc_obj = Document(page_content="Test content", metadata={"source": "test.txt", "author": "John Doe"})
store3 = InMemoryDocStore(documents=[doc_obj], embedding_model=None)
doc3 = store3.get_document("0")
print(f"Original Document: page_content='{doc_obj.page_content}', metadata={doc_obj.metadata}")
print(f"Stored document: {doc3}")
print(f"Has metadata: {'metadata' in doc3}")
print(f"Metadata value: {doc3.get('metadata', 'NOT FOUND')}")
print(f"Metadata preserved: {doc3.get('metadata') == doc_obj.metadata}")

# Test 4: Add documents with metadata
print("\n" + "="*80)
print("TEST 4: Add Documents with Metadata")
print("="*80)

store4 = InMemoryDocStore(embedding_model=None)
new_docs = [
    Document(page_content="Doc 1", metadata={"id": 1, "type": "article"}),
    Document(page_content="Doc 2", metadata={"id": 2, "type": "blog"}),
]
store4.add_documents(new_docs)

doc4_1 = store4.get_document("0")
doc4_2 = store4.get_document("1")

print(f"Doc 1 stored: {doc4_1}")
print(f"Doc 1 metadata: {doc4_1.get('metadata')}")
print(f"Doc 2 stored: {doc4_2}")
print(f"Doc 2 metadata: {doc4_2.get('metadata')}")

# Test 5: Mixed document types
print("\n" + "="*80)
print("TEST 5: Mixed Document Types")
print("="*80)

store5 = InMemoryDocStore(
    documents=[
        "Plain string",
        {"page_content": "Dict doc", "metadata": {"source": "dict"}},
        Document(page_content="Document obj", metadata={"source": "document"})
    ],
    embedding_model=None
)

for i, doc_id in enumerate(["0", "1", "2"]):
    doc = store5.get_document(doc_id)
    print(f"\nDocument {i}:")
    print(f"  Content: {doc.get('page_content')}")
    print(f"  Metadata: {doc.get('metadata')}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print("\n✅ All metadata preservation tests completed!")
print("Metadata should be preserved for all document types.")

