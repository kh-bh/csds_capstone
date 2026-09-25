import os
import pandas as pd
from supabase import create_client, Client
import re
import numpy as np
from dotenv import load_dotenv

load_dotenv() 

# Use SUPABASE_SERVICE_ROLE_KEY for bulk ingestion to bypass Row-Level Security (RLS)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "your-service-role-key")
print(f"Connecting to Supabase at {SUPABASE_KEY} with service role key in {SUPABASE_URL}.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Explicit target schema columns for 'cms_hospitals'
ALLOWED_COLUMNS = [
    "facility_id",
    "facility_name",
    "address",
    "city",
    "state",
    "zip_code",
    "county",
    "telephone_number",
    "hospital_type",
    "hospital_ownership",
    "emergency_services",
]


def sanitize_column_name(col_name: str) -> str:
    """Converts raw headers into sanitized SQL snake_case column names."""
    col = col_name.strip().lower()
    col = re.sub(r"[\s/-]+", "_", col)
    col = re.sub(r"[^\w_]", "", col)
    return col


def upload_cms_hospitals(csv_file_path: str):
    df = pd.read_csv(csv_file_path, dtype=str).fillna("")

    # Map raw CSV header variations to database column names
    column_mapping = {
        "Facility ID": "facility_id",
        "Facility Name": "facility_name",
        "Address": "address",
        "City/Town": "city",
        "City": "city",
        "State": "state",
        "ZIP Code": "zip_code",
        "County/Parish": "county",
        "County Name": "county",
        "Telephone Number": "telephone_number",
        "Hospital Type": "hospital_type",
        "Hospital Ownership": "hospital_ownership",
        "Emergency Services": "emergency_services",
    }
    df = df.rename(columns=column_mapping)

    # Keep ONLY columns defined in ALLOWED_COLUMNS; automatically drops all extra fields
    keep_cols = [c for c in df.columns if c in ALLOWED_COLUMNS]
    df = df[keep_cols]

    records = df.to_dict(orient="records")

    batch_size = 500
    total_records = len(records)
    print(f"Starting ingestion of {total_records} records into 'cms_hospitals'...")

    for i in range(0, total_records, batch_size):
        batch = records[i : i + batch_size]
        supabase.table("cms_hospitals").upsert(batch).execute()
        print(f"Processed [{min(i + batch_size, total_records)}/{total_records}] records.")

    print("\nData successfully uploaded to 'cms_hospitals'!")


def upload_hcahps_scores(csv_file_path: str):
    df = pd.read_csv(csv_file_path, dtype=str)

    # 1. Clean Column Names
    df.columns = [sanitize_column_name(c) for c in df.columns]

    # 2. Replace empty/missing string representations
    df = df.replace(
        to_replace=["Not Available", "N/A", "NA", "Not Applicable", ""],
        value=np.nan,
    )

    # 3. Identify non-string columns and convert whole numbers to nullable integers ('Int64')
    non_numeric_cols = [
        "facility_id",
        "facility_name",
        "address",
        "city_town",
        "state",
        "zip_code",
        "county_parish",
        "telephone_number",
        "start_date",
        "end_date",
    ]
    numeric_cols = [c for c in df.columns if c not in non_numeric_cols]

    for col in numeric_cols:
        # Convert to numeric float first to parse strings safely
        s = pd.to_numeric(df[col], errors="coerce")

        # Cast to nullable Int64 if non-null values are whole numbers
        if not s.dropna().empty and s.dropna().apply(lambda x: float(x).is_integer()).all():
            df[col] = s.astype("Int64")
        else:
            df[col] = s

    # 4. Format date columns
    for date_col in ["start_date", "end_date"]:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")

    # 5. Drop redundant metadata columns present in cms_hospitals table
    metadata_to_drop = [
        "facility_name",
        "address",
        "city_town",
        "state",
        "zip_code",
        "county_parish",
        "telephone_number",
    ]
    df = df.drop(columns=[c for c in metadata_to_drop if c in df.columns])

    # Convert DataFrame records replacing pandas <NA> / NaN with Python None
    records = df.replace({np.nan: None}).to_dict(orient="records")

    # Sanitize dictionary values to ensure native Python 'int' types instead of floats
    for record in records:
        for k, v in record.items():
            if isinstance(v, float) and v.is_integer():
                record[k] = int(v)

    # 6. Batch Upsert to Supabase
    batch_size = 500
    total_records = len(records)
    print(f"Uploading {total_records} HCAHPS records to Supabase...")

    for i in range(0, total_records, batch_size):
        batch = records[i : i + batch_size]
        supabase.table("hcahps_scores").upsert(batch).execute()
        print(f"Processed [{min(i + batch_size, total_records)}/{total_records}] records.")

    print("\nHCAHPS data upload complete!")

def upload_google_reviews(csv_file_path: str):
    df = pd.read_csv(csv_file_path, dtype=str)

    # 1. Drop redundant column
    if "Facility Name" in df.columns:
        df = df.drop(columns=["Facility Name"])

    # 2. Sanitize column names (e.g., 'Facility ID' -> 'facility_id')
    df.columns = [sanitize_column_name(c) for c in df.columns]

    # 3. Clean and convert numeric types
    numeric_cols = [
        "hospital_rating",
        "total_ratings",
        "review_id",
        "review_rating",
        "match_score",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Replace empty strings and NaN with None for proper SQL NULL handling
    df = df.replace({np.nan: None, "": None})

    records = df.to_dict(orient="records")

    # 4. Batch Upload to Supabase REST API
    batch_size = 500
    total_records = len(records)
    print(f"Uploading {total_records} review records to 'google_hospital_reviews'...")

    for i in range(0, total_records, batch_size):
        batch = records[i : i + batch_size]
        supabase.table("google_hospital_reviews").insert(batch).execute()
        print(f"Processed [{min(i + batch_size, total_records)}/{total_records}] records.")

    print("\nGoogle Places review data upload complete!")


if __name__ == "__main__":
    # upload_cms_hospitals("Hospital_General_Information.csv")
    # upload_hcahps_scores("HCAHPS-Hospital_cleaned.csv") 
    upload_google_reviews("reviews_matched.csv")
