-- Fix Evidence 21: Extract filename from file_path and set original_filename
UPDATE evidence 
SET original_filename = substring(file_path from '[^/\\]+$')
WHERE id = 21 AND original_filename IS NULL;

-- Verify the update
SELECT id, control_id, title, file_path, original_filename 
FROM evidence 
WHERE id = 21;
