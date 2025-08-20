import os
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import torch
from dataclasses import dataclass, field


load_dotenv()
model = os.environ.get("EMBEDDING_MODEL")
device = "cuda" if torch.cuda.is_available() else "cpu"
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


def embed(text: str) -> list[float]:
    return transformer.encode(text, normalize_embeddings=True).tolist()


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

    def retrieve_by_threshold(
        self, user_query: str, threshold: float = 0.6, sql_query: str = None
    ) -> list[Sentence]:
        embedding = embed(user_query)
        if sql_query is None:
            sql_query = """
            SELECT sentence_id, section_id, text, embedding <=> %s as distance FROM sentence
            WHERE distance < %s
            ORDER BY distance
            """
        self.cursor.execute(sql_query, (embedding, embedding, 1 - threshold, embedding))
        rows = self.cursor.fetchall()
        return [Sentence(*row) for row in rows]

    def retrieve_by_count(
        self, user_query: str, count: int, sql_query: str = None
    ) -> list[Sentence]:
        embedding = embed(user_query)
        if sql_query is None:
            sql_query = """
            SELECT 
                sentence_id, section_id, text,
                embedding <=> %s as distance
            FROM sentence
            ORDER BY distance
            LIMIT %s
            """
        self.cursor.execute(sql_query, (embedding, embedding, count))
        rows = self.cursor.fetchall()
        return [Sentence(*row) for row in rows]

    def close(self):
        self.cursor.close()
        self.conn.close()


class RelatedTextRetriever:
    def __init__(self, conn: psycopg2.extensions.connection = connect()):
        self.conn = conn
        self.cursor = conn.cursor()

    def retrieve_by_threshold(
        self, user_query: str, threshold: float = 0.6, sql_query: str = None
    ) -> list[RelatedText]:
        embedding = embed(user_query)

        if sql_query is None:
            sql_query = """
            SELECT
                rt.related_id, rt.details,
                src.source_id, src.source_type, src.author, src.date_info, src.concept, src.title,
                (rt.embedding <=> %s) AS rt_distance,
                s.sentence_id, s.section_id, s.text
            FROM related_text AS rt
            LEFT JOIN related_text_source AS src
                ON src.source_id = rt.source_id
            LEFT JOIN relationship AS rel
                ON rel.related_id = rt.related_id
            LEFT JOIN sentence AS s
                ON s.sentence_id = rel.sentence_id
            AND s.section_id  = rel.section_id
            WHERE rt_distance < %s
            ORDER BY rt_distance NULLS LAST
            """

        self.cursor.execute(sql_query, (embedding, embedding, embedding, 1 - threshold))
        return self.process_rows(self.cursor.fetchall())

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
            FROM related_text AS rt
            LEFT JOIN related_text_source AS src
                ON src.source_id = rt.source_id
            LEFT JOIN relationship AS rel
                ON rel.related_id = rt.related_id
            LEFT JOIN sentence AS s
                ON s.sentence_id = rel.sentence_id
            AND s.section_id  = rel.section_id
            ORDER BY rt_distance NULLS LAST
            LIMIT %s
            """

        self.cursor.execute(sql_query, (embedding, embedding, count))
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
                    similarity=rt_distance,
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
            prefix = rt.related_text_id[:idx]
            prefix_query = f"""
            SELECT related_id, details FROM related_text
            WHERE related_id LIKE '{prefix}%'
            """
            self.cursor.execute(prefix_query)
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
        self.base = kwargs.get("base", 0.5)

    def get_source_ids(self) -> list[str]:
        sql_query = """
        SELECT source_id, source_type, author, date_info, concept, title FROM related_text_source
        """
        self.cursor.execute(sql_query)
        self.source_ids = [row[0] for row in self.cursor.fetchall()]
        self.sources = [Source(*row).to_dict() for row in self.cursor.fetchall()]
        return self.source_ids

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
            ON rel.related_id = rt.related_id
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
        self.merge_sentences(results)
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
                        SentenceRelatedTexts(sentence=sentence, related_texts=[rt])
                    )
                    sentence_related_texts[-1].score = [rt.similarity]
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
            prefix = related_text.related_id.rsplit("_", 1)[0]
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
