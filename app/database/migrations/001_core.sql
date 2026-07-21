CREATE TABLE users (
    id INTEGER PRIMARY KEY,

    discord_user_id TEXT NOT NULL UNIQUE,
    display_name TEXT,

    timezone TEXT NOT NULL DEFAULT 'Asia/Seoul',

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE source_messages (
    id INTEGER PRIMARY KEY,

    discord_message_id TEXT NOT NULL UNIQUE,
    discord_channel_id TEXT NOT NULL,

    user_id INTEGER NOT NULL,
    message_text TEXT,

    received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_source_messages_user_received_at
    ON source_messages (
        user_id,
        received_at
    );
