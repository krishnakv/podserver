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

app = Flask(__name__)
app.config.from_file("config.json", load=json.load)
client = AzureOpenAI(
    api_key = app.config["LLM_API_KEY"],
    api_version = app.config["LLM_API_VERSION"],
    azure_endpoint = app.config["LLM_TARGET_URI"]
)

# HACK: this should come from the db repository layer
episodes = [
    {
        "id": 955,
        "title": "Creating Tools for Thought with Andy Matuschak",
        "summary": "Andy Matuschak is an independent researcher who explores user interfaces that expand what people can think and do. He sits down with Scott to talk about how we learn, why we learn, and what learning means in a world of AI and AGI.",
        "transcript": "",
        "sample-questions": [""],
    },
    {
        "id": 954,
        "title": "Defining Developer Relations with Angie Jones",
        "summary": "Scott's in Berlin this week and talks to Angie Jones, Global Vice President of Developer Relations, TBD @ Block, about the job of Developer Relations. What does a DevRel person even do? Are they just hanging out in the Delta Lounge or are the Developers? What does it mean to Advocate versus Evangelize?",
        "transcript": "",
        "sample-questions": [""],
    },
    {
        "id": 953,
        "title": "Computer Science Visualizations with Sam Rose",
        "summary": "Sam Rose creates visual introductions to computer science topics. Each post takes about a month to make, and he tries to cover foundational topics in a way that's accessible to beginners. Scott chats with Sam about the how and why of making such bespoke and sophisticated blog posts.",
        "transcript": "",
        "sample-questions": [""],
    },
    {
        "id": 952,
        "title": "Introducing .NET Aspire with Damian Edwards",
        "summary": ".NET Aspire has folks talking - but why? What is .NET Aspire and what does it me for the average ASP.NET developer like me? Is it a thing for Kubernetes? Is it just for .NET Devs? Scott sits down with Damian Edwards to get a sense of what .NET Aspire ahem aspires to do, and where it's heading.",
        "transcript": "",
        "sample-questions": [""],
    }
]

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
    # TODO: retrieve all episode details from the DB
    return jsonify(episodes)

@app.route("/podcasts/<pid>/episodes/<int:eid>", methods=["GET"])
def get_episode(pid, eid):
    # TODO: retrieve the episode details with the ID from the DB
    episode = next(e for e in episodes if e['id'] == eid)
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

