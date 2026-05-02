"""
phonebook.py  (Practice 8)
--------------------------
Extends Practice 7 with PostgreSQL functions and stored procedures.

New features vs Practice 7
---------------------------
* Pattern search  – calls search_contacts_by_pattern(pattern)
* Upsert          – calls upsert_contact(first, last, phone)
* Bulk insert     – calls bulk_insert_contacts(names[], phones[])
                    then shows any invalid rows from the temp table
* Paginated list  – calls get_contacts_paginated(limit, offset)
                    with interactive next/prev navigation
* Delete via proc – calls delete_contact(value, mode)

Run functions.sql and procedures.sql against your DB before starting:
    psql -U postgres -d phonebook_db -f functions.sql
    psql -U postgres -d phonebook_db -f procedures.sql
"""

import sys
import psycopg2
from connect import get_connection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_contacts(rows):
    """Pretty-print rows returned from the DB."""
    if not rows:
        print("  (no results)")
        return
    print(f"\n  {'ID':<5} {'First':<15} {'Last':<15} {'Phone':<20} {'Added'}")
    print("  " + "-" * 70)
    for row in rows:
        cid, first, last, phone, created = row
        print(f"  {cid:<5} {first:<15} {last:<15} {phone:<20} {created:%Y-%m-%d %H:%M}")


# ---------------------------------------------------------------------------
# 1. Pattern search  (calls DB function)
# ---------------------------------------------------------------------------

def pattern_search(conn):
    """Search contacts by any part of name or phone using the DB function."""
    pattern = input("\nEnter search pattern: ").strip()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM search_contacts_by_pattern(%s);", (pattern,))
        rows = cur.fetchall()
    _print_contacts(rows)


# ---------------------------------------------------------------------------
# 2. Upsert  (calls DB procedure)
# ---------------------------------------------------------------------------

def upsert_contact(conn):
    """Insert a new contact or update phone if the name already exists."""
    print("\n--- Upsert contact ---")
    first = input("First name : ").strip()
    last  = input("Last name  : ").strip()
    phone = input("Phone      : ").strip()

    if not first or not phone:
        print("[WARN] First name and phone are required.")
        return

    with conn.cursor() as cur:
        cur.execute("CALL upsert_contact(%s, %s, %s);", (first, last, phone))
    conn.commit()
    print("[OK] Done (inserted or updated).")


# ---------------------------------------------------------------------------
# 3. Bulk insert  (calls DB procedure, then reads invalid_contacts temp table)
# ---------------------------------------------------------------------------

def bulk_insert(conn):
    """
    Collect multiple name/phone pairs from the console,
    call the bulk_insert_contacts procedure, then display any invalid rows.
    """
    print("\n--- Bulk insert contacts ---")
    print("Enter contacts as 'FirstName LastName,phone'. Type 'done' to finish.")

    names  = []
    phones = []

    while True:
        line = input("  Contact: ").strip()
        if line.lower() == "done":
            break
        if "," not in line:
            print("  [WARN] Format must be 'FirstName LastName,phone'. Try again.")
            continue
        name_part, phone_part = line.split(",", 1)
        names.append(name_part.strip())
        phones.append(phone_part.strip())

    if not names:
        print("[WARN] Nothing to insert.")
        return

    with conn.cursor() as cur:
        cur.execute("CALL bulk_insert_contacts(%s, %s);", (names, phones))
        # Read invalid rows from the temp table created by the procedure
        cur.execute("SELECT name, phone, reason FROM invalid_contacts;")
        invalid = cur.fetchall()

    conn.commit()

    print(f"[OK] Bulk insert complete. {len(names) - len(invalid)} rows inserted/updated.")

    if invalid:
        print(f"\n  [!] {len(invalid)} invalid row(s) were skipped:")
        print(f"  {'Name':<25} {'Phone':<20} Reason")
        print("  " + "-" * 60)
        for name, phone, reason in invalid:
            print(f"  {name:<25} {phone:<20} {reason}")


# ---------------------------------------------------------------------------
# 4. Paginated list  (calls DB function with LIMIT / OFFSET)
# ---------------------------------------------------------------------------

PAGE_SIZE = 5


def paginated_list(conn):
    """Navigate through contacts page by page."""
    offset = 0

    while True:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM get_contacts_paginated(%s, %s);",
                (PAGE_SIZE, offset),
            )
            rows = cur.fetchall()

        print(f"\n--- Contacts (page {offset // PAGE_SIZE + 1}) ---")
        _print_contacts(rows)

        nav = input("\n[n]ext  [p]rev  [q]uit: ").strip().lower()
        if nav == "n":
            if len(rows) < PAGE_SIZE:
                print("  (already on last page)")
            else:
                offset += PAGE_SIZE
        elif nav == "p":
            offset = max(0, offset - PAGE_SIZE)
        elif nav == "q":
            break


# ---------------------------------------------------------------------------
# 5. Delete via stored procedure
# ---------------------------------------------------------------------------

def delete_contact(conn):
    """Delete a contact by name or phone using the DB procedure."""
    print("\n--- Delete contact ---")
    print("  1) By full name (First Last)")
    print("  2) By phone number")
    choice = input("Choice: ").strip()

    if choice == "1":
        value = input("Full name (First Last): ").strip()
        mode  = "name"
    elif choice == "2":
        value = input("Phone: ").strip()
        mode  = "phone"
    else:
        print("[WARN] Invalid choice.")
        return

    with conn.cursor() as cur:
        cur.execute("CALL delete_contact(%s, %s);", (value, mode))
    conn.commit()
    print("[OK] Delete procedure executed.")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

MENU = """
========================================
  PhoneBook – Practice 8  (Functions & Procedures)
========================================
  1) Pattern search
  2) Upsert contact (insert or update)
  3) Bulk insert contacts
  4) Browse contacts (paginated)
  5) Delete contact
  0) Exit
----------------------------------------
"""


def main():
    try:
        conn = get_connection()
    except Exception:
        sys.exit(1)

    while True:
        print(MENU)
        choice = input("Select an option: ").strip()

        if   choice == "1": pattern_search(conn)
        elif choice == "2": upsert_contact(conn)
        elif choice == "3": bulk_insert(conn)
        elif choice == "4": paginated_list(conn)
        elif choice == "5": delete_contact(conn)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("[WARN] Unknown option, please try again.")

    conn.close()


if __name__ == "__main__":
    main()
