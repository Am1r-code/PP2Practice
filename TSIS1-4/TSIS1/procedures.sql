CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR DEFAULT 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    -- Validate phone type
    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type "%". Must be home, work, or mobile.', p_type;
    END IF;

    -- Resolve contact id (case-insensitive match on first + last name combined)
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE LOWER(first_name || ' ' || last_name) = LOWER(p_contact_name)
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    -- Insert the new phone record
    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);

    RAISE NOTICE 'Phone % (%) added to contact "%".', p_phone, p_type, p_contact_name;
END;
$$;

CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id   INTEGER;
BEGIN
    -- Resolve (or create) the group
    SELECT id INTO v_group_id FROM groups WHERE LOWER(name) = LOWER(p_group_name);

    IF v_group_id IS NULL THEN
        INSERT INTO groups (name) VALUES (p_group_name) RETURNING id INTO v_group_id;
        RAISE NOTICE 'Created new group "%".', p_group_name;
    END IF;

    -- Resolve contact
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE LOWER(first_name || ' ' || last_name) = LOWER(p_contact_name)
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    -- Update the contact's group
    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;

    RAISE NOTICE 'Contact "%" moved to group "%".', p_contact_name, p_group_name;
END;
$$;


CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    contact_id  INTEGER,
    first_name  VARCHAR,
    last_name   VARCHAR,
    email       VARCHAR,
    birthday    DATE,
    group_name  VARCHAR,
    phones_list TEXT         -- comma-separated "number (type)" entries
)
LANGUAGE plpgsql AS $$
DECLARE
    v_pattern TEXT := '%' || LOWER(p_query) || '%';
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.first_name,
        c.last_name,
        c.email,
        c.birthday,
        g.name                        AS group_name,
        STRING_AGG(p.phone || ' (' || p.type || ')', ', '
                   ORDER BY p.type)   AS phones_list
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE
        -- name match (same as Practice 8 pattern search)
        LOWER(c.first_name)  LIKE v_pattern OR
        LOWER(c.last_name)   LIKE v_pattern OR
        -- email match (new)
        LOWER(c.email)       LIKE v_pattern OR
        -- phone match across all phones rows (new)
        c.id IN (
            SELECT ph.contact_id FROM phones ph
            WHERE LOWER(ph.phone) LIKE v_pattern
        )
    GROUP BY c.id, c.first_name, c.last_name, c.email, c.birthday, g.name
    ORDER BY c.last_name, c.first_name;
END;
$$;
