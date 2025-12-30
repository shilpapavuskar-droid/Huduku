from flask import Flask, jsonify ,request
import mysql.connector
import time
import os

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        use_pure=True,
    )


def wait_for_db(max_retries=30, delay_seconds=2):
    retries = 0
    while retries < max_retries:
        try:
            conn = get_db_connection()
            conn.close()
            print("Region DB is up, starting region service.")
            return
        except mysql.connector.Error as e:
            print(f"Region DB not ready yet ({e}), retrying in {delay_seconds}s...")
            time.sleep(delay_seconds)
            retries += 1
    raise RuntimeError("Region DB did not become ready in time")


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS states (
            code INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            slug VARCHAR(255) NOT NULL UNIQUE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS district (
            code INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(255) NOT NULL,
            state_code INT NOT NULL,
            CONSTRAINT fk_district_state
                FOREIGN KEY (state_code) REFERENCES states(code)
                ON DELETE CASCADE,
            CONSTRAINT uq_district_name_per_state
                UNIQUE (name, state_code),
            CONSTRAINT uq_district_slug_per_state
                UNIQUE (slug, state_code)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS city (
            code INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(255) NOT NULL,
            district_code INT NOT NULL,
            CONSTRAINT fk_city_district
                FOREIGN KEY (district_code) REFERENCES district(code)
                ON DELETE CASCADE,
            CONSTRAINT uq_city_name_per_district
                UNIQUE (name, district_code),
            CONSTRAINT uq_city_slug_per_district
                UNIQUE (slug, district_code)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS locality (
            code INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(255) NOT NULL,
            city_code INT NOT NULL,
            CONSTRAINT fk_locality_city
                FOREIGN KEY (city_code) REFERENCES city(code)
                ON DELETE CASCADE,
            CONSTRAINT uq_locality_name_per_city
                UNIQUE (name, city_code),
            CONSTRAINT uq_locality_slug_per_city
                UNIQUE (slug, city_code)
        )
        """
    )

    conn.commit()
    cursor.close()
    conn.close()
    print("Region DB tables are ensured.")



@app.route("/states", methods=["GET"])
def get_states():
    slug = request.args.get("slug")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if slug:
            cursor.execute(
                "SELECT code, name, slug FROM states WHERE slug = %s",
                (slug,),
            )
        else:
            cursor.execute("SELECT code, name, slug FROM states")
        rows = cursor.fetchall()
        states = [
            {"code": code, "name": name, "slug": s}
            for code, name, s in rows
        ]
        return jsonify(states)
    finally:
        cursor.close()
        conn.close()


@app.route("/states/<int:state_code>/districts", methods=["GET"])
def get_districts(state_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT code, name, slug FROM district WHERE state_code = %s",
        (state_code,),
    )
    districts = [
        {"code": code, "name": name, "slug": slug}
        for code, name, slug in cursor.fetchall()
    ]
    cursor.close()
    conn.close()
    return jsonify(districts)


@app.route(
    "/states/<int:state_code>/districts/<int:district_code>/cities",
    methods=["GET"],
)
def get_cities(state_code, district_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT code, name, slug FROM city WHERE district_code = %s",
        (district_code,),
    )
    cities = [
        {"code": code, "name": name, "slug": slug}
        for code, name, slug in cursor.fetchall()
    ]
    cursor.close()
    conn.close()
    return jsonify(cities)


@app.route(
    "/states/<int:state_code>/districts/<int:district_code>/cities/<int:city_code>/locality",
    methods=["GET"],
)
def get_localities(state_code, district_code, city_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT code, name, slug FROM locality WHERE city_code = %s",
        (city_code,),
    )
    localities = [
        {"code": code, "name": name, "slug": slug}
        for code, name, slug in cursor.fetchall()
    ]
    cursor.close()
    conn.close()
    return jsonify(localities)


@app.route(
    "/states/<int:state_code>/districts/<int:district_code>/cities/<int:city_code>/locality/<int:locality_code>",
    methods=["GET"],
)
def get_locality(state_code, district_code, city_code, locality_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT code, name, slug FROM locality WHERE code = %s AND city_code = %s",
        (locality_code, city_code),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return jsonify({"code": row[0], "name": row[1], "slug": row[2]})
    else:
        return jsonify({"error": "Locality not found"}), 404


if __name__ == "__main__":
    wait_for_db()
    init_db()
    app.run(debug=True, port=5000, host="0.0.0.0")
