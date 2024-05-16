import requests
from serpapi import GoogleSearch
from datetime import datetime

# Set up OpenAI API credentials
openai_api_key = "sk-proj-wQ4taTDDFhbuDrmkqIlOT3BlbkFJlJVo8Zlx0wucOcJ2atou"
openai_api_model = "gpt-3.5-turbo"

# Set up SerpAPI API credentials
serpapi_api_key = "30c976628a21ad91c354a84dfd3054b0ece66864fe19e21df5cefa6c46e910ed"

# Function to get destination suggestions from OpenAI ChatGPT
def get_destination_suggestions(trip_month, trip_type):
    messages = [
        {
            "role": "system",
            "content": f"Suggest 5 best places to visit in the month of {trip_month} for a {trip_type} trip. Start each location with the arrival airport code in uppercase, followed by a colon and the destination name."
        }
    ]
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_api_key}"
            },
            json={
                "messages": messages,
                "model": openai_api_model
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            suggestion_text = data["choices"][0]["message"]["content"].strip()
            suggestions = suggestion_text.split("\n")
            return suggestions
        elif response.status_code == 401:
            raise Exception("Looks like your OpenAI API key is incorrect. Please check your API key and try again.")
        else:
            raise Exception(f"Failed to fetch from OpenAI API. Status code: {response.status_code}")
    
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
        "gl": "il" ,
        "sort_by": "3",  # Sort by lowest price
        "api_key": serpapi_api_key
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    properties = results.get("properties", [])
    
    if not properties:
        return "No hotels found for the given destination and dates."
    
    cheapest_hotel = properties[0]
    cheapest_price_hotel = cheapest_hotel.get("total_rate", {}).get("extracted_lowest", 0)
    
    if cheapest_price_hotel > max_price:
        return "The budget is not enough for flight and hotel."
    
    highest_price_hotel = None
    highest_price = 0
    
    while True:
        for property in properties:
            price = property.get("total_rate", {})
            extracted_lowest = price.get("extracted_lowest", 0)
            
            if extracted_lowest <= max_price:
                if extracted_lowest > highest_price:
                    highest_price_hotel = {
                        "name": property.get("name"),
                        "total_rate": extracted_lowest
                    }
                    highest_price = extracted_lowest
            else:
                # Hotel price exceeds the maximum price per night, break the loop
                return highest_price_hotel
        
        pagination = results.get("serpapi_pagination", {})
        next_page_token = pagination.get("next_page_token")
        
        if next_page_token:
            params["next_page_token"] = next_page_token
            search = GoogleSearch(params)
            results = search.get_dict()
            properties = results.get("properties", [])
        else:
            break
    
    return highest_price_hotel

# Function to generate daily plan using OpenAI ChatGPT
def generate_daily_plan(destination_name, start_date, end_date, trip_type):
    messages = [
        {
            "role": "system",
            "content": f"Create a daily plan for a trip to {destination_name} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} for a {trip_type} trip. Also, provide a one-sentence that will start with the word Summary that wiil highlighting the main activities of the trip."
        }
    ]
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_api_key}"
            },
            json={
                "messages": messages,
                "model": openai_api_model
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            daily_plan, summary = content.split("\n\nSummary: ")
            return daily_plan.strip(), summary.strip()
        else:
            print(response.status_code)
            raise Exception("Failed to generate daily plan.")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None

# Function to generate trip images using OpenAI's DALL-E API
def generate_trip_images(destination_name, trip_month, trip_type, summary):
    prompt = f"Create 4 different images that showcase a {trip_type} trip to {destination_name} in month: {trip_month}, the 4 images should be inspired by the following trip summary: {summary}"
    print(prompt)
    
    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        },
        json={
            "prompt": prompt,
            "n": 4,
            "size": "1024x1024"
        }
    )
    
    image_urls = []
    
    if response.status_code == 200:
        data = response.json()["data"]
        for item in data:
            image_url = item["url"]
            image_urls.append(image_url)
    else:
        print(response.status_code)
        print("Failed to generate trip images.")
    
    return image_urls

# Get user input
date_template = "YYYY-MM-DD"  # Template for the date format
start_date_str = input(f"Enter the start date of your trip ({date_template}): ")
end_date_str = input(f"Enter the end date of your trip ({date_template}): ")
budget = float(input("Enter your total budget in USD for the trip (hotel+flights): "))
trip_type = input("Enter the type of trip (ski/beach/city): ")

