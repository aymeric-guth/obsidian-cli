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

-- name: drop-table#
DROP TABLE IF EXISTS tag;
