CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    clerk_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    firstname VARCHAR(100)
);

CREATE TABLE workspaces(
    id SERIAL PRIMARY KEY,
    owner_id INT NOT NULL REFERENCES users(id),
    space_name VARCHAR(255) NOT NULL,
    join_code VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE workspace_members(
    id SERIAL PRIMARY KEY,
    workspace_id INT NOT NULL REFERENCES workspaces(id),
    user_id INT NOT NULL REFERENCES users(id),
    UNIQUE (workspace_id, user_id)
);

CREATE TABLE tasks(
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    task_description TEXT,
    workspace_id INT NOT NULL REFERENCES workspaces(id),
    assigned_to INT REFERENCES users(id),
    task_status VARCHAR(50) NOT NULL DEFAULT 'todo',
    created_by INT NOT NULL REFERENCES users(id)
);