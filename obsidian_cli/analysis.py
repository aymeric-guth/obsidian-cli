import sqlite3

con = sqlite3.connect("db.sqlite")
cur = con.cursor()

cur = con.cursor()

cur.execute(
    """
DROP TABLE IF EXISTS filesearch;
"""
)

cur.execute(
    """
CREATE VIRTUAL TABLE IF NOT EXISTS filesearch
USING fts5(id, name, extension, path, tokenize="trigram");
"""
)

cur.execute(
    """
INSERT INTO filesearch SELECT id, name, extension, path FROM file;
"""
)

rows = cur.execute(
    """
SELECT f.path, f.name, f.extension
FROM filesearch AS f
WHERE f.id NOT IN (select parent_id FROM link)
AND f.id NOT IN (select child_id FROM link)
AND f.path MATCH '% NOT archives';
"""
).fetchall()

print(len(rows))
for p, f, e in rows:
    print(f"{p}/{f}{e}")

rows = cur.execute(
    """
SELECT * FROM file;
"""
).fetchall()
print(len(rows))


con.commit()
cur.close()
con.close()
