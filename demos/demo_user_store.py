from app.api.user_store import (
    initialize_database,
    create_user,
    authenticate_api_key,
    deactivate_user
)

initialize_database()

api_key = create_user("kishan_test", "admin")

print("Generated API key:", api_key)

user = authenticate_api_key(api_key)
print("Authenticated user:", user)

deactivate_user("kishan_test")

user = authenticate_api_key(api_key)
print("After deactivation:", user)