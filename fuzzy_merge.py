import pandas as pd
import re
from rapidfuzz import process, fuzz

# Load datasets
reviews = pd.read_csv('hospital_reviews_output.csv')
hospitals = pd.read_csv('Hospital_General_Information.csv')

# Drop rows missing necessary match fields
reviews.dropna(subset=['review_text'], inplace=True)

hospitals['zip_clean'] = hospitals['ZIP Code'].astype(str).str.extract(r'(\d+)')[0].str.zfill(5)
reviews['zip_clean'] = reviews['zip'].astype(str).str.extract(r'(\d+)')[0].str.zfill(5)

# Text cleaning helper
def preprocess_facility_name(name):
    name = name.lower()
    stop_words = r'\b(hospital|medical center|health|healthcare|system|inc|llc|regional|center|clinic|care)\b'
    name = re.sub(stop_words, '', name)
    name = re.sub(r'[^\w\s]', '', name)
    return name.strip()

# Apply name cleaning
hospitals['clean_name'] = hospitals['Facility Name'].apply(preprocess_facility_name)
reviews['clean_name'] = reviews['google_name'].apply(preprocess_facility_name)

# De-duplicate Google Places by ID to avoid matching identical places multiple times per review
google_places = reviews[['place_id', 'google_name', 'clean_name', 'zip_clean']].drop_duplicates(subset=['place_id'])
google_grouped = google_places.groupby('zip_clean')
matches = []
threshold = 80

# Perform fuzzy matching blocked by ZIP code
for zip_code, cms_group in hospitals.groupby('zip_clean'):
    if zip_code not in google_grouped.groups:
        continue

    google_group = google_grouped.get_group(zip_code)
    google_names = google_group['clean_name'].tolist()
    google_ids = google_group['place_id'].tolist()

    for _, cms_row in cms_group.iterrows():

        best_match = process.extractOne(
            cms_row['clean_name'],
            google_names,
            scorer=fuzz.token_set_ratio
        )

        if best_match and best_match[1] >= threshold:
            matched_idx = best_match[2]
            matches.append({
                'Facility ID': cms_row['Facility ID'],
                'place_id': google_ids[matched_idx],
                'match_score': best_match[1]
            })

match_df = pd.DataFrame(matches)

# Inner join matches back into the Google Reviews dataset (drops reviews with no matches)
reviews_matched = reviews.merge(
    match_df, 
    on='place_id', 
    how='inner'
)

reviews_matched = reviews_matched.merge(
    hospitals[['Facility ID', 'Facility Name']],
    on='Facility ID',    
    how='left')

print(f"Total reviews matched: {len(reviews_matched)}")
lowest_matches = (
    reviews_matched[['Facility Name', 'google_name', 'match_score']]
    .drop_duplicates()
    .sort_values(by='match_score', ascending=True)
)

print(lowest_matches.head(20))
lowest_matches.to_csv('lowest.csv')

reviews_matched.to_csv('reviews_matched.csv', index=False)