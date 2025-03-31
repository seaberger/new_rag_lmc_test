# metadata.py
import os
import time
import pickle
import asyncio
import threading
from pathlib import Path
from tqdm import tqdm
import openai

from llama_index.llms.openai import OpenAI

# from llama_index.core import Settings
# from llama_index.core.embeddings import OpenAIEmbedding
# from llama_index.core.schema import TextNode
# from llama_index.core.node_parser import SentenceSplitter
# from llama_index.core.ingestion import IngestionPipeline
# from llama_index.core.program import OpenAIPydanticProgram
# from llama_index.core.extractors import PydanticProgramExtractor
# from pydantic import BaseModel, Field
# Core settings
from llama_index.core import Settings

# Embeddings (integration package)
from llama_index.embeddings.openai import OpenAIEmbedding

# Core schema
from llama_index.core.schema import TextNode

# Core node parser
from llama_index.core.node_parser import SentenceSplitter

# Core ingestion
from llama_index.core.ingestion import IngestionPipeline

# Program (integration package)
from llama_index.program.openai import OpenAIPydanticProgram

# Core extractors
from llama_index.core.extractors import PydanticProgramExtractor

from pydantic import BaseModel, Field
from typing import List


# Set up OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
openai.api_key = OPENAI_API_KEY


# Define the Pydantic models for metadata extraction
class PartProductPair(BaseModel):
    part_number: str = Field(
        ..., description="Unique part number from first column of table"
    )
    product_name: str = Field(
        ..., description="Unique product name from second column of table"
    )


class NodeMetadata(BaseModel):
    """Node metadata."""

    pairs: List[PartProductPair] = Field(
        ...,
        description="List of dictionaries with part number and product name pairs found on a row within the table.",
    )


# Helper function to run async code in a thread
def run_in_thread(coro):
    res = None

    def target():
        nonlocal res
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(coro)
        loop.close()

    t = threading.Thread(target=target)
    t.start()
    t.join()
    return res


def load_docs_from_pickle(file_path):
    """
    Load documents from a pickle file.

    Args:
        file_path: Path to the pickle file

    Returns:
        List of Document objects
    """
    with open(file_path, "rb") as f:
        loaded_docs = pickle.load(f)

    print(f"Loaded {len(loaded_docs)} documents from {file_path}")
    return loaded_docs


def save_nodes_to_pickle(nodes, file_path):
    """
    Save a list of nodes to a pickle file.

    Args:
        nodes: List of nodes to save
        file_path: Path where to save the pickle file

    Returns:
        Path to the saved file
    """
    # Make sure the directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    # Save the nodes to pickle
    with open(file_path, "wb") as f:
        pickle.dump(nodes, f)

    print(f"Successfully saved {len(nodes)} nodes to {file_path}")
    return file_path


