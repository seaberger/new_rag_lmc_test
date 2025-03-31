#!/usr/bin/env python3
import os
import time
import argparse
import asyncio
import pickle
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional

from llama_cloud_services import LlamaParse
from llama_index.core import Document

# Custom parsing prompt for technical documents
DATASHEET_PARSE_PROMPT = """# CRITICAL PARSING INSTRUCTIONS - FOLLOW EXACTLY

These documents contain technical information about laser power meters, laser energy meters, and laser beam diagnostics products.

## TABLE FORMATTING RULES (HIGHEST PRIORITY):

1. FILL ALL EMPTY CELLS: Every cell in specification tables must be filled. No cell should be empty.
   - When a value spans multiple columns, copy that value to each individual cell it applies to.
   - Example: If "0.19 to 12" appears once but applies to all models, it must be repeated in each model's column.

2. TABLE STRUCTURE: Include model names in the first row of each column above specifications.
   - Example: |Model|PM2|PM10|PM30|

3. PART NUMBERS: 
   - Keep part numbers within specification tables
   - Remove any footnote symbols/superscripts from part numbers
   - Most part numbers have seven digits unless they start with 33 and include dashes

## EXAMPLES OF CORRECT TABLE FORMATTING:

INCORRECT (with empty cells):
|Wavelength Range (µm)| |0.19 to 12| | |
|Active Area Diameter (mm)|50| |25|10|

CORRECT (all cells filled):
|Wavelength Range (µm)|0.19 to 12|0.19 to 12|0.19 to 12|0.19 to 12|
|Active Area Diameter (mm)|50|50|25|10|

## ADDITIONAL INSTRUCTIONS:

1. Rename "Mechanical Specifications" to "Mechanical Dimensions"
2. Leave drawing dimensions as text, not in table format
3. Ignore footnotes with underscore numbers in part numbers

## VALIDATION STEP:
After completing the table, verify that:
1. Every cell contains a value (no empty cells)
2. Values that span multiple columns are copied to each relevant cell
3. All part numbers are properly formatted without superscripts

Please confirm you've followed these instructions with the statement: "All cells filled and formatted according to instructions."
"""


def create_parser() -> LlamaParse:
    """Create and configure the LlamaParse instance with appropriate settings."""
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable must be set")

    return LlamaParse(
        result_type="markdown",
        verbose=True,
        invalidate_cache=True,
        do_not_cache=True,
        use_vendor_multimodal_model=True,
        vendor_multimodal_model_name="openai-gpt4o",
        vendor_multimodal_api_key=api_key,
        user_prompt=DATASHEET_PARSE_PROMPT,
    )