# Convert start and end dates to datetime objects
try:
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    num_days = (end_date - start_date).days
except ValueError:
    print(f"Invalid date format. Please enter dates in the format: {date_template}")
    exit()

# Extract the month from the start date
trip_month = start_date.strftime("%B")

# # Get destination suggestions from OpenAI ChatGPT
# destination_suggestions = get_destination_suggestions(trip_month, trip_type)

# # Create a dictionary to store destination details
# destination_details = {}

# # Extract airport codes and destination names from destination suggestions
# for suggestion in destination_suggestions:
#     airport_code, destination_name = suggestion.split(":")
#     airport_code = airport_code.split()[-1]
#     destination_details[airport_code] = {"name": destination_name.strip()}

# # Get flight price insights and find the most expensive hotel for each destination
# for airport_code, details in destination_details.items():
#     destination_name = details["name"]
    
#     # Get flight price insights
#     flight_price = get_flight_price_insights("TLV", airport_code, start_date, end_date)
#     if flight_price is not None:
#         details["flight_price"] = flight_price
        
#         # Calculate the maximum price for hotels
#         max_hotel_price = budget - flight_price
        
#         # Find the most expensive hotel within the user's budget
#         hotel = find_most_expensive_hotel(destination_name, start_date, end_date, max_hotel_price, num_days)
#         if hotel:
#             details["hotel_name"] = hotel["name"]
#             details["hotel_Price"] = hotel["total_rate"]

# delete from here
            
# Create fake destination data for testing
fake_destination_details = {
    "MLE": {
        "name": "Maldives",
        "flight_price": 1200,
        "hotel_name": "Soneva Fushi",
        "hotel_Price": 2000
    },
    "HNL": {
        "name": "Honolulu, Hawaii",
        "flight_price": 1000,
        "hotel_name": "The Royal Hawaiian",
        "hotel_Price": 1500
    },
    "CUN": {
        "name": "Cancun, Mexico",
        "flight_price": 800,
        "hotel_name": "The Ritz-Carlton, Cancun",
        "hotel_Price": 1200
    },
    "PUJ": {
        "name": "Punta Cana, Dominican Republic",
        "flight_price": 900,
        "hotel_name": "Paradisus Palma Real Golf & Spa Resort",
        "hotel_Price": 1100
    },
    "PPT": {
        "name": "Bora Bora, French Polynesia",
        "flight_price": 1800,
        "hotel_name": "Four Seasons Resort Bora Bora",
        "hotel_Price": 2500
    }
}

destination_details = fake_destination_details

# to here

# Print the destination details with flight price and hotel information
print("Destination Details:")
for index, (airport_code, details) in enumerate(destination_details.items(), start=1):
    destination_name = details["name"]
    flight_price = details.get("flight_price", "N/A")
    hotel_name = details.get("hotel_name", "N/A")
    hotel_Price = details.get("hotel_Price", "N/A")
    total_price = flight_price + hotel_Price if flight_price != "N/A" and hotel_Price != "N/A" else "N/A"
    
    print(f"{index}. {destination_name} ({airport_code}):")
    print(f"   Flight Price: ${flight_price}")
    print(f"   Hotel Name: {hotel_name}")
    print(f"   Hotel Price: ${hotel_Price}")
    print(f"   Total Price: ${total_price}")
    print()

# Prompt the user to choose a destination
choice = int(input("Enter the number of your desired destination: "))

if 1 <= choice <= len(destination_details):
    selected_destination = list(destination_details.values())[choice - 1]
    destination_name = selected_destination["name"]
    
    # Generate daily plan
    daily_plan, summary = generate_daily_plan(destination_name, start_date, end_date, trip_type)

    if daily_plan:
        print(f"\nDaily Plan for {destination_name}:")
        print(daily_plan)
        print(f"\nTrip Summary: {summary}")
        
        # Generate trip images
        image_urls = generate_trip_images(destination_name, trip_month, trip_type, summary)
        
        if image_urls:
            print("\nTrip Images:")
            for i, url in enumerate(image_urls, start=1):
                print(f"Image {i}: {url}")
        else:
            print("Failed to generate trip images.")
    else:
        print("Failed to generate daily plan.")

else:
    print("Invalid choice. Please enter a valid number.")