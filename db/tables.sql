CREATE TABLE
    IF NOT EXISTS Sentence (
        sentence_id INT NOT NULL,
        section_id INT NOT NULL,
        paragraph_id INT,
        text TEXT NOT NULL,
        PRIMARY KEY (sentence_id, section_id)
    );

CREATE TABLE
    IF NOT EXISTS Related_text (
        related_id VARCHAR PRIMARY KEY,
        details TEXT NOT NULL,
        source VARCHAR
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

CREATE TABLE
    IF NOT EXISTS Entity (
        entity_id SERIAL PRIMARY KEY,
        entity_name VARCHAR NOT NULL,
        entity_type VARCHAR NOT NULL,
        UNIQUE (entity_name, entity_type)
    );

CREATE TABLE
    IF NOT EXISTS Concept (
        concept_id SERIAL PRIMARY KEY,
        concept VARCHAR NOT NULL UNIQUE
    );

CREATE TABLE
    IF NOT EXISTS entity_related_text (
        entity_id INT NOT NULL,
        related_text_id VARCHAR NOT NULL,
        relationship_type VARCHAR,
        PRIMARY KEY (entity_id, related_text_id),
        FOREIGN KEY (entity_id) REFERENCES Entity (entity_id),
        FOREIGN KEY (related_text_id) REFERENCES Related_text (related_id)
    );

CREATE TABLE
    IF NOT EXISTS concept_related_text (
        concept_id INT NOT NULL,
        related_text_id VARCHAR NOT NULL,
        relationship_type VARCHAR,
        PRIMARY KEY (concept_id, related_text_id),
        FOREIGN KEY (concept_id) REFERENCES Concept (concept_id),
        FOREIGN KEY (related_text_id) REFERENCES Related_text (related_id)
    );