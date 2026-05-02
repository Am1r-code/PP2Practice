-- schema.sql
-- Extended PhoneBook schema for TSIS 1
-- Builds on top of the base contacts table from Practice 7/8.
-- Run this once to migrate the existing database.

-- ── 1. Groups table ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Seed default categories
INSERT INTO groups (name)
    VALUES ('Family'), ('Work'), ('Friend'), ('Other')
    ON CONFLICT (name) DO NOTHING;

-- ── 2. Extend contacts table ──────────────────────────────────────────────
-- Add new columns only if they do not already exist (idempotent migration).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'contacts' AND column_name = 'email'
    ) THEN
        ALTER TABLE contacts ADD COLUMN email VARCHAR(100);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'contacts' AND column_name = 'birthday'
    ) THEN
        ALTER TABLE contacts ADD COLUMN birthday DATE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'contacts' AND column_name = 'group_id'
    ) THEN
        ALTER TABLE contacts
            ADD COLUMN group_id INTEGER REFERENCES groups(id);
    END IF;
END;
$$;

-- ── 3. Phones table (1-to-many) ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER      NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20)  NOT NULL,
    type       VARCHAR(10)  NOT NULL DEFAULT 'mobile'
                            CHECK (type IN ('home', 'work', 'mobile'))
);

-- Index for fast contact look-up
CREATE INDEX IF NOT EXISTS idx_phones_contact_id ON phones(contact_id);
CREATE INDEX IF NOT EXISTS idx_contacts_group_id ON contacts(group_id);
