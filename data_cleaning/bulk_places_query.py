import csv
import os
import time
import requests
import sqlite3
from dotenv import load_dotenv

load_dotenv() 

API_KEY = os.environ.get("PLACES_API_KEY")
NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"
DB_NAME = "us_hospitals_reviews.db"
CSV_OUTPUT = "hospital_reviews_output.csv"

# create a temporary database to store review data
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            place_id TEXT PRIMARY KEY,
            hifld_id TEXT,
            google_name TEXT,
            formatted_address TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            hospital_rating REAL,
            total_ratings INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT,
            author_name TEXT,
            rating REAL,
            text TEXT,
            publish_time TEXT,
            FOREIGN KEY (place_id) REFERENCES hospitals (place_id)
        )
    """)

    conn.commit()
    conn.close()

# get address components from a located hospital
def parse_google_address(place):
    address_components = place.get("addressComponents", [])
    city, state, zip_code = "", "", ""

    for comp in address_components:
        types = comp.get("types", [])
        if "locality" in types:
            city = comp.get("longText", "")
        elif "administrative_area_level_1" in types:
            state = comp.get("shortText", "")
        elif "postal_code" in types:
            zip_code = comp.get("longText", "")

    formatted_address = place.get("formattedAddress", "")
    return formatted_address, city, state, zip_code

# get hospital based on latitude and longitude from the HIFLD dataset
def fetch_hospital_by_coords(lat, lng, radius=2000.0):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.rating,"
            "places.userRatingCount,places.reviews,places.formattedAddress,"
            "places.addressComponents"
        )
    }
    payload = {
        "includedTypes": ["hospital"],
        "maxResultCount": 1,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(lat),
                    "longitude": float(lng)
                },
                "radius": radius
            }
        }
    }

    response = requests.post(NEARBY_SEARCH_URL, headers=headers, json=payload)
    if response.status_code == 200:
        places = response.json().get("places", [])
        return places[0] if places else None
    else:
        print(f"API Error [{response.status_code}]: {response.text}")
        return None

# check each hospital in the HIFLD dataset and get its Google Place data and reviews
def process_hifld_csv(csv_file_path):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    with open(csv_file_path, mode="r", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)
        
        for idx, row in enumerate(reader, 1):
            if idx % 50 == 0:
                print(f"Processed {idx} rows...")
            hifld_id = row.get("ID", "")
            lat_str = row.get("LATITUDE") or row.get("Y")
            lng_str = row.get("LONGITUDE") or row.get("X")

            if not lat_str or not lng_str:
                continue

            try:
                lat, lng = float(lat_str), float(lng_str)
            except ValueError:
                continue

            place = fetch_hospital_by_coords(lat, lng)
            if not place:
                print(f"[{idx}] No Google Place found near ({lat}, {lng}) for HIFLD ID: {hifld_id}")
                continue

            place_id = place.get("id")

            # Check if this Google Place ID was already fetched from a nearby coordinate
            cursor.execute("SELECT place_id FROM hospitals WHERE place_id = ?", (place_id,))
            if cursor.fetchone():
                continue

            # metadata exraction
            display_name = place.get("displayName", {}).get("text", "Unknown Hospital")
            formatted_address, city, state, zip_code = parse_google_address(place)
            hospital_rating = place.get("rating", 0.0)
            total_ratings = place.get("userRatingCount", 0)
            reviews = place.get("reviews", [])

            cursor.execute("""
                INSERT OR REPLACE INTO hospitals (place_id, hifld_id, google_name, formatted_address, city, state, zip, hospital_rating, total_ratings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (place_id, hifld_id, display_name, formatted_address, city, state, zip_code, hospital_rating, total_ratings))

            for r in reviews:
                author_name = r.get("authorAttribution", {}).get("displayName", "Anonymous")
                review_rating = r.get("rating")
                review_text = r.get("text", {}).get("text", "")
                publish_time = r.get("relativePublishTimeDescription", "")

                cursor.execute("""
                    INSERT INTO reviews (place_id, author_name, rating, text, publish_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (place_id, author_name, review_rating, review_text, publish_time))

            conn.commit()
            time.sleep(0.05)

    conn.close()

# convert database to CSV for further analysis
def export_db_to_csv(csv_output_path):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        SELECT 
            h.place_id,
            h.hifld_id,
            h.google_name,
            h.formatted_address,
            h.city,
            h.state,
            h.zip,
            h.hospital_rating,
            h.total_ratings,
            r.id AS review_id,
            r.author_name,
            r.rating AS review_rating,
            r.text AS review_text,
            r.publish_time
        FROM hospitals h
        LEFT JOIN reviews r ON h.place_id = r.place_id
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    headers = [description[0] for description in cursor.description]

    with open(csv_output_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)
        writer.writerows(rows)

    conn.close()
    print(f"\nExport complete: {csv_output_path}")


if __name__ == "__main__":
    init_db()
    process_hifld_csv("Hospitals.csv")
    export_db_to_csv(CSV_OUTPUT)