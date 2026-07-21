-- =========================================================
-- Dynamic exercise catalog metadata
-- =========================================================

ALTER TABLE exercises
ADD COLUMN catalog_scope TEXT NOT NULL DEFAULT 'core'
    CHECK (
        catalog_scope IN (
            'core',
            'personal'
        )
    );

ALTER TABLE exercises
ADD COLUMN owner_user_id INTEGER
    REFERENCES users(id)
    ON DELETE CASCADE;

ALTER TABLE exercises
ADD COLUMN source_type TEXT NOT NULL DEFAULT 'seed'
    CHECK (
        source_type IN (
            'seed',
            'user_created',
            'owner_created',
            'ai_suggested',
            'imported',
            'promoted'
        )
    );

ALTER TABLE exercises
ADD COLUMN review_status TEXT NOT NULL DEFAULT 'verified'
    CHECK (
        review_status IN (
            'verified',
            'pending_review',
            'rejected'
        )
    );

ALTER TABLE exercises
ADD COLUMN parent_exercise_id INTEGER
    REFERENCES exercises(id)
    ON DELETE SET NULL;

ALTER TABLE exercises
ADD COLUMN created_by_user_id INTEGER
    REFERENCES users(id)
    ON DELETE SET NULL;


-- =========================================================
-- Indexes
-- =========================================================

CREATE INDEX idx_exercises_catalog_scope
    ON exercises (
        catalog_scope,
        is_active
    );

CREATE INDEX idx_exercises_owner
    ON exercises (
        owner_user_id,
        is_active
    );

CREATE INDEX idx_exercises_parent
    ON exercises (
        parent_exercise_id
    );


-- =========================================================
-- Scope and ownership validation
-- =========================================================

CREATE TRIGGER trg_exercises_scope_owner_insert
BEFORE INSERT ON exercises
FOR EACH ROW
WHEN
    (
        NEW.catalog_scope = 'core'
        AND NEW.owner_user_id IS NOT NULL
    )
    OR
    (
        NEW.catalog_scope = 'personal'
        AND NEW.owner_user_id IS NULL
    )
BEGIN
    SELECT RAISE(
        ABORT,
        'core exercises must have no owner; personal exercises require an owner'
    );
END;


CREATE TRIGGER trg_exercises_scope_owner_update
BEFORE UPDATE OF
    catalog_scope,
    owner_user_id
ON exercises
FOR EACH ROW
WHEN
    (
        NEW.catalog_scope = 'core'
        AND NEW.owner_user_id IS NOT NULL
    )
    OR
    (
        NEW.catalog_scope = 'personal'
        AND NEW.owner_user_id IS NULL
    )
BEGIN
    SELECT RAISE(
        ABORT,
        'core exercises must have no owner; personal exercises require an owner'
    );
END;


CREATE TRIGGER trg_exercises_parent_not_self
BEFORE UPDATE OF parent_exercise_id
ON exercises
FOR EACH ROW
WHEN NEW.parent_exercise_id = NEW.id
BEGIN
    SELECT RAISE(
        ABORT,
        'an exercise cannot be its own parent'
    );
END;
