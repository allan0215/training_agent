-- =========================================================
-- Muscle group catalog
-- Future personalization uses this catalog.
-- =========================================================

CREATE TABLE muscle_groups (
    id INTEGER PRIMARY KEY,

    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name TEXT NOT NULL,
    description TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO muscle_groups (
    code,
    display_name
)
VALUES
    ('quads', '대퇴사두근'),
    ('hamstrings', '햄스트링'),
    ('glutes', '둔근'),
    ('calves', '종아리'),
    ('chest', '가슴'),
    ('lats', '광배근'),
    ('upper_back', '상부 등'),
    ('front_delts', '전면 삼각근'),
    ('side_delts', '측면 삼각근'),
    ('rear_delts', '후면 삼각근'),
    ('triceps', '삼두근'),
    ('biceps', '이두근'),
    ('forearms_grip', '전완 및 그립'),
    ('spinal_erectors', '척추기립근'),
    ('abdominals', '복부 및 코어'),
    ('other', '기타');


-- =========================================================
-- Weekly and period-based training targets
-- =========================================================

CREATE TABLE training_targets (
    id INTEGER PRIMARY KEY,

    user_id INTEGER NOT NULL,

    name TEXT NOT NULL,

    scope_type TEXT NOT NULL
        CHECK (
            scope_type IN (
                'movement_pattern',
                'exercise',
                'block_type'
            )
        ),

    movement_pattern_id INTEGER,
    exercise_id INTEGER,

    block_type TEXT
        CHECK (
            block_type IS NULL
            OR block_type IN (
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

    metric_type TEXT NOT NULL
        CHECK (
            metric_type IN (
                'effective_sets',
                'exposure_count',
                'frequency',
                'duration_minutes',
                'distance_meters'
            )
        ),

    minimum_value REAL
        CHECK (
            minimum_value IS NULL
            OR minimum_value >= 0
        ),

    target_value REAL NOT NULL
        CHECK (target_value >= 0),

    maximum_value REAL
        CHECK (
            maximum_value IS NULL
            OR maximum_value >= 0
        ),

    period_type TEXT NOT NULL DEFAULT 'weekly'
        CHECK (
            period_type IN (
                'weekly',
                'rolling_7_days'
            )
        ),

    priority INTEGER NOT NULL DEFAULT 3
        CHECK (priority BETWEEN 1 AND 5),

    valid_from TEXT NOT NULL,
    valid_until TEXT,

    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        (
            scope_type = 'movement_pattern'
            AND movement_pattern_id IS NOT NULL
            AND exercise_id IS NULL
            AND block_type IS NULL
        )
        OR
        (
            scope_type = 'exercise'
            AND movement_pattern_id IS NULL
            AND exercise_id IS NOT NULL
            AND block_type IS NULL
        )
        OR
        (
            scope_type = 'block_type'
            AND movement_pattern_id IS NULL
            AND exercise_id IS NULL
            AND block_type IS NOT NULL
        )
    ),

    CHECK (
        minimum_value IS NULL
        OR minimum_value <= target_value
    ),

    CHECK (
        maximum_value IS NULL
        OR target_value <= maximum_value
    ),

    CHECK (
        valid_until IS NULL
        OR valid_until >= valid_from
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (movement_pattern_id)
        REFERENCES movement_patterns(id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_training_targets_user_active
    ON training_targets (
        user_id,
        is_active
    );

CREATE INDEX idx_training_targets_scope
    ON training_targets (
        scope_type,
        metric_type
    );


-- =========================================================
-- Recommendation batches
-- One analysis request can create several recommendations.
-- =========================================================

CREATE TABLE recommendation_batches (
    id INTEGER PRIMARY KEY,

    user_id INTEGER NOT NULL,

    week_start TEXT NOT NULL,
    week_end TEXT NOT NULL,

    requested_location_id INTEGER,

    status TEXT NOT NULL DEFAULT 'proposed'
        CHECK (
            status IN (
                'proposed',
                'partially_approved',
                'approved',
                'rejected',
                'expired'
            )
        ),

    analysis_snapshot_json TEXT,
    notes TEXT,

    source_message_id INTEGER,

    expires_at TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (week_end >= week_start),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (requested_location_id)
        REFERENCES locations(id)
        ON DELETE SET NULL,

    FOREIGN KEY (source_message_id)
        REFERENCES source_messages(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_recommendation_batches_user_week
    ON recommendation_batches (
        user_id,
        week_start
    );

CREATE INDEX idx_recommendation_batches_status
    ON recommendation_batches (
        status
    );


-- =========================================================
-- Individual recommendation items
-- =========================================================

CREATE TABLE recommendation_items (
    id INTEGER PRIMARY KEY,

    recommendation_batch_id INTEGER NOT NULL,

    rank INTEGER NOT NULL
        CHECK (rank >= 1),

    exercise_id INTEGER NOT NULL,
    movement_pattern_id INTEGER,

    training_target_id INTEGER,
    location_id INTEGER,

    status TEXT NOT NULL DEFAULT 'proposed'
        CHECK (
            status IN (
                'proposed',
                'approved',
                'rejected',
                'scheduled',
                'expired'
            )
        ),

    deficit_metric_type TEXT
        CHECK (
            deficit_metric_type IS NULL
            OR deficit_metric_type IN (
                'effective_sets',
                'exposure_count',
                'frequency',
                'duration_minutes',
                'distance_meters'
            )
        ),

    deficit_value REAL
        CHECK (
            deficit_value IS NULL
            OR deficit_value >= 0
        ),

    proposed_sets INTEGER
        CHECK (
            proposed_sets IS NULL
            OR proposed_sets >= 1
        ),

    proposed_reps_min INTEGER
        CHECK (
            proposed_reps_min IS NULL
            OR proposed_reps_min >= 0
        ),

    proposed_reps_max INTEGER
        CHECK (
            proposed_reps_max IS NULL
            OR proposed_reps_max >= 0
        ),

    proposed_duration_seconds INTEGER
        CHECK (
            proposed_duration_seconds IS NULL
            OR proposed_duration_seconds >= 0
        ),

    proposed_distance_meters REAL
        CHECK (
            proposed_distance_meters IS NULL
            OR proposed_distance_meters >= 0
        ),

    proposed_load_value REAL
        CHECK (
            proposed_load_value IS NULL
            OR proposed_load_value >= 0
        ),

    proposed_load_unit TEXT
        CHECK (
            proposed_load_unit IS NULL
            OR proposed_load_unit IN ('kg', 'lb')
        ),

    rationale TEXT NOT NULL,

    excluded_alternatives_json TEXT,
    constraints_snapshot_json TEXT,

    confidence REAL
        CHECK (
            confidence IS NULL
            OR confidence BETWEEN 0 AND 1
        ),

    created_planned_block_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        proposed_reps_min IS NULL
        OR proposed_reps_max IS NULL
        OR proposed_reps_min <= proposed_reps_max
    ),

    UNIQUE (
        recommendation_batch_id,
        rank
    ),

    FOREIGN KEY (recommendation_batch_id)
        REFERENCES recommendation_batches(id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE RESTRICT,

    FOREIGN KEY (movement_pattern_id)
        REFERENCES movement_patterns(id)
        ON DELETE SET NULL,

    FOREIGN KEY (training_target_id)
        REFERENCES training_targets(id)
        ON DELETE SET NULL,

    FOREIGN KEY (location_id)
        REFERENCES locations(id)
        ON DELETE SET NULL,

    FOREIGN KEY (created_planned_block_id)
        REFERENCES planned_blocks(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_recommendation_items_batch_status
    ON recommendation_items (
        recommendation_batch_id,
        status
    );

CREATE INDEX idx_recommendation_items_exercise
    ON recommendation_items (
        exercise_id
    );


-- =========================================================
-- General recovery check-ins
-- =========================================================

CREATE TABLE recovery_checkins (
    id INTEGER PRIMARY KEY,

    user_id INTEGER NOT NULL,

    recorded_at TEXT NOT NULL,
    reference_date TEXT NOT NULL,

    overall_fatigue INTEGER
        CHECK (
            overall_fatigue IS NULL
            OR overall_fatigue BETWEEN 1 AND 5
        ),

    sleep_quality INTEGER
        CHECK (
            sleep_quality IS NULL
            OR sleep_quality BETWEEN 1 AND 5
        ),

    energy_level INTEGER
        CHECK (
            energy_level IS NULL
            OR energy_level BETWEEN 1 AND 5
        ),

    motivation INTEGER
        CHECK (
            motivation IS NULL
            OR motivation BETWEEN 1 AND 5
        ),

    stress_level INTEGER
        CHECK (
            stress_level IS NULL
            OR stress_level BETWEEN 1 AND 5
        ),

    notes TEXT,
    source_message_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        overall_fatigue IS NOT NULL
        OR sleep_quality IS NOT NULL
        OR energy_level IS NOT NULL
        OR motivation IS NOT NULL
        OR stress_level IS NOT NULL
        OR notes IS NOT NULL
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (source_message_id)
        REFERENCES source_messages(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_recovery_checkins_user_date
    ON recovery_checkins (
        user_id,
        reference_date
    );


-- =========================================================
-- Muscle soreness, fatigue and pain observations
-- =========================================================

CREATE TABLE muscle_status_observations (
    id INTEGER PRIMARY KEY,

    user_id INTEGER NOT NULL,
    muscle_group_id INTEGER NOT NULL,

    recorded_at TEXT NOT NULL,

    soreness_score INTEGER
        CHECK (
            soreness_score IS NULL
            OR soreness_score BETWEEN 0 AND 5
        ),

    fatigue_score INTEGER
        CHECK (
            fatigue_score IS NULL
            OR fatigue_score BETWEEN 0 AND 5
        ),

    pain_score INTEGER
        CHECK (
            pain_score IS NULL
            OR pain_score BETWEEN 0 AND 5
        ),

    stiffness_score INTEGER
        CHECK (
            stiffness_score IS NULL
            OR stiffness_score BETWEEN 0 AND 5
        ),

    laterality TEXT NOT NULL DEFAULT 'unknown'
        CHECK (
            laterality IN (
                'left',
                'right',
                'bilateral',
                'central',
                'not_applicable',
                'unknown'
            )
        ),

    notes TEXT,
    source_message_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        soreness_score IS NOT NULL
        OR fatigue_score IS NOT NULL
        OR pain_score IS NOT NULL
        OR stiffness_score IS NOT NULL
        OR notes IS NOT NULL
    ),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (muscle_group_id)
        REFERENCES muscle_groups(id)
        ON DELETE RESTRICT,

    FOREIGN KEY (source_message_id)
        REFERENCES source_messages(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_muscle_status_user_recorded
    ON muscle_status_observations (
        user_id,
        recorded_at
    );

CREATE INDEX idx_muscle_status_group
    ON muscle_status_observations (
        muscle_group_id
    );


-- =========================================================
-- Optional links between observations and prior workouts
-- A soreness report does not have to be attributed to one workout.
-- =========================================================

CREATE TABLE observation_workout_links (
    observation_id INTEGER NOT NULL,
    workout_session_id INTEGER NOT NULL,

    attribution_type TEXT NOT NULL DEFAULT 'temporal'
        CHECK (
            attribution_type IN (
                'temporal',
                'self_reported',
                'model_inferred',
                'unknown'
            )
        ),

    attribution_weight REAL
        CHECK (
            attribution_weight IS NULL
            OR attribution_weight BETWEEN 0 AND 1
        ),

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (
        observation_id,
        workout_session_id
    ),

    FOREIGN KEY (observation_id)
        REFERENCES muscle_status_observations(id)
        ON DELETE CASCADE,

    FOREIGN KEY (workout_session_id)
        REFERENCES workout_sessions(id)
        ON DELETE CASCADE
);


-- =========================================================
-- Performance observations
-- Raw workouts remain the primary source.
-- This table stores explicit or derived performance metrics.
-- =========================================================

CREATE TABLE performance_observations (
    id INTEGER PRIMARY KEY,

    user_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,

    workout_session_id INTEGER,
    workout_block_id INTEGER,

    observed_at TEXT NOT NULL,

    metric_type TEXT NOT NULL
        CHECK (
            metric_type IN (
                'estimated_1rm',
                'max_unbroken_reps',
                'working_weight',
                'time_seconds',
                'pace_seconds_per_km',
                'rounds',
                'reps_completed',
                'set_dropoff_percent',
                'other'
            )
        ),

    metric_value REAL NOT NULL,

    metric_unit TEXT,

    is_derived INTEGER NOT NULL DEFAULT 0
        CHECK (is_derived IN (0, 1)),

    calculation_version TEXT,

    confidence REAL
        CHECK (
            confidence IS NULL
            OR confidence BETWEEN 0 AND 1
        ),

    notes TEXT,
    source_message_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (exercise_id)
        REFERENCES exercises(id)
        ON DELETE RESTRICT,

    FOREIGN KEY (workout_session_id)
        REFERENCES workout_sessions(id)
        ON DELETE SET NULL,

    FOREIGN KEY (workout_block_id)
        REFERENCES workout_blocks(id)
        ON DELETE SET NULL,

    FOREIGN KEY (source_message_id)
        REFERENCES source_messages(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_performance_observations_user_exercise
    ON performance_observations (
        user_id,
        exercise_id,
        observed_at
    );
