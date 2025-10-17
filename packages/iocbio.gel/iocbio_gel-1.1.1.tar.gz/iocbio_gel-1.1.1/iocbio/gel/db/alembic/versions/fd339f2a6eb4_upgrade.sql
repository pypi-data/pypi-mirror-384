DROP VIEW IF EXISTS project_with_path;

CREATE VIEW project_with_path AS
WITH RECURSIVE with_path (id, parent_id, name, path) AS
(
    SELECT id, parent_id, name, name as path
    FROM project
    WHERE parent_id IS NULL
    UNION ALL
    SELECT p.id, p.parent_id, p.name, p_path.path || '/' || p.name
    FROM with_path AS p_path JOIN project AS p
    ON p_path.id = p.parent_id
)
SELECT * FROM with_path;
