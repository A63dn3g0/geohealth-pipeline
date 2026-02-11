-- This query will list all schemas, tables, and columns in your PostgreSQL database
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
ORDER BY table_schema, table_name, ordinal_position;
