import flask
from flask_cors import CORS
from playground.test import RetrieverBySource, SentenceRelatedTexts
import json

app = flask.Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": ["http://localhost:3000"]}},
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"],
)
retriever = RetrieverBySource()
DEFAULT_COUNT = 50

@app.route("/query-without-inference", methods=["POST"])
def query():
    """
    This endpoint expects the following from the user
    1. The list of source_ids to check (if not specified, checks all)
    2. The user query
    The endpoint returns a dictionary as follows:
    {
        "sentences": [
            {
               "sentence": {
                   "sentence_id": integer,
                   "section_id": integer,
                   "text": "string",
                   "similarity": float, # can be ignored
                   "related_text_ids": ["string", ...]
               },
            },
            ...
        ],
        "related_texts": [
            {
                {
                    "related_text_id": "string",
                    "details": "string",
                    "similarity": float, # can be ignored
                    "source_id": "string"
                },
                ...
            },
            ...
        ]
    }
    """
    data = flask.request.get_json()
    query = data.get("query", None)
    if not query:
        return {"error": "Query is required"}, 400
    sources = data.get("sources")
    if not sources:
        sources = retriever.source_ids
    try:
        results = retriever.retrieve(query, sources, DEFAULT_COUNT)
    except Exception as e:
        # rollback on error
        try:
            retriever.conn.rollback()
        except Exception:
            pass
        raise e
    response = results.to_dict()
    return response, 200


@app.route("/query-with-inference", methods=["POST"])
def query_with_inference():
    """
    This endpoint expects the following from the user
    1. The list of source_ids to check (if not specified, checks all)
    2. The user query

    This endpoint returns a string
    """
    data = flask.request.get_json()
    query: str = data.get("query", "")
    sources: list[str] = data.get("sources", retriever.source_ids)
    try:
        results = retriever.retrieve(query, sources, DEFAULT_COUNT)
    except Exception as e:
        # rollback on error
        try:
            retriever.conn.rollback()
        except Exception:
            pass
        raise e
    response = results.to_dict()
    # currently a placeholder till we set up LLM
    dump = json.dumps({"response": str(response)}, ensure_ascii=False, indent=4)
    return dump, 200


@app.route("/sources", methods=["GET"])
def get_sources():
    """
    This endpoint returns the list of available source IDs.
    """
    return {"sources": retriever.sources}, 200


if __name__ == "__main__":
    app.run()
