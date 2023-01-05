-- name: create-table#
CREATE TABLE IF NOT EXISTS file (
    id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
	name NVARCHAR(250)  NULL,
    extension NVARCHAR(250)  NULL,
	path NVARCHAR(250)  NULL
);

-- name: drop-table#
DROP TABLE IF EXISTS file;
