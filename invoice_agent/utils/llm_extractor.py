"""LLM Extractor for Day 10 - Structured Output (Azure OpenAI version)"""
import os
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from utils.prompts import get_full_extraction_prompt_template, SYSTEM_MESSAGE_EXTRACTOR

# Load environment variables from .env file
load_dotenv()

try:
    from langchain_openai import AzureChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

class LLMExtractor:
    """
    Extracts structured data from invoice text using an LLM.
    Supports Azure OpenAI.
    """

    def __init__(self, logger):
        self.logger = logger
        
        # Azure OpenAI Settings
        self.api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")

        self.llm = None

        if LANGCHAIN_AVAILABLE and self.api_key and self.endpoint:
            try:
                self.llm = AzureChatOpenAI(
                    azure_deployment=self.deployment,
                    openai_api_version=self.api_version,
                    azure_endpoint=self.endpoint,
                    api_key=self.api_key,
                    temperature=0
                )
                self.logger.log_info(f"[LANGCHAIN] Azure OpenAI initialized (Deployment: {self.deployment})")
            except Exception as e:
                self.logger.log_error(f"[LANGCHAIN] Failed to initialize: {e}")
        else:
            if not LANGCHAIN_AVAILABLE:
                self.logger.log_warning("[LANGCHAIN] 'langchain-openai' package not found.")
            if not self.api_key or not self.endpoint:
                self.logger.log_warning("[LANGCHAIN] Azure credentials missing in environment variables.")

    def extract(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract fields from text using Azure OpenAI.
        Returns a dict with extracted fields or None if it fails.
        """
        try:
            self.logger.log_info("[LANGCHAIN] Sending extraction request...")
            
            # 1. Prepare the Prompt Template
            template = get_full_extraction_prompt_template()
            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_MESSAGE_EXTRACTOR),
                ("user", template)
            ])
            
            # 2. Build the Chain (Prompt | LLM)
            # Use JSON mode if supported
            if self.api_version >= "2023-12-01-preview":
                chain = chat_prompt | self.llm.bind(response_format={"type": "json_object"})
            else:
                chain = chat_prompt | self.llm
            
            # 3. Invoke the Chain
            response = chain.invoke({"text": text})
            
            # 4. Parse the result
            content = response.content.strip()
            data = json.loads(content)
            
            # Basic normalization/validation
            normalized = self._normalize_results(data)
            self.logger.log_info(f"[LLM] Successfully extracted metadata via Azure OpenAI.")
            return normalized

        except Exception as e:
            self.logger.log_error(f"[LLM] Azure OpenAI extraction failed: {e}")
            return None

    def _normalize_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize types and formats."""
        result = {}
        
        # Strings
        result['invoice_number'] = str(data.get('invoice_number', '')).strip()
        result['vendor_name'] = str(data.get('vendor_name', '')).strip()
        result['currency'] = str(data.get('currency', 'USD')).upper().strip()
        
        # Date (YYYY-MM-DD)
        date_str = str(data.get('invoice_date', '')).strip()
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
        result['invoice_date'] = date_match.group(1) if date_match else date_str

        # Numbers
        for key in ['total_amount', 'tax_amount']:
            val = data.get(key)
            if isinstance(val, (int, float)):
                result[key] = float(val)
            elif isinstance(val, str):
                # Handle European format: "3.900,00" -> 3900.00
                # Handle US format: "3,900.00" -> 3900.00
                
                # If there's a comma and a dot, comma is usually thousands if it comes first, or vice versa
                if ',' in val and '.' in val:
                    if val.find(',') < val.find('.'): # US: 1,000.00
                        clean_val = val.replace(',', '')
                    else: # EU: 1.000,00
                        clean_val = val.replace('.', '').replace(',', '.')
                elif ',' in val: # Only comma: could be 1000,00 or 1,000
                    # If comma is followed by exactly 2 digits, it's likely a decimal
                    if re.search(r',\d{2}$', val):
                        clean_val = val.replace(',', '.')
                    else:
                        clean_val = val.replace(',', '')
                else:
                    clean_val = val
                
                # Final cleanup: remove anything not a digit or dot
                clean_val = re.sub(r'[^\d.]', '', clean_val)
                try:
                    result[key] = float(clean_val)
                except ValueError:
                    result[key] = 0.0
            else:
                result[key] = 0.0
                
        return result
