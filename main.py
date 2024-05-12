import requests
from datetime import datetime

# Set up OpenAI API credentials
api_key = "sk-proj-wQ4taTDDFhbuDrmkqIlOT3BlbkFJlJVo8Zlx0wucOcJ2atou"
api_model = "gpt-3.5-turbo"
temperature = 0.7

# Function to get destination suggestions from OpenAI ChatGPT
def get_destination_suggestions(trip_month, trip_type):
    messages = [
        {
            "role": "system",
            "content": f"Suggest 5 best places to visit in the month of {trip_month} for a {trip_type} trip."
        }
    ]
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "messages": messages,
                "model": api_model,
                "temperature": temperature
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            suggestion_text = data["choices"][0]["message"]["content"].strip()
            suggestions = suggestion_text.split("\n")
            return suggestions
        elif response.status_code == 401:
            raise Exception("Looks like your API key is incorrect. Please check your API key and try again.")
        else:
            raise Exception(f"Failed to fetch. Status code: {response.status_code}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

# Get user input
start_date_str = input("Enter the start date of your trip (YYYY-MM-DD): ")
end_date_str = input("Enter the end date of your trip (YYYY-MM-DD): ")
budget = float(input("Enter your total budget in USD for the trip (hotel+flights): "))
trip_type = input("Enter the type of trip (ski/beach/city): ")

# Convert start and end dates to datetime objects
start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

# Extract the month from the start date
trip_month = start_date.strftime("%B")

# Get destination suggestions from OpenAI ChatGPT
destination_suggestions = get_destination_suggestions(trip_month, trip_type)

# Print the destination suggestions
print("Destination Suggestions:")
for suggestion in destination_suggestions:
    print(suggestion)