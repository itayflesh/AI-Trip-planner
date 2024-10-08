from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
from serpapi import GoogleSearch
from datetime import datetime
from openai import OpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TripInput(BaseModel):
    start_date: str
    end_date: str
    budget: float
    trip_type: str

# Set up OpenAI API credentials
openai_api_key = "" # Add your OpenAI API key here
openai_api_model = "gpt-3.5-turbo"
openai = OpenAI(api_key=openai_api_key)

# Set up SerpAPI API credentials
serpapi_api_key = "" # Add your SerpAPI API key here

# Function to get destination suggestions from OpenAI ChatGPT
def get_destination_suggestions(trip_month, trip_type):
    prompt = f"Suggest 5 best places to visit in the month of {trip_month} for a {trip_type} trip. Start each location with the arrival airport code in uppercase, followed by a colon and the destination name."
    
    try:
        response = openai.chat.completions.create(
            model=openai_api_model,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        
        suggestion_text = response.choices[0].message.content.strip()
        suggestions = suggestion_text.split("\n")
        return suggestions
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

# Function to get flight price insights from Google Flights using SerpAPI
def get_flight_price_insights(departure_id, arrival_id, start_date, end_date):
    try:
        params = {
            "engine": "google_flights",
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "outbound_date": start_date.strftime("%Y-%m-%d"),
            "return_date": end_date.strftime("%Y-%m-%d"),
            "currency": "USD",
            "hl": "en",
            "api_key": serpapi_api_key
        }
        
        response = requests.get("https://serpapi.com/search", params=params)
        
        if response.status_code == 200:
            data = response.json()
            price_insights = data.get("price_insights", {})
            if price_insights:
                lowest_price = price_insights.get("lowest_price", 0)
                return lowest_price
            else:
                return None
        else:
            raise Exception(f"Failed to fetch from SerpAPI. Status code: {response.status_code}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# Function to find the most expensive hotel within the user's budget
def find_most_expensive_hotel(destination, check_in_date, check_out_date, max_price, num_days):
    params = {
        "engine": "google_hotels",
        "q": destination,
        "check_in_date": check_in_date.strftime("%Y-%m-%d"),
        "check_out_date": check_out_date.strftime("%Y-%m-%d"),
        "adults": "1",
        "currency": "USD",
        "hl": "en",
        "gl": "il",
        "sort_by": "13",  # Sort by highest rating
        "max_price": int(max_price/num_days),  # Set the maximum price
        "api_key": serpapi_api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    properties = results.get("properties", [])

    if not properties:
        return "No hotels found for the given destination and dates."
    
    for property in properties:
            price = property.get("total_rate", {}).get("extracted_lowest", 0)
            if(price <= max_price):
                highest_price_hotel = {
                            "name": property.get("name"),
                            "total_rate": price
                        }
                return highest_price_hotel
            
    highest_price_hotel = {
                            "name":"---",
                            "total_rate": "---"
                        }
    return highest_price_hotel
    # return "The budget is not enough for flight and hotel."

# Function to generate daily plan using OpenAI ChatGPT
def generate_daily_plan(destination_name, start_date, end_date, trip_type):
    prompt = f"Create a daily plan for a trip to {destination_name} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} for a {trip_type} trip. Format your response as follows:\n\nDaily Plan:\n[Detailed daily plan - start each day with his number below each activity in different line]\n\nSummary: [One sentence that contains 4 visual descriptions that will help imagine what the vacation will look like]"
    
    try:
        response = openai.chat.completions.create(
            model=openai_api_model,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        
        if "Daily Plan:" in content and "Summary:" in content:
            daily_plan, summary = content.split("Summary:")
            daily_plan = daily_plan.replace("Daily Plan:", "").strip()
            summary = summary.strip()
            return daily_plan, summary
        else:
            raise Exception("Unexpected response format from OpenAI ChatGPT.")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None

# Function to generate trip images using OpenAI's DALL-E API
def generate_trip_images(destination_name, trip_month, trip_type, summary):
    image_urls = []
    
    for i in range(4):
        prompt = f"Create a single photo-realistic image that captures a specific moment or location during a {trip_type} trip to {destination_name} in the month of {trip_month}. The image should look like a photograph taken by a traveler, inspired by the following trip summary: {summary}"
        
        response = openai.images.generate(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        
        image_url = response.data[0].url
        image_urls.append(image_url)
    
    return image_urls

@app.post("/destinations")
async def get_destinations(trip_input: TripInput):
    start_date_str = trip_input.start_date
    end_date_str = trip_input.end_date
    budget = trip_input.budget
    trip_type = trip_input.trip_type

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        num_days = (end_date - start_date).days
    except ValueError:
        return {"error": "Invalid date format. Please enter dates in the format: YYYY-MM-DD"}

    trip_month = start_date.strftime("%B")

    destination_suggestions = get_destination_suggestions(trip_month, trip_type)
    destination_details = {}

    for suggestion in destination_suggestions:
        airport_code, destination_name = suggestion.split(":")
        airport_code = airport_code.split()[-1]
        destination_details[airport_code] = {"name": destination_name.strip()}

    for airport_code, details in destination_details.items():
        destination_name = details["name"]
        flight_price = get_flight_price_insights("TLV", airport_code, start_date, end_date)
        if flight_price is not None:
            details["flight_price"] = flight_price
            if flight_price > budget:
                details["message"] = "The flight price alone exceeds the entire budget."
            else:
                max_hotel_price = budget - flight_price
                hotel = find_most_expensive_hotel(destination_name, start_date, end_date, max_hotel_price, num_days)
                if hotel:
                    details["hotel_name"] = hotel["name"]
                    details["hotel_price"] = hotel["total_rate"]
                else:
                    details["message"] = "No suitable hotels found within the remaining budget."
        else:
            details["message"] = "Failed to retrieve flight price insights."

    return {"destination_details": destination_details}

@app.post("/daily-plan")
async def get_daily_plan(request: Request):
    data = await request.json()
    destination_name = data["destination_name"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    trip_type = data["trip_type"]

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Please enter dates in the format: YYYY-MM-DD"}

    daily_plan, summary = generate_daily_plan(destination_name, start_date_obj, end_date_obj, trip_type)
    if daily_plan:
        return {"daily_plan": daily_plan, "summary": summary}
    else:
        return {"error": "Failed to generate daily plan."}

@app.post("/trip-images")
async def get_trip_images(request: Request):
    data = await request.json()
    destination_name = data["destination_name"]
    trip_month = data["trip_month"]
    trip_type = data["trip_type"]
    summary = data["summary"]

    image_urls = generate_trip_images(destination_name, trip_month, trip_type, summary)
    if image_urls:
        return {"image_urls": image_urls}
    else:
        return {"error": "Failed to generate trip images."}