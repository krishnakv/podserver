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
from enum import Enum
from string import Template

import psycopg2
from flask import Flask, Response, jsonify, render_template, request
from flask_cors import CORS
from openai import AzureOpenAI
from psycopg2 import sql

from data_repository import DataRepository

app = Flask(__name__)
CORS(app, origins=["http://localhost:5000"])
app.config.from_file("config.json", load=json.load)
client = AzureOpenAI(
    api_key=app.config["LLM_API_KEY"],
    api_version=app.config["LLM_API_VERSION"],
    azure_endpoint=app.config["LLM_TARGET_URI"],
)
db_repo_config = {
    "DB_NAME": app.config["DBNAME"],
    "DB_HOST": app.config["HOST"],
    "DB_USER": app.config["USER"],
    "DB_PASSWORD": app.config["PASS"],
    "DB_PORT": app.config["PORT"],
}


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


@app.route("/")
def index() -> str:
    """Render the main game page."""
    return render_template("index.html")


@app.route("/about", methods=["GET"])
async def about():
    return {"app_version": "0.2.1"}, 200


"""
The `get_podcasts` function, handles GET requests at the `/podcasts` endpoint.
It retrieves and returns a list of podcasts available on the server.

Methods:
---------
- **GET /podcasts**: Retrieves a list of all podcasts available on the server.

Returns:
--------
A JSON response containing details of each podcast, including title, host, and release date.
"""


@app.route("/podcasts/<pid>/episodes", methods=["GET"])
def get_all_episodes(pid):
    # retrieve all episode details from the DB
    episodes = DataRepository(db_repo_config).get_episodes(pid)
    return jsonify(episodes)


@app.route("/podcasts/<pid>/episodes/<int:eid>", methods=["GET"])
def get_episode(pid, eid):
    # retrieve the episode details with the ID from the DB
    episode = DataRepository(db_repo_config).get_episode(pid, eid)
    return jsonify(episode)


def select_from_episodes_with_episodeid(episodeid):
    # Read configuration from JSON file
    connection_string = f"dbname='{app.config["DBNAME"]}' user='{app.config["USER"]}' password='{app.config["PASS"]}' host='{app.config["HOST"]}' port='{app.config["PORT"]}'"
    print(connection_string)

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
    connection_string = f"dbname='{app.config["DBNAME"]}' user='{app.config["USER"]}' password='{app.config["PASS"]}' host='{app.config["HOST"]}' port='{app.config["PORT"]}'"

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


@app.route("/ask", methods=["GET"])
def ask():
    question = request.args.get("q")
    # podcast_id = request.args.get("pid") # at this stage, its Hanselminutes
    episode_id = request.args.get("eid")
    request_type = request.args.get("type")  # expected: "norag", "fulltext" or "rag"

    system_prompt = """
    You are a helpful assistant that answers user questions. You will use any context
    provided, if available, and answer the questions as truthfully as possible. You 
    will provide your response in 200 words or less.
    """
    user_prompt = ""

    if request_type == "norag":
        user_prompt = question
    elif request_type == "fulltext":
        # retrieve transcript from DB for context
        record = select_from_episodes_with_episodeid(episode_id)
        title = record[EpisodeAttributes.TITLE.value]
        transcripttext = record[EpisodeAttributes.TRANSCRIPTTEXT.value]

        user_prompt = """
        The input enclosed in backticks is the transcript of a podcast with the title "%s". 
        Based on this transcript and in keeping with your role as a helpful assistant,
        please answer the question "%s" from a user. You will ignore any parts of the 
        transcript that are not relevant to the core topic such as ad reads.
        `%s`
        """ % (
            title,
            question,
            transcripttext,
        )

    else:  # default request type is "rag"
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

        user_prompt = """
        Based on the context enclosed in backticks below and in keeping with your role as 
        a helpful assistant, please answer the question "%s" from a user. Along with the 
        response, you will also return the episodes and timecodes from where you got context
        inputs. You will ignore any parts of the context that are not relevant to the question 
        such as ad reads.
        `%s`
        """ % (
            question,
            context,
        )

    def generate_answer(sprompt, uprompt):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": sprompt,
                },
                {"role": "user", "content": uprompt},
            ],
            stream=True,
        )
        for chunk in response:
            yield f'data: {chunk.choices[0].delta.content or ""}\n\n'

    return Response(
        generate_answer(system_prompt, user_prompt), mimetype="text/event-stream"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
