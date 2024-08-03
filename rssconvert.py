import json

import feedparser
import psycopg2
from psycopg2 import sql


def write_to_postgresql(data):
    # Read configuration from JSON file
    with open("config.json") as config_file:
        config = json.load(config_file)

    # Connect to the PostgreSQL database

    conn = psycopg2.connect(**config)
    cursor = conn.cursor()

    # Prepare and execute an SQL INSERT statement
    insert_query = sql.SQL(
        "INSERT INTO your_table (column1, column2, ...) VALUES (%s, %s, ...);"
    ).format(
        sql.Identifier("your_table")  # Replace with the actual table name
    )

    for item in data:
        cursor.execute(insert_query, tuple(item.values()))

    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()


# Example usage
data = [
    {"column1": "value1", "column2": "value2"},
    {"column1": "value3", "column2": "value4"},
]
write_to_postgresql(data)


def parse_rss_feed(file_path):
    """
    Reads an RSS or Atom feed from a specified file path, parses it using feedparser,
    and prints out the items listed in the feed.

    Args:
        file_path (str): The path to the XML file containing the RSS or Atom feed.

    Returns:
        None
    """
    # Read the RSS/Atom feed from the specified file path
    rss_feed = feedparser.parse(file_path)

    # Check if the parsed content has an 'items' key, which is typical for both RSS and Atom feeds
    if "items" in rss_feed:
        # Iterate through each item in the items list
        for item in rss_feed["items"]:
            print(item)  # Print out each item
    else:
        print("The feed does not contain any items.")


# Example usage of the function with a sample RSS file path
if __name__ == "__main__":
    # Specify the path to your XML file here
    xml_file_path = "./gvtxUiIf.rss"

    # Call the function to parse and print the feed items
    parse_rss_feed(xml_file_path)
