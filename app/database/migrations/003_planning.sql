-- =========================================================
-- Program definitions
-- =========================================================

CREATE TABLE programs (
    id INTEGER PRIMARY KEY,

    name TEXT NOT NULL COLLATE NOCASE,
    provider TEXT COLLATE NOCASE,

    program_type TEXT,
    version_label TEXT,

    description TEXT,
    notes TEXT,

    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_programs_name_provider
    ON programs (
        name,
        provider
    );


-- =========================================================
-- User program runs
-- =========================================================

CREATE TABLE program_runs (
    id INTEGER PRIMARY KEY,

    user_id INTEGER NOT NULL,
    program_id INTEGER NOT NULL,

    status TEXT NOT NULL DEFAULT 'active'
        CHECK (
            status IN (
                'active',
                'paused',
                'completed',
                'abandoned'
            )
        ),

    started_on TEXT NOT NULL,
    ended_on TEXT,

    current_week INTEGER
        CHECK (
            current_week IS NULL
            OR current_week >= 1
        ),

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        ended_on IS NULL
        OR ended_on >= started_on
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (program_id)
        REFERENCES programs(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_program_runs_user_status
    ON program_runs (
        user_id,
        status
    );

CREATE INDEX idx_program_runs_program
    ON program_runs (
        program_id
    );


-- =========================================================
-- Planned sessions
-- =========================================================

CREATE TABLE planned_sessions (
    id INTEGER PRIMARY KEY,

    user_id INTEGER NOT NULL,
    location_id INTEGER,

    session_date TEXT NOT NULL,
    planned_start_time TEXT,
    planned_end_time TEXT,

    title TEXT,

    status TEXT NOT NULL DEFAULT 'planned'
        CHECK (
            status IN (
                'planned',
                'completed',
                'partially_completed',
                'skipped',
                'rescheduled',
                'cancelled'
            )
        ),

    notes TEXT,

    rescheduled_from_session_id INTEGER,
    source_message_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,

    CHECK (
        planned_end_time IS NULL
        OR planned_start_time IS NULL
        OR planned_end_time >= planned_start_time
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (location_id)
        REFERENCES locations(id)
        ON DELETE SET NULL,

    FOREIGN KEY (rescheduled_from_session_id)
        REFERENCES planned_sessions(id)
        ON DELETE SET NULL,

    FOREIGN KEY (source_message_id)
        REFERENCES source_messages(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_planned_sessions_user_date
    ON planned_sessions (
        user_id,
        session_date
    );

CREATE INDEX idx_planned_sessions_status
    ON planned_sessions (
        status
    );


-- =========================================================
-- Planned blocks
-- =========================================================

CREATE TABLE planned_blocks (
    id INTEGER PRIMARY KEY,

    planned_session_id INTEGER NOT NULL,

    sequence INTEGER NOT NULL
        CHECK (sequence >= 1),

    title TEXT,

    block_type TEXT NOT NULL
        CHECK (
            block_type IN (
                'resistance',
                'metcon',
                'cardio',
                'skill',
                'mobility',
                'recovery',
                'warmup',
                'cooldown',
                'other'
            )
        ),

    training_goal TEXT NOT NULL DEFAULT 'unknown'
        CHECK (
            training_goal IN (
                'maximal_strength',
                'strength',
                'hypertrophy',
                'power',
                'weightlifting_technique',
                'gymnastics_skill',
                'conditioning',
                'aerobic_endurance',
                'speed',
                'mobility',
                'recovery',
                'mixed',
                'unknown'
            )
        ),

    status TEXT NOT NULL DEFAULT 'planned'
        CHECK (
            status IN (
                'planned',
                'completed',
                'partially_completed',
                'skipped',
                'rescheduled',
                'cancelled'
            )
        ),

    estimated_duration_minutes INTEGER
        CHECK (
            estimated_duration_minutes IS NULL
            OR estimated_duration_minutes >= 0
        ),

    prescription_text TEXT,
    notes TEXT,

    source_message_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,

    UNIQUE (
        planned_session_id,
        sequence
    ),

    FOREIGN KEY (planned_session_id)
        REFERENCES planned_sessions(id)
        ON DELETE CASCADE,

    FOREIGN KEY (source_message_id)
        REFERENCES source_messages(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_planned_blocks_session
    ON planned_blocks (
        planned_session_id
    );

CREATE INDEX idx_planned_blocks_type_goal
    ON planned_blocks (
        block_type,
        training_goal
    );


-- =========================================================
-- Optional many-to-many program source links
-- =========================================================

CREATE TABLE planned_block_program_runs (
    planned_block_id INTEGER NOT NULL,
    program_run_id INTEGER NOT NULL,

    source_role TEXT NOT NULL DEFAULT 'primary'
        CHECK (
            source_role IN (
                'primary',
                'supplemental',
                'inspired_by',
                'modified_from'
            )
        ),

    source_reference TEXT,
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (
        planned_block_id,
        program_run_id
    ),

    FOREIGN KEY (planned_block_id)
        REFERENCES planned_blocks(id)
        ON DELETE CASCADE,

    FOREIGN KEY (program_run_id)
        REFERENCES program_runs(id)
        ON DELETE CASCADE
);


-- =========================================================
-- Planned resistance, skill and general exercises
-- =========================================================

CREATE TABLE planned_exercises (
    id INTEGER PRIMARY KEY,

    planned_block_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,

    sequence INTEGER NOT NULL
        CHECK (sequence >= 1),

    group_label TEXT,

    sets INTEGER
        CHECK (
            sets IS NULL
            OR sets >= 1
        ),

    reps_min INTEGER
        CHECK (
            reps_min IS NULL
            OR reps_min >= 0
        ),

    reps_max INTEGER
        CHECK (
            reps_max IS NULL
            OR reps_max >= 0
        ),

    weight REAL
        CHECK (
            weight IS NULL
            OR weight >= 0
        ),

    weight_unit TEXT
        CHECK (
            weight_unit IS NULL
            OR weight_unit IN ('kg', 'lb')
        ),

    percentage_1rm REAL
        CHECK (
            percentage_1rm IS NULL
            OR percentage_1rm BETWEEN 0 AND 150
        ),

    target_rpe REAL
        CHECK (
            target_rpe IS NULL
            OR target_rpe BETWEEN 0 AND 10
        ),

    target_rir REAL
        CHECK (
            target_rir IS NULL
            OR target_rir BETWEEN 0 AND 10
        ),

    duration_seconds INTEGER
        CHECK (
            duration_seconds IS NULL
            OR duration_seconds >= 0
        ),

    distance_meters REAL
        CHECK (
            distance_meters IS NULL
            OR distance_meters >= 0
        ),

    calories REAL
        CHECK (
            calories IS NULL
            OR calories >= 0
        ),

    rest_seconds INTEGER
        CHECK (
            rest_seconds IS NULL
            OR rest_seconds >= 0
        ),

    tempo TEXT,
    prescription_text TEXT,
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        reps_min IS NULL
        OR reps_max IS NULL
        OR reps_min <= reps_max
    ),

    UNIQUE (
        planned_block_id,
        sequence
    ),

    FOREIGN KEY (planned_block_id)
        REFERENCES planned_blocks(id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_planned_exercises_exercise
    ON planned_exercises (
        exercise_id
    );


-- =========================================================
-- Planned metcons
-- =========================================================

CREATE TABLE planned_metcons (
    id INTEGER PRIMARY KEY,

    planned_block_id INTEGER NOT NULL UNIQUE,

    format TEXT NOT NULL DEFAULT 'unknown'
        CHECK (
            format IN (
                'for_time',
                'amrap',
                'emom',
                'every_n_minutes',
                'chipper',
                'interval',
                'rounds',
                'completion',
                'other',
                'unknown'
            )
        ),

    score_type TEXT NOT NULL DEFAULT 'other'
        CHECK (
            score_type IN (
                'time',
                'rounds_reps',
                'reps',
                'load',
                'distance',
                'calories',
                'completion',
                'other'
            )
        ),

    rounds INTEGER
        CHECK (
            rounds IS NULL
            OR rounds >= 1
        ),

    time_cap_seconds INTEGER
        CHECK (
            time_cap_seconds IS NULL
            OR time_cap_seconds >= 0
        ),

    work_interval_seconds INTEGER
        CHECK (
            work_interval_seconds IS NULL
            OR work_interval_seconds >= 0
        ),

    rest_interval_seconds INTEGER
        CHECK (
            rest_interval_seconds IS NULL
            OR rest_interval_seconds >= 0
        ),

    prescription_text TEXT NOT NULL,
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (planned_block_id)
        REFERENCES planned_blocks(id)
        ON DELETE CASCADE
);


-- =========================================================
-- Planned metcon movements
-- =========================================================

CREATE TABLE planned_metcon_movements (
    id INTEGER PRIMARY KEY,

    planned_metcon_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,

    sequence INTEGER NOT NULL
        CHECK (sequence >= 1),

    round_number INTEGER
        CHECK (
            round_number IS NULL
            OR round_number >= 1
        ),

    reps INTEGER
        CHECK (
            reps IS NULL
            OR reps >= 0
        ),

    distance_meters REAL
        CHECK (
            distance_meters IS NULL
            OR distance_meters >= 0
        ),

    calories REAL
        CHECK (
            calories IS NULL
            OR calories >= 0
        ),

    weight REAL
        CHECK (
            weight IS NULL
            OR weight >= 0
        ),

    weight_unit TEXT
        CHECK (
            weight_unit IS NULL
            OR weight_unit IN ('kg', 'lb')
        ),

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (
        planned_metcon_id,
        sequence
    ),

    FOREIGN KEY (planned_metcon_id)
        REFERENCES planned_metcons(id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE RESTRICT
);
