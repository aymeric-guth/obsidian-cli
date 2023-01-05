-- name: create-table#
CREATE TABLE IF NOT EXISTS file (
    id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
	name NVARCHAR(250)  NULL,
    extension NVARCHAR(250)  NULL,
	path NVARCHAR(250)  NULL
);

-- name: create-many*!
INSERT INTO file (path, name, extension)
VALUES (:path, :name, :extension);

-- name: find-by-name-extension
SELECT id FROM file WHERE name = :name AND extension = :extension;

-- name: find-by-name-extension-path$
SELECT id FROM file WHERE name = :name AND extension = :extension AND path = :path;

-- name: drop-table#
DROP TABLE IF EXISTS file;
