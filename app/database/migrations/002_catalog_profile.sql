-- =========================================================
-- Movement patterns
-- =========================================================

CREATE TABLE movement_patterns (
    id INTEGER PRIMARY KEY,

    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name TEXT NOT NULL,
    description TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO movement_patterns (
    code,
    display_name
)
VALUES
    ('squat', '스쿼트'),
    ('hinge', '힌지'),
    ('horizontal_push', '수평 밀기'),
    ('horizontal_pull', '수평 당기기'),
    ('vertical_push', '수직 밀기'),
    ('vertical_pull', '수직 당기기'),
    ('knee_flexion', '무릎 굽힘'),
    ('carry', '운반'),
    ('locomotion', '이동'),
    ('jump', '점프'),
    ('core', '코어'),
    ('other', '기타');


-- =========================================================
-- Exercise catalog
-- =========================================================

CREATE TABLE exercises (
    id INTEGER PRIMARY KEY,

    canonical_name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    korean_name TEXT,

    category TEXT,
    default_block_type TEXT,

    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE exercise_aliases (
    id INTEGER PRIMARY KEY,

    exercise_id INTEGER NOT NULL,

    alias TEXT NOT NULL,
    alias_normalized TEXT NOT NULL COLLATE NOCASE,

    language TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (
        alias_normalized,
        exercise_id
    ),

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_exercise_aliases_normalized
    ON exercise_aliases (
        alias_normalized
    );

CREATE TABLE exercise_movement_patterns (
    exercise_id INTEGER NOT NULL,
    movement_pattern_id INTEGER NOT NULL,

    role TEXT NOT NULL DEFAULT 'primary'
        CHECK (
            role IN (
                'primary',
                'secondary',
                'stabilizer'
            )
        ),

    contribution_weight REAL NOT NULL DEFAULT 1.0
        CHECK (contribution_weight > 0),

    PRIMARY KEY (
        exercise_id,
        movement_pattern_id
    ),

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE CASCADE,

    FOREIGN KEY (movement_pattern_id)
        REFERENCES movement_patterns(id)
        ON DELETE CASCADE
);


-- =========================================================
-- Equipment catalog
-- =========================================================

CREATE TABLE equipment (
    id INTEGER PRIMARY KEY,

    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name TEXT NOT NULL,

    category TEXT,
    notes TEXT,

    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE exercise_equipment (
    exercise_id INTEGER NOT NULL,
    equipment_id INTEGER NOT NULL,

    is_required INTEGER NOT NULL DEFAULT 1
        CHECK (is_required IN (0, 1)),

    quantity_required INTEGER
        CHECK (
            quantity_required IS NULL
            OR quantity_required >= 0
        ),

    notes TEXT,

    PRIMARY KEY (
        exercise_id,
        equipment_id
    ),

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE CASCADE,

    FOREIGN KEY (equipment_id)
        REFERENCES equipment(id)
        ON DELETE CASCADE
);


-- =========================================================
-- User locations and available equipment
-- =========================================================

CREATE TABLE locations (
    id INTEGER PRIMARY KEY,

    user_id INTEGER NOT NULL,

    name TEXT NOT NULL COLLATE NOCASE,

    location_type TEXT NOT NULL
        CHECK (
            location_type IN (
                'home_gym',
                'commercial_gym',
                'crossfit_box',
                'outdoor',
                'temporary_location',
                'other'
            )
        ),

    notes TEXT,

    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (
        user_id,
        name
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE location_equipment (
    location_id INTEGER NOT NULL,
    equipment_id INTEGER NOT NULL,

    quantity INTEGER
        CHECK (
            quantity IS NULL
            OR quantity >= 0
        ),

    minimum_weight REAL
        CHECK (
            minimum_weight IS NULL
            OR minimum_weight >= 0
        ),

    maximum_weight REAL
        CHECK (
            maximum_weight IS NULL
            OR maximum_weight >= 0
        ),

    weight_unit TEXT
        CHECK (
            weight_unit IS NULL
            OR weight_unit IN ('kg', 'lb')
        ),

    notes TEXT,

    PRIMARY KEY (
        location_id,
        equipment_id
    ),

    CHECK (
        minimum_weight IS NULL
        OR maximum_weight IS NULL
        OR minimum_weight <= maximum_weight
    ),

    FOREIGN KEY (location_id)
        REFERENCES locations(id)
        ON DELETE CASCADE,

    FOREIGN KEY (equipment_id)
        REFERENCES equipment(id)
        ON DELETE CASCADE
);


-- =========================================================
-- User exercise preferences
-- =========================================================

CREATE TABLE exercise_preferences (
    user_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,

    preference_score INTEGER NOT NULL DEFAULT 0
        CHECK (
            preference_score BETWEEN -2 AND 2
        ),

    reason TEXT,
    context TEXT,

    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (
        user_id,
        exercise_id
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE CASCADE
);


-- =========================================================
-- User exercise capabilities
-- =========================================================

CREATE TABLE exercise_capabilities (
    user_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,

    status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (
            status IN (
                'available',
                'learning',
                'scaled_only',
                'restricted',
                'unavailable',
                'unknown'
            )
        ),

    skill_level TEXT,

    max_unbroken_reps INTEGER
        CHECK (
            max_unbroken_reps IS NULL
            OR max_unbroken_reps >= 0
        ),

    max_weight REAL
        CHECK (
            max_weight IS NULL
            OR max_weight >= 0
        ),

    weight_unit TEXT
        CHECK (
            weight_unit IS NULL
            OR weight_unit IN ('kg', 'lb')
        ),

    notes TEXT,

    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (
        user_id,
        exercise_id
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE CASCADE
);


-- =========================================================
-- Temporary restrictions
-- =========================================================

CREATE TABLE exercise_restrictions (
    id INTEGER PRIMARY KEY,

    user_id INTEGER NOT NULL,

    exercise_id INTEGER,
    movement_pattern_id INTEGER,

    restriction_level TEXT NOT NULL
        CHECK (
            restriction_level IN (
                'avoid',
                'limit',
                'modify'
            )
        ),

    status TEXT NOT NULL DEFAULT 'active'
        CHECK (
            status IN (
                'active',
                'review_required',
                'resolved'
            )
        ),

    reason TEXT NOT NULL,

    starts_on TEXT NOT NULL,
    expected_end_on TEXT,
    resolved_at TEXT,

    notes TEXT,

    source_message_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        exercise_id IS NOT NULL
        OR movement_pattern_id IS NOT NULL
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE CASCADE,

    FOREIGN KEY (movement_pattern_id)
        REFERENCES movement_patterns(id)
        ON DELETE CASCADE,

    FOREIGN KEY (source_message_id)
        REFERENCES source_messages(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_exercise_restrictions_user_status
    ON exercise_restrictions (
        user_id,
        status
    );

CREATE INDEX idx_exercise_restrictions_dates
    ON exercise_restrictions (
        starts_on,
        expected_end_on
    );
