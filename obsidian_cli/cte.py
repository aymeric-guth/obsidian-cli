import sqlite3

# un moyen simple et puissant pour query les données
# /path/to/file = clé qui permet d'identifier un fichier
# composé de noeuds individuels
# composé d'un nom (non-unique)
# d'une relation qui posistionne le noeud dans la hierarchie

### queries
# une note avec les liens qu'elle contient
# toutes les notes avec les liens que chacune contient

con = sqlite3.connect("db.sqlite")

cur = con.execute(
    """
SELECT * FROM file;
"""
)

data = [i for i in cur]

con.commit()
cur.close()
con.close()

con = sqlite3.connect("db2.sqlite")

con.execute(
    """
DROP TABLE IF EXISTS path;
"""
)

con.execute(
    """
DROP TABLE IF EXISTS file;
"""
)

con.execute(
    """
CREATE TABLE IF NOT EXISTS file (
    id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
	name NVARCHAR(250) NULL,
    ext NVARCHAR(250) NULL
);
"""
)

# closure table
con.execute(
    """
CREATE TABLE IF NOT EXISTS path (
    ancestor_id INTEGER NOT NULL,
    descendant_id INTEGER,
    PRIMARY KEY (ancestor_id, descendant_id),
    FOREIGN KEY(ancestor_id)
        REFERENCES file(id),
	FOREIGN KEY(descendant_id)
        REFERENCES file(id)
);
"""
)

for id, name, ext, path in data:
    if path == ".":
        p = ["/"]
    else:
        p = path.split("/")
        p = ["/"] + p

    cur = con.execute(
        """INSERT INTO file (name, ext) VALUES (?, ?) RETURNING id;""", (name, ext)
    )
    _id = cur.fetchone()
    cur.close()

    print(_id, p)

con.commit()
con.close()


raise SystemExit

rows = cur.execute(
    """
SELECT * FROM file;
"""
).fetchall()
print(len(rows))


con.commit()
cur.close()
con.close()
