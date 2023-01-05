-- name: create-table#
CREATE TABLE IF NOT EXISTS link (
    parent_id INTEGER  NOT NULL,
    child_id INTEGER  NOT NULL,
    FOREIGN KEY(parent_id) REFERENCES file(id),
	FOREIGN KEY(child_id) REFERENCES file(id)
);

-- name: drop-table#
DROP TABLE IF EXISTS link;
