"""Gemini/Google Vision extractor module.

Uses Google Cloud Vision API to extract text from images.
"""
from typing import Any
import os

try:
    from google.cloud import vision
except Exception:
    vision = None

try:
    import google.generativeai as genai
except Exception:
    genai = None


class GeminiExtractor:
    """Extractor that uses Google's AI services for text extraction."""
    
    def __init__(self, api_key: str | None = None, use_genai: bool = False, **kwargs: Any):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
        self.use_genai = use_genai and genai is not None
        self.is_enable_extract_tables = False
        self.is_enable_extract_forms = False

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./google-vision-api-testing.json"
        
        # if self.use_genai and self.api_key:
        #     genai.configure(api_key=self.api_key)

    def extract(self, file_path: str):
        # Try Gemini AI first if available
        if self.use_genai and genai is not None and self.api_key:
            try:
                return self._extract_with_genai(file_path)
            except Exception as e:
                print(f"Gemini AI extraction failed ({e}), trying Google Vision...")
        
        # Try Google Cloud Vision API
        if vision is not None:
            try:
                return self._extract_with_vision(file_path)
            except Exception as e:
                print(f"Google Vision extraction failed ({e}), falling back to tesseract...")
        
    
    def _extract_with_genai(self, file_path: str):
        """Extract text using Gemini AI with structured data extraction."""
        import PIL.Image
        import json
        
        model = genai.GenerativeModel('gemma-3n-e4b-it')
        image = PIL.Image.open(file_path)
        
        # Enhanced prompt for structured extraction
        prompt = """
        Analyze this image and extract all content in the following JSON format:
        {
            "raw_text": "all visible text content",
            "forms": {
                "key1": "value1",
                "key2": "value2"
            },
            "tables": [
                [["row1col1", "row1col2"], ["row2col1", "row2col2"]]
            ]
        }

        Instructions:
        - raw_text: Extract all visible text as it appears
        - forms: Identify key-value pairs (labels with corresponding values, form fields, etc.)
        - tables: Extract any tabular data as arrays of rows and columns
        - Return only valid JSON, no additional text
        """
        
        response = model.generate_content([prompt, image])
        
        try:
            # Parse JSON response
            result = json.loads(response.text.strip())
            return {
                "raw_text": result.get("raw_text", ""),
                "forms": result.get("forms", {}),
                "tables": result.get("tables", [])
            }
        except json.JSONDecodeError:
            # Fallback: extract just raw text if JSON parsing fails
            text = response.text.strip() if response.text else ""
            return {"raw_text": text, "forms": {}, "tables": []}
    
    def _extract_with_vision(self, file_path: str):
        """Extract text using Google Cloud Vision API with document analysis."""
        client = vision.ImageAnnotatorClient()
        
        with open(file_path, "rb") as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Use document text detection for better structure
        response = client.document_text_detection(image=image)
        
        if response.error.message:
            raise RuntimeError(f"Vision API error: {response.error.message}")
        
        raw_text = ""
        forms = {}
        tables = []
        
        if response.full_text_annotation:
            raw_text = response.full_text_annotation.text
            
            # Extract structured content from pages/blocks/paragraphs
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    block_text = ""
                    for paragraph in block.paragraphs:
                        para_text = ""
                        for word in paragraph.words:
                            word_text = "".join([symbol.text for symbol in word.symbols])
                            para_text += word_text + " "
                        block_text += para_text.strip() + "\n"
                    
                    # Simple heuristic: detect key-value pairs
                    lines = block_text.strip().split('\n')
                    for line in lines:
                        if ':' in line and len(line.split(':', 1)) == 2:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            if key and value:
                                forms[key] = value
        
        return {"raw_text": raw_text, "forms": forms, "tables": tables}

    def save_results(self, results_dict, output_file_path):
        """Save extraction results to a text file with structured formatting.
        
        Args:
            results_dict: Dictionary with page numbers as keys and extraction results as values
            output_file_path: Path to the output text file
        """
        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("GEMINI EXTRACTOR RESULTS\n")
                f.write("=" * 80 + "\n\n")
                
                for page_num in sorted(results_dict.keys()):
                    result = results_dict[page_num]
                    
                    f.write(f"{'-' * 35} Page {page_num} {'-' * 35}\n\n")
                    
                    # Raw text
                    raw_text = result.get("raw_text", "")
                    f.write("RAW TEXT:\n")
                    f.write("-" * 20 + "\n")
                    f.write(raw_text.strip() + "\n\n" if raw_text else "(No text found)\n\n")
                    
                    # Forms/Key-value pairs
                    if(self.is_enable_extract_forms):
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
                    if(self.is_enable_extract_tables):
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
                    
                    f.write("\n")
        except Exception as e:
            print(f"Error saving Gemini results: {e}")
