-- name: create-table#
CREATE TABLE IF NOT EXISTS link (
    parent_id INTEGER  NOT NULL,
    child_id INTEGER  NOT NULL,
    FOREIGN KEY(parent_id) REFERENCES file(id),
	FOREIGN KEY(child_id) REFERENCES file(id)
);

-- name: create-one!
INSERT INTO link (parent_id, child_id)
VALUES (:parent_id, :child_id);

-- name: read-all
SELECT * FROM link;

-- name: find-file-by-link
SELECT p.id, p.path, p.name, p.extension
FROM link AS l
JOIN file AS c
ON l.child_id = c.id
JOIN file AS p
ON l.parent_id = p.id
WHERE c.name = :name;

-- name: find-orphaned
SELECT f.id, f.path, f.name, f.extension
FROM link AS l
FULL JOIN file AS f
ON l.child_id = f.id
WHERE l.child_id IS NULL
AND f.extension = '.md'
AND f.path NOT LIKE '%Archives%';

-- name: find-orphaned-dir
SELECT f.id, f.path, f.name, f.extension
FROM link AS l
FULL JOIN file AS f
ON l.child_id = f.id
WHERE l.child_id IS NULL
AND f.extension = '.md'
AND f.path LIKE :dir;

-- name: drop-table#
DROP TABLE IF EXISTS link;
