import sqlite3
from pathlib import Path
import pandas as pd
from utils.paths import user_data_dir

DB_PATH = user_data_dir() / "actuarial_pricing.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        policy_name TEXT NOT NULL,
        exposure REAL NOT NULL,
        vehicle_year INTEGER NOT NULL,
        pricing_year INTEGER NOT NULL,
        policy_year INTEGER NOT NULL,
        veh_age REAL NOT NULL,
        driv_age REAL NOT NULL,
        bonus_malus REAL NOT NULL,
        density REAL NOT NULL,
        veh_gas TEXT NOT NULL,
        veh_brand TEXT NOT NULL,
        region TEXT NOT NULL,
        area TEXT NOT NULL,
        no_accident_years INTEGER NOT NULL DEFAULT 0,
        accident_count_recent INTEGER NOT NULL DEFAULT 0,
        source_policy_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
        FOREIGN KEY (source_policy_id) REFERENCES policies(id) ON DELETE SET NULL
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id INTEGER NOT NULL,
        expected_claims REAL NOT NULL,
        expected_severity REAL NOT NULL,
        expected_loss REAL NOT NULL,
        inflated_loss REAL NOT NULL,
        technical_premium REAL NOT NULL,
        final_premium REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulated_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_name TEXT NOT NULL,
        pricing_year INTEGER NOT NULL,
        target_policy_count INTEGER NOT NULL,
        created_customer_count INTEGER NOT NULL DEFAULT 0,
        created_policy_count INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulated_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id INTEGER NOT NULL,
        simulation_year INTEGER NOT NULL,
        had_claim INTEGER NOT NULL,
        claim_count INTEGER NOT NULL,
        total_claim_amount REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_year INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        source_created_at TIMESTAMP,
        snapshot_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policy_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_year INTEGER NOT NULL,
        policy_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        policy_name TEXT NOT NULL,
        exposure REAL NOT NULL,
        vehicle_year INTEGER NOT NULL,
        pricing_year INTEGER NOT NULL,
        policy_year INTEGER NOT NULL,
        veh_age REAL NOT NULL,
        driv_age REAL NOT NULL,
        bonus_malus REAL NOT NULL,
        density REAL NOT NULL,
        veh_gas TEXT NOT NULL,
        veh_brand TEXT NOT NULL,
        region TEXT NOT NULL,
        area TEXT NOT NULL,
        no_accident_years INTEGER NOT NULL,
        accident_count_recent INTEGER NOT NULL,
        source_policy_id INTEGER,
        source_created_at TIMESTAMP,
        snapshot_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

    conn.commit()
    conn.close()


