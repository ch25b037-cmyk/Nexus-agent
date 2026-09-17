# chat_cli.py
from app.db.session import SessionLocal
from app.agent.core import run_agent_turn


def main():
    print("=" * 60)
    print("🤖 NEXUS Career Intelligence Agent — Interactive Console")
    print("Ask questions about your jobs, top skills, or search by tech stack.")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 60 + "\n")

    db = SessionLocal()
    conversation_history = []

    try:
        while True:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye!")
                break

            response = run_agent_turn(db, conversation_history, user_input)
            print(f"\nNEXUS > {response}\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()