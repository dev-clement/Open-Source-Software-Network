-- Note: a "user" is a reserved keyword in SQL, so we need to use double quotes around it when creating the table.
CREATE TABLE IF NOT EXISTS "user" (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    github_page VARCHAR(255),
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE IF NOT EXISTS "projects" (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    repository_url VARCHAR(255) NOT NULL UNIQUE,
    help_wanted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contributions (Many-to-Many Join Table)
-- This links users to projects they have contributed to.
CREATE TABLE IF NOT EXISTS "contributions" (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    fk_user_id BIGINT NOT NULL,
    fk_project_id BIGINT NOT NULL,
    FOREIGN KEY (fk_user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (fk_project_id) REFERENCES "projects"(id) ON DELETE CASCADE,
    
    -- Status can be either 'interested', 'contributed', or 'closed'
    status VARCHAR(20) NOT NULL DEFAULT 'interested',

    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure a user doesn't apply to the same project multiple times
    CONSTRAINT unique_user_project_contribution UNIQUE (fk_user_id, fk_project_id)
);

-- Trigger to automatically update the "updated_at" column at row change
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER updated_user_modtime BEFORE UPDATE ON "user" FOR EACH ROW EXECUTE update_updated_at_column();
CREATE TRIGGER updated_projects_modtime BEFORE UPDATE ON "projects" FOR EACH ROW EXECUTE update_updated_at_column();
CREATE TRIGGER updated_contributions_modtime BEFORE UPDATE ON "contributions" FOR EACH ROW EXECUTE update_updated_at_column();