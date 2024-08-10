"""
This module contains Flask route definitions for a podcast server.

The main entry point is the `get_podcasts` function, which handles GET 
requests at the `/podcasts` endpoint. It retrieves and returns a list of 
podcasts available on the server.

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
from string import Template

import psycopg2
import requests
import swagger_client
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


with open("config.json") as config_file:
    config = json.load(config_file)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p %Z",
)

client = AzureOpenAI(
    api_key=config["LLM_API_KEY"],
    api_version=config["LLM_API_VERSION"],
    azure_endpoint=config["LLM_TARGET_URI"],
)


def select_from_episodes_with_episodeid(episodeid):
    # Read configuration from JSON file
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


def select_embeddings(text):

    # Generate embedding from the input text
    embedding = (
        client.embeddings.create(input=[text], model="text-embedding-ada-002")
        .data[0]
        .embedding
    )

    # Read configuration from JSON file
    connection_string = f"dbname='{config["DBNAME"]}' user='{config["USER"]}' password='{config["PASS"]}' host='{config["HOST"]}' port='{config["PORT"]}'"

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()

    # Construct the SQL query with a join
    select_query = """
                   SELECT episodes.episodeid, episodes.title, simple_embeddings.timecode, simple_embeddings.chunk
                   FROM simple_embeddings
                   JOIN episodes
                   ON simple_embeddings.episodeid = episodes.episodeid
                   ORDER BY embedding <-> %s
                   LIMIT %s
                   """

    cursor.execute(
        select_query,
        (
            str(embedding),
            5,
        ),
    )

    # Fetch and print the result of the SELECT statement
    results = cursor.fetchall()

    # Close the cursor and the connection
    cursor.close()
    conn.close()

    return results


def askfulltext(q, pid, eid):
    question = q  # request.args.get("q")
    podcast_id = pid  # request.args.get("pid")
    episode_id = eid  # request.args.get("eid")

    # retrieve transcript from DB for context
    record = select_from_episodes_with_episodeid(episode_id)
    title = record[EpisodeAttributes.TITLE.value]
    transcripttext = record[EpisodeAttributes.TRANSCRIPTTEXT.value]

    system_prompt = """
    You are a helpful assistant that answers user questions. You will use any context
    provided and answer the questions as truthfully as possible. You will provide your
    response in 100 words or less.
    """

    user_prompt = """
    The input enclosed in backticks is the transcript of a podcast with the title "%s". 
    Based on this transcript and in keeping with your role as a helpful assistant,
    please answer the question "%s" from a user. You will ignore any parts of the 
    transcript that are not relevant to the core topic such as ad reads.
    `%s`
    """

    def generate_answer(question):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt % (title, question, transcripttext),
                },
            ],
            stream=True,
        )
        for chunk in response:
            yield f'{chunk.choices[0].delta.content or ""}'

    response = generate_answer(question)
    answer = StringIO()
    for data in response:
        answer.write(" " + data)

    print(answer.getvalue())
    # return Response(generate_answer(question), mimetype="text/event-stream")


def askrag(q, pid, eid):
    question = q  # request.args.get("q")
    podcast_id = pid  # request.args.get("pid")
    episode_id = eid  # request.args.get("eid")

    # retrieve transcript from DB for context
    embeddings = select_embeddings(question)

    context_tmpl = Template(
        "Episode ID ${eid} with the title ${title} at the timecode ${timecode} provides the context #${context}#\n"
    )
    context = ""

    for val in embeddings:
        context += context_tmpl.substitute(
            eid=val[0], title=val[1], timecode=str(val[2]), context=val[3]
        )

    print(context)

    SYSTEM_PROMPT = """
    You are a helpful assistant that answers user questions. You will use any context
    provided and answer the questions as truthfully as possible. You will provide your
    response in 100 words or less.
    """

    USER_PROMPT = """
    Based on the context enclosed in backticks below and in keeping with your role as 
    a helpful assistant, please answer the question "%s" from a user. Along with the 
    response, you will also return the episodes and timecodes from where you got context
    inputs. You will ignore any parts of the context that are not relevant to the question 
    such as ad reads.
    `%s`
    """

    def generate_answer(question):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": USER_PROMPT % (question, context),
                },
            ],
            stream=True,
        )
        for chunk in response:
            yield f'{chunk.choices[0].delta.content or ""}'
            # yield f'data: {chunk.choices[0].delta.content or ""}\n\n'

    response = generate_answer(question)
    answer = StringIO()
    for data in response:
        answer.write(" " + data)

    print(answer.getvalue())
    # return Response(generate_answer(question), mimetype="text/event-stream")
    # return Response(generate_answer(question), mimetype="text/event-stream")


# accept the episode ID, transcribe, create question list and update in DB
if __name__ == "__main__":

    # accept episodeid and question as input
    episodeid = sys.argv[1]
    question = sys.argv[2]

    # Send the question to openai with selected RAG context lines
    askrag(question, 1, episodeid)

    # Send the question to openai with full text
    # askfulltext(question, 1, episodeid)
