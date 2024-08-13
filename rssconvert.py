import json
import sys

import feedparser
import psycopg2
from psycopg2 import sql


def write_to_postgresql(pid, items):
    # Read configuration from JSON file
    with open("config.json") as config_file:
        config = json.load(config_file)

    connection_string = f"dbname='{config["DBNAME"]}' user='{config["USER"]}' host='{config["HOST"]}' password='{config["PASS"]}' port='{config["PORT"]}'"

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()

    # Prepare and execute an SQL INSERT statement
    insert_query = sql.SQL(
        "INSERT INTO episodes (podcastid, episodeid, title, summary, url, authors, published, duration, questions, transcribed, transcript) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, FALSE, NULL);"
    ).format(
        sql.Identifier("episodes")  # Replace with the actual table name
    )

    running_eid = len(items)
    authors = "Bill Caskey and Bryan Neale"  # A good default from "Advanced Selling Podcast" :-)

    if len(items) > 0 and "author" in items[0].keys():
        authors = items[0]["author"]

    for item in items:
        entry = {
            "podcastid": pid,
            "episodeid": running_eid,
            "title": item["title"],
            "summary": item["summary"],
            "url": item["links"][1]["href"] if len(item["links"]) > 1 else "",
            "authors": authors,
            "published": item["published"],
            "duration": (
                item["itunes_duration"]
                if "itunes_duration" in item.keys()
                else "0 seconds"
            ),
        }
        cursor.execute(insert_query, tuple(entry.values()))

        running_eid -= 1

    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()


def parse_write_rss_feed(podcastid, file_path):
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
        # for item in rss_feed["items"]:
        #     print(item)  # Print out each item
        write_to_postgresql(podcastid, rss_feed["items"])
    else:
        print("The feed does not contain any items.")


# Example usage of the function with a sample RSS file path
if __name__ == "__main__":
    # Specify the path to your XML file here
    podcastid = sys.argv[1]
    xml_file_path = sys.argv[2]

    # Call the function to parse and print the feed items
    parse_write_rss_feed(podcastid, xml_file_path)
