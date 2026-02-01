# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from itemadapter import ItemAdapter


class ScraperPipeline:
    def process_item(self, item, spider):
        return item


class RagPipeline:
    """
    Pipeline for RAG spider that saves each page as a separate JSON file
    organized in folders matching the website structure.

    Output structure:
    output/
      domain.com/
        page1_hash.json
        subfolder/
          page2_hash.json
    """

    def __init__(self):
        # Output folder in project (ignored by git)
        # __file__ is in scraper/pipelines.py
        # parent = scraper/, parent.parent = scrapy_splash_project/
        project_root = Path(__file__).parent.parent
        self.output_dir = project_root / "output"
        self.files_created = 0

    def open_spider(self, spider):
        """Create base output directory"""
        self.output_dir.mkdir(exist_ok=True)
        spider.logger.info(
            f"RAG Pipeline initialized. Output dir: {self.output_dir.absolute()}"
        )

    def close_spider(self, spider):
        """Log summary"""
        spider.logger.info(f"RAG Pipeline: Created {self.files_created} JSON files")

    def process_item(self, item, spider):
        """Save item as JSON file in appropriate folder"""

        # Create domain folder (handle subdomains properly)
        domain = item.get("domain", "unknown")

        # Parse domain to handle subdomains
        # e.g., "example.integreat.app" -> folder: integreat_app/example
        # e.g., "integreat.app" -> folder: integreat_app
        domain_parts = domain.split(".")

        if len(domain_parts) > 2:
            # Has subdomain: example.integreat.app
            base_domain = "_".join(domain_parts[-2:])  # integreat_app
            subdomain = "_".join(domain_parts[:-2])  # example
            domain_folder = self.output_dir / base_domain / subdomain
        else:
            # No subdomain: integreat.app
            base_domain = "_".join(domain_parts)  # integreat_app
            domain_folder = self.output_dir / base_domain

        domain_folder.mkdir(parents=True, exist_ok=True)

        # Create subfolder structure based on URL path
        path_parts = item.get("path_parts", [])
        current_folder = domain_folder

        # Create subfolders for all but the last part (which is the page)
        if len(path_parts) > 1:
            for part in path_parts[:-1]:
                current_folder = current_folder / self.sanitize_filename(part)
                current_folder.mkdir(exist_ok=True)

        # Generate filename from URL hash or last path part
        url_hash = item.get("url_hash", hashlib.md5(item["url"].encode()).hexdigest())

        # Use last path part + hash for better readability
        if path_parts:
            last_part = self.sanitize_filename(path_parts[-1])
            filename = f"{last_part}_{url_hash[:8]}.json"
        else:
            filename = f"index_{url_hash[:8]}.json"

        filepath = current_folder / filename

        # Save JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(dict(item), f, ensure_ascii=False, indent=2)

        self.files_created += 1
        spider.logger.info(f"Saved: {filepath}")

        return item

    def sanitize_filename(self, name):
        """Remove invalid characters from filename/folder name"""
        # Replace invalid characters with underscore
        name = name.replace("/", "_").replace("\\", "_")
        name = name.replace(":", "_").replace("*", "_")
        name = name.replace("?", "_").replace('"', "_")
        name = name.replace("<", "_").replace(">", "_")
        name = name.replace("|", "_")

        # Remove leading/trailing dots and spaces
        name = name.strip(". ")

        # If empty after sanitization, use default
        if not name:
            name = "page"

        return name
