"""
Task Monitoring Example - Demonstrating User-Friendly SDK Methods

This example showcases the three main user-friendly methods for task management:
1. wait_for_completion() - Automated task monitoring with polling
2. get_ai_messages() - Fetch AI conversation history
3. get_git_changes() - Get git diff from task instance

These methods wrap complex operations into simple, intuitive SDK calls.
"""

from netint_agents_sdk import NetIntClient, NetIntConfig


def main():
    # ============================================
    # Setup
    # ============================================
    config = NetIntConfig(
        base_url="http://10.0.10.125:8888",
        api_token="svc_7lmX1Av2ALIoq4SSLkJAEnRvVdtiS4MkBiQTjSIZbsrlvk6z",
        timeout=600,
    )
    client = NetIntClient(config)

    try:
        # ============================================
        # Create Task with Instance (One-Liner)
        # ============================================
        print("🚀 Creating task with instance...")
        task = client.tasks.create_with_instance(
            title="Add logging functionality",
            prompt="Add comprehensive logging to the main application file with info, warning, and error levels",
            environment_id=66,
            description="Enhance application with proper logging",
            ask_mode=False,
        )
        print(f"✅ Task created: {task.id}")
        print(f"   Instance URL: {task.instance_url}")

        # ============================================
        # METHOD 1: wait_for_completion()
        # Automatic polling with progress tracking
        # ============================================
        print("\n" + "="*60)
        print("METHOD 1: Automated Task Monitoring")
        print("="*60)

        # Example 1a: Simple wait (blocking)
        print("\n📊 Waiting for task completion...")

        def progress_callback(task):
            """Custom callback to display progress updates"""
            status_icon = "🔄" if task.ai_status == "running" else "⏳"
            print(f"{status_icon} Progress: {task.ai_progress}% | Status: {task.ai_status}")

        try:
            final_task = client.tasks.wait_for_completion(
                task.id,
                poll_interval=10,        # Check every 10 seconds
                timeout=600,             # 10 minute timeout
                callback=progress_callback  # Optional progress callback
            )
            print(f"\n✅ Task completed successfully!")
            print(f"   Final progress: {final_task.ai_progress}%")
            print(f"   Status: {final_task.ai_status}")

        except TimeoutError as e:
            print(f"\n⏱️  Task timed out: {e}")
            return
        except Exception as e:
            print(f"\n❌ Task failed: {e}")
            return

        # ============================================
        # METHOD 2: get_ai_messages()
        # Fetch complete AI conversation history
        # ============================================
        print("\n" + "="*60)
        print("METHOD 2: AI Conversation History")
        print("="*60)

        ai_messages = client.tasks.get_ai_messages(task.id)
        print(f"\n💬 Total AI messages: {len(ai_messages)}")
        print("\nConversation Summary:")

        for i, msg in enumerate(ai_messages, 1):
            # Create readable preview
            content_preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
            role_icon = "👤" if msg.role == "user" else "🤖"

            print(f"{i}. {role_icon} [{msg.role}] {content_preview}")

        # Show full content of last message
        if ai_messages:
            last_msg = ai_messages[-1]
            print(f"\n📝 Last message (full content):")
            print(f"   Role: {last_msg.role}")
            print(f"   Timestamp: {last_msg.timestamp}")
            print(f"   Content:\n{last_msg.content[:500]}...")

        # ============================================
        # METHOD 3: get_git_changes()
        # Fetch git diff from task instance
        # ============================================
        print("\n" + "="*60)
        print("METHOD 3: Git Changes Analysis")
        print("="*60)

        try:
            # Fetch with full patch content
            git_data = client.tasks.get_git_changes(task.id, include_patch=True)

            print(f"\n📊 Change Summary:")
            print(f"   Files changed: {git_data.get('files_changed', 0)}")
            print(f"   Lines added:   +{git_data.get('insertions', 0)}")
            print(f"   Lines removed: -{git_data.get('deletions', 0)}")

            # Show file-by-file breakdown
            files = git_data.get('files', [])
            if files:
                print(f"\n📁 Changed Files ({len(files)}):")
                for file_change in files:
                    filename = file_change.get('path', 'unknown')
                    status = file_change.get('status', 'modified')
                    insertions = file_change.get('insertions', 0)
                    deletions = file_change.get('deletions', 0)

                    status_icon = "✨" if status == "added" else "🔄" if status == "modified" else "🗑️"
                    print(f"   {status_icon} {filename} (+{insertions}/-{deletions}) [{status}]")

                # Show full diff for first file
                if files and git_data.get('files', [])[0].get('patch'):
                    print(f"\n📄 Diff for {files[0]['path']}:")
                    print("-" * 60)
                    print(files[0]['patch'])
                    print("-" * 60)

            # Example: Fetch without patch (faster, for summaries only)
            print("\n⚡ Quick summary (without patch):")
            quick_summary = client.tasks.get_git_changes(task.id, include_patch=False)
            print(f"   Files: {quick_summary.get('files_changed', 0)}")
            print(f"   Impact: +{quick_summary.get('insertions', 0)}/-{quick_summary.get('deletions', 0)}")

        except ValueError as e:
            print(f"\n⚠️  Git changes not available: {e}")
        except Exception as e:
            print(f"\n❌ Error fetching git changes: {e}")

        # ============================================
        # Comparison: Old vs New Approach
        # ============================================
        print("\n" + "="*60)
        print("COMPARISON: Old vs New Approach")
        print("="*60)

        print("""
OLD WAY (Manual Implementation):
---------------------------------
# Task monitoring - manual while loop
import time
while True:
    time.sleep(10)
    task = client.tasks.get(task.id)
    if task.ai_status == "succeeded":
        break
    if task.ai_status == "failed":
        break

# Git changes - manual HTTP requests
import requests
response = requests.get(f"{task.instance_url}/api/git/changes?patch=true")
git_data = response.json()

NEW WAY (SDK Methods):
----------------------
# Task monitoring - one method call
final_task = client.tasks.wait_for_completion(
    task.id,
    callback=progress_callback
)

# Git changes - one method call
git_data = client.tasks.get_git_changes(task.id)

Benefits:
- ✅ Cleaner code
- ✅ Better error handling
- ✅ Automatic retries
- ✅ Built-in timeout support
- ✅ Progress callbacks
- ✅ Type-safe responses
        """)

    finally:
        client.close()
        print("\n👋 Example complete!")


if __name__ == "__main__":
    main()
