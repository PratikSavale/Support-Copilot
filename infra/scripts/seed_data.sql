-- Optional demo seed data (run after init_db.sql)
-- Demo login (when auth is wired): username "demo", password "password" (bcrypt below).
-- Hash is the common Laravel testing default for the literal password "password".
-- Replace before any real deployment.

INSERT INTO users (id, username, email, password_hash, role)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'demo',
    'demo@example.com',
    '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
    'agent'
)
ON CONFLICT (username) DO NOTHING;

-- Example session for local integration tests (optional)
INSERT INTO sessions (id, user_id, title, status)
VALUES (
    '00000000-0000-0000-0000-000000000010',
    '00000000-0000-0000-0000-000000000001',
    'Demo session',
    'active'
)
ON CONFLICT (id) DO NOTHING;
