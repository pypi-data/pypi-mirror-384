import os
import argparse
import asyncio
from src.henotace_ai import HenotaceAI, create_tutor


async def run_chat(args):
    api_key = args.api_key or os.getenv("HENOTACE_API_KEY")
    if not api_key:
        print("Error: Provide --api-key or set HENOTACE_API_KEY env var")
        return 1

    sdk = HenotaceAI(api_key=api_key)
    tutor = await create_tutor(
        sdk=sdk,
        student_id=args.student_id or "cli_student",
        tutor_name=args.tutor_name or "cli_tutor",
    )

    if args.persona:
        tutor.set_persona(args.persona)

    if args.context:
        tutor.set_context(args.context)

    if args.message:
        reply = await tutor.send(args.message)
        print(reply)
        return 0

    # REPL mode
    print("Henotace CLI - type 'exit' to quit")
    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg or msg.lower() in {"exit", "quit"}:
            break
        ai = await tutor.send(msg)
        print(f"AI: {ai}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Henotace AI Python SDK CLI")
    parser.add_argument("message", nargs="?", help="Message to send (omit for interactive mode)")
    parser.add_argument("--api-key", dest="api_key", help="Henotace API key")
    parser.add_argument("--student-id", dest="student_id", help="Student ID")
    parser.add_argument("--tutor-name", dest="tutor_name", help="Tutor name")
    parser.add_argument("--persona", dest="persona", help="Tutor persona text")
    parser.add_argument("--context", dest="context", nargs="*", help="Context lines")

    args = parser.parse_args()
    try:
        exit(asyncio.run(run_chat(args)))
    except RuntimeError:
        # In case of already running loop (e.g., some environments)
        loop = asyncio.get_event_loop()
        exit(loop.run_until_complete(run_chat(args)))


if __name__ == "__main__":
    main()


