"""
This module will generate embeddings using the default document chunking.

Methods:
---------
- **GET /podcasts**: Retrieves a list of all podcasts available on the server.

Returns:
--------
A JSON response containing details of each podcast, including title, host, and 
release date.
"""

import json
import logging
import sys
import time
from enum import Enum
from io import StringIO

import psycopg2
import requests
import swagger_client
import tiktoken
from azure.cognitiveservices.speech import AudioConfig, SpeechConfig, SpeechRecognizer
from flask import Flask, Response, jsonify, render_template, request
from openai import AzureOpenAI
from psycopg2 import sql


class EpisodeAttributes(Enum):
    ID = 0
    PODCASTID = 1
    EPISODEID = 2
    TITLE = 3
    SUMMARY = 4
    URL = 5
    AUTHORS = 6
    PUBLISHED = 7
    DURATION = 8
    QUESTIONS = 9
    TRANSCRIBED = 10
    TRANSCRIPT = 11
    TRANSCRIPTTEXT = 12


logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p %Z",
)

# Read configuration from JSON file
with open("config.json") as config_file:
    config = json.load(config_file)


def select_from_episodes_with_episodeid(episodeid):

    connection_string = f"dbname='{config["DBNAME"]}' user='{config["USER"]}' password='{config["PASS"]}' host='{config["HOST"]}' port='{config["PORT"]}'"

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()

    # Prepare and execute an SQL SELECT statement
    select_query = sql.SQL("SELECT * FROM episodes WHERE episodeid = %s;").format(
        sql.Identifier("episodes")
    )

    cursor.execute(select_query, (episodeid,))

    # Fetch and print the result of the SELECT statement
    result = cursor.fetchall()

    # Close the cursor and the connection
    cursor.close()
    conn.close()

    return result[0]


def insert_embedding(podcastid, episodeid, timecode, chunk, embedding):

    connection_string = f"dbname='{config["DBNAME"]}' user='{config["USER"]}' password='{config["PASS"]}' host='{config["HOST"]}' port='{config["PORT"]}'"

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()

    # Prepare and execute an SQL SELECT statement
    insert_query = sql.SQL(
        """
        INSERT INTO simple_embeddings(podcastid, episodeid, timecode, chunk, embedding)
        VALUES (%s, %s, %s, %s, %s);
        """
    ).format(sql.Identifier("simple_embeddings"))

    cursor.execute(
        insert_query,
        (
            podcastid,
            episodeid,
            timecode,
            chunk,
            embedding,
        ),
    )
    conn.commit()

    # Close the cursor and the connection
    cursor.close()
    conn.close()


client = AzureOpenAI(
    api_key=config["LLM_API_KEY"],
    api_version=config["LLM_API_VERSION"],
    azure_endpoint=config["LLM_TARGET_URI"],
)

TIKTOKEN_MODEL_NAME = "cl100k_base"
TIKTOKEN_MAX_TOKENS = 8192
# Characters that are considered sentence terminators
TERMINATING_CHARS = [".", "?"]

tokenizer = tiktoken.get_encoding(TIKTOKEN_MODEL_NAME)


# Chunk text with timestamp at a sentence boundary that is just less than max token size
def chunktext(transcript_json, max_tokens=TIKTOKEN_MAX_TOKENS / 10):

    timecodes = []
    chunks = []
    running_token_length = 0
    curr_timecode = "PT0.00S"
    sentence_boundary_index = 0
    curr_chunk = ""
    i = 0
    while i < len(transcript_json["recognizedPhrases"]):
        phrase = transcript_json["recognizedPhrases"][i]["nBest"][0]["display"]
        if running_token_length + len(tokenizer.encode(phrase)) > max_tokens:
            chunks.append(curr_chunk)
            timecodes.append(curr_timecode)
            i = sentence_boundary_index + 1  # move just past last sentence bounday
            curr_chunk = transcript_json["recognizedPhrases"][i]["nBest"][0]["display"]
            running_token_length = len(tokenizer.encode(curr_chunk))
            curr_timecode = transcript_json["recognizedPhrases"][i]["offset"]
        else:
            curr_chunk += " " + phrase
            running_token_length += len(tokenizer.encode(phrase))
            for chr in TERMINATING_CHARS:
                if phrase.endswith(chr):
                    sentence_boundary_index = i
            i += 1

    return (timecodes, chunks)


def generate_embeddings(
    chunks, model="text-embedding-ada-002"
):  # model = "deployment_name"
    return client.embeddings.create(input=chunks, model=model)


if __name__ == "__main__":

    # accept episodeid and question as input
    episodeid = sys.argv[1]

    records = select_from_episodes_with_episodeid(episodeid)

    # retrieve transcript from DB for context
    record = select_from_episodes_with_episodeid(episodeid)
    transcript = record[EpisodeAttributes.TRANSCRIPT.value]
    transcripttext = record[EpisodeAttributes.TRANSCRIPTTEXT.value]

    print(len(tokenizer.encode(transcripttext)))
    timecodes_and_chunks = chunktext(transcript)

    embeddings = generate_embeddings(timecodes_and_chunks[1])

    for i in range(0, len(embeddings.data)):
        insert_embedding(
            1,
            episodeid,
            timecodes_and_chunks[0][i],
            timecodes_and_chunks[1][i],
            embeddings.data[i].embedding,
        )
        print(
            timecodes_and_chunks[0][i],
            timecodes_and_chunks[1][i][0:20],
            embeddings.data[i].embedding[0:3],
        )

    # print(embeddings)
    # return client.embeddings.create(input = [text], model=model).data[0].embedding
