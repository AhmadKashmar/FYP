import os
import psycopg2
from pgvector.psycopg2 import register_vector
from pgvector.vector import Vector
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import torch
from dataclasses import dataclass, field
import numpy as np
from psycopg2.extensions import register_adapter, AsIs
import logging

register_adapter(np.int64, lambda v: AsIs(int(v)))
register_adapter(np.int32, lambda v: AsIs(int(v)))
register_adapter(np.float64, lambda v: AsIs(float(v)))
register_adapter(np.bool_, lambda v: AsIs(bool(v)))


load_dotenv()
def setup_logger(app_name="logs"):
    log_dir = "logs"
    log_file_name = f"{app_name}.log"
    log_file_path = os.path.join(log_dir, log_file_name)
    warn_error_log_file_name = f"{app_name}_warn_error.log"
    warn_error_log_file_path = os.path.join(log_dir, warn_error_log_file_name)

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file_path, mode="a")
    file_handler.setLevel(logging.DEBUG)

    warn_error_file_handler = logging.FileHandler(warn_error_log_file_path, mode="a")
    warn_error_file_handler.setLevel(logging.WARNING)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    warn_error_file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(warn_error_file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
model = os.environ.get("EMBEDDING_MODEL")
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Loading model")
transformer = SentenceTransformer(model, device=device)


def connect():
    conn = psycopg2.connect(
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
    )
    register_vector(conn)
    return conn


def execute_query(
    cursor: psycopg2.extensions.cursor,
    conn: psycopg2.extensions.connection,
    sql: str,
    params=None,
):
    logger.info(f"SQL EXECUTE:\n{sql}")
    try:
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)
        logger.info("SQL OK")
    except Exception as e:
        logger.exception("SQL ERROR: %s", e)
        try:
            conn.rollback()
            logger.warning("Transaction rolled back")
        except Exception as re:
            logger.error("Rollback failed: %s", re)
        raise


def embed(text: str) -> list[float]:
    logger.info("Embedding text")
    vec = transformer.encode(text, normalize_embeddings=True).tolist()
    return Vector(vec)


@dataclass(eq=True)
class Sentence:
    sentence_id: int
    section_id: int
    text: str
    similarity: float = field(compare=False, default=-1)

    def to_dict(self) -> dict[str, str | int]:
        return {
            "sentence_id": self.sentence_id,
            "section_id": self.section_id,
            "text": self.text,
            "similarity": self.similarity,
        }


@dataclass
class Source:
    source_id: str
    source_type: str
    author: str
    date_info: str
    concept: str
    title: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "author": self.author,
            "date_info": self.date_info,
            "concept": self.concept,
            "title": self.title,
        }


@dataclass(eq=True)
class RelatedText:
    related_text_id: str
    related_sentences: list[Sentence]
    source: Source
    details: str
    similarity: float = field(compare=False)

    def to_dict(self) -> dict[str, str | list[dict[str, str | int]]]:
        return {
            "related_text_id": self.related_text_id,
            # "source": self.source.to_dict(), # omit source for now
            "details": self.details,
            "similarity": self.similarity,
        }


@dataclass(eq=True)
class SentenceRelatedTexts:
    sentence: Sentence = field(compare=False)
    related_texts: list[RelatedText]
    score: list[float]
    final_score: float = field(compare=False, default=0)

    def to_dict(self) -> dict[str, str | list[dict[str, str | int]]]:
        # group related_texts by source
        source_ids_rel_texts: dict[str, list[RelatedText]] = {}
        source_list: list[dict[str, dict[str, Source | list[RelatedText]]]] = []
        for rt in self.related_texts:
            if rt.source.source_id not in source_ids_rel_texts:
                source_ids_rel_texts[rt.source.source_id] = [rt]
            else:
                source_ids_rel_texts[rt.source.source_id].append(rt)
        for source_id, related_texts in source_ids_rel_texts.items():
            source_list.append(
                {
                    source_id: [rt.to_dict() for rt in related_texts],
                }
            )

        return {"sentence": self.sentence.to_dict(), "related_texts": source_list}


class SentenceRetriever:
    """Directly queries on the sentence table"""

    def __init__(self, conn: psycopg2.extensions.connection = connect()):
        self.conn = conn
        self.cursor = conn.cursor()

    def retrieve_by_count(
        self, user_query: str, count: int, sql_query: str = None
    ) -> list[Sentence]:
        embedding = embed(user_query)
        if sql_query is None:
            sql_query = """
                SELECT sentence_id, section_id, text, (embedding <=> %s) AS distance
                FROM sentence
                ORDER BY distance
                LIMIT %s
            """
        execute_query(self.cursor, self.conn, sql_query, (embedding, count))
        rows = self.cursor.fetchall()
        return [Sentence(*row) for row in rows]

    def close(self):
        self.cursor.close()
        self.conn.close()


