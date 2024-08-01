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

from flask import Flask, jsonify

app = Flask(__name__)

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


@app.route("/podcasts/<int:pid>", methods=["GET"])
def get_podcast(pid):
    # TODO: retrieve the podcast details with the ID from the DB
    podcasts = [{"id": f"{pid}", "name": "Hanselminutes"}]
    return jsonify({"podcasts": podcasts})


@app.route("/podcasts", methods=["GET"])
def get_all_podcasts():
    # TODO: retrieve all podcast details from the DB
    podcasts = [{"id": "1", "name": "Hanselminutes"}]
    return jsonify({"podcasts": podcasts})


@app.route("/episodes/<int:pid>/<int:eid>", methods=["GET"])
def get_episode(pid, eid):
    # TODO: retrieve the episode details with the ID from the DB
    episodes = [
        {
            "id": f"{pid}-{eid}",
            "episode-name": "Name of the pod episode",
            "summary": "The summary of the episode",
            "transcript": "Long detailed transcript here",
            "sample-questions": "A list of sample questions to ask",
        }
    ]
    return jsonify({"episodes": episodes})


@app.route("/episodes/<int:pid>", methods=["GET"])
def get_all_episodes():
    # TODO: retrieve all episode details from the DB
    episodes = [
        {
            "id": "1",
            "episode-name": "Name of the pod episode",
            "summary": "The summary of the episode",
            "transcript": "Long, detailed transcript here",
            "sample-questions": "A list of sample questions to ask",
        }
    ]
    return jsonify({"episodes": episodes})


if __name__ == "__main__":
    app.run(debug=True)
