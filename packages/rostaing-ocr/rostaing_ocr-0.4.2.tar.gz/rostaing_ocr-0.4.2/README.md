# Rostaing OCR

[![PyPI version](https://img.shields.io/pypi/v/rostaing-ocr.svg)](https://pypi.org/project/rostaing-ocr/)
[![Python versions](https://img.shields.io/pypi/pyversions/rostaing-ocr.svg)](https://pypi.org/project/rostaing-ocr/)
[![PyPI license](https://img.shields.io/pypi/l/rostaing-ocr.svg)](https://pypi.org/project/rostaing-ocr/)
[![PyPI downloads](https://img.shields.io/pypi/dm/rostaing-ocr.svg)](https://pypi.org/project/rostaing-ocr/)

**An advanced semantic OCR tool that extracts structured content (titles, paragraphs, lists, and tables) from PDFs and images. Optimized for AI, LLMs, and RAG systems.**

Created by Davila Rostaing.

## Key Features

-   ✨ **Semantic Layout Analysis**: Doesn't just extract text—it understands the document's structure. It identifies titles, paragraphs, lists, and tables for a perfectly formatted output.
-   🧠 **Advanced Table Recognition**: Intelligently identifies table structures, infers missing headers using data-type analysis, and generates a dual output: **Markdown** (for readability) and structured data (for analysis by AI).
-   🚀 **High-Accuracy OCR**: It delivers excellent accuracy on both scanned and digital documents.
-   📦 **Flexible Installation**: A lightweight core with optional AI dependencies. Install only what you need.
-   📄 **Handles Mixed Content**: Intelligently extracts text from both the text layers and embedded images within PDFs.
-   ⚙️ **Versatile Input**: Processes single or multiple files (PDF, PNG, JPG, etc.) in a single run.
-   🔗 **Feature Extraction**: Automatically detects and extracts URLs and signatures (experimental) present in the document.

## Installation

### Best Practice: Use a Virtual Environment

To keep project dependencies isolated, using a virtual environment is highly recommended.

**On macOS/Linux:**
```bash
# Create an environment named '.venv'
python3 -m venv .venv

# Activate the environment
source .venv/bin/activate
```

**On Windows:**
```bash
# Create an environment named '.venv'
python -m venv .venv

# Activate the environment
.venv\Scripts\activate
```

### Prerequisites
-   Python 3.9 or higher.
-   Using a virtual environment is highly recommended.

### Installation Instructions
Installation is a two-step process to provide maximum flexibility.

**1. Install the Core Library:**
This command is lightweight and fast. It installs all the package's processing logic.
```bash
pip install rostaing-ocr
```

**2. Install the AI Backend:**
To perform the image analysis and OCR, you must install the AI dependencies. This is a heavier installation that downloads the required deep learning models.
```bash
pip install "rostaing-ocr[torch]"
```
**Note:** The first time you run the extractor, the AI models will be downloaded. This may take a moment and requires an internet connection. This is a one-time process.

## Usage
Using the library is simple. The extraction process starts as soon as you create an instance of the `RostaingOCR` class.

### --- Example 1: Simple Processing of a Single File ---
This example creates `output.md` and `output.txt` with the extracted semantic content.

```python
from rostaing_ocr import RostaingOCR

# Extraction is launched on initialization
extractor = RostaingOCR(
    "path/to/my_document.pdf",
    output_basename="document_report", # Custom name for output files
    print_to_console=True              # Optional: display results in the terminal
)

# Print a summary of the operation
print(extractor)
```

### --- Example 2: Advanced Processing of Multiple Files ---
This example processes a PDF and an image, specifies French and English as languages, and saves image assets to a separate folder.

```python
from rostaing_ocr import RostaingOCR

multi_file_extractor = RostaingOCR(
    input_path_or_paths=["annual_report.pdf", "invoice.jpg"],
    output_basename="combined_report", # Optional
    print_to_console=True              # Optional: display results in the terminal
    save_images_externally=True,       # Saves detected signatures, etc.
    languages=['fra', 'eng']           # Specify languages for better accuracy
    image_dpi= 300,                    # Optional : default --> 300
)

print(multi_file_extractor)
```

## Application for LLM and RAG Pipelines
Large Language Models (LLMs) need clean, structured data. `rostaing-ocr` is the crucial first step in any data ingestion pipeline for Retrieval-Augmented Generation (RAG) systems.

By converting visual documents (scanned PDFs, invoices, contracts) into semantic Markdown, it prepares the data for AI. The structure (titles, paragraphs) is preserved, which dramatically improves the quality of answers in RAG systems.

**Typical Workflow:**

1.  **Input**: A set of PDFs or images.
2.  **Extraction (rostaing-ocr)**: Convert all documents into structured Markdown.
3.  **Processing**: The text and table are fed into text splitters and embedding models.
4.  **Indexing**: The resulting vectors are stored in a vector database (e.g., Chroma, Pinecone, FAISS, etc) for efficient retrieval.

In short, `rostaing-ocr` unlocks your documents, making them ready for any modern AI stack.

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Useful Links
-   **GitHub**: [https://github.com/Rostaing/rostaing-ocr](https://github.com/Rostaing/rostaing-ocr)
-   **PyPI**: [https://pypi.org/project/rostaing-ocr/](https://pypi.org/project/rostaing-ocr/)
-   **LinkedIn**: [https://www.linkedin.com/in/davila-rostaing/](https://www.linkedin.com/in/davila-rostaing/)
-   **YouTube**: [youtube.com/@RostaingAI](https://youtube.com/@rostaingai?si=8wo5H5Xk4i0grNyH)