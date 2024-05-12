import requests
from datetime import datetime

# Set up OpenAI API credentials
openai_api_key = "sk-proj-wQ4taTDDFhbuDrmkqIlOT3BlbkFJlJVo8Zlx0wucOcJ2atou"
openai_api_model = "gpt-3.5-turbo"

# Set up SerpAPI API credentials
serpapi_api_key = "8c584f8e82f0a0e913e3398f17bad84f7ff22dbdcae6ba5774070fb971307443"

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
except ValueError:
    print(f"Invalid date format. Please enter dates in the format: {date_template}")
    exit()

# Extract the month from the start date
trip_month = start_date.strftime("%B")

# Get destination suggestions from OpenAI ChatGPT
destination_suggestions = get_destination_suggestions(trip_month, trip_type)

# Create a dictionary to store destination details
destination_details = {}

# Extract airport codes and destination names from destination suggestions
for suggestion in destination_suggestions:
    airport_code, destination_name = suggestion.split(":")
    airport_code = airport_code.split()[-1]
    destination_details[airport_code] = {"name": destination_name.strip()}

# Get flight price insights for each destination using SerpAPI
for airport_code in destination_details:
    lowest_price = get_flight_price_insights("TLV", airport_code, start_date, end_date)
    if lowest_price is not None:
        destination_details[airport_code]["lowest_price"] = lowest_price

# Print the destination details with the lowest price
print("Destination Details:")
for airport_code, details in destination_details.items():
    destination_name = details["name"]
    lowest_price = details.get("lowest_price", "N/A")
    print(f"{destination_name} ({airport_code}) - Lowest Price: ${lowest_price}")