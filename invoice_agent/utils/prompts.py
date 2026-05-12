"""
Central prompt library for LLM extraction.
This file handles dynamic prompt generation based on configuration.
"""
import config

def get_extraction_fields_str() -> str:
    """
    Returns a formatted string of fields and their descriptions.
    """
    fields_desc = ""
    for field, desc in config.EXTRACTION_FIELDS.items():
        fields_desc += f"- {field}: {desc}\n"
    return fields_desc

# Day 10 - Invoice Extraction Prompt (LangChain Template)
INVOICE_EXTRACTION_PROMPT = """
Extract the following fields from the invoice text provided below. 
Normalize all values to the specified formats:
{fields_desc}

IMPORTANT INSTRUCTIONS:
1. CURRENCY: Pay extremely close attention to currency symbols ($, €, £) and explicit mentions of currency (e.g., "Importes en Euros", "USD"). Use the 3-letter ISO code.
2. NUMBERS: Handle European formats where "." is a thousands separator and "," is a decimal separator (e.g., "3.900,00" is 3900.0). Return numeric values without thousands separators.
3. LANGUAGE: The invoice might be in Spanish, French, or English. Interpret labels correctly.

Return ONLY a valid JSON object with these keys.

INVOICE TEXT:
\"\"\"
{{text}}
\"\"\"
"""

# Helper to get the full prompt with fields injected
def get_full_extraction_prompt_template() -> str:
    return INVOICE_EXTRACTION_PROMPT.format(fields_desc=get_extraction_fields_str())

# System Messages
SYSTEM_MESSAGE_EXTRACTOR = "You are a professional invoice data extractor. Return only JSON."
