-- DROP TABLE IF EXISTS relationship;
-- DROP TABLE IF EXISTS Related_text;
-- DROP TABLE IF EXISTS Related_text_source;
-- DROP TABLE IF EXISTS Sentence;
CREATE TABLE
    IF NOT EXISTS Sentence (
        sentence_id INT NOT NULL,
        section_id INT NOT NULL,
        paragraph_id INT,
        text TEXT NOT NULL,
        PRIMARY KEY (sentence_id, section_id)
    );

CREATE TABLE
    IF NOT EXISTS Related_text_source (
        source_id VARCHAR PRIMARY KEY,
        source_type VARCHAR NOT NULL,
        author VARCHAR,
        date_info VARCHAR,
        concept VARCHAR,
        title VARCHAR NOT NULL
    );

CREATE TABLE
    IF NOT EXISTS Related_text (
        related_id VARCHAR PRIMARY KEY,
        details TEXT NOT NULL,
        source_id VARCHAR,
        FOREIGN KEY (source_id) REFERENCES Related_text_source (source_id)
    );

CREATE TABLE
    IF NOT EXISTS relationship (
        sentence_id INT NOT NULL,
        section_id INT NOT NULL,
        related_text_id VARCHAR NOT NULL,
        PRIMARY KEY (sentence_id, section_id, related_text_id),
        FOREIGN KEY (sentence_id, section_id) REFERENCES Sentence (sentence_id, section_id),
        FOREIGN KEY (related_text_id) REFERENCES Related_text (related_id)
    );