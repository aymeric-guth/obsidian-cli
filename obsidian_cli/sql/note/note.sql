-- name: create-many*!
INSERT INTO file (path, name, extension)
VALUES (:path, :name, '.md');

-- name: read-all
SELECT id, path, name, extension FROM file WHERE extension = '.md';

-- name: find-by-name-path$
SELECT id FROM file WHERE name = :name AND extension = '.md' AND path = :path;

-- name: find-by-name
SELECT id
FROM file
WHERE name LIKE :name
AND extension = '.md';
