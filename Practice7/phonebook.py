"""
phonebook.py
------------
Console-based PhoneBook application backed by PostgreSQL.

Features
--------
* Create the contacts table automatically on first run
* Insert a single contact via console input
* Import contacts in bulk from a CSV file
* Query contacts with various filters (by name, by phone prefix, or list all)
* Update a contact's first name or phone number
* Delete a contact by username (first+last name) or by phone number
"""

import csv
import sys

import psycopg2
from connect import get_connection


# ---------------------------------------------------------------------------
# Schema setup
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS contacts (
    id         SERIAL PRIMARY KEY,
    first_name VARCHAR(50)  NOT NULL,
    last_name  VARCHAR(50)  NOT NULL,
    phone      VARCHAR(20)  NOT NULL,
    created_at TIMESTAMP    DEFAULT NOW()
);
"""


def create_table(conn):
    """Create the contacts table if it does not already exist."""
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    print("[OK] Table 'contacts' is ready.")


# ---------------------------------------------------------------------------
# INSERT – single contact via console
# ---------------------------------------------------------------------------

def insert_contact(conn):
    """Prompt the user for contact details and insert one row."""
    print("\n--- Add a new contact ---")
    first_name = input("First name: ").strip()
    last_name  = input("Last name : ").strip()
    phone      = input("Phone     : ").strip()

    if not first_name or not phone:
        print("[WARN] First name and phone are required. Skipping.")
        return

    sql = "INSERT INTO contacts (first_name, last_name, phone) VALUES (%s, %s, %s);"
    with conn.cursor() as cur:
        cur.execute(sql, (first_name, last_name, phone))
    conn.commit()
    print(f"[OK] Contact '{first_name} {last_name}' added.")


# ---------------------------------------------------------------------------
# INSERT – bulk import from CSV
# ---------------------------------------------------------------------------

def import_from_csv(conn):
    """
    Import contacts from a CSV file.

    Expected columns: first_name, last_name, phone
    Rows that are missing required fields are skipped with a warning.
    """
    path = input("\nEnter path to CSV file [contacts.csv]: ").strip() or "contacts.csv"

    try:
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows   = list(reader)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}")
        return

    inserted = 0
    skipped  = 0

    with conn.cursor() as cur:
        for row in rows:
            first_name = row.get("first_name", "").strip()
            last_name  = row.get("last_name",  "").strip()
            phone      = row.get("phone",      "").strip()

            if not first_name or not phone:
                print(f"[WARN] Skipping incomplete row: {row}")
                skipped += 1
                continue

            cur.execute(
                "INSERT INTO contacts (first_name, last_name, phone) VALUES (%s, %s, %s);",
                (first_name, last_name, phone),
            )
            inserted += 1

    conn.commit()
    print(f"[OK] Imported {inserted} contacts ({skipped} skipped).")


# ---------------------------------------------------------------------------
# SELECT – query / search
# ---------------------------------------------------------------------------

def _print_contacts(rows):
    """Pretty-print a list of contact rows."""
    if not rows:
        print("  (no results)")
        return
    print(f"\n  {'ID':<5} {'First':<15} {'Last':<15} {'Phone':<20} {'Added'}")
    print("  " + "-" * 70)
    for row in rows:
        cid, first, last, phone, created = row
        print(f"  {cid:<5} {first:<15} {last:<15} {phone:<20} {created:%Y-%m-%d %H:%M}")


def query_contacts(conn):
    """Interactive submenu for searching contacts."""
    print("\n--- Query contacts ---")
    print("  1) List all")
    print("  2) Search by first or last name")
    print("  3) Search by phone prefix")
    choice = input("Choice: ").strip()

    sql_base = "SELECT id, first_name, last_name, phone, created_at FROM contacts"

    with conn.cursor() as cur:
        if choice == "1":
            cur.execute(sql_base + " ORDER BY last_name, first_name;")

        elif choice == "2":
            name = input("Enter name (or part of it): ").strip()
            cur.execute(
                sql_base + " WHERE first_name ILIKE %s OR last_name ILIKE %s ORDER BY last_name;",
                (f"%{name}%", f"%{name}%"),
            )

        elif choice == "3":
            prefix = input("Enter phone prefix: ").strip()
            cur.execute(
                sql_base + " WHERE phone LIKE %s ORDER BY phone;",
                (f"{prefix}%",),
            )

        else:
            print("[WARN] Invalid choice.")
            return

        rows = cur.fetchall()

    _print_contacts(rows)


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def update_contact(conn):
    """Update a contact's first name or phone number, looked up by ID."""
    query_contacts(conn)   # show current data so the user knows the IDs

    print("\n--- Update a contact ---")
    try:
        contact_id = int(input("Enter the ID of the contact to update: ").strip())
    except ValueError:
        print("[WARN] Invalid ID.")
        return

    print("  1) Update first name")
    print("  2) Update last name")
    print("  3) Update phone")
    field_choice = input("What to update: ").strip()

    if field_choice == "1":
        new_value = input("New first name: ").strip()
        column    = "first_name"
    elif field_choice == "2":
        new_value = input("New last name: ").strip()
        column    = "last_name"
    elif field_choice == "3":
        new_value = input("New phone: ").strip()
        column    = "phone"
    else:
        print("[WARN] Invalid choice.")
        return

    if not new_value:
        print("[WARN] Value cannot be empty.")
        return

    # Build the query safely using a whitelist for the column name
    sql = f"UPDATE contacts SET {column} = %s WHERE id = %s;"
    with conn.cursor() as cur:
        cur.execute(sql, (new_value, contact_id))
        updated = cur.rowcount
    conn.commit()

    if updated:
        print(f"[OK] Contact {contact_id} updated.")
    else:
        print(f"[WARN] No contact found with ID {contact_id}.")


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def delete_contact(conn):
    """Delete a contact by ID, by full name, or by phone number."""
    print("\n--- Delete a contact ---")
    print("  1) Delete by ID")
    print("  2) Delete by full name (first + last)")
    print("  3) Delete by phone number")
    choice = input("Choice: ").strip()

    with conn.cursor() as cur:
        if choice == "1":
            try:
                cid = int(input("Contact ID: ").strip())
            except ValueError:
                print("[WARN] Invalid ID.")
                return
            cur.execute("DELETE FROM contacts WHERE id = %s;", (cid,))

        elif choice == "2":
            first = input("First name: ").strip()
            last  = input("Last name : ").strip()
            cur.execute(
                "DELETE FROM contacts WHERE first_name ILIKE %s AND last_name ILIKE %s;",
                (first, last),
            )

        elif choice == "3":
            phone = input("Phone: ").strip()
            cur.execute("DELETE FROM contacts WHERE phone = %s;", (phone,))

        else:
            print("[WARN] Invalid choice.")
            return

        deleted = cur.rowcount

    conn.commit()
    print(f"[OK] {deleted} contact(s) deleted.")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

MENU = """
========================================
  PhoneBook – Main Menu
========================================
  1) Add contact (console)
  2) Import contacts from CSV
  3) Search / list contacts
  4) Update a contact
  5) Delete a contact
  0) Exit
----------------------------------------
"""


def main():
    try:
        conn = get_connection()
    except Exception:
        sys.exit(1)

    create_table(conn)

    while True:
        print(MENU)
        choice = input("Select an option: ").strip()

        if   choice == "1": insert_contact(conn)
        elif choice == "2": import_from_csv(conn)
        elif choice == "3": query_contacts(conn)
        elif choice == "4": update_contact(conn)
        elif choice == "5": delete_contact(conn)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("[WARN] Unknown option, please try again.")

    conn.close()


if __name__ == "__main__":
    main()
