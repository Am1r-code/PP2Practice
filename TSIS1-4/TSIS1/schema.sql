CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

INSERT INTO groups (name)
    VALUES ('Family'), ('Work'), ('Friend'), ('Other')
    ON CONFLICT (name) DO NOTHING;

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

CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER      NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20)  NOT NULL,
    type       VARCHAR(10)  NOT NULL DEFAULT 'mobile'
                            CHECK (type IN ('home', 'work', 'mobile'))
);

CREATE INDEX IF NOT EXISTS idx_phones_contact_id ON phones(contact_id);
CREATE INDEX IF NOT EXISTS idx_contacts_group_id ON contacts(group_id);
