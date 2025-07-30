from app.core.llm import get_ai_response

def perform_action(user_input: str, api_key=None) -> str:
    # You can add more parsing logic later
    return get_ai_response(user_input, api_key=api_key)
