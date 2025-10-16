"""OpenAI extractor module.

Uses OpenAI's vision capabilities to extract text from images.
"""
from typing import Any
import os
import base64

try:
    import openai
except Exception:
    openai = None


class OpenAIExtractor:
    """Extractor that uses OpenAI's vision API to extract text from images."""
    
    def __init__(self, api_key: str | None = None, **kwargs: Any):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = "gpt-5-mini"
        if openai is not None and self.api_key:
            if hasattr(openai, 'OpenAI'):
                # New OpenAI SDK
                self.client = openai.OpenAI(api_key=self.api_key)
            else:
                # Old OpenAI SDK
                openai.api_key = self.api_key

    def extract(self, file_path: str):

        if not self.api_key:
            raise RuntimeError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")

        try:
            with open(file_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Use new OpenAI SDK if available
            print("[openAI] using new sdk api")

            if hasattr(openai, 'OpenAI') and hasattr(self, 'client'):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Extract all content from this image in Markdown format.
                                        Instructions:
                                        - Output all visible text as it appears, using Markdown formatting for headings, lists, tables, etc.
                                        - If there are forms (key-value pairs), present them as a Markdown list or table.
                                        - If there are tables, present them as Markdown tables.
                                        - Return only valid Markdown, no additional commentary or explanation."""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    # max_tokens=4000
                )
                result_text = response.choices[0].message.content.strip()
            else:
                # Old SDK fallback
                print("[openAI] using old sdk api")
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Extract all content from this image in Markdown format.
                                        Instructions:
                                        - Output all visible text as it appears, using Markdown formatting for headings, lists, tables, etc.
                                        - If there are forms (key-value pairs), present them as a Markdown list or table.
                                        - If there are tables, present them as Markdown tables.
                                        - Return only valid Markdown, no additional commentary or explanation."""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    # max_tokens=4000
                )
                result_text = response['choices'][0]['message']['content'].strip()

            # Try to parse JSON response
            try:
                import json
                # result = json.loads(result_text)
                # return {
                #     "raw_text": result.get("raw_text", ""),
                #     "forms": result.get("forms", {}),
                #     "tables": result.get("tables", [])
                # }
                return result_text
            except json.JSONDecodeError:
                # Fallback: treat as raw text
                return {"raw_text": result_text, "forms": {}, "tables": []}

            return {"raw_text": text, "forms": {}, "tables": []}

        except Exception as e:
            # Fallback to tesseract on any error
            print(f"OpenAI extraction failed ({e}), falling back to tesseract...")
            from tesseract_extractor import TesseractExtractor
            return TesseractExtractor().extract(file_path)

    def save_results(self, results_dict, output_file_path):
        """Save extraction results to a text file with structured formatting.
        
        Args:
            results_dict: Dictionary with page numbers as keys and extraction results as values
            output_file_path: Path to the output text file
        """
        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("OPENAI EXTRACTOR RESULTS\n")
                f.write("=" * 80 + "\n\n")
                
                for page_num in sorted(results_dict.keys()):
                    result = results_dict[page_num]
                    
                    f.write(f"{'-' * 35} Page {page_num} {'-' * 35}\n\n")

                    raw_text = result
                    f.write("RAW TEXT:\n")
                    f.write("-" * 20 + "\n")
                    f.write(raw_text.strip() + "\n\n" if raw_text else "(No text found)\n\n")

                    continue

                    
                    # Raw text
                    raw_text = result.get("raw_text", "")
                    f.write("RAW TEXT:\n")
                    f.write("-" * 20 + "\n")
                    f.write(raw_text.strip() + "\n\n" if raw_text else "(No text found)\n\n")
                    
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
                    
                    f.write("\n")
        except Exception as e:
            print(f"Error saving OpenAI results: {e}")
