import requests
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv() 

API_KEY = os.environ.get("YELP_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

# function to find hospitals based on latitude and longitude
def find_hospitals(latitude=40.7128, longitude=-74.0060, limit=5):
    url = "https://api.yelp.com/v3/businesses/search"
    params = {
        "term": "hospital",
        "categories": "hospitals",
        "latitude": latitude,
        "longitude": longitude,
        "limit": limit
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get("businesses", [])
    return []

# get reviews for a hospital
def get_hospital_reviews(identifier, locale="en_US"):

    safe_identifier = urllib.parse.quote(str(identifier), safe="")
    url = f"https://api.yelp.com/v3/businesses/{safe_identifier}/reviews"
    params = {"locale": locale}
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        return response.json().get("reviews", [])
    
    print(f"API Call Failed [{response.status_code}] for '{identifier}': {response.text}")
    return None

def main():
    hospitals = find_hospitals(latitude=40.7128, longitude=-74.0060, limit=5)
    
    for hospital in hospitals:
        name = hospital.get("name", "Unknown")
        rating = hospital.get("rating", "N/A")
        total_ratings = hospital.get("review_count", 0)
        
        # Try alias first, then fallback to business ID
        alias = hospital.get("alias")
        biz_id = hospital.get("id")
        
        reviews = get_hospital_reviews(alias) if alias else None
        if reviews is None and biz_id:
            reviews = get_hospital_reviews(biz_id)

        print(f"\n{'='*50}")
        print(f"Hospital: {name}")
        print(f"Average Rating: {rating} ({total_ratings} total ratings)")
        print(f"{'='*50}\n")

        if not reviews:
            print("No reviews returned by API (category restricted or unlisted).")
            continue

        for idx, r in enumerate(reviews, 1):
            author = r.get("user", {}).get("name", "Anonymous")
            rev_rating = r.get("rating", "N/A")
            text = r.get("text", "No text provided.")
            print(f"Review #{idx} by {author} ({rev_rating} stars):")
            print(f"\"{text}\"\n")

if __name__ == "__main__":
    main()