def generate_context(node_text, max_retries=3):
    """
    Generate context for a node using direct OpenAI API.

    Args:
        node_text: Text content of the node
        max_retries: Number of retries in case of API errors

    Returns:
        Generated context string
    """
    prompt = f"""
    Generate keywords and brief phrases describing the main topics, entities, and actions in this text.
    Replace any pronouns with their specific referents.
    Format as comma-separated phrases.
    
    TEXT:
    {node_text[:1000]}  # Limit text length to avoid token issues
    """

    for attempt in range(max_retries):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates concise context for document chunks.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.2,
            )

            # Extract the content from the response
            context = response.choices[0].message.content.strip()
            return context

        except Exception as e:
            print(f"Error on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retrying

    return "Failed to generate context after multiple attempts"


def enhance_all_nodes(nodes, batch_size=5, sleep_time=1):
    """
    Enhance all nodes by appending context to the content.

    Args:
        nodes: List of nodes to process
        batch_size: Number of nodes to process before sleeping
        sleep_time: Time to sleep between batches to avoid rate limits

    Returns:
        The enhanced nodes list
    """
    print(f"Enhancing {len(nodes)} nodes with context...")

    # Create a progress bar with standard tqdm
    for i, node in enumerate(tqdm(nodes)):
        try:
            # Check if context already exists in metadata
            if "context" in node.metadata:
                # Use existing context from metadata
                context = node.metadata["context"]
                # Remove it from metadata
                del node.metadata["context"]
            else:
                # Generate new context
                context = generate_context(node.text)

            # Append context to the content with a separator
            node.text = f"{node.text}\n\nContext: {context}"

            # Sleep after each batch to avoid rate limits
            if (i + 1) % batch_size == 0:
                time.sleep(sleep_time)

        except Exception as e:
            print(f"Error processing node {i}: {str(e)}")
            # Add a placeholder context
            node.text = f"{node.text}\n\nContext: Error generating context: {str(e)}"
            # Make sure we don't have context in metadata
            if "context" in node.metadata:
                del node.metadata["context"]
            time.sleep(sleep_time)  # Sleep after an error

    # Count successful enhancements
    successful = sum(
        1
        for node in nodes
        if "\n\nContext: " in node.text and not "Error generating context" in node.text
    )
    print(f"Successfully enhanced {successful}/{len(nodes)} nodes")

    return nodes


def process_pairs_metadata(nodes):
    """
    Process nodes to properly format part number and product name pairs,
    with the correct metadata structure.

    Args:
        nodes: List of nodes to process

    Returns:
        The processed nodes
    """
    print(f"Processing {len(nodes)} nodes to format part-product pairs...")

    for node in nodes:
        # Process pairs field if it exists
        if "pairs" in node.metadata:
            # Create more accessible part_numbers and product_names arrays
            part_numbers = []
            product_names = []

            for pair in node.metadata["pairs"]:
                if (
                    isinstance(pair, dict)
                    and "part_number" in pair
                    and "product_name" in pair
                ):
                    part_numbers.append(pair["part_number"])
                    product_names.append(pair["product_name"])

            # Add the arrays to metadata
            node.metadata["part_numbers"] = part_numbers
            node.metadata["product_names"] = product_names

            # Add count
            node.metadata["pairs_count"] = len(part_numbers)

            # Rename the original pairs field to product_part_pairs
            node.metadata["product_part_pairs"] = node.metadata["pairs"]
            del node.metadata["pairs"]

    print(f"Successfully processed metadata for {len(nodes)} nodes")
    return nodes


def initialize_extractor():
    """Initialize the PydanticProgramExtractor for metadata extraction"""
    EXTRACT_TEMPLATE_STR = """\
    Here is the content of the section:
    ----------------
    {context_str}
    ----------------
    Extract the following information as a {class_name} object:
    - Pairs: List of dictionaries, each containing a part number and its corresponding product name.

    The output format should be:
    [
        {"part_number": "1224020", "product_name": "BeamMaster-USB System BM-7 (InGaAs 5mm)"},
        {"part_number": "1230323", "product_name": "PowerMax-RS PM2X"}
    ]
    Ensure that the output is a valid JSON format. Avoid invalid control characters in the output.
    """

    # Initialize the OpenAI program
    llm = OpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
    Settings.llm = llm

    openai_program = OpenAIPydanticProgram.from_defaults(
        output_cls=NodeMetadata,
        prompt_template_str="{input}",
        extract_template_str=EXTRACT_TEMPLATE_STR,
    )

    program_extractor = PydanticProgramExtractor(
        program=openai_program, input_key="input", show_progress=True
    )

    return program_extractor


def create_origin_nodes(input_file_path):
    """
    Create origin nodes from the input pickle file using the ingestion pipeline.

    Args:
        input_file_path: Path to the input pickle file

    Returns:
        List of processed nodes
    """
    # Load documents
    loaded_docs = load_docs_from_pickle(input_file_path)

    # Initialize LLM and program extractor
    program_extractor = initialize_extractor()

    # Initialize node parser
    node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=128)

    # Create ingestion pipeline
    pipeline = IngestionPipeline(transformations=[node_parser, program_extractor])

    # Run the pipeline
    print("Running ingestion pipeline to create origin nodes...")
    origin_nodes = run_in_thread(pipeline.arun(documents=loaded_docs))
    print(f"Created {len(origin_nodes)} origin nodes")

    return origin_nodes


def main(
    input_file="./parsed_lmc_docs.pkl",
    output_file="./enhanced_laser_nodes.pkl",
):
    """
    Main function to process the metadata pipeline.

    Args:
        input_file: Path to the input pickle file
        output_file: Path to the output pickle file
    """
    print(f"Starting metadata processing pipeline...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")

    # Step 1: Create origin nodes
    origin_nodes = create_origin_nodes(input_file)

    # Step 2: Process pairs metadata
    processed_nodes = process_pairs_metadata(origin_nodes)

    # Step 3: Enhance nodes with context
    enhanced_nodes = enhance_all_nodes(processed_nodes)

    # Step 4: Save the enhanced nodes
    save_nodes_to_pickle(enhanced_nodes, output_file)

    print(f"Metadata processing pipeline completed successfully!")
    return enhanced_nodes


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process metadata for document nodes")
    parser.add_argument(
        "--input",
        default="./parsed_docs.pkl",
        help="Path to the input pickle file",
    )
    parser.add_argument(
        "--output",
        default="./enhanced_laser_nodes.pkl",
        help="Path to the output pickle file",
    )

    args = parser.parse_args()

    main(input_file=args.input, output_file=args.output)
