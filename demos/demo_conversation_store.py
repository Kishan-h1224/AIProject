from app.memory.conversation_store import (
    initialize_conversation_db,
    save_message,
    get_conversation
)

print("Initializing database...")
initialize_conversation_db()

user_id = 1
conversation_id = "conversation_001"

print("Saving messages...")

save_message(
    user_id,
    conversation_id,
    "user",
    "My name is Kishan"
)

save_message(
    user_id,
    conversation_id,
    "assistant",
    "Nice to meet you, Kishan"
)

print("Retrieving conversation...")

history = get_conversation(user_id, conversation_id)

print("Total messages:", len(history))

for message in history:
    print(message)