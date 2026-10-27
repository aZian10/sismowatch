-- ==============================================================================
-- 04_seed.sql: Initial Seed Data for SismoWatch
-- ==============================================================================

-- Seed Administrator User
INSERT INTO curated.users (username, email, password_hash, role, full_name, is_active)
VALUES (
    'admin',
    'admin@sismowatch.internal',
    '$2b$12$m36TTsYBNQniJDfaCwmFoeNZghWhdCBgGL/4orNzlilMkfwqKxTN2',
    'admin',
    'System Administrator',
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- Seed Viewer User
INSERT INTO curated.users (username, email, password_hash, role, full_name, is_active)
VALUES (
    'viewer',
    'viewer@sismowatch.internal',
    '$2b$12$u3HV4Rs/x18F69SZIsVAgOBGZ/mzaQgsAg26zax3BYXqnya.Bg2qS',
    'viewer',
    'Risk Analyst Viewer',
    TRUE
)
ON CONFLICT (username) DO NOTHING;
