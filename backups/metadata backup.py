# metadata.py
import os
import re
import time
import json
import pickle
import asyncio
import logging
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
    """A pair of part number and product name."""

    part_number: str = Field(
        ..., description="Part number from a table in the datasheet."
    )
    product_name: str = Field(
        ...,
        description="Product name found in the column header above the part number in the specification table.",
    )


class NodeMetadata(BaseModel):
    """Node metadata."""

    pairs: List[PartProductPair] = Field(
        ...,
        description="List of dictionaries with part number and product name pairs found on a row within the table.",
    )


def load_docs_from_pickle(file_path):
    """
    Load documents from a pickle file.

    Args:
        file_path: Path to the pickle file

    Returns:
        List of Document objects
    """
    logging.info(f"Loading documents from {file_path}")
    with open(file_path, "rb") as f:
        loaded_docs = pickle.load(f)
        logging.info(f"Loaded {len(loaded_docs)} documents from {file_path}")
        for i, doc in enumerate(loaded_docs, start=1):
            logging.info(f"Document {i}: Length = {len(doc.text)}")
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

    logging.info(f"Successfully saved {len(nodes)} nodes to {file_path}")
    return file_path


async def generate_context(node_text, max_retries=3):
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
            logging.error(f"Error on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retrying

    return "Failed to generate context after multiple attempts"


async def enhance_all_nodes(nodes, batch_size=5, sleep_time=1):
    """
    Enhance all nodes by appending context to the content.

    Args:
        nodes: List of nodes to process
        batch_size: Number of nodes to process before sleeping
        sleep_time: Time to sleep between batches to avoid rate limits

    Returns:
        The enhanced nodes list
    """
    logging.info(f"Enhancing {len(nodes)} nodes with context...")

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
                context = await generate_context(node.text)

            # Append context to the content with a separator
            node.text = f"{node.text}\n\nContext: {context}"

            # Sleep after each batch to avoid rate limits
            if (i + 1) % batch_size == 0:
                time.sleep(sleep_time)

        except Exception as e:
            logging.error(f"Error processing node {i}: {str(e)}")
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
    logging.info(f"Successfully enhanced {successful}/{len(nodes)} nodes")

    return nodes


def process_pairs_metadata(nodes):
    """
    Process nodes to properly format product identifiers with the correct metadata structure.

    Args:
        nodes: List of nodes to process

    Returns:
        The processed nodes
    """
    logging.info(f"Processing {len(nodes)} nodes to format product identifiers...")

    # Compile regex patterns for part number validation
    part_number_pattern = re.compile(r"^(?:\d{7}|\d{2}-\d{3}-\d{3})$")
    # Pattern to match 8-9 digit numbers that might be 7 digits + subscript
    subscript_pattern = re.compile(r"^(\d{7})(\d{1,2})$")

    valid_pairs_count = 0
    invalid_pairs_count = 0

    for node in nodes:
        node_id = node.metadata.get('id', 'unknown')
        file_name = node.metadata.get('file_name', 'unknown')
        logging.info(f"Processing node with ID: {node_id}, File Name: {file_name}")
        if "pairs" in node.metadata:
            logging.info(f"Initial pairs count: {len(node.metadata['pairs'])}")
            valid_pairs = []

            for pair in node.metadata["pairs"]:
                if (
                    isinstance(pair, dict)
                    and "part_number" in pair
                    and "product_name" in pair
                ):
                    part_num = str(pair["part_number"])
                    prod_name = str(pair["product_name"])

                    # First try exact match
                    if part_number_pattern.match(part_num):
                        valid_pairs.append(
                            {"part_number": part_num, "product_name": prod_name}
                        )
                        valid_pairs_count += 1
                        continue

                    # Check for subscript pattern
                    subscript_match = subscript_pattern.match(part_num)
                    if subscript_match:
                        # Extract the 7-digit base number
                        base_number = subscript_match.group(1)
                        subscript = subscript_match.group(2)
                        logging.info(
                            f"Handling subscript: {part_num} -> {base_number} (subscript: {subscript})"
                        )
                        valid_pairs.append(
                            {"part_number": base_number, "product_name": prod_name}
                        )
                        valid_pairs_count += 1
                        continue

                    invalid_pairs_count += 1
                    logging.info(f"Invalid part number format: {part_num}")

            if valid_pairs:
                node.metadata["pairs"] = valid_pairs
            else:
                del node.metadata["pairs"]
                # Clean up any old metadata fields
                node.metadata.pop("identifiers", None)
                node.metadata.pop("identifiers_count", None)
                node.metadata.pop("product_identifiers", None)

    logging.info(f"Successfully processed metadata for {len(nodes)} nodes")
    logging.info(f"Valid pairs found: {valid_pairs_count}")
    logging.info(f"Invalid pairs rejected: {invalid_pairs_count}")
    return nodes


def initialize_extractor():
    """Initialize the PydanticProgramExtractor for metadata extraction"""
    EXTRACT_TEMPLATE_STR = """
    Here is the content of the section:
    ----------------
    {context_str}
    ----------------
    Your task is to find ALL part numbers and their associated product names in this content.
    Be thorough - check every specification table within the datasheets.

    FIELD DEFINITIONS:
    1. part_number field - MUST ONLY contain:
       - EXACTLY 7 digits (e.g., 1299161)
       - OR XX-XXXX-XXX format (e.g., 33-3336-000)
       - NEVER put model names like 'FieldMaxII-TOP' or 'PM10K+' here
       - NEVER put descriptive text here
       - Examples of valid part numbers: 1299161, 33-3336-000
       - Examples of invalid entries: 'FieldMaxII-TOP', 'PM10K+', 'Thermopile'

    2. product_name field - MUST contain:
       - The model name from the column header (e.g., 'FieldMaxII-TOP', 'PM10K+')
       - This is where model names and series names belong
       - Examples of valid product names: 'FieldMaxII-TOP', 'PM10K+', 'Thermopile'

    IMPORTANT: Handle subscripts carefully!
    - Many part numbers have subscript notes at the end
    - If you see an 8 or 9 digit number, it's likely a 7-digit part number with a subscript
    - Example: If you see "10979011", the real part number is "1097901" (the 1 is a subscript)
    - ALWAYS check if longer numbers are actually 7-digit part numbers with subscripts

    WHERE TO LOOK:
    - Use contextual cues from surrounding text to differentiate between part numbers and product names
    - Pay attention to table headers and labels that might indicate a model or series name
    """

    # Check for OpenAI API key
    logging.info("Checking OpenAI configuration...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Initialize the OpenAI program
    logging.info("Initializing OpenAI program...")
    try:
        llm = OpenAI(
            model="gpt-4o",
            api_key=api_key,
            temperature=0.0,  # Be deterministic for extraction
            max_tokens=1000,
        )
        Settings.llm = llm
        logging.info("Successfully initialized OpenAI LLM")
    except Exception as e:
        logging.error(f"Error initializing OpenAI: {str(e)}")
        raise

    def is_valid_part_number(part_num: str) -> bool:
        """Check if a string matches valid part number patterns."""
        return bool(re.match(r"^(?:\d{7}|\d{2}-\d{3}-\d{3})$", str(part_num)))

    def preprocess_response(response_str: str) -> dict:
        """Pre-process the LLM response to ensure model numbers are handled correctly."""
        try:
            data = json.loads(response_str)
            if isinstance(data, list) and len(data) > 0:
                filtered_pairs = []
                logging.info("\nPreprocessing pairs:")
                for pair in data:
                    part_num = str(pair.get("part_number", ""))
                    prod_name = str(pair.get("product_name", ""))

                    if is_valid_part_number(part_num):
                        logging.info(f"  Valid: '{part_num}' -> '{prod_name}'")
                        filtered_pairs.append(pair)
                    else:
                        logging.info(
                            f"  Invalid part number format: '{part_num}' (must be 7 digits or XX-XXX-XXX)"
                        )

                logging.info(
                    f"\nFound {len(filtered_pairs)} valid pairs out of {len(data)} total"
                )
                return {"pairs": filtered_pairs}
            return {"pairs": []}
        except Exception as e:
            logging.error(f"Error preprocessing response: {str(e)}")
            return {"pairs": []}

    openai_program = OpenAIPydanticProgram.from_defaults(
        output_cls=NodeMetadata,
        prompt_template_str="{input}",
        extract_template_str=EXTRACT_TEMPLATE_STR,
        response_preprocessor=preprocess_response,
    )

    program_extractor = PydanticProgramExtractor(
        program=openai_program, input_key="input", show_progress=True
    )

    return program_extractor


async def create_origin_nodes(input_file_path):
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

    # Initialize node parser with smaller chunk size for better table handling
    node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)

    # Create ingestion pipeline
    pipeline = IngestionPipeline(transformations=[node_parser, program_extractor])

    # Run the pipeline with error handling
    logging.info("Running ingestion pipeline to create origin nodes...")
    try:
        # Print document info for debugging
        if loaded_docs:
            logging.info(f"\nProcessing {len(loaded_docs)} documents")
            for i, doc in enumerate(loaded_docs[:2]):  # Show first 2 docs
                logging.info(f"\nDocument {i + 1}:")
                logging.info("-" * 40)
                logging.info(f"Text length: {len(doc.text)}")
                logging.info("Sample content:")
                logging.info(doc.text[:500] + "...")
                logging.info("-" * 40)

        logging.info("\nStarting pipeline run...")
        origin_nodes = await pipeline.arun(documents=loaded_docs)
        logging.info("Pipeline run completed")

        if origin_nodes:
            logging.info(f"Created {len(origin_nodes)} origin nodes")
            # Print sample nodes
            for i, node in enumerate(origin_nodes[:2]):  # Show first 2 nodes
                logging.info(f"\nNode {i + 1}:")
                logging.info("-" * 40)
                logging.info(f"Text length: {len(node.text)}")
                logging.info(f"Metadata: {node.metadata}")
                logging.info("Sample content:")
                logging.info(node.text[:500] + "...")
                logging.info("-" * 40)
            return origin_nodes
        else:
            logging.info(
                "No valid nodes were created. Check the extraction rules and validation."
            )
            return []
    except Exception as e:
        logging.error(f"Error during node creation: {str(e)}")
        logging.info("Stack trace:")
        import traceback

        traceback.print_exc()
        logging.info("\nReturning empty node list to allow pipeline to continue")
        return []


async def main(
    input_file="./parsed_lmc_docs.pkl",
    output_file="./enhanced_laser_nodes.pkl",
):
    """
    Main function to process the metadata pipeline.

    Args:
        input_file: Path to the input pickle file
        output_file: Path to the output pickle file
    """
    logging.info(f"Starting metadata processing pipeline...")
    logging.info(f"Input file: {input_file}")
    logging.info(f"Output file: {output_file}")

    # Step 1: Create origin nodes
    origin_nodes = await create_origin_nodes(input_file)

    # Step 2: Process pairs metadata
    processed_nodes = process_pairs_metadata(origin_nodes)

    # Step 3: Enhance nodes with context
    enhanced_nodes = await enhance_all_nodes(processed_nodes)

    # Step 4: Save the enhanced nodes
    save_nodes_to_pickle(enhanced_nodes, output_file)

    logging.info(f"Metadata processing pipeline completed successfully!")
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

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Run the async main function
    asyncio.run(main(input_file=args.input, output_file=args.output))
