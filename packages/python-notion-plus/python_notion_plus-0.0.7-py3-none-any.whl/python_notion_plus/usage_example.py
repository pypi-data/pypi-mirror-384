import json
import os

from python_notion_plus import NotionClient


def main() -> None:
    notion_client = NotionClient(database_id=os.getenv("NOTION_DATABASE_ID"))

    metadata = notion_client.get_metadata()
    print(f"notion_schema: {metadata}")

    notion_title = notion_client.get_database_title()
    print(f"notion_title: {notion_title}")

    notion_properties = notion_client.get_database_properties()
    print(f"notion_properties: {notion_properties}")

    total_results = notion_client.get_total_results()
    print(f"total_results: {total_results}")

    notion_content = notion_client.get_database_content()
    print(f"notion_content: {notion_content}")
    for page in notion_content:
        properties = notion_client.format_notion_page(page)
        formatted_data = json.dumps(properties, indent=4)

        print(f"notion_page_properties: {formatted_data}\n")


if __name__ == "__main__":
    main()
