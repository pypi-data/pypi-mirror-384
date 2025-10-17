"""
Basic usage example for the NetInt Agents SDK.

This example demonstrates the core functionality:
- Creating a client
- Managing environments
- Creating tasks
- Working with instances
"""

from netint_agents_sdk import NetIntClient, NetIntConfig
from netint_agents_sdk.models import (
    EnvironmentCreate,
    InstanceCreate,
    TaskCreate,
)


def main():
    # Create client with configuration
    config = NetIntConfig(
        base_url="http://10.0.10.125:8888",
        api_token="svc_7lmX1Av2ALIoq4SSLkJAEnRvVdtiS4MkBiQTjSIZbsrlvk6z",  # Replace with your token
        timeout=600,  # 10 minutes for long-running operations like instance creation
    )
    client = NetIntClient(config)

    # Or use environment variables
    # client = NetIntClient.from_env()

    try:
        # List environments
        print("=== Listing Environments ===")
        # environments = client.environments.list()
        # for env in environments:
        #     print(f"  {env.id}: {env.name} ({env.repository_path})")

        # # Get first environment (or create one)
        # if environments:
        #     env_id = environments[0].id
        # else:
        #     print("\n=== Creating Environment ===")
        #     env = client.environments.create(
        #         EnvironmentCreate(
        #             name="Example Environment",
        #             description="Created by SDK example",
        #             repository_path="ni-public-ai/example-repo",
        #             branch="main",
        #         )
        #     )
        #     env_id = env.id
        #     print(f"  Created environment: {env.id}")

        env_id = 66

        # Create a task
        print("\n=== Creating Task ===")
        task = client.tasks.create(
            TaskCreate(
                title="Create hello_world.md",
                description="Create a simple hello world markdown file",
                environment_id=env_id,
                ask_mode=False,
                mcp_servers={}
            )
        )
        print(f"  Task created: {task.id}")
        print(f"  Status: {task.status}")

        # Create an instance
        print("\n=== Creating Instance ===")
        instance = client.instances.create(
            InstanceCreate(
                env_id=env_id,
                prompt="Create a hello_world.md file with a friendly greeting",
                is_ask_mode=False,
                instance_name=f"example-task-{task.id}",
                task_id=task.id,
                mcp_servers={}
            )
        )
        print(f"  Instance created: {instance.instance_id}")
        print(f"  URL: {instance.instance_url}")
        print(f"  Status: {instance.status}")

        # Link instance to task
        print("\n=== Linking Instance to Task ===")
        task = client.tasks.link_instance(
            task_id=task.id,
            instance_id=instance.instance_id,
            instance_name=instance.instance_name,
            instance_url=instance.instance_url
        )
        print(f"  Task status updated: {task.status}")
        print(f"  AI status: {task.ai_status}")

        # Get task details
        print("\n=== Task Details ===")
        task = client.tasks.get(task.id)
        print(f"  Title: {task.title}")
        print(f"  Status: {task.status}")
        print(f"  Progress: {task.ai_progress}%")
        print(f"  Instance: {task.instance_url}")

        # List all tasks
        print("\n=== All Tasks ===")
        result = client.tasks.list(per_page=5)
        print(f"  Total tasks: {result['total']}")
        for task in result["tasks"]:
            print(f"    {task.id}: {task.title} ({task.status})")

        # Get task statistics
        print("\n=== Task Statistics ===")
        stats = client.tasks.get_stats()
        print(f"  Total: {stats.total_tasks}")
        print(f"  Pending: {stats.pending_tasks}")
        print(f"  In Progress: {stats.in_progress_tasks}")
        print(f"  Completed: {stats.completed_tasks}")

    finally:
        # Clean up
        client.close()


if __name__ == "__main__":
    main()
