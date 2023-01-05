# select all files containing tags and their relative tags
cur = conn.execute(
    """
SELECT f.name, t.name
FROM tag AS t
JOIN file_tag AS ft
ON t.id = ft.tag_id
JOIN file AS f
ON ft.file_id = f.id
ORDER BY f.name;
"""
)

# select all MD files without a reference to them
cur = conn.execute(
    """
SELECT f.path, f.name, f.extension
FROM link AS l
FULL JOIN file AS f
ON l.child_id = f.id
WHERE l.child_id IS NULL
AND f.extension = '.md'
AND f.path NOT LIKE '%Archives%';
"""
)
orphaned_md_files = [i for i in cur]

# select all non-MD files without a reference to them
cur = conn.execute(
    """
SELECT f.path, f.name, f.extension
FROM link AS l
FULL JOIN file AS f
ON l.child_id = f.id
WHERE l.child_id IS NULL
AND f.extension != '.md'
AND f.path NOT LIKE '%Archives%';
"""
)
orphaned_non_md_files = [i for i in cur]

total_md_files, *_ = conn.execute(
    """
SELECT count(*)
FROM file
WHERE extension = '.md';
"""
).fetchone()

total_non_md_files, *_ = conn.execute(
    """
SELECT count(*)
FROM file
WHERE extension != '.md';
"""
).fetchone()

total_tags, *_ = conn.execute(
    """
SELECT count(*)
FROM tag;
"""
).fetchone()

# select all files without tags
md_files_without_tag, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
FULL JOIN file_tag AS ft
ON f.id = ft.file_id
WHERE ft.tag_id IS NULL
AND f.extension = '.md'
AND f.path NOT LIKE '%Archives%';
"""
).fetchone()

# select all files at zettelkasten root
md_files_zk_root, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension = '.md'
AND f.path = '001 Zettelkasten';
"""
).fetchone()
non_md_files_zk_root, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension != '.md'
AND f.path = '001 Zettelkasten';
"""
).fetchone()
md_files_in_zk, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension = '.md'
AND f.path LIKE '001 Zettelkasten%';
"""
).fetchone()
non_md_files_in_zk, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension != '.md'
AND f.path LIKE '001 Zettelkasten%';
"""
).fetchone()

# select all files at attachment root
non_md_files_attachment_root, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension != '.md'
AND f.path = '000 Attachments';
"""
).fetchone()
md_files_attachment_root, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension = '.md'
AND f.path = '000 Attachments';
"""
).fetchone()
non_md_files_in_attachment, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension != '.md'
AND f.path LIKE '000 Attachments%';
"""
).fetchone()
md_files_in_attachment, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension = '.md'
AND f.path LIKE '000 Attachments%';
"""
).fetchone()


rapport = [
    f"Total MD files: {total_md_files}",
    f"Total non-MD files: {total_non_md_files}",
    f"Dead links: {dead_links}",
    f"Orphaned MD files: {len(orphaned_md_files)}",
    f"Orphaned non-MD files: {len(orphaned_non_md_files)}",
    f"Total tags: {total_tags}",
    f"MD files without tag: {md_files_without_tag}",
    f"MD files at Zettelkasten root: {md_files_zk_root}",
    f"non-MD files at Zettelkasten root: {non_md_files_zk_root}",
    f"MD files at Attachments root: {md_files_attachment_root}",
    f"Non-MD files at Attachments root: {non_md_files_attachment_root}",
    f"MD files in Attachments: {md_files_in_attachment}",
    f"Non-MD files in Attachments: {non_md_files_in_attachment}",
    f"MD files in Zettelkasten: {md_files_in_zk}",
    f"Non-MD files in Zettelkasten: {non_md_files_in_zk}",
]
