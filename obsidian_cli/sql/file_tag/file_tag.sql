-- name: create-table#
CREATE TABLE IF NOT EXISTS file_tag (
    file_id INTEGER  NOT NULL,
    tag_id INTEGER  NOT NULL,
    PRIMARY KEY (file_id, tag_id),
    FOREIGN KEY(file_id) REFERENCES file(id),
	FOREIGN KEY(tag_id) REFERENCES tag(id)
);

-- name: create-one!
INSERT INTO file_tag (file_id, tag_id) VALUES (:file_id, :tag_id);

-- name: find-file-by-tag
SELECT f.path, f.name, f.extension
FROM file AS f
JOIN file_tag AS ft
ON f.id = ft.file_id
JOIN tag AS t
ON ft.tag_id = t.id
WHERE t.name = :name
ORDER BY t.name DESC;

-- name: find-tag-by-filename
SELECT t.name
FROM tag AS t
JOIN file_tag AS ft
ON t.id = ft.tag_id
JOIN file AS f
ON ft.file_id = f.id
WHERE f.name = :name;

-- name: drop-table#
DROP TABLE IF EXISTS file_tag;
