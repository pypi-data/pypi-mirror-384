"""
Simple task creation example demonstrating the convenience method.

This example shows how easy it is to create and run a task with just one method call.
It also demonstrates the new SDK methods for:
- Monitoring task completion with automatic polling
- Fetching AI conversation history
- Getting git changes with full diff content
"""

from netint_agents_sdk import NetIntClient, NetIntConfig


def main():
    # Create client
    config = NetIntConfig(
        base_url="http://10.0.10.125:8888",
        api_token="svc_7lmX1Av2ALIoq4SSLkJAEnRvVdtiS4MkBiQTjSIZbsrlvk6z",
        timeout=600,  # 10 minutes for instance creation
        debug=True
    )
    client = NetIntClient(config)

    try:
        print("=== Creating Task with Instance (One-Liner) ===")
        task = client.tasks.create_with_instance(
            title="Create hello_world.md",
            prompt="Create a hello_world.md file with a friendly greeting",
            environment_id=66,
            description="Simple hello world task created via SDK",
            ask_mode=False,
        )

        print(f"✅ Task created successfully!")
        print(f"   Task ID: {task.id}")
        print(f"   Title: {task.title}")
        print(f"   Status: {task.status}")
        print(f"   AI Status: {task.ai_status}")
        print(f"   Instance URL: {task.instance_url}")
        print(f"   Progress: {task.ai_progress}%")

        # ============================================
        # Wait for Task Completion
        # ============================================
        print("\n=== Monitoring Task (New SDK Method) ===")

        # Define a callback for progress updates
        def on_progress(task):
            print(f"Progress: {task.ai_progress}% - Status: {task.ai_status}")

        # Wait for completion with automatic polling
        try:
            final_task = client.tasks.wait_for_completion(
                task.id,
                poll_interval=10,  # Check every 10 seconds
                timeout=600,       # Timeout after 10 minutes
                callback=on_progress  # Custom progress callback
            )
            print("✅ Task completed!")
        except TimeoutError as e:
            print(f"⏱️  Timeout: {e}")
        except Exception as e:
            print(f"❌ Task failed: {e}")

        # ============================================
        # Get AI Conversation History (Existing SDK Method)
        # ============================================
        print("\n=== AI Conversation History ===")
        ai_messages = client.tasks.get_ai_messages(task.id)
        print(f"Total AI messages: {len(ai_messages)}")
        for i, msg in enumerate(ai_messages, 1):
            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            print(f"  {i}. [{msg.role}] {content_preview}")

        # ============================================
        # Get Git Changes
        # ============================================
        print("\n=== Git Changes (New SDK Method) ===")
        try:
            # Fetch git changes using the new SDK method
            git_data = client.tasks.get_git_changes(task.id, include_patch=True)

            print(f"Files changed: {git_data.get('files_changed', 0)}")
            print(f"Insertions: +{git_data.get('insertions', 0)}")
            print(f"Deletions: -{git_data.get('deletions', 0)}")

            print("\n=== Changed Files ===")
            for file_change in git_data.get('files', []):
                filename = file_change.get('path', 'unknown')
                insertions = file_change.get('insertions', 0)
                deletions = file_change.get('deletions', 0)
                patch = file_change.get('patch', '')

                print(f"[{filename} (+{insertions}/-{deletions})]")
                print(patch)
                print("-----")
        except ValueError as e:
            print(f"⚠️  No git changes available: {e}")
        except Exception as e:
            print(f"❌ Error fetching git changes: {e}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
