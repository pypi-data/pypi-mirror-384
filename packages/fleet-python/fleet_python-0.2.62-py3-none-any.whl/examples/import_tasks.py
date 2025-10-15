import asyncio
import argparse
import json
import sys
import fleet
from dotenv import load_dotenv

load_dotenv()


async def main():
    parser = argparse.ArgumentParser(description="Import tasks from a JSON file")
    parser.add_argument("json_file", help="Path to the JSON file containing tasks")
    parser.add_argument(
        "--project-key",
        "-p",
        help="Optional project key to associate with the tasks",
        default=None,
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt and import automatically",
    )

    args = parser.parse_args()

    # Load and parse the JSON file
    try:
        with open(args.json_file, "r", encoding="utf-8") as f:
            tasks_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{args.json_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{args.json_file}': {e}")
        sys.exit(1)

    # Extract task information and validate verifier_func
    task_count = len(tasks_data)
    task_keys = []
    missing_verifier = []
    for task_data in tasks_data:
        task_key = task_data.get("key") or task_data.get("id")
        if task_key:
            task_keys.append(task_key)
        else:
            task_keys.append("(no key)")
        
        # Check for verifier_func
        verifier_code = task_data.get("verifier_func") or task_data.get("verifier_code")
        if not verifier_code:
            missing_verifier.append(task_key or "(no key)")

    # Validate all tasks have verifier_func
    if missing_verifier:
        print(f"✗ Error: {len(missing_verifier)} task(s) missing verifier_func:")
        for key in missing_verifier[:10]:  # Show first 10
            print(f"  - {key}")
        if len(missing_verifier) > 10:
            print(f"  ... and {len(missing_verifier) - 10} more")
        print("\nAll tasks must have a verifier_func to be imported.")
        sys.exit(1)

    # Get account info
    account = await fleet.env.account_async()

    # Print summary
    print(f"Importing to team: {account.team_name}")
    print(f"\nFound {task_count} task(s) in '{args.json_file}':")
    print("\nTask keys:")
    for i, key in enumerate(task_keys, 1):
        print(f"  {i}. {key}")

    if args.project_key:
        print(f"\nProject key: {args.project_key}")
    else:
        print("\nProject key: (none)")

    # Confirmation prompt (unless --yes flag is provided)
    if not args.yes:
        print("\n" + "=" * 60)
        response = input("Type 'YES' to proceed with import: ")
        if response != "YES":
            print("Import cancelled.")
            sys.exit(0)

    # Import tasks
    print("\nImporting tasks...")
    try:
        results = await fleet.import_tasks_async(
            args.json_file, project_key=args.project_key
        )
        print(f"\n✓ Successfully imported {len(results)} task(s)")
    except Exception as e:
        print(f"\n✗ Error importing tasks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
