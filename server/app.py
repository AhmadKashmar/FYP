import flask
from playground.test import RetrieverBySource, SentenceRelatedTexts
import json

app = flask.Flask(__name__)

retriever = RetrieverBySource()


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
                   "similarity": float # can be ignored
               },
               "related_texts": [
                   {
                       "source_id": [ # for this source, we have the following related texts
                           {
                               "related_text_id": "string",
                               "details": "string",
                               "similarity": float # can be ignored
                           },
                           ...
                       ]
                   },
                   ...
               ]
            },
            ...
        ]
    }
    """
    data = flask.request.get_json()
    query = data.get("query", "")
    sources = data.get("sources", retriever.source_ids)
    sentences_related_texts = retriever.retrieve(query, sources)
    sentences = [st.to_dict() for st in sentences_related_texts]
    response = {"sentences": sentences}
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
    sentences_related_texts: list[SentenceRelatedTexts] = retriever.retrieve(
        query, sources
    )
    sentences = [st.to_dict() for st in sentences_related_texts]
    # currently a placeholder till we set up LLM
    dump = json.dumps({"response": sentences}, ensure_ascii=False, indent=4)
    return dump, 200


if __name__ == "__main__":
    app.run()
