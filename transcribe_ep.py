import psycopg2
from psycopg2 import sql
import sys
import json
from azure.cognitiveservices.speech import SpeechConfig, AudioConfig, SpeechRecognizer
from enum import Enum

class EpisodeAttributes(Enum):
    EPISODEID = 0
    TITLE = 1
    SUMMARY = 2
    URL = 3
    AUTHORS = 4
    PUBLISHED = 5
    DURATION = 6

def select_from_episodes_with_episodeid(episodeid):
    # Read configuration from JSON file
    with open("config.json") as config_file:
        config = json.load(config_file)

    connection_string = f"dbname='{config["DBNAME"]}' user='{config["USER"]}' host='{config["HOST"]}' port='{config["PORT"]}'"

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()

    # Prepare and execute an SQL SELECT statement
    select_query = sql.SQL(
        "SELECT * FROM episodes WHERE episodeid = %s;"
    ).format(
        sql.Identifier("episodes")  # Replace with the actual table name
    )

    cursor.execute(select_query, (episodeid,))

    # Fetch and print the result of the SELECT statement
    result = cursor.fetchall()
    print(result)

    # Close the cursor and the connection
    cursor.close()
    conn.close()

    return result[EpisodeAttributes.URL.value]

# create and print the transcription of the episode audio using Azure speech services
# the function takes as input the URL where audio is stores and prints the transcription
def transcribe_episode_from_audio_url(audio_url):
    # Read configuration from JSON file
    with open("config.json") as config_file:
        config = json.load(config_file)

    # Set up the Azure Speech configuration
    speech_key = config["SPEECH_KEY"]
    service_region = config["SERVICE_REGION"]
    speech_config = SpeechConfig(subscription=speech_key, region=service_region)
    audio_config = AudioConfig(url=audio_url)

    # Create a SpeechRecognizer object and use it to transcribe the audio
    speech_recognizer = SpeechRecognizer(speech_config, audio_config)
    result = speech_recognizer.recognize_once()

    # Print the transcribed text
    print(result.text)

def write_to_postgresql(items):
    # Read configuration from JSON file
    with open("config.json") as config_file:
        config = json.load(config_file)

    connection_string = f"dbname='{config["DBNAME"]}' user='{config["USER"]}' host='{config["HOST"]}' port='{config["PORT"]}'"

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()

    # Prepare and execute an SQL INSERT statement
    insert_query = sql.SQL(
        "INSERT INTO episodes (podcastid, episodeid, title, summary, url, authors, published, duration, questions, transcribed, transcript) VALUES (1, %s, %s, %s, %s, %s, %s, %s, NULL, FALSE, NULL);"
    ).format(
        sql.Identifier("episodes")  # Replace with the actual table name
    )

    for item in items:
        entry = {
            "episodeid": item["itunes_episode"],
            "title": item["itunes_title"],
            "summary": item["summary"],
            "url": item["links"][1]["href"],
            "authors": item["author"],
            "published": item["published"],
            "duration": item["itunes_duration"]
        }
        cursor.execute(insert_query, tuple(entry.values()))

    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

def parse_write_rss_feed(file_path):
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
        write_to_postgresql(rss_feed["items"])
    else:
        print("The feed does not contain any items.")


# Example usage of the function with a sample RSS file path
if __name__ == "__main__":

    # accept from command line as input, the episodeid to transcribe
    episodeid = sys.argv[1]

    # Call the function to select the episode from the database
    audio_url = select_from_episodes_with_episodeid(episodeid)
    transcribe_episode_from_audio_url(audio_url)


