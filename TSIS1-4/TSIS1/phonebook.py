"""
phonebook.py  –  PhoneBook Extended Console Application  (TSIS 1)
=================================================================
New features over Practice 7 / 8:
  • Extended schema  (phones table, groups, email, birthday)
  • Filter by group
  • Search by email (partial)
  • Sort results by name / birthday / date added
  • Paginated navigation (next / prev / quit)
  • Export all contacts to JSON
  • Import contacts from JSON (with skip / overwrite on duplicate)
  • Extended CSV import (email, birthday, group, phone type)
  • Stored procedure  add_phone
  • Stored procedure  move_to_group
  • DB function       search_contacts  (name + email + phones)

Run:  python phonebook.py
"""

import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

import psycopg2

from config import DB_CONFIG, PAGE_SIZE
from connect import get_connection, get_cursor

# Helpers

def _date_serial(obj):
    """JSON serialiser for date / datetime objects."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")


def ask(prompt: str, default: str = "") -> str:
    """Prompt the user and return stripped input (or default on blank)."""
    val = input(prompt).strip()
    return val if val else default


def confirm(prompt: str) -> bool:
    return ask(f"{prompt} [y/N]: ").lower() == "y"


def print_contact_row(row: dict):
    """Pretty-print a single contact dict."""
    phones = row.get("phones_list") or row.get("phones") or "—"
    print(
        f"  [{row.get('contact_id', row.get('id', '?'))}] "
        f"{row.get('first_name', '')} {row.get('last_name', '')} | "
        f"Email: {row.get('email') or '—'} | "
        f"Birthday: {row.get('birthday') or '—'} | "
        f"Group: {row.get('group_name') or '—'} | "
        f"Phones: {phones}"
    )


# 3.1  Schema bootstrap  (apply schema.sql + procedures.sql on first run)

def apply_sql_file(conn, path: str):
    """Execute every statement in a .sql file."""
    sql = Path(path).read_text()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"  Applied {path}")


def bootstrap_schema():
    """Run schema.sql and procedures.sql to set up / migrate the DB."""
    try:
        conn = get_connection()
        print("Applying schema migrations …")
        apply_sql_file(conn, "schema.sql")
        apply_sql_file(conn, "procedures.sql")
        conn.close()
        print("Schema ready.\n")
    except Exception as exc:
        print(f"[ERROR] Could not apply schema: {exc}")
        sys.exit(1)


# 3.2  Advanced Console Search & Filter

def _fetch_groups(conn) -> list[dict]:
    with get_cursor(conn) as cur:
        cur.execute("SELECT id, name FROM groups ORDER BY name;")
        return cur.fetchall()


def filter_by_group(conn):
    """Show contacts belonging to a user-selected group, with sort & paging."""
    groups = _fetch_groups(conn)
    if not groups:
        print("No groups found.")
        return

    print("\nAvailable groups:")
    for g in groups:
        print(f"  {g['id']}. {g['name']}")

    group_input = ask("Enter group name or id: ")
    sort_field  = _ask_sort_field()

    # Build query
    order_clause = _sort_to_sql(sort_field)
    query = f"""
        SELECT c.id AS contact_id, c.first_name, c.last_name,
               c.email, c.birthday, g.name AS group_name,
               STRING_AGG(p.phone || ' (' || p.type || ')', ', ') AS phones_list
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones p ON p.contact_id = c.id
        WHERE g.name ILIKE %s OR g.id::TEXT = %s
        GROUP BY c.id, c.first_name, c.last_name,
                 c.email, c.birthday, g.name
        ORDER BY {order_clause};
    """

    with get_cursor(conn) as cur:
        cur.execute(query, (f"%{group_input}%", group_input))
        rows = cur.fetchall()

    if not rows:
        print("No contacts found for that group.")
        return

    _display_pages(rows)


def search_by_email(conn):
    """Partial email search."""
    term = ask("Email fragment to search: ")
    if not term:
        return

    sort_field = _ask_sort_field()
    order_clause = _sort_to_sql(sort_field)

    query = f"""
        SELECT c.id AS contact_id, c.first_name, c.last_name,
               c.email, c.birthday, g.name AS group_name,
               STRING_AGG(p.phone || ' (' || p.type || ')', ', ') AS phones_list
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones p ON p.contact_id = c.id
        WHERE c.email ILIKE %s
        GROUP BY c.id, c.first_name, c.last_name,
                 c.email, c.birthday, g.name
        ORDER BY {order_clause};
    """

    with get_cursor(conn) as cur:
        cur.execute(query, (f"%{term}%",))
        rows = cur.fetchall()

    if not rows:
        print("No contacts found.")
        return

    _display_pages(rows)


def search_all_fields(conn):
    """Full search via the DB function: name, email, all phones."""
    term = ask("Search (name / email / phone): ")
    if not term:
        return

    with get_cursor(conn) as cur:
        cur.execute("SELECT * FROM search_contacts(%s);", (term,))
        rows = cur.fetchall()

    if not rows:
        print("No contacts found.")
        return

    _display_pages(rows)


def _ask_sort_field() -> str:
    print("Sort by: [1] Name  [2] Birthday  [3] Date added")
    choice = ask("Choice [1]: ", "1")
    return {"1": "name", "2": "birthday", "3": "date"}.get(choice, "name")


def _sort_to_sql(field: str) -> str:
    return {
        "name":     "c.last_name, c.first_name",
        "birthday": "c.birthday NULLS LAST",
        "date":     "c.id",          # id is chronological (SERIAL)
    }.get(field, "c.last_name, c.first_name")


def _display_pages(rows: list):
    """Console pager: navigate a list of contact dicts with next/prev/quit."""
    total   = len(rows)
    page    = 0
    per_page = PAGE_SIZE

    while True:
        start = page * per_page
        end   = min(start + per_page, total)
        print(f"\n── Page {page + 1} ({start + 1}–{end} of {total}) ─────────")
        for row in rows[start:end]:
            print_contact_row(row)

        nav_opts = []
        if start > 0:
            nav_opts.append("[P]rev")
        if end < total:
            nav_opts.append("[N]ext")
        nav_opts.append("[Q]uit")

        choice = ask(f"\n{' / '.join(nav_opts)}: ").lower()
        if choice == "n" and end < total:
            page += 1
        elif choice == "p" and start > 0:
            page -= 1
        else:
            break


# 3.3  Import / Export

def export_to_json(conn):
    """Write all contacts (with phones and group) to a .json file."""
    query = """
        SELECT c.id, c.first_name, c.last_name, c.email,
               c.birthday, g.name AS group_name,
               JSON_AGG(
                   JSON_BUILD_OBJECT('phone', p.phone, 'type', p.type)
                   ORDER BY p.id
               ) FILTER (WHERE p.id IS NOT NULL) AS phones
        FROM contacts c
        LEFT JOIN groups  g ON g.id = c.group_id
        LEFT JOIN phones  p ON p.contact_id = c.id
        GROUP BY c.id, c.first_name, c.last_name,
                 c.email, c.birthday, g.name
        ORDER BY c.last_name, c.first_name;
    """

    with get_cursor(conn) as cur:
        cur.execute(query)
        rows = [dict(r) for r in cur.fetchall()]

    filepath = ask("Export filename [contacts.json]: ", "contacts.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, default=_date_serial, ensure_ascii=False)

    print(f"Exported {len(rows)} contacts to '{filepath}'.")


def import_from_json(conn):
    """
    Import contacts from a JSON file.
    On duplicate (same first + last name) ask: skip or overwrite.
    """
    filepath = ask("JSON file to import [contacts.json]: ", "contacts.json")
    if not Path(filepath).exists():
        print(f"File '{filepath}' not found.")
        return

    with open(filepath, encoding="utf-8") as f:
        records = json.load(f)

    inserted = skipped = overwritten = 0

    for rec in records:
        fname = rec.get("first_name", "").strip()
        lname = rec.get("last_name",  "").strip()
        if not fname and not lname:
            continue

        with get_cursor(conn) as cur:
            # Check for duplicate
            cur.execute(
                "SELECT id FROM contacts "
                "WHERE LOWER(first_name)=LOWER(%s) AND LOWER(last_name)=LOWER(%s);",
                (fname, lname),
            )
            existing = cur.fetchone()

        if existing:
            print(f"  Duplicate: {fname} {lname}")
            action = ask("  [S]kip / [O]verwrite? [S]: ", "s").lower()
            if action != "o":
                skipped += 1
                continue
            # Overwrite: delete old record (phones cascade)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM contacts WHERE id = %s;", (existing["id"],))
            conn.commit()
            overwritten += 1

        _insert_contact_record(conn, rec)
        inserted += 1

    print(f"Import complete: {inserted} inserted, {overwritten} overwritten, {skipped} skipped.")


def _insert_contact_record(conn, rec: dict):
    """Insert a single contact dict (from JSON) into the DB."""
    group_id = _resolve_group(conn, rec.get("group_name"))

    # Parse birthday safely
    birthday = None
    if rec.get("birthday"):
        try:
            birthday = date.fromisoformat(str(rec["birthday"])[:10])
        except ValueError:
            pass

    with get_cursor(conn) as cur:
        cur.execute(
            """INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
               VALUES (%s, %s, %s, %s, %s) RETURNING id;""",
            (rec.get("first_name"), rec.get("last_name"),
             rec.get("email"), birthday, group_id),
        )
        contact_id = cur.fetchone()["id"]

    conn.commit()

    # Insert phones
    phones = rec.get("phones") or []
    for ph in phones:
        if isinstance(ph, dict):
            _add_phone_direct(conn, contact_id, ph.get("phone", ""), ph.get("type", "mobile"))
        elif isinstance(ph, str) and ph.strip():
            _add_phone_direct(conn, contact_id, ph.strip(), "mobile")


def _add_phone_direct(conn, contact_id: int, phone: str, ph_type: str):
    """Low-level phone insert (bypasses the stored procedure)."""
    valid_types = {"home", "work", "mobile"}
    ph_type = ph_type if ph_type in valid_types else "mobile"
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s);",
            (contact_id, phone, ph_type),
        )
    conn.commit()


def import_from_csv(conn):
    """
    Extended CSV importer that handles:
      first_name, last_name, email, birthday, group, phone, phone_type
    Columns are optional; missing ones are silently skipped.
    """
    filepath = ask("CSV file to import [contacts.csv]: ", "contacts.csv")
    if not Path(filepath).exists():
        print(f"File '{filepath}' not found.")
        return

    inserted = errors = 0
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fname = row.get("first_name", "").strip()
            lname = row.get("last_name",  "").strip()
            if not fname and not lname:
                continue
            try:
                _insert_contact_record(conn, {
                    "first_name":  fname,
                    "last_name":   lname,
                    "email":       row.get("email", "").strip() or None,
                    "birthday":    row.get("birthday", "").strip() or None,
                    "group_name":  row.get("group",  "").strip() or None,
                    "phones": [{
                        "phone": row.get("phone", "").strip(),
                        "type":  row.get("phone_type", "mobile").strip() or "mobile",
                    }] if row.get("phone", "").strip() else [],
                })
                inserted += 1
            except Exception as exc:
                print(f"  [WARN] Row skipped ({fname} {lname}): {exc}")
                conn.rollback()
                errors += 1

    print(f"CSV import complete: {inserted} inserted, {errors} errors.")


# 3.4  Stored Procedure wrappers

def _resolve_group(conn, group_name: str | None) -> int | None:
    """Return group id for the given name (case-insensitive), or None."""
    if not group_name:
        return None
    with get_cursor(conn) as cur:
        cur.execute("SELECT id FROM groups WHERE LOWER(name)=LOWER(%s);", (group_name,))
        row = cur.fetchone()
        return row["id"] if row else None


def call_add_phone(conn):
    """Console wrapper for the add_phone stored procedure."""
    contact_name = ask("Contact full name: ")
    phone        = ask("Phone number: ")
    ph_type      = ask("Type [mobile/home/work] (default mobile): ", "mobile").lower()

    try:
        with conn.cursor() as cur:
            cur.execute("CALL add_phone(%s, %s, %s);", (contact_name, phone, ph_type))
        conn.commit()
        print("Phone added successfully.")
    except psycopg2.Error as exc:
        conn.rollback()
        print(f"[ERROR] {exc.pgerror or exc}")


def call_move_to_group(conn):
    """Console wrapper for the move_to_group stored procedure."""
    contact_name = ask("Contact full name: ")
    group_name   = ask("Target group name: ")

    try:
        with conn.cursor() as cur:
            cur.execute("CALL move_to_group(%s, %s);", (contact_name, group_name))
        conn.commit()
        print("Contact moved successfully.")
    except psycopg2.Error as exc:
        conn.rollback()
        print(f"[ERROR] {exc.pgerror or exc}")


# Main menu

MENU = """
╔══════════════════════════════════════════════╗
║         PhoneBook Extended  –  TSIS 1        ║
╠══════════════════════════════════════════════╣
║  Search & Filter                             ║
║  1. Search (name / email / phone)            ║
║  2. Filter by group                          ║
║  3. Search by email                          ║
║                                              ║
║  Phone / Group Management                   ║
║  4. Add phone to contact                     ║
║  5. Move contact to group                    ║
║                                              ║
║  Import / Export                             ║
║  6. Export contacts to JSON                  ║
║  7. Import contacts from JSON                ║
║  8. Import contacts from CSV (extended)      ║
║                                              ║
║  0. Exit                                     ║
╚══════════════════════════════════════════════╝
"""


def main():
    bootstrap_schema()

    try:
        conn = get_connection()
    except psycopg2.Error as exc:
        print(f"[ERROR] Cannot connect to database: {exc}")
        sys.exit(1)

    print("Connected to database.")

    actions = {
        "1": search_all_fields,
        "2": filter_by_group,
        "3": search_by_email,
        "4": call_add_phone,
        "5": call_move_to_group,
        "6": export_to_json,
        "7": import_from_json,
        "8": import_from_csv,
    }

    while True:
        print(MENU)
        choice = ask("Choice: ")

        if choice == "0":
            print("Goodbye.")
            break
        elif choice in actions:
            try:
                actions[choice](conn)
            except psycopg2.Error as exc:
                conn.rollback()
                print(f"[DB ERROR] {exc.pgerror or exc}")
            except KeyboardInterrupt:
                print("\n(cancelled)")
        else:
            print("Invalid choice. Please try again.")

    conn.close()


if __name__ == "__main__":
    main()
