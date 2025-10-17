"""
Complete workflow example for the NetInt Agents SDK.

This example demonstrates a full end-to-end workflow:
1. Create a task
2. Create an instance
3. Monitor setup and execution
4. Get git changes
5. Commit and push changes
"""

import time

from netint_agents_sdk import NetIntClient
from netint_agents_sdk.models import InstanceCreate, TaskCreate


def wait_for_setup(client: NetIntClient, task_id: int, max_wait: int = 300):
    """Wait for environment setup to complete."""
    print("Waiting for environment setup...")
    start_time = time.time()

    while time.time() - start_time < max_wait:
        status = client.tasks.get_setup_status(task_id)

        if status.can_run_ai:
            print("✓ Environment setup complete")
            return True
        elif status.setup_status == 1:
            print("✗ Setup failed:", status.message)
            return False

        print(f"  Setup in progress... ({int(time.time() - start_time)}s)")
        time.sleep(5)

    print("✗ Setup timed out")
    return False


def monitor_task_progress(client: NetIntClient, task_id: int, max_wait: int = 600):
    """Monitor task execution progress."""
    print("Monitoring task progress...")
    start_time = time.time()
    last_progress = -1

    while time.time() - start_time < max_wait:
        task = client.tasks.get(task_id)

        if task.ai_progress != last_progress:
            print(f"  Progress: {task.ai_progress}% - Status: {task.status}")
            last_progress = task.ai_progress

        if task.status == "completed":
            print("✓ Task completed")
            return True
        elif task.status == "failed":
            print(f"✗ Task failed: {task.ai_error}")
            return False

        time.sleep(10)

    print("✗ Task execution timed out")
    return False


def main():
    # Initialize client from environment variables
    client = NetIntClient.from_env()

    try:
        # Step 1: Create a task
        print("=== Step 1: Creating Task ===")
        task = client.tasks.create(
            TaskCreate(
                title="Implement feature X",
                description="Add a new feature to the application with tests",
                environment_id=65,  # Replace with your environment ID
                ask_mode=False,
                tags=["feature", "automated"],
            )
        )
        print(f"✓ Task created: {task.id}")
        print(f"  Title: {task.title}")

        # Step 2: Create an instance
        print("\n=== Step 2: Creating Instance ===")
        instance = client.instances.create(
            InstanceCreate(
                env_id=65,  # Replace with your environment ID
                prompt="Implement feature X as described in the task",
                is_ask_mode=False,
                instance_name=f"feature-x-{task.id}",
                task_id=task.id,
            )
        )
        print(f"✓ Instance created: {instance.instance_id}")
        print(f"  URL: {instance.instance_url}")

        # Step 3: Link instance to task
        print("\n=== Step 3: Linking Instance to Task ===")
        task = client.tasks.link_instance(
            task_id=task.id,
            instance_id=instance.instance_id,
            instance_name=instance.instance_name,
            instance_url=instance.instance_url,
        )
        print(f"✓ Instance linked")
        print(f"  Task status: {task.status}")
        print(f"  AI status: {task.ai_status}")

        # Step 4: Wait for environment setup
        print("\n=== Step 4: Environment Setup ===")
        if not wait_for_setup(client, task.id):
            print("Aborting due to setup failure")
            return

        # Step 5: Monitor task execution
        print("\n=== Step 5: Task Execution ===")
        if not monitor_task_progress(client, task.id):
            print("Task did not complete successfully")
            return

        # Step 6: Get AI messages
        print("\n=== Step 6: AI Conversation ===")
        messages = client.tasks.get_ai_messages(task.id)
        print(f"Total messages: {len(messages)}")
        for msg in messages[-3:]:  # Show last 3 messages
            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            print(f"  {msg.role}: {content_preview}")

        # Step 7: Get git changes
        print("\n=== Step 7: Git Changes ===")
        changes = client.git.get_changes(
            instance_url=instance.instance_url, task_id=task.id, include_patch=False
        )
        print(f"Repository: {changes.repository.name}")
        print(f"Branch: {changes.repository.branch}")
        print(f"Files changed: {changes.changes.total_files}")
        print(f"Additions: +{changes.changes.additions}")
        print(f"Deletions: -{changes.changes.deletions}")

        for file in changes.changes.files:
            print(f"  {file.status:8s} {file.path:40s} +{file.additions} -{file.deletions}")

        # Step 8: Commit changes
        print("\n=== Step 8: Committing Changes ===")
        commit_result = client.git.commit_unstaged(instance.instance_url, task.id)

        if commit_result.success:
            print(f"✓ Commit successful")
            print(f"  SHA: {commit_result.commit_sha}")
            print(f"  Files: {commit_result.files_committed}")
            print(f"  Message: {commit_result.message[:80]}...")

            # Step 9: Push changes
            print("\n=== Step 9: Pushing Changes ===")
            push_result = client.git.push(instance.instance_url, task.id)

            if push_result.success:
                print(f"✓ Push successful")
                print(f"  Branch: {push_result.branch}")
                print(f"  Commits: {push_result.pushed_commits}")
            else:
                print(f"✗ Push failed: {push_result.message}")
        else:
            print(f"✗ Commit failed: {commit_result.message}")

        # Step 10: Final task status
        print("\n=== Step 10: Final Status ===")
        task = client.tasks.get(task.id)
        print(f"Task: {task.title}")
        print(f"Status: {task.status}")
        print(f"Progress: {task.ai_progress}%")
        print(f"Git changes: {task.git_changes} files")
        print(f"Lines: +{task.git_additions} -{task.git_deletions}")

        print("\n✓ Workflow completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise

    finally:
        client.close()


if __name__ == "__main__":
    main()
