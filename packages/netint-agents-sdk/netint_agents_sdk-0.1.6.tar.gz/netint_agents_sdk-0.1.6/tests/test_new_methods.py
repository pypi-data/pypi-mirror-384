"""
Tests for the new user-friendly SDK methods:
- wait_for_completion()
- get_git_changes()
"""

import pytest
import requests
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from netint_agents_sdk.resources.tasks import TasksResource
from netint_agents_sdk.models.task import Task, TaskStatus


def create_mock_task_data(**overrides):
    """Helper to create complete task data with required fields"""
    base_data = {
        "id": 1,
        "user_id": 1,
        "title": "Test Task",
        "status": "in_progress",
        "ai_status": "running",
        "ai_progress": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    base_data.update(overrides)
    return base_data


class TestWaitForCompletion:
    """Tests for the wait_for_completion method"""

    def test_wait_for_completion_success(self):
        """Test waiting for a successful task completion"""
        # Create mock HTTP client
        mock_http = Mock()

        # Simulate task progressing through states
        task_states = [
            create_mock_task_data(ai_status="running", ai_progress=20),
            create_mock_task_data(ai_status="running", ai_progress=50),
            create_mock_task_data(ai_status="running", ai_progress=80),
            create_mock_task_data(ai_status="succeeded", ai_progress=100, status="completed"),
        ]

        mock_http.get.side_effect = task_states

        # Create TasksResource with mock
        tasks = TasksResource(mock_http)

        # Mock time.sleep to speed up test
        with patch('time.sleep'):
            result = tasks.wait_for_completion(1, poll_interval=1)

        assert result.ai_status == "succeeded"
        assert result.ai_progress == 100
        assert mock_http.get.call_count == 4

    def test_wait_for_completion_with_callback(self):
        """Test wait_for_completion with progress callback"""
        mock_http = Mock()

        task_states = [
            create_mock_task_data(ai_status="running", ai_progress=30),
            create_mock_task_data(ai_status="succeeded", ai_progress=100, status="completed"),
        ]

        mock_http.get.side_effect = task_states
        tasks = TasksResource(mock_http)

        # Track callback calls
        callback_calls = []
        def progress_callback(task):
            callback_calls.append((task.ai_progress, task.ai_status))

        with patch('time.sleep'):
            result = tasks.wait_for_completion(1, callback=progress_callback)

        assert len(callback_calls) == 2
        assert callback_calls[0] == (30, "running")
        assert callback_calls[1] == (100, "succeeded")

    def test_wait_for_completion_timeout(self):
        """Test timeout handling"""
        mock_http = Mock()

        # Task never completes
        mock_http.get.return_value = create_mock_task_data(
            ai_status="running",
            ai_progress=50
        )

        tasks = TasksResource(mock_http)

        # Mock time to trigger timeout
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 10, 20, 31]  # Exceeds 30s timeout

            with pytest.raises(TimeoutError) as exc_info:
                with patch('time.sleep'):
                    tasks.wait_for_completion(1, timeout=30, poll_interval=1)

            assert "did not complete within 30 seconds" in str(exc_info.value)

    def test_wait_for_completion_failure(self):
        """Test handling task failure"""
        mock_http = Mock()

        task_states = [
            create_mock_task_data(ai_status="running", ai_progress=20),
            create_mock_task_data(ai_status="failed", ai_progress=25, ai_error="Something went wrong", status="failed"),
        ]

        mock_http.get.side_effect = task_states
        tasks = TasksResource(mock_http)

        with pytest.raises(Exception) as exc_info:
            with patch('time.sleep'):
                tasks.wait_for_completion(1)

        assert "Something went wrong" in str(exc_info.value)


