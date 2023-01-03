import sqlite3

con = sqlite3.connect("db.sqlite")
cur = con.cursor()

cur.execute(
    """
DROP TABLE IF EXISTS filesearch;
"""
)

# cur.execute(
#     """
# CREATE VIRTUAL TABLE IF NOT EXISTS filesearch
# USING fts5(id, name, extension, path, tokenize="trigram");
# """
# )

cur.execute(
    """
CREATE VIRTUAL TABLE IF NOT EXISTS filesearch
USING fts5(id, name, extension, path);
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
WHERE f.id NOT IN (
    SELECT parent_id FROM link
    UNION
    SELECT child_id FROM link
)
AND f.path MATCH 'archives';
"""
).fetchall()

"""
select date_trunc('day', days)::date as created_at, count(n.user_id) as new_users
from generate_series
         ( (select min(created_at) from contribution
           )
         , (select max(created_at) from contribution where project_id = 44861
         )
         , '1 day'::interval) days
         left outer join
     ( select user_id, min(created_at) as min_created_at
       from contribution
       group by user_id
     ) n
     on date_trunc('day', days)::date = n.min_created_at
group by created_at
order by created_at desc;
"""

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
