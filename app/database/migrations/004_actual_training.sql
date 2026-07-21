-- =========================================================
-- Actual workout sessions
-- =========================================================

CREATE TABLE workout_sessions (
    id INTEGER PRIMARY KEY,

    user_id INTEGER NOT NULL,
    location_id INTEGER,

    performed_on TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,

    title TEXT,

    status TEXT NOT NULL DEFAULT 'completed'
        CHECK (
            status IN (
                'completed',
                'partially_completed',
                'stopped',
                'unknown'
            )
        ),

    overall_rpe REAL
        CHECK (
            overall_rpe IS NULL
            OR overall_rpe BETWEEN 0 AND 10
        ),

    condition_score INTEGER
        CHECK (
            condition_score IS NULL
            OR condition_score BETWEEN 1 AND 5
        ),

    notes TEXT,
    source_message_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,

    CHECK (
        ended_at IS NULL
        OR started_at IS NULL
        OR ended_at >= started_at
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (location_id)
        REFERENCES locations(id)
        ON DELETE SET NULL,

    FOREIGN KEY (source_message_id)
        REFERENCES source_messages(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_workout_sessions_user_date
    ON workout_sessions (
        user_id,
        performed_on
    );

CREATE INDEX idx_workout_sessions_status
    ON workout_sessions (
        status
    );


-- =========================================================
-- Actual workout blocks
-- =========================================================

CREATE TABLE workout_blocks (
    id INTEGER PRIMARY KEY,

    workout_session_id INTEGER NOT NULL,

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

    status TEXT NOT NULL DEFAULT 'completed'
        CHECK (
            status IN (
                'completed',
                'partially_completed',
                'stopped',
                'unknown'
            )
        ),

    result_text TEXT,
    notes TEXT,

    source_message_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT,

    UNIQUE (
        workout_session_id,
        sequence
    ),

    FOREIGN KEY (workout_session_id)
        REFERENCES workout_sessions(id)
        ON DELETE CASCADE,

    FOREIGN KEY (source_message_id)
        REFERENCES source_messages(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_workout_blocks_session
    ON workout_blocks (
        workout_session_id
    );

CREATE INDEX idx_workout_blocks_type_goal
    ON workout_blocks (
        block_type,
        training_goal
    );


-- =========================================================
-- Links between actual blocks and planned blocks
-- =========================================================

CREATE TABLE workout_block_planned_blocks (
    workout_block_id INTEGER NOT NULL,
    planned_block_id INTEGER NOT NULL,

    relation_type TEXT NOT NULL DEFAULT 'exact'
        CHECK (
            relation_type IN (
                'exact',
                'modified',
                'substituted',
                'combined',
                'derived_from'
            )
        ),

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (
        workout_block_id,
        planned_block_id
    ),

    FOREIGN KEY (workout_block_id)
        REFERENCES workout_blocks(id)
        ON DELETE CASCADE,

    FOREIGN KEY (planned_block_id)
        REFERENCES planned_blocks(id)
        ON DELETE CASCADE
);


-- =========================================================
-- Optional program links for actual blocks
-- =========================================================

CREATE TABLE workout_block_program_runs (
    workout_block_id INTEGER NOT NULL,
    program_run_id INTEGER NOT NULL,

    source_role TEXT NOT NULL DEFAULT 'primary'
        CHECK (
            source_role IN (
                'primary',
                'supplemental',
                'modified_from',
                'inspired_by'
            )
        ),

    source_reference TEXT,
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (
        workout_block_id,
        program_run_id
    ),

    FOREIGN KEY (workout_block_id)
        REFERENCES workout_blocks(id)
        ON DELETE CASCADE,

    FOREIGN KEY (program_run_id)
        REFERENCES program_runs(id)
        ON DELETE CASCADE
);


-- =========================================================
-- Exercises performed inside an actual block
-- =========================================================

CREATE TABLE workout_exercises (
    id INTEGER PRIMARY KEY,

    workout_block_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,

    sequence INTEGER NOT NULL
        CHECK (sequence >= 1),

    group_label TEXT,
    variation_text TEXT,
    notes TEXT,

    source_message_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (
        workout_block_id,
        sequence
    ),

    FOREIGN KEY (workout_block_id)
        REFERENCES workout_blocks(id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE RESTRICT,

    FOREIGN KEY (source_message_id)
        REFERENCES source_messages(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_workout_exercises_exercise
    ON workout_exercises (
        exercise_id
    );


-- =========================================================
-- Individual exercise sets
-- =========================================================

CREATE TABLE exercise_sets (
    id INTEGER PRIMARY KEY,

    workout_exercise_id INTEGER NOT NULL,

    set_number INTEGER NOT NULL
        CHECK (set_number >= 1),

    set_type TEXT NOT NULL DEFAULT 'working'
        CHECK (
            set_type IN (
                'warmup',
                'working',
                'backoff',
                'drop',
                'test',
                'technique',
                'unknown'
            )
        ),

    reps INTEGER
        CHECK (
            reps IS NULL
            OR reps >= 0
        ),

    load_value REAL
        CHECK (
            load_value IS NULL
            OR load_value >= 0
        ),

    load_unit TEXT
        CHECK (
            load_unit IS NULL
            OR load_unit IN ('kg', 'lb')
        ),

    load_type TEXT NOT NULL DEFAULT 'external'
        CHECK (
            load_type IN (
                'external',
                'total',
                'assistance',
                'machine',
                'bodyweight',
                'unknown'
            )
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

    rpe REAL
        CHECK (
            rpe IS NULL
            OR rpe BETWEEN 0 AND 10
        ),

    rir REAL
        CHECK (
            rir IS NULL
            OR rir BETWEEN 0 AND 10
        ),

    is_failure INTEGER NOT NULL DEFAULT 0
        CHECK (is_failure IN (0, 1)),

    completed INTEGER NOT NULL DEFAULT 1
        CHECK (completed IN (0, 1)),

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (
        workout_exercise_id,
        set_number
    ),

    FOREIGN KEY (workout_exercise_id)
        REFERENCES workout_exercises(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_exercise_sets_workout_exercise
    ON exercise_sets (
        workout_exercise_id
    );


-- =========================================================
-- Metcon results
-- =========================================================

CREATE TABLE metcon_results (
    id INTEGER PRIMARY KEY,

    workout_block_id INTEGER NOT NULL UNIQUE,

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

    time_seconds INTEGER
        CHECK (
            time_seconds IS NULL
            OR time_seconds >= 0
        ),

    rounds_completed INTEGER
        CHECK (
            rounds_completed IS NULL
            OR rounds_completed >= 0
        ),

    reps_completed INTEGER
        CHECK (
            reps_completed IS NULL
            OR reps_completed >= 0
        ),

    load_value REAL
        CHECK (
            load_value IS NULL
            OR load_value >= 0
        ),

    load_unit TEXT
        CHECK (
            load_unit IS NULL
            OR load_unit IN ('kg', 'lb')
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

    time_cap_seconds INTEGER
        CHECK (
            time_cap_seconds IS NULL
            OR time_cap_seconds >= 0
        ),

    completed_within_cap INTEGER
        CHECK (
            completed_within_cap IS NULL
            OR completed_within_cap IN (0, 1)
        ),

    rx_status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (
            rx_status IN (
                'rx',
                'scaled',
                'modified',
                'foundations',
                'not_applicable',
                'unknown'
            )
        ),

    result_text TEXT,
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (workout_block_id)
        REFERENCES workout_blocks(id)
        ON DELETE CASCADE
);


-- =========================================================
-- Actual movement totals inside a metcon
-- =========================================================

CREATE TABLE metcon_movement_results (
    id INTEGER PRIMARY KEY,

    metcon_result_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,

    sequence INTEGER NOT NULL
        CHECK (sequence >= 1),

    total_reps INTEGER
        CHECK (
            total_reps IS NULL
            OR total_reps >= 0
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

    load_value REAL
        CHECK (
            load_value IS NULL
            OR load_value >= 0
        ),

    load_unit TEXT
        CHECK (
            load_unit IS NULL
            OR load_unit IN ('kg', 'lb')
        ),

    modification_text TEXT,
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (
        metcon_result_id,
        sequence
    ),

    FOREIGN KEY (metcon_result_id)
        REFERENCES metcon_results(id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE RESTRICT
);


-- =========================================================
-- Cardio results
-- =========================================================

CREATE TABLE cardio_results (
    id INTEGER PRIMARY KEY,

    workout_block_id INTEGER NOT NULL UNIQUE,
    exercise_id INTEGER NOT NULL,

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

    average_pace_seconds_per_km REAL
        CHECK (
            average_pace_seconds_per_km IS NULL
            OR average_pace_seconds_per_km >= 0
        ),

    average_speed_kph REAL
        CHECK (
            average_speed_kph IS NULL
            OR average_speed_kph >= 0
        ),

    average_heart_rate INTEGER
        CHECK (
            average_heart_rate IS NULL
            OR average_heart_rate >= 0
        ),

    maximum_heart_rate INTEGER
        CHECK (
            maximum_heart_rate IS NULL
            OR maximum_heart_rate >= 0
        ),

    intensity_zone TEXT,
    elevation_gain_meters REAL
        CHECK (
            elevation_gain_meters IS NULL
            OR elevation_gain_meters >= 0
        ),

    intervals_text TEXT,
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        duration_seconds IS NOT NULL
        OR distance_meters IS NOT NULL
    ),

    FOREIGN KEY (workout_block_id)
        REFERENCES workout_blocks(id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE RESTRICT
);