class TestGetGitChanges:
    """Tests for the get_git_changes method"""

    def test_get_git_changes_with_patch(self):
        """Test fetching git changes with patch content"""
        mock_http = Mock()

        # Mock task with instance URL
        mock_http.get.return_value = create_mock_task_data(
            instance_url="http://localhost:8100",
            status="completed"
        )

        tasks = TasksResource(mock_http)

        # Mock requests.get for git changes
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "files_changed": 2,
            "insertions": 50,
            "deletions": 10,
            "files": [
                {
                    "path": "app.py",
                    "status": "modified",
                    "insertions": 30,
                    "deletions": 5,
                    "patch": "@@ -1,5 +1,10 @@\n+import logging\n"
                },
                {
                    "path": "test.py",
                    "status": "added",
                    "insertions": 20,
                    "deletions": 5,
                    "patch": "@@ -0,0 +1,20 @@\n+def test():\n"
                }
            ]
        }

        with patch('requests.get', return_value=mock_response):
            result = tasks.get_git_changes(1, include_patch=True)

        assert result['files_changed'] == 2
        assert result['insertions'] == 50
        assert result['deletions'] == 10
        assert len(result['files']) == 2
        assert result['files'][0]['path'] == 'app.py'
        assert 'patch' in result['files'][0]

    def test_get_git_changes_without_patch(self):
        """Test fetching git changes without patch content"""
        mock_http = Mock()

        mock_http.get.return_value = create_mock_task_data(
            instance_url="http://localhost:8100",
            status="completed"
        )

        tasks = TasksResource(mock_http)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "files_changed": 2,
            "insertions": 50,
            "deletions": 10,
            "files": []
        }

        with patch('requests.get', return_value=mock_response) as mock_req:
            result = tasks.get_git_changes(1, include_patch=False)

            # Verify the correct parameter was sent
            call_args = mock_req.call_args
            assert call_args[1]['params']['patch'] == 'false'

        assert result['files_changed'] == 2

    def test_get_git_changes_no_instance_url(self):
        """Test error when task has no instance URL"""
        mock_http = Mock()

        # Task without instance URL
        mock_http.get.return_value = create_mock_task_data(
            instance_url=None,
            status="pending"
        )

        tasks = TasksResource(mock_http)

        with pytest.raises(ValueError) as exc_info:
            tasks.get_git_changes(1)

        assert "no associated instance URL" in str(exc_info.value)

    def test_get_git_changes_request_error(self):
        """Test handling of request errors"""
        mock_http = Mock()

        mock_http.get.return_value = create_mock_task_data(
            instance_url="http://localhost:8100",
            status="completed"
        )

        tasks = TasksResource(mock_http)

        # Mock requests to raise a RequestException
        with patch('requests.get', side_effect=requests.RequestException("Connection error")):
            with pytest.raises(Exception) as exc_info:
                tasks.get_git_changes(1)

            assert "Failed to fetch git changes" in str(exc_info.value)
            assert "Connection error" in str(exc_info.value)


class TestIntegration:
    """Integration tests for the new methods"""

    def test_complete_workflow(self):
        """Test a complete workflow: create task, wait, get results"""
        mock_http = Mock()

        # Sequence: get task twice (polling), then final state
        mock_http.get.side_effect = [
            create_mock_task_data(ai_progress=50, ai_status="running", instance_url="http://localhost:8100"),
            create_mock_task_data(ai_progress=100, ai_status="succeeded", status="completed", instance_url="http://localhost:8100"),
            create_mock_task_data(ai_progress=100, ai_status="succeeded", status="completed", instance_url="http://localhost:8100"),  # For get_git_changes
        ]

        tasks = TasksResource(mock_http)

        # Wait for completion
        with patch('time.sleep'):
            result = tasks.wait_for_completion(1)

        assert result.ai_status == "succeeded"

        # Get git changes
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "files_changed": 1,
            "insertions": 10,
            "deletions": 2,
            "files": []
        }

        with patch('requests.get', return_value=mock_response):
            git_data = tasks.get_git_changes(1)

        assert git_data['files_changed'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
