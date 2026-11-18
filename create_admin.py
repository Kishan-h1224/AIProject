
from app.api.user_store import initialize_database, create_user

initialize_database()

api_key = create_user(
    username="kishan1",
    role="admin"
)

print("Your API key:", api_key)
