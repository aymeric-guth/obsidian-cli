-- name: create*!
INSERT INTO file (path, name, extension)
VALUES (:path, :name, '.md');

-- name: read-all
SELECT id, name, extension, path FROM file WHERE extension = '.md';

-- name: find-by-name-path
SELECT * FROM file WHERE name = :name AND extension = '.md' AND path = :path;

-- name: find-by-name
SELECT path, name, extension
FROM file
WHERE name LIKE :name
AND extension = '.md';
