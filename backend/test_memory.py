from conversation_memory import ConversationMemory

memory = ConversationMemory()

memory.add_examiner_message("Where are you from?")
memory.add_candidate_message("I'm from Mymensingh.")
memory.add_examiner_message("What do you like about your hometown?")
memory.add_candidate_message("I like the peaceful environment.")

for message in memory.get_messages():
    print(message["role"], ":", message["content"])
