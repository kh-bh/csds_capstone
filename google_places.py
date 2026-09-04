import requests
import os
from dotenv import load_dotenv

load_dotenv() 

# function to get hospital reviews based on latitude and longitude
def get_hospital_reviews(latitude=40.7128, longitude=-74.0060, radius=5000.0):
    url = "https://places.googleapis.com/v1/places:searchNearby"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": os.environ.get("PLACES_API_KEY"),
        # Mandatory in Places API (New): specifies exactly which attributes to return
        "X-Goog-FieldMask": "places.id,places.displayName,places.rating,places.userRatingCount,places.reviews"
    }

    # Define the parameters for the request
    payload = {
        "includedTypes": ["hospital"],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "radius": radius
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"API Error ({response.status_code}): {response.text}")
        return
        
    data = response.json()
    places = data.get("places", [])
    
    if not places:
        print("No hospitals found.")
        return

    for place in places:
        name = place.get("displayName", {}).get("text", "Unknown")
        rating = place.get("rating", "N/A")
        total_ratings = place.get("userRatingCount", 0)
        reviews = place.get("reviews", [])
        
        print(f"\n{'='*50}")
        print(f"Hospital: {name}")
        print(f"Average Rating: {rating} ({total_ratings} total ratings)")
        print(f"{'='*50}\n")
        
        if not reviews:
            print("No reviews available.")
            continue

        for idx, r in enumerate(reviews, 1):
            author = r.get("authorAttribution", {}).get("displayName", "Anonymous")
            rev_rating = r.get("rating", "N/A")
            text = r.get("text", {}).get("text", "No text provided.")
            time_str = r.get("relativePublishTimeDescription", "")
            
            print(f"Review #{idx} by {author} ({rev_rating} stars) - {time_str}:")
            print(f"\"{text}\"\n")

if __name__ == "__main__":
    get_hospital_reviews()