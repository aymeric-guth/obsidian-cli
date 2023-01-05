-- name: create-table#
CREATE TABLE IF NOT EXISTS tag (
    id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
	name NVARCHAR(250)  NULL
);

-- name: drop-table#
DROP TABLE IF EXISTS tag;
