#!/usr/bin/env python3
from .extractor_factory import get_extractor, list_extractors
import argparse
import tempfile
import os
import sys
import json
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv

load_dotenv()

# Try to import PyMuPDF (fitz) for PDF -> image conversion. If missing, show instruction.
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None


class ExtractorClient:
    """
    A client for extracting text from PDF files using various extraction backends.
    Can be used as a library or as a CLI tool.
    """
    
    def __init__(self, extractor_type: str = "aws", region: str = "us-east-1", **kwargs):
        """
        Initialize the ExtractorClient.
        
        Args:
            extractor_type: Type of extractor to use (aws, openai, gemini, mathpix)
            region: AWS region for AWS Textract
            **kwargs: Additional parameters for the extractor (api keys, etc.)
        """
        self.extractor_type = extractor_type
        self.region = region
        self.extractor_kwargs = kwargs
        self.extractor = None
        self.dpi = 150
        self._initialize_extractor()
    
    def _initialize_extractor(self):
        """Initialize the extractor with current settings."""
        try:
            extractor_kwargs = {"region": self.region, **self.extractor_kwargs}
            self.extractor = get_extractor(self.extractor_type, **extractor_kwargs)
        except Exception as e:
            raise RuntimeError(f"Error initializing {self.extractor_type} extractor: {e}")
    
    def change_extractor(self, extractor_type: str, **kwargs):
        """
        Change the extractor at runtime.
        
        Args:
            extractor_type: New extractor type
            **kwargs: Additional parameters for the new extractor
        """
        self.extractor_type = extractor_type
        self.extractor_kwargs.update(kwargs)
        self._initialize_extractor()
    
    def set_dpi(self, dpi: int):
        """Set the DPI for PDF rendering."""
        self.dpi = dpi
    
    @staticmethod
    def parse_pages(pages_str: str, max_pages: int) -> List[int]:
        """Parse a pages string like '1,3-5,7' into a sorted list of 1-based page numbers within range."""
        pages = set()
        for part in pages_str.split(','):
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                try:
                    a, b = part.split('-', 1)
                    a = int(a)
                    b = int(b)
                except ValueError:
                    raise argparse.ArgumentTypeError(f"Invalid page range: '{part}'")
                if a > b:
                    raise argparse.ArgumentTypeError(f"Invalid page range: '{part}' (start > end)")
                pages.update(range(a, b + 1))
            else:
                try:
                    pages.add(int(part))
                except ValueError:
                    raise argparse.ArgumentTypeError(f"Invalid page number: '{part}'")

        # Validate and clamp to available pages
        valid = sorted(p for p in pages if 1 <= p <= max_pages)
        if not valid:
            raise ValueError(f"No valid pages to process. Valid page numbers are 1..{max_pages}")
        return valid

    @staticmethod
    def render_pdf_page_to_png(doc, page_number: int, dpi: int = 150) -> str:
        """Render a 1-based page_number from PyMuPDF doc to a temporary PNG file and return its path."""
        page = doc.load_page(page_number - 1)  # 0-based internal
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        tmp = tempfile.NamedTemporaryFile(prefix=f"page_{page_number}_", suffix=".png", delete=False)
        tmp.close()
        pix.save(tmp.name)
        # pix.save(f"output/image_{page_number}.png")
        return tmp.name
    
    def process_pdf(self, pdf_path: str, page_numbers: Optional[List[int]] = None) -> Dict[int, str]:
        """
        Extract text from specified pages of a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            page_numbers: List of page numbers to process (1-based). If None, process all pages.
            
        Returns:
            Dict with page numbers as keys and extracted raw text as values
        """
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if fitz is None:
            raise RuntimeError("PyMuPDF is required to render PDF pages. Install it with: pip install PyMuPDF")
        
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise RuntimeError(f"Error opening PDF: {e}")
        
        # If no page numbers specified, process all pages
        if page_numbers is None:
            page_numbers = list(range(1, doc.page_count + 1))
        else:
            # Validate page numbers
            valid_pages = [p for p in page_numbers if 1 <= p <= doc.page_count]
            if not valid_pages:
                raise ValueError(f"No valid pages to process. Valid page numbers are 1..{doc.page_count}")
            page_numbers = valid_pages
        
        results = {}
        temp_files = []
        
        try:
            for page_num in page_numbers:
                try:
                    img_path = self.render_pdf_page_to_png(doc, page_num, dpi=self.dpi)
                    temp_files.append(img_path)
                    
                    extraction_result = self.extractor.extract(img_path)
                    # Extract just the raw text for the return value
                    raw_text = extraction_result.get("raw_text", "") if isinstance(extraction_result, dict) else str(extraction_result)
                    results[page_num] = raw_text
                    
                except Exception as e:
                    print(f"Error processing page {page_num}: {e}")
                    results[page_num] = f"Error: {str(e)}"
        
        finally:
            # Cleanup temporary images
            for fpath in temp_files:
                try:
                    os.remove(fpath)
                except Exception:
                    pass
            doc.close()
        
        return results
    
    def dump_results(self, results: Dict[int, Union[str, Dict]], output_path: str, format: str = "txt"):
        """
        Save extracted results to a file.
        
        Args:
            results: Dictionary with page numbers as keys and results as values
            output_path: Path to save the results
            format: Output format ("txt" or "json")
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        if format.lower() == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        else:  # Default to txt format
            with open(output_path, 'w', encoding='utf-8') as f:
                for page_num in sorted(results.keys()):
                    result = results[page_num]
                    f.write(f"{'=' * 40}\n")
                    f.write(f"Page {page_num} Results:\n")
                    f.write(f"{'=' * 40}\n")
                    
                    if isinstance(result, dict):
                        f.write(f"Raw Text:\n{result.get('raw_text', '(none)')}\n\n")
                        f.write(f"Forms:\n{result.get('forms', '(none)')}\n\n")
                        f.write(f"Tables:\n{result.get('tables', '(none)')}\n\n")
                    else:
                        f.write(f"{result}\n\n")


def parse_pages(pages_str, max_pages):
    """Legacy function for backward compatibility."""
    return ExtractorClient.parse_pages(pages_str, max_pages)


def render_pdf_page_to_png(doc, page_number, dpi=150):
    """Legacy function for backward compatibility."""
    return ExtractorClient.render_pdf_page_to_png(doc, page_number, dpi)


def main():
    """CLI interface for the ExtractorClient - preserved for backward compatibility."""
    parser = argparse.ArgumentParser(description="Extract text/forms/tables from selected pages of a PDF using various extractors")
    parser.add_argument("pdf", help="Path to the PDF file to process")
    parser.add_argument("--pages", required=True, help="Comma-separated list of pages or ranges to process, e.g. '1,3-5,7'")
    parser.add_argument("--extractor", default="aws", help=f"Extractor to use: {', '.join(list_extractors())} (default: aws)")
    parser.add_argument("--region", default="us-east-1", help="AWS region to use for AWS Textract (default: us-east-1)")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for rendering PDF pages to images (default: 150)")
    parser.add_argument("--output", "-o", help="Path to output text file (default: <pdf_basename>_extracted.txt in current directory)")
    parser.add_argument("--format", choices=["txt", "json"], default="txt", help="Output format (default: txt)")
    parser.add_argument("--openai-api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--gemini-api-key", help="Gemini/Google AI API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--mathpix-app-id", help="Mathpix App ID (or set MATHPIX_APP_ID env var)")
    parser.add_argument("--mathpix-app-key", help="Mathpix App Key (or set MATHPIX_APP_KEY env var)")
    args = parser.parse_args()

    if not os.path.isfile(args.pdf):
        print(f"Error: PDF file not found: {args.pdf}")
        sys.exit(2)

    if fitz is None:
        print("Error: PyMuPDF is required to render PDF pages. Install it with: pip install PyMuPDF")
        sys.exit(2)

    try:
        # Parse pages using the static method
        doc = fitz.open(args.pdf)
        page_list = ExtractorClient.parse_pages(args.pages, doc.page_count)
        doc.close()
    except Exception as e:
        print(f"Error parsing pages or opening PDF: {e}")
        sys.exit(2)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        base = os.path.splitext(os.path.basename(args.pdf))[0]
        output_path = os.path.join(os.getcwd(), f"output/{base}_extracted.{args.format}")

    # Create extractor kwargs
    extractor_kwargs = {}
    if args.openai_api_key:
        extractor_kwargs["api_key"] = args.openai_api_key
    if args.gemini_api_key:
        extractor_kwargs["api_key"] = args.gemini_api_key
    if args.mathpix_app_id:
        extractor_kwargs["app_id"] = args.mathpix_app_id
    if args.mathpix_app_key:
        extractor_kwargs["app_key"] = args.mathpix_app_key
    
    try:
        # Create ExtractorClient instance
        client = ExtractorClient(
            extractor_type=args.extractor,
            region=args.region,
            **extractor_kwargs
        )
        client.set_dpi(args.dpi)
        print(f"Using {args.extractor} extractor")
        
        # Process the PDF
        print(f"Processing pages: {page_list}")
        results = client.process_pdf(args.pdf, page_list)
        
        # Print summary to console
        for page_num in sorted(results.keys()):
            result = results[page_num]
            print("\n" + "=" * 40)
            print(f"Page {page_num} Results:")
            print("=" * 40)
            if len(result) > 200:
                print(result[:200] + "...")
            else:
                print(result)
        
        # Save results
        client.dump_results(results, output_path, args.format)
        print(f"\nSaved extracted results to: {output_path}")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
