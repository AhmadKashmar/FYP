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
        related_id CHAR PRIMARY KEY,
        details TEXT NOT NULL,
        source VARCHAR
    );

CREATE TABLE
    IF NOT EXISTS relationship (
        sentence_id INT NOT NULL,
        section_id INT NOT NULL,
        related_text_id CHAR NOT NULL,
        PRIMARY KEY (sentence_id, section_id, related_text_id),
        FOREIGN KEY (sentence_id, section_id) REFERENCES Sentence (sentence_id, section_id),
        FOREIGN KEY (related_text_id) REFERENCES Related_text (related_id)
    );