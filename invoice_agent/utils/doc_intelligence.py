"""
Azure Document Intelligence Utility
Handles OCR and extraction from scanned PDFs and images.
"""
import os
from typing import Optional
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

class DocumentIntelligenceHandler:
    """
    Handles connection to Azure Document Intelligence.
    """

    def __init__(self, logger):
        self.logger = logger
        self.endpoint = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.key = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        self.client = None

        if self.endpoint and self.key:
            try:
                self.client = DocumentAnalysisClient(
                    endpoint=self.endpoint, 
                    credential=AzureKeyCredential(self.key)
                )
                self.logger.log_info("[DOC-INTEL] Azure Document Intelligence initialized.")
            except Exception as e:
                self.logger.log_error(f"[DOC-INTEL] Failed to initialize: {e}")

    def extract_text(self, file_path: str) -> Optional[str]:
        """
        Extract raw text from a PDF or image using Azure Document Intelligence OCR.
        """
        if not self.client:
            self.logger.log_error("[DOC-INTEL] Client not initialized. Check credentials.")
            return None

        try:
            self.logger.log_info(f"[DOC-INTEL] Analyzing document: {os.path.basename(file_path)}")
            
            with open(file_path, "rb") as f:
                poller = self.client.begin_analyze_document(
                    "prebuilt-read", document=f
                )
                result = poller.result()

            # Concatenate all lines found in the document
            full_text = ""
            for page in result.pages:
                for line in page.lines:
                    full_text += line.content + "\n"

            self.logger.log_info(f"[DOC-INTEL] Successfully extracted {len(full_text)} characters.")
            return full_text

        except Exception as e:
            self.logger.log_error(f"[DOC-INTEL] Extraction failed: {e}")
            return None
