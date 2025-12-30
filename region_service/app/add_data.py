import os
import pandas as pd
import mysql.connector as connector
import sql_connect
import numpy as np
import re

def slugify(value: str) -> str:
    """Simple slug generator from a name."""
    if value is None:
        return ""
    value = value.strip().lower()
    # replace non-alphanumeric with hyphen
    value = re.sub(r"[^a-z0-9]+", "-", value)
    # remove leading/trailing hyphens
    value = value.strip("-")
    return value or ""

def get_state_code(state_name, conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT code FROM states WHERE name = %s;", (state_name,))
        result = cursor.fetchone()
        _ = cursor.fetchall()
        return result[0] if result else None

def get_district_code(district_name, state_code, conn):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT code FROM district WHERE name = %s and state_code = %s;",
            (district_name, state_code),
        )
        result = cursor.fetchone()
        _ = cursor.fetchall()
        return result[0] if result else None

def get_city_code(city_name, district_code, conn):
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT code FROM city WHERE name = %s and district_code=%s;",
            (city_name, district_code),
        )
        result = cursor.fetchone()
        _ = cursor.fetchall()
        return result[0] if result else None

def insert_states(states, conn):
    cursor = conn.cursor()
    for index, state in enumerate(states, start=1):
        try:
            slug = slugify(state)
            cursor.execute(
                "INSERT INTO states (code, name, slug) VALUES (%s, %s, %s);",
                (index, state, slug),
            )
        except Exception as e:
            print(f"Skipped state '{state}' due to error: {e}")
    conn.commit()

def insert_districts(districts, conn):
    state = list(districts.keys())[0]
    state_code = get_state_code(state, conn)
    with conn.cursor() as cursor:
        for index, district in enumerate(districts[state], start=1):
            try:
                slug = slugify(district)
                cursor.execute(
                    "INSERT INTO district (name, slug, state_code) VALUES (%s, %s, %s);",
                    (district, slug, state_code),
                )
            except Exception as e:
                print(f"Skipped district '{district}' due to error: {e}")
        conn.commit()
    return state_code

def insert_cities(places, state_code, conn):
    with conn.cursor() as cursor:
        for district_name in places.keys():
            district_code = get_district_code(district_name, state_code, conn)
            cities = places[district_name]
            for city_name, locality_list in cities.items():
                try:
                    city_slug = slugify(city_name)
                    cursor.execute(
                        "INSERT IGNORE INTO city (name, slug, district_code) "
                        "VALUES (%s, %s, %s);",
                        (city_name, city_slug, district_code),
                    )
                    conn.commit()
                    city_code = get_city_code(city_name, district_code, conn)
                    for location in locality_list:
                        try:
                            loc_slug = slugify(location)
                            cursor.execute(
                                "INSERT IGNORE INTO locality (name, slug, city_code) "
                                "VALUES (%s, %s, %s);",
                                (location, loc_slug, city_code),
                            )
                            conn.commit()
                        except Exception as e:
                            print(f"Skipped locality '{location}' due to error: {e}")
                except Exception as e:
                    print(f"Skipped city '{city_name}' due to error: {e}")

# remove or keep insert_localities commented out, it is broken and unused
# def insert_localities(...): ...

def get_region_info(file):
    df = pd.read_csv("c:/Indian's States/converted/" + file)
    valid_data = df.loc[4:]
    district_names = valid_data.iloc[:, 2].unique()
    district = {file.split(".")[0]: district_names.tolist()}
    cities = valid_data.groupby(valid_data.columns[2])[valid_data.columns[4]].unique()
    locality = valid_data.groupby(valid_data.columns[4])[valid_data.columns[7]].unique()
    places = {}
    for dis in district_names:
        if dis is not np.nan:
            places[dis] = {}
            city = cities[dis].tolist()
            for c in city:
                places[dis][c] = []
                loc = locality[c].tolist()
                for l in loc:
                    places[dis][c].append(l)
    return district, places

if __name__ == "__main__":
    states = []
    files = [
        f
        for f in os.listdir("c:/Indian's States/converted")
        if f.endswith(".csv")
    ]
    for file in files:
        state = file.split(".")[0]
        states.append(state)

    with sql_connect.connect_sql() as conn:
        insert_states(states, conn)

    with sql_connect.connect_sql() as conn:
        for file in files:
            district, places = get_region_info(file)
            state_code = insert_districts(district, conn)
            insert_cities(places, state_code, conn)
