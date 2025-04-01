import pickle

# Load the documents from the pickle file
with open('test_parsed_doc.pkl', 'rb') as f:
    documents = pickle.load(f)

# Inspect the structure of the documents
if documents:
    total_pairs = 0
    all_pairs = []
    for i, doc in enumerate(documents, start=1):
        pairs = doc.metadata.get('pairs', [])
        total_pairs += len(pairs)
        all_pairs.extend(pairs)
        print(f"Document {i}:")
        print(f"Text Length: {len(doc.text)}")
        print("Sample Content:")
        print(doc.text[:500] + '...')
        print("Metadata:")
        print(doc.metadata)
        print("-" * 40)

    print(f"Total number of part number, model name pairs: {total_pairs}")
    print("List of all pairs:")
    for pair in all_pairs:
        print(pair)
else:
    print("No documents found in the pickle file.")
