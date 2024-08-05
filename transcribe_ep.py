#!/usr/bin/env python3
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.
import psycopg2
from psycopg2 import sql
import sys
import json
from azure.cognitiveservices.speech import SpeechConfig, AudioConfig, SpeechRecognizer
from enum import Enum
import logging
import sys
import requests
import time
import swagger_client

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

    return result[0][EpisodeAttributes.URL.value]

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
        format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p %Z")

def transcribe_from_single_file(uri, properties):
    """
    Transcribe a single audio file located at `uri` using the settings specified in `properties`
    using the base model for the specified locale.
    """
    transcription_definition = swagger_client.Transcription(
        display_name=NAME,
        description=DESCRIPTION,
        locale=LOCALE,
        content_urls=[uri],
        properties=properties
    )

    return transcription_definition

NAME = "POdcast transcription"
DESCRIPTION = "Moltocasto podcast app transcription"

LOCALE = "en-US"
RECORDINGS_BLOB_URI = "<Your SAS Uri to the recording>"

# Provide the uri of a container with audio files for transcribing all of them
# with a single request. At least 'read' and 'list' (rl) permissions are required.
RECORDINGS_CONTAINER_URI = "<Your SAS Uri to a container of audio files>"

# Set model information when doing transcription with custom models
MODEL_REFERENCE = None  # guid of a custom model

def transcribe(audio_url):
    logging.info("Starting transcription client...")

    # Read configuration from JSON file
    with open("config.json") as config_file:
        config = json.load(config_file)

    # Set up the Azure Speech configuration
    SUBSCRIPTION_KEY = config["SPEECH_KEY"]
    SERVICE_REGION = config["SERVICE_REGION"]

    # configure API key authorization: subscription_key
    configuration = swagger_client.Configuration()
    configuration.api_key["Ocp-Apim-Subscription-Key"] = SUBSCRIPTION_KEY
    configuration.host = f"https://{SERVICE_REGION}.api.cognitive.microsoft.com/speechtotext/v3.2"

    # create the client object and authenticate
    client = swagger_client.ApiClient(configuration)

    # create an instance of the transcription api class
    api = swagger_client.CustomSpeechTranscriptionsApi(api_client=client)

    # Specify transcription properties by passing a dict to the properties parameter. See
    # https://learn.microsoft.com/azure/cognitive-services/speech-service/batch-transcription-create?pivots=rest-api#request-configuration-options
    # for supported parameters.
    properties = swagger_client.TranscriptionProperties()
    # properties.word_level_timestamps_enabled = True
    # properties.display_form_word_level_timestamps_enabled = True
    # properties.punctuation_mode = "DictatedAndAutomatic"
    # properties.profanity_filter_mode = "Masked"
    # properties.destination_container_url = "<SAS Uri with at least write (w) permissions for an Azure Storage blob container that results should be written to>"
    # properties.time_to_live = "PT1H"

    # uncomment the following block to enable and configure speaker separation
    # properties.diarization_enabled = True
    # properties.diarization = swagger_client.DiarizationProperties(
    #     swagger_client.DiarizationSpeakersProperties(min_count=1, max_count=5))

    # uncomment the following block to enable and configure language identification prior to transcription. Available modes are "single" and "continuous".
    # properties.language_identification = swagger_client.LanguageIdentificationProperties(mode="single", candidate_locales=["en-US", "ja-JP"])

    # Use base models for transcription. Comment this block if you are using a custom model.
    transcription_definition = transcribe_from_single_file(audio_url, properties)

    # Uncomment this block to use custom models for transcription.
    # transcription_definition = transcribe_with_custom_model(client, RECORDINGS_BLOB_URI, properties)

    # uncomment the following block to enable and configure language identification prior to transcription
    # Uncomment this block to transcribe all files from a container.
    # transcription_definition = transcribe_from_container(RECORDINGS_CONTAINER_URI, properties)

    created_transcription, status, headers = api.transcriptions_create_with_http_info(transcription=transcription_definition)

    # get the transcription Id from the location URI
    transcription_id = headers["location"].split("/")[-1]

    # Log information about the created transcription. If you should ask for support, please
    # include this information.
    logging.info(f"Created new transcription with id '{transcription_id}' in region {SERVICE_REGION}")

    logging.info("Checking status.")

    completed = False

    while not completed:
        # wait for 5 seconds before refreshing the transcription status
        time.sleep(5)

        transcription = api.transcriptions_get(transcription_id)
        logging.info(f"Transcriptions status: {transcription.status}")

        if transcription.status in ("Failed", "Succeeded"):
            completed = True

        if transcription.status == "Succeeded":
            if properties.destination_container_url is not None:
                logging.info("Transcription succeeded. Results are located in your Azure Blob Storage.")
                break

            pag_files = api.transcriptions_list_files(transcription_id)
            for file_data in _paginate(api, pag_files):
                if file_data.kind != "Transcription":
                    continue

                audiofilename = file_data.name
                results_url = file_data.links.content_url
                results = requests.get(results_url)
                logging.info(f"Results for {audiofilename}:\n{results.content.decode('utf-8')}")
        elif transcription.status == "Failed":
            logging.info(f"Transcription failed: {transcription.properties.error.message}")


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
    # transcribe_episode_from_audio_url(audio_url)

    transcribe(audio_url)


