"""Mathpix extractor module.

Uses Mathpix OCR API to extract text, math, and tables from images.
"""
from typing import Any
import os
import json

try:
    from mpxpy.mathpix_client import MathpixClient
except Exception:
    MathpixClient = None


class MathpixExtractor:
    """Extractor that uses Mathpix OCR API to extract text, math, and tables from images."""
    
    def __init__(self, app_id: str | None = None, app_key: str | None = None, **kwargs: Any):
        self.app_id = app_id or os.getenv("MATHPIX_APP_ID")
        self.app_key = app_key or os.getenv("MATHPIX_APP_KEY")
        
        if MathpixClient is None:
            raise RuntimeError("Mathpix client is not available. Install it with: pip install mpxpy")
            
        if not self.app_id or not self.app_key:
            raise RuntimeError("Mathpix API credentials are required. Set MATHPIX_APP_ID and MATHPIX_APP_KEY environment variables or pass app_id and app_key parameters.")
        
        self.client = MathpixClient(app_id=self.app_id, app_key=self.app_key)

    def extract(self, file_path: str):
        """Extract text, math, and tables from an image using Mathpix OCR.
        
        Args:
            file_path: Path to the image file to process
            
        Returns:
            Dictionary containing extracted content in Mathpix Markdown format
        """
        try:
            # Process the image file
            image = self.client.image_new(file_path=file_path)
            
            # Get the detected content in Mathpix Markdown (MMD) format
            mathpix_markdown = image.mmd()
            
            # Get detailed OCR lines in JSON format for structured data
            try:
                lines_data = image.lines_json()
            except Exception as e:
                print(f"Warning: Could not get JSON lines data: {e}")
                lines_data = {}
            
            # Try to extract structured data from the JSON response
            forms = self._extract_forms_from_json(lines_data)
            tables = self._extract_tables_from_markdown(mathpix_markdown)
            
            return {
                "raw_text": mathpix_markdown,
                "forms": forms,
                "tables": tables,
                "json_data": lines_data
            }
            
        except Exception as e:
            print(f"Mathpix extraction failed: {e}")
            return {
                "raw_text": f"Error: Mathpix extraction failed: {str(e)}",
                "forms": {},
                "tables": [],
                "json_data": {}
            }

    def _extract_forms_from_json(self, json_data):
        """Extract key-value pairs from Mathpix JSON response."""
        forms = {}
        
        if not json_data or not isinstance(json_data, dict):
            return forms
            
        # Look for key-value patterns in the JSON structure
        # This is a simplified approach - Mathpix may have specific structures for forms
        try:
            if "lines" in json_data:
                for line in json_data["lines"]:
                    if isinstance(line, dict) and "text" in line:
                        text = line["text"]
                        # Simple heuristic: look for colon-separated key-value pairs
                        if ":" in text and len(text.split(":")) == 2:
                            key, value = text.split(":", 1)
                            forms[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Error extracting forms from JSON: {e}")
            
        return forms

    def _extract_tables_from_markdown(self, markdown_text):
        """Extract tables from Mathpix Markdown format."""
        tables = []
        
        if not markdown_text:
            return tables
            
        # Split by lines and look for Markdown table patterns
        lines = markdown_text.split('\n')
        current_table = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            
            # Check if this line looks like a table row (contains |)
            if '|' in line and line.startswith('|') and line.endswith('|'):
                # Remove leading/trailing pipes and split
                cells = [cell.strip() for cell in line[1:-1].split('|')]
                current_table.append(cells)
                in_table = True
            elif line.startswith('|') and '---' in line:
                # Table separator line, continue
                continue
            elif in_table and current_table:
                # End of table
                tables.append(current_table)
                current_table = []
                in_table = False
        
        # Don't forget the last table if the text ends with a table
        if current_table:
            tables.append(current_table)
            
        return tables

    def save_results(self, results_dict, output_file_path):
        """Save extraction results to a text file with structured formatting.
        
        Args:
            results_dict: Dictionary with page numbers as keys and extraction results as values
            output_file_path: Path to the output text file
        """
        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("MATHPIX EXTRACTOR RESULTS\n")
                f.write("=" * 80 + "\n\n")
                
                for page_num in sorted(results_dict.keys()):
                    result = results_dict[page_num]
                    
                    f.write(f"{'-' * 35} Page {page_num} {'-' * 35}\n\n")
                    
                    # Raw Mathpix Markdown
                    raw_text = result.get("raw_text", "")
                    f.write(raw_text.strip() + "\n\n" if raw_text else "(No content found)\n\n")
                    
                    # Forms/Key-value pairs
                    forms = result.get("forms", {})
                    f.write("FORMS/KEY-VALUE PAIRS:\n")
                    f.write("-" * 20 + "\n")
                    if forms:
                        for key, value in forms.items():
                            f.write(f"{key}: {value}\n")
                        f.write("\n")
                    else:
                        f.write("(No forms detected)\n\n")
                    
                    # Tables
                    tables = result.get("tables", [])
                    f.write("TABLES:\n")
                    f.write("-" * 20 + "\n")
                    if tables:
                        for i, table in enumerate(tables, 1):
                            f.write(f"Table {i}:\n")
                            for row in table:
                                f.write(" | ".join(str(cell) for cell in row) + "\n")
                            f.write("\n")
                    else:
                        f.write("(No tables detected)\n\n")
                    
                    # JSON Data (optional debug info)
                    json_data = result.get("json_data", {})
                    if json_data:
                        f.write("JSON DEBUG DATA:\n")
                        f.write("-" * 16 + "\n")
                        f.write(json.dumps(json_data, indent=2, ensure_ascii=False))
                        f.write("\n\n")
                    
                    f.write("\n")
        except Exception as e:
            print(f"Error saving Mathpix results: {e}")
