from app.core.llm import get_ai_response

def perform_action(user_input: str) -> str:
    # You can add more parsing logic later
    return get_ai_response(user_input)
