import os
import asyncio
from pathlib import Path
from llama_cloud_services import LlamaParse
from typing import List
import pickle

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

For each datasheet table, identify pairs of model names and part numbers and insert into the metadata. 
To structure the metadata with part number and model name pairs, you can use a list of tuples, where each tuple contains a model name and its corresponding part number. Here's an example of how it can be structured in the metadata:

```python
metadata = {
    'pairs': [
        ('PM2', '1174264'),
        ('PM10', '1174262'),
        ('PM30', '1174257')
    ]
}
```
"""


def create_experiment_parser() -> LlamaParse:
    """Create and configure the LlamaParse instance with experimental settings."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable must be set")

    return LlamaParse(
        result_type="markdown",
        auto_mode=True,
        auto_mode_trigger_on_image_in_page=True,
        auto_mode_trigger_on_table_in_page=True,
        invalidate_cache=True,
        do_not_cache=True,
        # vendor_multimodal_api_key=api_key,
        user_prompt=DATASHEET_PARSE_PROMPT,
    )


async def process_documents_experiment(
    file_list: List[Path], parser_template: LlamaParse
):
    results = {}
    for file_path in file_list:
        try:
            print(f"Processing {file_path.name}...")
            doc = await parser_template.aload_data(file_path)
            if doc:
                results[file_path] = doc
                print(f"Successfully processed {file_path.name}")
            else:
                print(f"No content extracted from {file_path.name}")
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    # Save results to a pickle file
    with open("test_parsed_doc.pkl", "wb") as f:
        pickle.dump(results, f)
    print("Results saved to test_parsed_doc.pkl")


if __name__ == "__main__":
    # Example usage
    experiment_parser = create_experiment_parser()
    file_list = [
        Path(
            "data/sample_docs/COHR_Air-CooledThermopileSensors_USB_RS232_DS_1119_3.pdf"
        )
    ]
    asyncio.run(process_documents_experiment(file_list, experiment_parser))
