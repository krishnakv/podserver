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

from flask import Flask, render_template, request, Response, jsonify
import json
from openai import AzureOpenAI
from data_repository import DataRepository

app = Flask(__name__)
app.config.from_file("config.json", load=json.load)
client = AzureOpenAI(
    api_key = app.config["LLM_API_KEY"],
    api_version = app.config["LLM_API_VERSION"],
    azure_endpoint = app.config["LLM_TARGET_URI"]
)
db_repo_config = {"DB_NAME": app.config["DB_NAME"],
                    "DB_HOST": app.config["DB_HOST"],
                    "DB_USER": app.config["DB_USER"],
                    "DB_PASSWORD": app.config["DB_PASSWORD"],
                    "DB_PORT": app.config["DB_PORT"]}

@app.route('/')
def index() -> str:
    """Render the main game page."""
    return render_template('index.html')

@app.route('/about', methods=['GET'])
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


# @app.route("/podcasts/<int:pid>", methods=["GET"])
# def get_podcast(pid):
#     # TODO: retrieve the podcast details with the ID from the DB
#     podcasts = [{"id": f"{pid}", "name": "Hanselminutes"}]
#     return jsonify({"podcasts": podcasts})


# @app.route("/podcasts", methods=["GET"])
# def get_all_podcasts():
#     # TODO: retrieve all podcast details from the DB
#     podcasts = [{"id": "1", "name": "Hanselminutes"}]
#     return jsonify({"podcasts": podcasts})

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

@app.route('/ask', methods=['GET'])
def ask():
  question = request.args.get('q')
  def generate_answer(question):
    response = client.chat.completions.create(
      model="gpt-4o",
      messages=[{"role": "system", "content": "Provide your response in 100 words or less."}, {"role": "user", "content": question}],
      stream=True,
    )
    for chunk in response:
      yield f'data: {chunk.choices[0].delta.content or ""}\n\n'
      
  return Response(generate_answer(question), mimetype='text/event-stream')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
