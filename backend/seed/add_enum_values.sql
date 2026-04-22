-- Add missing exercise type enum values to PostgreSQL
-- Run inside postgres container: docker exec math-platform-postgres-1 psql -U mathplatform -d mathplatform -c "\df" to verify

DO $$
BEGIN
    -- Add each value only if it doesn't already exist
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'bar_model' AND enumtypid = 'exercisetype'::regtype) THEN
        ALTER TYPE exercisetype ADD VALUE 'bar_model';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'word_problem' AND enumtypid = 'exercisetype'::regtype) THEN
        ALTER TYPE exercisetype ADD VALUE 'word_problem';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'true_false' AND enumtypid = 'exercisetype'::regtype) THEN
        ALTER TYPE exercisetype ADD VALUE 'true_false';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ordering' AND enumtypid = 'exercisetype'::regtype) THEN
        ALTER TYPE exercisetype ADD VALUE 'ordering';
    END IF;
END $$;