def create_customer(full_name, email, phone):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO customers (full_name, email, phone)
        VALUES (?, ?, ?)
    """, (full_name, email, phone))

    customer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return customer_id


def get_all_customers():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, full_name, email, phone, created_at
        FROM customers
        ORDER BY full_name ASC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def create_policy(
    customer_id,
    policy_name,
    exposure,
    vehicle_year,
    pricing_year,
    policy_year,
    veh_age,
    driv_age,
    bonus_malus,
    density,
    veh_gas,
    veh_brand,
    region,
    area,
    no_accident_years,
    accident_count_recent,
    source_policy_id=None
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO policies (
            customer_id, policy_name, exposure, vehicle_year, pricing_year, policy_year, veh_age,
            driv_age, bonus_malus, density, veh_gas, veh_brand, region, area,
            no_accident_years, accident_count_recent, source_policy_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        customer_id, policy_name, exposure, vehicle_year, pricing_year, policy_year, veh_age,
        driv_age, bonus_malus, density, veh_gas, veh_brand, region, area,
        no_accident_years, accident_count_recent, source_policy_id
    ))

    policy_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return policy_id


def get_all_policies():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
                   SELECT p.id,
                          p.customer_id,
                          c.full_name,
                          p.policy_name,
                          p.exposure,
                          p.vehicle_year,
                          p.pricing_year,
                          p.veh_age,
                          p.driv_age,
                          p.bonus_malus,
                          p.density,
                          p.veh_gas,
                          p.veh_brand,
                          p.region,
                          p.area,
                          p.no_accident_years,
                          p.accident_count_recent,
                          p.created_at
                   FROM policies p
                            JOIN customers c ON p.customer_id = c.id
                   ORDER BY p.id DESC
                   """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_policy_by_id(policy_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.id,
            p.customer_id,
            c.full_name,
            p.policy_name,
            p.exposure,
            p.vehicle_year,
            p.pricing_year,
            p.veh_age,
            p.driv_age,
            p.bonus_malus,
            p.density,
            p.veh_gas,
            p.veh_brand,
            p.region,
            p.area,
            p.no_accident_years,
            p.accident_count_recent,
            p.created_at
        FROM policies p
        JOIN customers c ON p.customer_id = c.id
        WHERE p.id = ?
    """, (policy_id,))

    row = cursor.fetchone()
    conn.close()
    return row


def create_quote(
    policy_id,
    expected_claims,
    expected_severity,
    expected_loss,
    inflated_loss,
    technical_premium,
    final_premium
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quotes (
            policy_id, expected_claims, expected_severity,
            expected_loss, inflated_loss, technical_premium, final_premium
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        policy_id,
        expected_claims,
        expected_severity,
        expected_loss,
        inflated_loss,
        technical_premium,
        final_premium
    ))

    conn.commit()
    conn.close()


def get_all_quotes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            q.id,
            q.policy_id,
            c.full_name,
            p.policy_name,
            q.expected_claims,
            q.expected_severity,
            q.expected_loss,
            q.inflated_loss,
            q.technical_premium,
            q.final_premium,
            q.created_at
        FROM quotes q
        JOIN policies p ON q.policy_id = p.id
        JOIN customers c ON p.customer_id = c.id
        ORDER BY q.created_at DESC, q.id DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

def search_customers(search_text):
    conn = get_connection()
    cursor = conn.cursor()

    like_value = f"%{search_text}%"

    cursor.execute("""
        SELECT id, full_name, email, phone, created_at
        FROM customers
        WHERE full_name LIKE ?
           OR email LIKE ?
           OR phone LIKE ?
        ORDER BY full_name ASC
    """, (like_value, like_value, like_value))

    rows = cursor.fetchall()
    conn.close()
    return rows


def search_policies(search_text):
    conn = get_connection()
    cursor = conn.cursor()

    like_value = f"%{search_text}%"

    cursor.execute("""
        SELECT
            p.id,
            p.customer_id,
            c.full_name,
            p.policy_name,
            p.exposure,
            p.veh_age,
            p.driv_age,
            p.bonus_malus,
            p.density,
            p.veh_gas,
            p.veh_brand,
            p.region,
            p.area,
            p.created_at
        FROM policies p
        JOIN customers c ON p.customer_id = c.id
        WHERE c.full_name LIKE ?
           OR p.policy_name LIKE ?
           OR p.veh_brand LIKE ?
           OR p.region LIKE ?
        ORDER BY p.id DESC
    """, (like_value, like_value, like_value, like_value))

    rows = cursor.fetchall()
    conn.close()
    return rows


def search_quotes(search_text):
    conn = get_connection()
    cursor = conn.cursor()

    like_value = f"%{search_text}%"

    cursor.execute("""
        SELECT
            q.id,
            q.policy_id,
            c.full_name,
            p.policy_name,
            q.expected_claims,
            q.expected_severity,
            q.premium,
            q.created_at
        FROM quotes q
        JOIN policies p ON q.policy_id = p.id
        JOIN customers c ON p.customer_id = c.id
        WHERE c.full_name LIKE ?
           OR p.policy_name LIKE ?
        ORDER BY q.created_at DESC, q.id DESC
    """, (like_value, like_value))

    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_customer(customer_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))

    conn.commit()
    conn.close()


def delete_policy(policy_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM policies WHERE id = ?", (policy_id,))

    conn.commit()
    conn.close()


def delete_quote(quote_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))

    conn.commit()
    conn.close()

def update_customer(customer_id, full_name, email, phone):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE customers
        SET full_name = ?, email = ?, phone = ?
        WHERE id = ?
    """, (full_name, email, phone, customer_id))

    conn.commit()
    conn.close()


def update_policy(
    policy_id,
    customer_id,
    policy_name,
    exposure,
    vehicle_year,
    pricing_year,
    veh_age,
    driv_age,
    bonus_malus,
    density,
    veh_gas,
    veh_brand,
    region,
    area,
    no_accident_years,
    accident_count_recent
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE policies
        SET customer_id = ?, policy_name = ?, exposure = ?, vehicle_year = ?, pricing_year = ?,
            policy_year = ?, veh_age = ?, driv_age = ?, bonus_malus = ?, density = ?, veh_gas = ?,
            veh_brand = ?, region = ?, area = ?, no_accident_years = ?, accident_count_recent = ?
        WHERE id = ?
    """, (
        customer_id, policy_name, exposure, vehicle_year, pricing_year, pricing_year,
        veh_age, driv_age, bonus_malus, density, veh_gas,
        veh_brand, region, area, no_accident_years, accident_count_recent,
        policy_id
    ))

    conn.commit()
    conn.close()

def create_simulation_batch(batch_name, pricing_year, target_policy_count):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO simulated_batches (
            batch_name, pricing_year, target_policy_count
        )
        VALUES (?, ?, ?)
    """, (batch_name, pricing_year, target_policy_count))

    batch_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return batch_id


