from typing import Any


def get_extractor(name: str, **kwargs: Any):
    """Return an extractor instance by name.

    Supported names: 'aws'|'textract', 'tesseract', 'openai', 'gemini'
    Additional kwargs are forwarded to the extractor constructor.
    """
    n = (name or "").strip().lower()
    if n in ("aws", "textract"):
        try:
            from .extractor_textract import AWSTextractExtractor
        except Exception as e:
            raise RuntimeError("textract_extractor not available: " + str(e))
        return AWSTextractExtractor(**kwargs)
    if n == "openai":
        from .extractor_openai import OpenAIExtractor
        return OpenAIExtractor(**kwargs)
    if n == "gemini":
        from .extractor_gemini import GeminiExtractor
        return GeminiExtractor(**kwargs)
    if n == "mathpix":
        from .extractor_mathpix import MathpixExtractor
        return MathpixExtractor(**kwargs)
    raise ValueError(f"Unknown extractor: {name}")


def list_extractors():
    """Return list of available extractors."""
    return ["aws", "textract", "openai", "gemini", "mathpix"]
