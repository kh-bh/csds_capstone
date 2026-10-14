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
print(f"Connecting to Supabase at {SUPABASE_URL} with service role key in {SUPABASE_KEY}.")

reviews_df = pd.read_csv('reviews_with_topics.csv')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. Prepare dataset for update/upsert
# Replace 'review_id' with your table's Primary Key column name
PRIMARY_KEY_COL = 'id'  

ids = []

for i in range(len(reviews_df)):
    ids.append(i + 5501)

reviews_df[PRIMARY_KEY_COL] = ids
update_data = reviews_df[[PRIMARY_KEY_COL, 'operational_category']].to_dict(orient='records')

# 4. Batch upload to Supabase to prevent HTTP request timeouts
TABLE_NAME = 'google_hospital_reviews'  # Replace with your Supabase table name
BATCH_SIZE = 1000

print(f"Starting upload of {len(update_data)} rows to '{TABLE_NAME}'...")

for i in range(0, len(update_data), BATCH_SIZE):
    batch = update_data[i : i + BATCH_SIZE]
    response = (
        supabase.table(TABLE_NAME)
        .upsert(batch, on_conflict=PRIMARY_KEY_COL)
        .execute()
    )
    print(f"Uploaded batch {i // BATCH_SIZE + 1} of {(len(update_data) - 1) // BATCH_SIZE + 1}")

print("Upload complete!")