class RelatedTextRetriever:
    def __init__(self, conn: psycopg2.extensions.connection = connect()):
        self.conn = conn
        self.cursor = conn.cursor()

    def retrieve_by_count(
        self, user_query: str, count: int, sql_query: str = None
    ) -> list[RelatedText]:
        embedding = embed(user_query)
        if sql_query is None:
            sql_query = """
                SELECT
                rt.related_id, rt.details,
                src.source_id, src.source_type, src.author, src.date_info, src.concept, src.title,
                (rt.embedding <=> %s) AS rt_distance,
                s.sentence_id, s.section_id, s.text
                FROM related_text rt
                LEFT JOIN related_text_source src ON src.source_id = rt.source_id
                LEFT JOIN relationship rel ON rel.related_text_id = rt.related_id
                LEFT JOIN sentence s ON s.sentence_id = rel.sentence_id AND s.section_id = rel.section_id
                ORDER BY rt_distance NULLS LAST
                LIMIT %s
            """

        execute_query(self.cursor, self.conn, sql_query, (embedding, count))
        return self.process_rows(self.cursor.fetchall())

    def process_rows(
        self,
        rows: list[tuple[str, str, str, str, str, str, str, str, float, int, int, str]],
    ) -> list[RelatedText]:
        related_texts_as_dict: dict[str, RelatedText] = {}
        for (
            related_id,
            details,
            source_id,
            source_type,
            author,
            date_info,
            concept,
            title,
            rt_distance,
            sentence_id,
            section_id,
            text,
        ) in rows:
            if related_id not in related_texts_as_dict:
                src = Source(
                    source_id=source_id,
                    source_type=source_type,
                    author=author,
                    date_info=date_info,
                    concept=concept,
                    title=title,
                )
                related_texts_as_dict[related_id] = RelatedText(
                    related_text_id=related_id,
                    related_sentences=[],
                    source=src,
                    details=details,
                    similarity=1 - rt_distance,
                )
            related_texts_as_dict[related_id].related_sentences.append(
                Sentence(
                    sentence_id=sentence_id,
                    section_id=section_id,
                    text=text,
                    similarity=-1,
                )
            )

        related_texts: list[RelatedText] = list(related_texts_as_dict.values())

        # for each related text, we need to fetch its siblings
        # siblings have the same prefix id
        for rt in related_texts:
            idx = rt.related_text_id.rfind("_")
            prefix = rt.related_text_id[:idx] + "_"
            prefix_query = f"""
            SELECT related_id, details FROM related_text
            WHERE related_id LIKE '{prefix}%'
            """
            execute_query(self.cursor, self.conn, prefix_query)
            siblings = self.cursor.fetchall()
            siblings = [
                (related_id.rsplit("_", 1)[-1], details)
                for related_id, details in siblings
            ]
            for i, (id, details) in enumerate(siblings):
                if id == rt.related_text_id.rsplit("_", 1)[-1]:
                    siblings[i] = (id, "$$" + details + "$$")
            siblings.sort(key=lambda x: int(x[0]))
            siblings = [details for _, details in siblings]
            rt.details = " ".join(siblings)

        return related_texts


