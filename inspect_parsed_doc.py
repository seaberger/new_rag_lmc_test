import pickle

# Load the parsed document from the pickle file
with open('test_parsed_doc.pkl', 'rb') as f:
    parsed_docs = pickle.load(f)

# Inspect the structure of the parsed document
if parsed_docs:
    for i, (file_path, docs) in enumerate(parsed_docs.items(), start=1):
        print(f"Document {i} from {file_path.name}:")
        for doc in docs:
            print(f"Text Length: {len(doc.text)}")
            print("Content:")
            print(doc.text)  # Print the entire content
            print("Metadata:")
            print(doc.metadata)
            print("-" * 40)
else:
    print("No documents found in the pickle file.")
