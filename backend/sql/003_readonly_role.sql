-- Read-only role for Text-to-SQL / chatbot runtime.
-- Password placeholder __CHATBOT_READONLY_PASSWORD__ is replaced by migrate script from env.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'chatbot_readonly') THEN
        CREATE ROLE chatbot_readonly WITH LOGIN PASSWORD '__CHATBOT_READONLY_PASSWORD__';
    ELSE
        ALTER ROLE chatbot_readonly WITH LOGIN PASSWORD '__CHATBOT_READONLY_PASSWORD__';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO chatbot_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO chatbot_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO chatbot_readonly;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO chatbot_readonly;
