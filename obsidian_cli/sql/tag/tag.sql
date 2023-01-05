-- name: create-table#
CREATE TABLE IF NOT EXISTS tag (
    id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
	name NVARCHAR(250)  NULL
);

-- name: find-by-name
SELECT id, name FROM tag WHERE name = :tagname;

-- name: read-all
SELECT t.name
FROM tag AS t
ORDER BY t.name DESC;

-- name: read-one$
SELECT id FROM tag WHERE name = :name;

-- name: create-one<!
INSERT INTO tag (name) VALUES (:name) RETURNING id;

-- name: drop-table#
DROP TABLE IF EXISTS tag;
