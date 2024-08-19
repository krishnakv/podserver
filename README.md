# podserver
This project was created for an Azure AI hackathon. The aims of the hackathon are to create an application that is able to transcribe podcasts and answer questions based on the content of the cast.

The types of Q&A supported by the application are with (1) no context, (2) full text of the episode sent as context with the question, (3) RAG.

Azure Open AI model GPT-4o, Embedding model and text transcription services are used.

## Overall architecture

The architecture is a flask server backed by a Postgresql database. Flask is used to render the UI and communicate with the OpenAI API. PGVector is used to store embeddings for the RAG flow. psycopg is used by the Flask application to communicate with Postgresql.

## The scripts to run one-time for setup of the application and podcast are:
1. `create_tables.sql` is the script that creates all tables in Postgressl.
2. `rssconvert.py` takes the initial downloaded rss feed to populate all episode data in the DB. This has to be done once using the full RSS feed.
3. `transcripe_ep.py` accepts an episode ID and populates the DB with transcript and sample questions.
4. `gen-embeddings-simple.py` accepts and episode ID and populated the DB wtih embeddings for that episode.

## Running the Flask server

The flask server can be run wtih the following command:
```sh
python ./server.py
```

The recommendation is to run the server in a virtual env with all the packages referenced in `requiremnets.txt` installed.
