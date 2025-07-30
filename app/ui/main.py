from app.ui.state import init_session_state
from app.ui.chat_ui import render_chat_ui  # To be added in Step 2

def main():
    init_session_state()
    render_chat_ui()

if __name__ == "__main__":
    main()