class RetrieverBySource(RelatedTextRetriever):
    def __init__(self, conn: psycopg2.extensions.connection = connect(), **kwargs):
        self.conn = conn
        self.cursor = conn.cursor()
        self.source_ids, self.sources = self.get_source_ids()
        print("Source IDs: ", self.source_ids)
        self.base = kwargs.get("base", 0.5)

    def get_source_ids(self) -> tuple[list[str], list[dict]]:
        sql_query = """
        SELECT source_id, source_type, author, date_info, concept, title FROM related_text_source
        """
        execute_query(self.cursor, self.conn, sql_query)
        sources = [Source(*row).to_dict() for row in self.cursor.fetchall()]
        source_ids = [source.get("source_id") for source in sources]
        return source_ids, sources

    def retrieve_by_source_id(
        self,
        user_query: str,
        source_id: str,
        count: int,
    ) -> list[RelatedText]:
        sql_query = f"""
        SELECT
            rt.related_id, rt.details,
            src.source_id, src.source_type, src.author, src.date_info, src.concept, src.title,
            (rt.embedding <=> %s) AS rt_distance,
            s.sentence_id, s.section_id, s.text
        FROM related_text AS rt
        LEFT JOIN related_text_source AS src
            ON src.source_id = rt.source_id
        LEFT JOIN relationship AS rel
            ON rel.related_text_id = rt.related_id
        LEFT JOIN sentence AS s
            ON s.sentence_id = rel.sentence_id
        AND s.section_id  = rel.section_id
        WHERE rt.source_id = '{source_id}'
        ORDER BY rt_distance NULLS LAST
        LIMIT %s
        """
        return self.retrieve_by_count(user_query, count, sql_query)

    def retrieve(
        self, user_query: str, source_ids: list[str], count: int
    ) -> list[SentenceRelatedTexts]:
        """
        Does the following:
        1. For each source, retrieves the top `count` candidate related text chunks
        2. These chunks are then merged together with ther siblings to form the entire related_text paragraph, we also mark this related_text by ...$$this is the relevant part$$...
        3. After this step, the related_text : list[sentence] becomes sentence_related_texts: list[RT]
        4. A score is calculated for each sentence from its related text from this source only
        5. Finally, a final score is calculated based on the entire sources
        6. we cut-off any sentences that seem to be below a threshold
        7. for each sentence's related text, we cut-off any related text that is also below a threshold
        """
        results: list[SentenceRelatedTexts] = []
        for source_id in source_ids:
            # get the rt per source
            related_texts = self.retrieve_by_source_id(user_query, source_id, count)
            # transform data
            result = self.related_texts_to_sentences(related_texts)
            # calculate score per source
            for sentence in result:
                sentence.score = [self.score_sentence(sentence)]
            results.extend(result)
        # merge each sentence so that all its related texts are grouped
        results = self.merge_sentences(results)
        results = self.filter_results(results)
        return results

    def related_texts_to_sentences(
        self, related_texts: list[RelatedText]
    ) -> list[SentenceRelatedTexts]:
        """
        Transforms the returned values from RT: list[S] to S: list[RT]
        It also calculates the score for the sentence based on its related text
        """
        sentence_related_texts: list[SentenceRelatedTexts] = list()
        for rt in related_texts:
            for sentence in rt.related_sentences:
                if sentence in sentence_related_texts:
                    idx = sentence_related_texts.index(sentence)
                    sentence_related_texts[idx].related_texts.append(rt)
                    sentence_related_texts[idx].score.append(rt.similarity)
                else:
                    sentence_related_texts.append(
                        SentenceRelatedTexts(
                            sentence=sentence, related_texts=[rt], score=[rt.similarity]
                        )
                    )
        return sentence_related_texts

    def score_sentence(self, sentence_related_text: SentenceRelatedTexts) -> float:
        """
        this should do the following:
        1. for each related text, if it has the same prefix excluding the ending after _ (xxx_x)
        we add a significant part of its score, else we add a small asymptotic part of its score
        2. we sort the related_texts by score value and get a final score from them (currently adds them as a power series)
        """
        related_text_id_counts: dict[str, list[float]] = {}
        for related_text in sentence_related_text.related_texts:
            prefix = related_text.related_text_id.rsplit("_", 1)[0]
            if prefix not in related_text_id_counts:
                related_text_id_counts[prefix] = [related_text.similarity]
            else:
                related_text_id_counts[prefix].append(related_text.similarity)
        # now for each one, compute a similarity score using a power series
        related_text_id_scores: dict[str, float] = {}
        for prefix, similarities in related_text_id_counts.items():
            related_text_id_scores[prefix] = self.get_score(similarities)

        related_text_id_scores = dict(
            sorted(
                related_text_id_scores.items(), key=lambda item: item[1], reverse=True
            )
        )

        score = self.get_score(related_text_id_scores.values())
        return score

    def get_score(self, vals: list[float]) -> float:
        return sum(val * (self.base**i) for i, val in enumerate(vals))

    def merge_sentences(
        self, sentence_related_texts: list[SentenceRelatedTexts]
    ) -> list[SentenceRelatedTexts]:
        """
        Merges the sentences' related texts from all the different sources
        Also re-calculates the final scores for each sentence
        """
        merged: dict[str, SentenceRelatedTexts] = {}
        for sentence_related_text in sentence_related_texts:
            sentence = sentence_related_text.sentence
            key = f"{sentence.sentence_id}_{sentence.section_id}"
            if key not in merged:
                merged[key] = sentence_related_text
            else:
                merged[key].related_texts.extend(sentence_related_text.related_texts)
                merged[key].score.extend(sentence_related_text.score)
        # here, each object has the score a list of scores across different sources
        sentences = sorted(merged.values(), key=lambda x: max(x.score), reverse=True)
        for sentence in sentences:
            sentence.final_score = self.get_score(sentence.score)
        # now each sentence has its final score
        return sentences

    def filter_results(
        self,
        results: list[SentenceRelatedTexts],
        sentence_threshold=1,
        rt_threshold=0.5,
    ) -> list[SentenceRelatedTexts]:
        filtered_results: list[SentenceRelatedTexts] = []
        # we need to delete sentences that have a final score below the threshold
        for sentence in results:
            if sentence.final_score >= sentence_threshold:
                filtered_results.append(sentence)
        # now for the remaining sentences, filter the related texts with a low contribution
        for sentence in filtered_results:
            sentence.related_texts = [
                rt for rt in sentence.related_texts if rt.similarity >= rt_threshold
            ]
        return filtered_results
