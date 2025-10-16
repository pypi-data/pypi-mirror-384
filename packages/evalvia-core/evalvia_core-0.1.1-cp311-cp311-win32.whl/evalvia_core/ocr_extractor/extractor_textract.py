import boto3
import json
import os


class AWSTextractExtractor:
    def __init__(self, region=""):
        self.client = boto3.client("textract")
        self.is_enable_extract_tables = False
        self.is_enable_extract_forms = False

    def extract(self, file_path: str):
        with open(file_path, "rb") as f:
            if self.is_enable_extract_forms or self.is_enable_extract_tables:
                response = self.client.analyze_document(
                    Document={"Bytes": f.read()},
                    FeatureTypes=["FORMS", "TABLES"]
                )
            else:
                response = self.client.detect_document_text(
                    Document={'Bytes': f.read()})

        os.makedirs("output", exist_ok=True)
        with open("output/aws_block.txt", "w") as f:
            for idx, block in enumerate(response["Blocks"]):
                f.write(f"{'=*'*8} Block {idx} {'='*8}\n")
                f.write(json.dumps(block, indent=2))
                f.write("\n\n")
        
        return {
            "raw_text": self._extract_text(response),
            "forms": self._extract_forms(response),
            "tables": self._extract_tables(response)
        }

    def _extract_text(self, response):
        """Get raw text lines"""
        lines = []
        for block in response["Blocks"]:
            if block["BlockType"] == "LINE":
                lines.append(block["Text"])
        return "\n".join(lines)

    def _extract_forms(self, response):
        """Extract key-value pairs"""
        kvs = {}

        if not self.is_enable_extract_forms:
            return kvs

        for block in response["Blocks"]:
            if block["BlockType"] == "KEY_VALUE_SET" and "EntityTypes" in block and "KEY" in block["EntityTypes"]:
                key = block["Text"] if "Text" in block else None
                if key:
                    kvs[key] = block
        return kvs

    def _extract_tables(self, response):
        """Extract tables as list of rows"""
        tables = []
        if not self.is_enable_extract_tables:
            return tables
        
        for block in response["Blocks"]:
            if block["BlockType"] == "TABLE":
                rows = []
                for relationship in block.get("Relationships", []):
                    if relationship["Type"] == "CHILD":
                        row = []
                        for cid in relationship["Ids"]:
                            cell = next((b for b in response["Blocks"] if b["Id"] == cid), None)
                            if cell and cell["BlockType"] == "CELL":
                                row.append(" ".join([t["Text"] for t in response["Blocks"] if t["BlockType"]=="WORD" and "Relationships" in cell and t["Id"] in [rid for r in cell["Relationships"] for rid in r["Ids"]]]))
                        if row:
                            rows.append(row)
                tables.append(rows)
                # tables.append(block) // when want to dump the entre table block (for debugging)
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
                f.write("AWS TEXTRACT EXTRACTOR RESULTS\n")
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

                            # dumping json directly
                            # f.write(f"Table {i}:\n")
                            # f.write(json.dumps(table, indent=2))
                    else:
                        f.write("(No tables detected)\n\n")
                    
                    f.write("\n")
        except Exception as e:
            print(f"Error saving AWS Textract results: {e}")
