-- procedures.sql
-- PostgreSQL stored procedures for the PhoneBook application

-- 1. Upsert: insert a contact, or update phone if name already exists
CREATE OR REPLACE PROCEDURE upsert_contact(p_first_name VARCHAR, p_last_name VARCHAR, p_phone VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM contacts
        WHERE first_name ILIKE p_first_name AND last_name ILIKE p_last_name
    ) THEN
        UPDATE contacts
        SET phone = p_phone
        WHERE first_name ILIKE p_first_name AND last_name ILIKE p_last_name;
        RAISE NOTICE 'Updated phone for % %', p_first_name, p_last_name;
    ELSE
        INSERT INTO contacts (first_name, last_name, phone)
        VALUES (p_first_name, p_last_name, p_phone);
        RAISE NOTICE 'Inserted new contact % %', p_first_name, p_last_name;
    END IF;
END;
$$;


-- 2. Bulk insert from a list; validates phone format; returns invalid entries
--    Invalid rows are collected into a temp table "invalid_contacts"
--    which the Python caller can query after the CALL.
CREATE OR REPLACE PROCEDURE bulk_insert_contacts(
    p_names  TEXT[],   -- array of 'FirstName LastName' strings
    p_phones TEXT[]    -- matching array of phone strings
)
LANGUAGE plpgsql AS $$
DECLARE
    i         INT;
    v_first   VARCHAR;
    v_last    VARCHAR;
    v_phone   TEXT;
    v_parts   TEXT[];
BEGIN
    -- Temporary table to collect invalid rows (visible in the same session)
    DROP TABLE IF EXISTS invalid_contacts;
    CREATE TEMP TABLE invalid_contacts (
        name  TEXT,
        phone TEXT,
        reason TEXT
    );

    IF array_length(p_names, 1) IS NULL THEN
        RAISE NOTICE 'Empty input arrays – nothing to insert.';
        RETURN;
    END IF;

    FOR i IN 1 .. array_length(p_names, 1) LOOP
        v_phone := trim(p_phones[i]);
        v_parts := string_to_array(trim(p_names[i]), ' ');

        -- Validate: phone must contain only digits, spaces, +, -, ()
        IF v_phone !~ '^[0-9 \+\-\(\)]+$' OR length(v_phone) < 7 THEN
            INSERT INTO invalid_contacts VALUES (p_names[i], v_phone, 'invalid phone format');
            CONTINUE;
        END IF;

        -- Parse first / last name
        v_first := v_parts[1];
        v_last  := COALESCE(v_parts[2], '');

        -- Upsert
        IF EXISTS (
            SELECT 1 FROM contacts
            WHERE first_name ILIKE v_first AND last_name ILIKE v_last
        ) THEN
            UPDATE contacts SET phone = v_phone
            WHERE first_name ILIKE v_first AND last_name ILIKE v_last;
        ELSE
            INSERT INTO contacts (first_name, last_name, phone)
            VALUES (v_first, v_last, v_phone);
        END IF;
    END LOOP;
END;
$$;


-- 3. Delete a contact by username (first+last) or by phone
CREATE OR REPLACE PROCEDURE delete_contact(p_value VARCHAR, p_mode VARCHAR)
-- p_mode: 'name' or 'phone'
LANGUAGE plpgsql AS $$
DECLARE
    v_parts TEXT[];
    v_deleted INT;
BEGIN
    IF p_mode = 'phone' THEN
        DELETE FROM contacts WHERE phone = p_value;
        GET DIAGNOSTICS v_deleted = ROW_COUNT;
        RAISE NOTICE 'Deleted % row(s) by phone.', v_deleted;

    ELSIF p_mode = 'name' THEN
        v_parts := string_to_array(trim(p_value), ' ');
        DELETE FROM contacts
        WHERE first_name ILIKE v_parts[1]
          AND last_name  ILIKE COALESCE(v_parts[2], '');
        GET DIAGNOSTICS v_deleted = ROW_COUNT;
        RAISE NOTICE 'Deleted % row(s) by name.', v_deleted;

    ELSE
        RAISE EXCEPTION 'Unknown mode: %. Use ''name'' or ''phone''.', p_mode;
    END IF;
END;
$$;