def update_simulation_batch_counts(batch_id, created_customer_count, created_policy_count):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE simulated_batches
        SET created_customer_count = ?, created_policy_count = ?
        WHERE id = ?
    """, (created_customer_count, created_policy_count, batch_id))

    conn.commit()
    conn.close()


def create_simulated_claim(policy_id, simulation_year, had_claim, claim_count, total_claim_amount):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO simulated_claims (
            policy_id, simulation_year, had_claim, claim_count, total_claim_amount
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        policy_id,
        simulation_year,
        had_claim,
        claim_count,
        total_claim_amount
    ))

    conn.commit()
    conn.close()


def get_all_policies_raw():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            customer_id,
            policy_name,
            exposure,
            vehicle_year,
            pricing_year,
            policy_year,
            veh_age,
            driv_age,
            bonus_malus,
            density,
            veh_gas,
            veh_brand,
            region,
            area,
            no_accident_years,
            accident_count_recent,
            source_policy_id
        FROM policies
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_simulated_claims():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            policy_id,
            simulation_year,
            had_claim,
            claim_count,
            total_claim_amount,
            created_at
        FROM simulated_claims
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

def get_latest_policies_for_roll_forward(conn=None):
    owns_connection = conn is None
    if owns_connection:
        conn = get_connection()

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            customer_id,
            policy_name,
            exposure,
            vehicle_year,
            pricing_year,
            policy_year,
            veh_age,
            driv_age,
            bonus_malus,
            density,
            veh_gas,
            veh_brand,
            region,
            area,
            no_accident_years,
            accident_count_recent
        FROM policies
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()

    if owns_connection:
        conn.close()

    return rows


def get_simulated_claims_for_year(simulation_year: int, conn=None):
    owns_connection = conn is None
    if owns_connection:
        conn = get_connection()

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            policy_id,
            simulation_year,
            had_claim,
            claim_count,
            total_claim_amount
        FROM simulated_claims
        WHERE simulation_year = ?
        ORDER BY policy_id ASC
    """, (simulation_year,))
    rows = cursor.fetchall()

    if owns_connection:
        conn.close()

    return rows


def snapshot_exists_for_year(snapshot_year: int, conn=None) -> bool:
    owns_connection = conn is None
    if owns_connection:
        conn = get_connection()

    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1
        FROM policy_snapshots
        WHERE snapshot_year = ?
        LIMIT 1
    """, (snapshot_year,))
    exists = cursor.fetchone() is not None

    if owns_connection:
        conn.close()

    return exists


def snapshot_customers_for_year(snapshot_year: int, conn):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO customer_snapshots (
            snapshot_year,
            customer_id,
            full_name,
            email,
            phone,
            source_created_at
        )
        SELECT
            ?,
            id,
            full_name,
            email,
            phone,
            created_at
        FROM customers
    """, (snapshot_year,))
    return cursor.rowcount


def snapshot_policies_for_year(snapshot_year: int, conn):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO policy_snapshots (
            snapshot_year,
            policy_id,
            customer_id,
            policy_name,
            exposure,
            vehicle_year,
            pricing_year,
            policy_year,
            veh_age,
            driv_age,
            bonus_malus,
            density,
            veh_gas,
            veh_brand,
            region,
            area,
            no_accident_years,
            accident_count_recent,
            source_policy_id,
            source_created_at
        )
        SELECT
            ?,
            id,
            customer_id,
            policy_name,
            exposure,
            vehicle_year,
            pricing_year,
            policy_year,
            veh_age,
            driv_age,
            bonus_malus,
            density,
            veh_gas,
            veh_brand,
            region,
            area,
            no_accident_years,
            accident_count_recent,
            source_policy_id,
            created_at
        FROM policies
    """, (snapshot_year,))
    return cursor.rowcount


def update_policy_for_roll_forward(
    conn,
    policy_id: int,
    pricing_year: int,
    policy_year: int,
    veh_age: float,
    driv_age: float,
    bonus_malus: float,
    no_accident_years: int,
    accident_count_recent: int,
):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE policies
        SET
            pricing_year = ?,
            policy_year = ?,
            veh_age = ?,
            driv_age = ?,
            bonus_malus = ?,
            no_accident_years = ?,
            accident_count_recent = ?
        WHERE id = ?
    """, (
        pricing_year,
        policy_year,
        veh_age,
        driv_age,
        bonus_malus,
        no_accident_years,
        accident_count_recent,
        policy_id,
    ))
    return cursor.rowcount


