from app.api.user_store import authenticate_api_key

api_key = input("Enter your admin API key: ")

user = authenticate_api_key(api_key)

print("Authenticated user:", user)