async def process_documents_parallel(
    file_list: List[Path],
    parser_template: LlamaParse,
    max_workers: int = 8,
    max_retries: int = 5,
    timeout_seconds: int = 120,
) -> Dict[Path, List[Document]]:
    """
    Process multiple documents in parallel using async.

    Args:
        file_list: List of file paths to process
        parser_template: LlamaParse template to use for parsing
        max_workers: Maximum number of concurrent workers
        max_retries: Maximum number of retry attempts
        timeout_seconds: Timeout in seconds for each parsing job

    Returns:
        Dictionary mapping file paths to parsed document lists
    """
    results = {}

    # Define the worker function that will process each document
    async def process_single_doc(fname: Path):
        # Create a fresh parser instance for each document with the timeout set
        parser = LlamaParse(
            **{
                k: v
                for k, v in parser_template.__dict__.items()
                if not k.startswith("_") and k != "custom_client"
            }
        )

        # Set the timeout specifically for this job
        parser.job_timeout_in_seconds = timeout_seconds

        for attempt in range(max_retries):
            try:
                print(
                    f"Attempt {attempt + 1} parsing {fname.name} (timeout: {timeout_seconds}s)..."
                )
                start_time = time.time()

                doc = await parser.aload_data(fname)

                elapsed = time.time() - start_time

                # If we got here and doc has content, parsing worked
                if doc and len(doc) > 0:
                    print(f"Successfully parsed {fname.name} in {elapsed:.2f} seconds")
                    return doc
                else:
                    print(f"No content returned on attempt {attempt + 1}")
            except Exception as e:
                print(f"Error on attempt {attempt + 1} for {fname.name}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Brief pause before retry

        print(f"Failed to parse {fname.name} after {max_retries} attempts")
        return None

    # Process documents with asyncio.gather with concurrency limit
    semaphore = asyncio.Semaphore(max_workers)

    async def process_with_semaphore(fname):
        async with semaphore:
            return fname, await process_single_doc(fname)

    tasks = [process_with_semaphore(fname) for fname in file_list]
    results_list = await asyncio.gather(*tasks)

    # Process results
    for fname, doc_result in results_list:
        if doc_result:
            results[fname] = doc_result
            print(f"✅ {fname.name}: {len(doc_result)} sections")
        else:
            print(f"❌ {fname.name}: Failed to parse")

    return results


def convert_to_standard_docs(docs_dict: Dict[Path, List[Document]]) -> List[Document]:
    """
    Convert parser output to standard Document objects with enhanced metadata.

    Args:
        docs_dict: Dictionary with filenames as keys and document lists as values

    Returns:
        List of standardized Document objects
    """
    standard_docs = []
    for file_path, doc_list in docs_dict.items():
        file_name = file_path.name  # Get just the filename
        total_docs = len(doc_list)

        for i, doc in enumerate(doc_list, 1):
            # Create standard Document object with enhanced metadata
            standard_doc = Document(
                text=doc.text_resource.text,
                metadata={
                    "source": str(file_path),
                    "file_name": file_name,
                    "doc_num": i,
                    "total_docs": total_docs,
                    "id": doc.id_ if hasattr(doc, "id_") else None,
                },
            )
            standard_docs.append(standard_doc)

    return standard_docs


def save_docs_to_pickle(docs: List[Document], file_path: str = "parsed_docs.pkl"):
    """
    Save parsed documents to a pickle file.

    Args:
        docs: List of Document objects
        file_path: Path to save the pickle file
    """
    # Make sure parent directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    # Save to pickle file
    with open(file_path, "wb") as f:
        pickle.dump(docs, f)

    print(f"Saved {len(docs)} documents to {file_path}")


async def main(
    input_dir: str = "data",
    output_file: str = "parsed_docs.pkl",
    max_workers: int = 8,
    timeout: int = 120,
):
    """
    Main function to parse all PDF files in a directory.

    Args:
        input_dir: Directory containing PDF files to parse
        output_file: Path to save the parsed documents
        max_workers: Maximum number of concurrent workers
        timeout: Timeout in seconds for each parsing job
    """
    # Get all PDF files in the input directory
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory {input_dir} does not exist")

    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return

    print(f"Found {len(pdf_files)} PDF files in {input_dir}")

    # Create parser template
    parser_template = create_parser()

    # Process documents in parallel
    results = await process_documents_parallel(
        pdf_files, parser_template, max_workers=max_workers, timeout_seconds=timeout
    )

    # Print summary
    print(f"\nSuccessfully processed {len(results)} out of {len(pdf_files)} documents")
    for fname, doc in results.items():
        print(f"- {fname.name}: {len(doc)} sections")

    # Convert to standard documents
    standard_docs = convert_to_standard_docs(results)

    # Save to pickle file
    save_docs_to_pickle(standard_docs, output_file)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Parse PDF documents using LlamaParse")
    parser.add_argument(
        "--input-dir",
        "-i",
        type=str,
        default="data",
        help="Directory containing PDF files to parse (default: data)",
    )
    parser.add_argument(
        "--output-file",
        "-o",
        type=str,
        default="parsed_docs.pkl",
        help="Path to save the parsed documents (default: parsed_docs.pkl)",
    )
    parser.add_argument(
        "--max-workers",
        "-w",
        type=int,
        default=8,
        help="Maximum number of concurrent workers (default: 8)",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=120,
        help="Timeout in seconds for each parsing job (default: 120)",
    )

    args = parser.parse_args()

    # Run the main function
    asyncio.run(
        main(
            input_dir=args.input_dir,
            output_file=args.output_file,
            max_workers=args.max_workers,
            timeout=args.timeout,
        )
    )