def roll_forward_portfolio_in_place(simulation_year: int, update_bonus_malus_fn):
    """
    1. Snapshot current customers and policies for simulation_year.
    2. Update active policies in place for next year.
    3. Commit as one transaction.
    """
    from utils.dates import calculate_vehicle_age

    conn = get_connection()
    try:
        conn.execute("BEGIN")

        if snapshot_exists_for_year(simulation_year, conn=conn):
            raise ValueError(
                f"A snapshot already exists for year {simulation_year}. "
                f"Roll forward for that year has already been run."
            )

        latest_policies = get_latest_policies_for_roll_forward(conn=conn)
        if not latest_policies:
            raise ValueError("No active policies found to roll forward.")

        claims_rows = get_simulated_claims_for_year(simulation_year, conn=conn)

        claims_lookup = {
            row[0]: {
                "simulation_year": row[1],
                "had_claim": row[2],
                "claim_count": row[3],
                "total_claim_amount": row[4],
            }
            for row in claims_rows
        }

        customer_snapshot_count = snapshot_customers_for_year(simulation_year, conn)
        policy_snapshot_count = snapshot_policies_for_year(simulation_year, conn)

        results = []
        updated_policy_count = 0

        for row in latest_policies:
            policy_id = row[0]
            customer_id = row[1]
            policy_name = row[2]
            exposure = float(row[3])
            vehicle_year = int(row[4])
            current_pricing_year = int(row[5])
            current_policy_year = int(row[6])
            current_veh_age = float(row[7])
            current_driv_age = float(row[8])
            current_bonus_malus = float(row[9])
            density = float(row[10])
            veh_gas = str(row[11])
            veh_brand = str(row[12])
            region = str(row[13])
            area = str(row[14])
            no_accident_years = int(row[15])
            accident_count_recent = int(row[16])

            claim_info = claims_lookup.get(policy_id)
            claim_count = 0 if claim_info is None else int(claim_info["claim_count"])

            next_pricing_year = max(current_pricing_year, simulation_year) + 1
            next_policy_year = max(current_policy_year, simulation_year) + 1
            next_driv_age = current_driv_age + 1
            next_veh_age = calculate_vehicle_age(vehicle_year, next_pricing_year)

            if claim_count == 0:
                next_no_accident_years = no_accident_years + 1
            else:
                next_no_accident_years = 0

            next_accident_count_recent = min(claim_count, 3)
            next_bonus_malus = update_bonus_malus_fn(current_bonus_malus, claim_count)

            updated = update_policy_for_roll_forward(
                conn=conn,
                policy_id=policy_id,
                pricing_year=next_pricing_year,
                policy_year=next_policy_year,
                veh_age=next_veh_age,
                driv_age=next_driv_age,
                bonus_malus=next_bonus_malus,
                no_accident_years=next_no_accident_years,
                accident_count_recent=next_accident_count_recent,
            )
            updated_policy_count += updated

            results.append({
                "policy_id": policy_id,
                "customer_id": customer_id,
                "policy_name": policy_name,
                "exposure": exposure,
                "vehicle_year": vehicle_year,
                "old_pricing_year": current_pricing_year,
                "new_pricing_year": next_pricing_year,
                "old_policy_year": current_policy_year,
                "new_policy_year": next_policy_year,
                "old_driv_age": current_driv_age,
                "new_driv_age": next_driv_age,
                "old_veh_age": current_veh_age,
                "new_veh_age": next_veh_age,
                "old_bonus_malus": current_bonus_malus,
                "new_bonus_malus": next_bonus_malus,
                "claim_count": claim_count,
                "old_no_accident_years": no_accident_years,
                "new_no_accident_years": next_no_accident_years,
                "old_accident_count_recent": accident_count_recent,
                "new_accident_count_recent": next_accident_count_recent,
                "density": density,
                "veh_gas": veh_gas,
                "veh_brand": veh_brand,
                "region": region,
                "area": area,
            })

        conn.commit()

        df = pd.DataFrame(results)
        summary = {
            "rolled_policy_count": int(len(df)),
            "snapshot_year": int(simulation_year),
            "customer_snapshots_created": int(customer_snapshot_count),
            "policy_snapshots_created": int(policy_snapshot_count),
            "updated_policy_count": int(updated_policy_count),
            "claims_rows_used": int(len(claims_rows)),
        }
        return df, summary

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()