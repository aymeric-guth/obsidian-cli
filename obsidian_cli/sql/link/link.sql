-- name: create-table#
CREATE TABLE IF NOT EXISTS link (
    parent_id INTEGER  NOT NULL,
    child_id INTEGER  NOT NULL,
    FOREIGN KEY(parent_id) REFERENCES file(id),
	FOREIGN KEY(child_id) REFERENCES file(id)
);

-- name: create-one
INSERT INTO link (parent_id, child_id)
VALUES (:parent_id, :child_id);

-- name: read-many
SELECT * FROM link;

-- name: drop-table#
DROP TABLE IF EXISTS link;
