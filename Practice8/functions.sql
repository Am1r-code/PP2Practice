-- functions.sql
-- PostgreSQL functions for the PhoneBook application

-- 1. Search contacts by pattern (name or phone)
CREATE OR REPLACE FUNCTION search_contacts_by_pattern(p_pattern TEXT)
RETURNS TABLE(id INT, first_name VARCHAR, last_name VARCHAR, phone VARCHAR, created_at TIMESTAMP) AS $$
BEGIN
    RETURN QUERY
        SELECT c.id, c.first_name, c.last_name, c.phone, c.created_at
        FROM contacts c
        WHERE c.first_name ILIKE '%' || p_pattern || '%'
           OR c.last_name  ILIKE '%' || p_pattern || '%'
           OR c.phone      ILIKE '%' || p_pattern || '%'
        ORDER BY c.last_name, c.first_name;
END;
$$ LANGUAGE plpgsql;


-- 2. Paginated query (returns one page of contacts)
CREATE OR REPLACE FUNCTION get_contacts_paginated(p_limit INT, p_offset INT)
RETURNS TABLE(id INT, first_name VARCHAR, last_name VARCHAR, phone VARCHAR, created_at TIMESTAMP) AS $$
BEGIN
    RETURN QUERY
        SELECT c.id, c.first_name, c.last_name, c.phone, c.created_at
        FROM contacts c
        ORDER BY c.last_name, c.first_name
        LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;
