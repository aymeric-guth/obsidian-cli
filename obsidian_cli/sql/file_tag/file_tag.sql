-- name: create-table#
CREATE TABLE IF NOT EXISTS file_tag (
    file_id INTEGER  NOT NULL,
    tag_id INTEGER  NOT NULL,
    PRIMARY KEY (file_id, tag_id),
    FOREIGN KEY(file_id) REFERENCES file(id),
	FOREIGN KEY(tag_id) REFERENCES tag(id)
);

-- name: drop-table#
DROP TABLE IF EXISTS file_tag;
