"""
PDF Parser — MCP Server
-----------------------
Extracts text and tables from uploaded medical history PDFs.
Uses pdfplumber for clean text extraction and camelot for table detection.

Day 2 course concept: MCP server + tool interoperability.
Security: PII redaction happens in security/guardrails.py AFTER extraction,
so this server never logs or stores raw extracted content.
"""

import io
import json
from mcp.server import MCPServer, tool

try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # graceful degradation if not installed

app = MCPServer(name="pdf_parser", version="1.0.0")


@app.tool(
    name="extract_text",
    description="Extract raw text from a PDF file path. Returns page-by-page text.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute path to the PDF file"},
            "max_pages": {"type": "integer", "default": 20, "description": "Max pages to extract"},
        },
        "required": ["file_path"],
    },
)
def extract_text(file_path: str, max_pages: int = 20) -> dict:
    """Extract text from each page of a PDF."""
    if pdfplumber is None:
        return {"error": "pdfplumber not installed. Run: pip install pdfplumber"}

    pages = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages[:max_pages]):
                text = page.extract_text() or ""
                pages.append({"page": i + 1, "text": text.strip()})
    except Exception as e:
        return {"error": str(e), "pages": []}

    return {
        "total_pages": len(pages),
        "pages": pages,
        "full_text": "\n\n".join(p["text"] for p in pages),
    }


@app.tool(
    name="extract_tables",
    description="Extract tabular data (e.g. lab results) from a PDF.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute path to the PDF file"},
        },
        "required": ["file_path"],
    },
)
def extract_tables(file_path: str) -> dict:
    """Extract tables from a PDF — useful for lab reports."""
    if pdfplumber is None:
        return {"error": "pdfplumber not installed"}

    all_tables = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for j, table in enumerate(tables):
                    # Convert to list of dicts using first row as header
                    if table and len(table) > 1:
                        headers = [str(h).strip() for h in table[0]]
                        rows = []
                        for row in table[1:]:
                            rows.append({
                                headers[k]: str(cell).strip() if cell else ""
                                for k, cell in enumerate(row)
                            })
                        all_tables.append({
                            "page": i + 1,
                            "table_index": j,
                            "headers": headers,
                            "rows": rows,
                        })
    except Exception as e:
        return {"error": str(e), "tables": []}

    return {"table_count": len(all_tables), "tables": all_tables}


if __name__ == "__main__":
    app.run(transport="stdio")
