"""File handler utility for Invoice Portal Automation Agent"""
import os
import json
import shutil
from pathlib import Path
from datetime import datetime


class FileHandler:
    """Utility for handling files - screenshots, downloads, etc."""

    def __init__(self, run_dir: str, vendor_name: str, run_id: str = None):
        """
        Initialize file handler

        Args:
            run_dir (str): Base run directory
            vendor_name (str): Vendor name for organizing files
            run_id (str):  Unique run identifier (UUID hex). If provided,
                           artifacts are stored under run/artifacts/{run_id}/
        """
        self.run_dir = run_dir
        self.vendor_name = vendor_name
        self.run_id = run_id

        # Structured artifact folder (Day 9)
        if run_id:
            artifact_base = os.path.join(run_dir, "artifacts", run_id)
        else:
            artifact_base = os.path.join(run_dir, "artifacts", "default")

        self.artifact_dir = artifact_base
        self.screenshots_dir = os.path.join(artifact_base, "screenshots")
        self.downloads_dir   = os.path.join(artifact_base, "downloads")
        self.logs_dir        = os.path.join(artifact_base, "logs")

        # Create artifact subdirectories
        for d in [self.screenshots_dir, self.downloads_dir, self.logs_dir]:
            os.makedirs(d, exist_ok=True)

        # Only create results/ at the run root (shared across all runs)
        os.makedirs(os.path.join(run_dir, "results"), exist_ok=True)

        self.vendor_screenshots = self.screenshots_dir
        self.vendor_downloads   = self.downloads_dir

        # Ordered screenshot index: [{step, path, timestamp}, ...]
        self._screenshot_index: list = []


    
    def save_screenshot(self, image_data: bytes, step_name: str) -> str:
        """
        Save screenshot
        
        Args:
            image_data (bytes): Image data
            step_name (str): Name of the step (for filename)
            
        Returns:
            str: Path to saved screenshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{step_name}_{timestamp}.png"
        filepath = os.path.join(self.vendor_screenshots, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return filepath
    
    def save_downloaded_file(self, source_path: str, invoice_number: str = None) -> str:
        """
        Save downloaded invoice file
        
        Args:
            source_path (str): Path to source file
            invoice_number (str): Invoice number (for filename)
            
        Returns:
            str: Path to saved file
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Get file extension
        _, ext = os.path.splitext(source_path)
        
        # Create filename
        if invoice_number:
            filename = f"invoice_{invoice_number}{ext}"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"invoice_{timestamp}{ext}"
        
        destination = os.path.join(self.vendor_downloads, filename)
        
        # Copy file
        shutil.copy2(source_path, destination)
        
        return destination
    
    def get_screenshot_dir(self) -> str:
        """Get vendor-specific screenshots directory"""
        return self.vendor_screenshots
    
    def get_downloads_dir(self) -> str:
        """Get vendor-specific downloads directory"""
        return self.vendor_downloads

    def get_download_dir(self) -> str:
        """Alias for get_downloads_dir() — consistent naming across steps."""
        return self.vendor_downloads

    def get_artifact_dir(self) -> str:
        """Return the run_id-scoped artifact root directory."""
        return self.artifact_dir

    def record_screenshot(self, step_name: str, path: str):
        """
        Record a screenshot in the ordered index.

        Args:
            step_name: Human label (e.g. '01_login_page')
            path:      Absolute or relative path to the PNG file.
        """
        self._screenshot_index.append({
            "step": step_name,
            "path": path,
            "timestamp": datetime.now().isoformat(),
        })

    def get_screenshot_index(self) -> list:
        """Return the full ordered screenshot list."""
        return list(self._screenshot_index)

    def list_screenshots(self) -> list:
        """List all screenshots for this vendor"""
        if not os.path.exists(self.vendor_screenshots):
            return []
        return [os.path.join(self.vendor_screenshots, f) 
                for f in os.listdir(self.vendor_screenshots) 
                if f.endswith('.png')]
    
    def list_downloads(self) -> list:
        """List all downloads for this vendor"""
        if not os.path.exists(self.vendor_downloads):
            return []
        return [os.path.join(self.vendor_downloads, f)
                for f in os.listdir(self.vendor_downloads)]

    def save_metadata(self, metadata: dict, invoice_number: str) -> str:
        """
        Persist extracted invoice metadata as a JSON file.

        Args:
            metadata:       Dictionary of extracted fields.
            invoice_number: Used to name the file.

        Returns:
            str: Path to the saved JSON file.
        """
        import json
        filename = f"metadata_{invoice_number}.json"
        filepath = os.path.join(self.vendor_downloads, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        return filepath
    
    def cleanup_old_files(self, days_to_keep: int = 7):
        """
        Clean up old files (older than specified days)
        
        Args:
            days_to_keep (int): Number of days of files to keep
        """
        import time
        current_time = time.time()
        cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
        
        for directory in [self.vendor_screenshots, self.vendor_downloads]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    filepath = os.path.join(directory, filename)
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
