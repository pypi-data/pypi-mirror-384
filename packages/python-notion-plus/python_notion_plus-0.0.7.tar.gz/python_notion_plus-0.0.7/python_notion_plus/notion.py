import os
import re

from custom_python_logger import get_logger
from notion_client import Client


def remove_emojis(text: str) -> str:
    return re.sub(r"[\U00010000-\U0010ffff]", "", text).strip()


class NotionClient:
    def __init__(self, database_id: str, token: str = None) -> None:
        self.logger = get_logger(self.__class__.__name__)

        self.token = token or os.getenv("NOTION_TOKEN")
        self.database_id = database_id

        self.client = Client(auth=self.token)

    def get_metadata(self) -> dict:
        """Get metadata of the database."""
        self.logger.info("Fetching database metadata")
        try:
            return self.client.databases.retrieve(database_id=self.database_id)
        except Exception as e:
            self.logger.error(f"Failed to fetch metadata: {e}")
            raise

    def get_database_title(self) -> str | None:
        metadata = self.get_metadata()
        if title := metadata.get("title", []):
            return title[0].get("plain_text", "")
        return None

    def get_database_properties(self) -> dict:
        metadata = self.get_metadata()
        return metadata.get("properties", {})

    def get_database_content(self, page_size: int = 100) -> list:
        try:
            return self.client.databases.query(database_id=self.database_id, page_size=page_size).get("results", [])
        except Exception as e:
            self.logger.error(f"Failed to fetch content: {e}")
            raise

    def get_total_results(self) -> int:
        """Get the total number of results in the database."""
        try:
            response = self.client.databases.query(database_id=self.database_id)
            return len(response.get("results", []))
        except Exception as e:
            self.logger.error(f"Failed to fetch total results: {e}")
            raise

    def get_page_properties(self, page_id: str) -> dict:
        """Get properties of a specific page."""
        try:
            return self.client.pages.retrieve(page_id=page_id).get("properties", {})
        except Exception as e:
            self.logger.error(f"Failed to fetch page properties: {e}")
            raise

    @staticmethod
    def format_notion_page(raw: dict) -> dict:  # pylint: disable=R1260
        props = raw.get("properties", {})
        simplified_props = {}

        for name, prop in props.items():
            prop_type = prop.get("type")
            value = prop.get(prop_type)

            if prop_type == "title":
                simplified_props[name] = " ".join([remove_emojis(t.get("plain_text", "")) for t in value])
            elif prop_type == "rich_text":
                simplified_props[name] = " ".join([remove_emojis(t.get("plain_text", "")) for t in value])
            elif prop_type == "select":
                simplified_props[name] = remove_emojis(value.get("name")) if value else None
            elif prop_type == "multi_select":
                simplified_props[name] = [remove_emojis(v.get("name")) for v in value] if value else []
            elif prop_type == "date":
                simplified_props[name] = remove_emojis(value.get("start")) if value else None
            elif prop_type == "checkbox":
                simplified_props[name] = remove_emojis(value)
            elif prop_type == "number":
                simplified_props[name] = remove_emojis(value)
            elif prop_type == "people":
                simplified_props[name] = [remove_emojis(p.get("name")) for p in value]
            elif prop_type == "status":
                simplified_props[name] = remove_emojis(value.get("name")) if value else None
            else:
                simplified_props[name] = remove_emojis(value)  # fallback

        return {
            "id": raw.get("id"),
            "created_time": raw.get("created_time"),
            "last_edited_time": raw.get("last_edited_time"),
            "url": raw.get("url"),
            "archived": raw.get("archived"),
            "parent": raw.get("parent"),
            "properties": simplified_props,
        }

    def write_to_page(self, message_text: str, notion_page_id: str) -> None:
        self.client.blocks.children.append(
            block_id=notion_page_id,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": message_text}}]},
                }
            ],
        )

    def add_row_to_db(self, notion_database_id: str, properties: dict) -> None:
        self.client.pages.create(parent={"database_id": notion_database_id}, properties=properties)
