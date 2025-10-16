"""Tests for the helper_test module."""
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from taskqueue.libs.helper_test import assert_task_in_queue
from taskqueue.libs.helper_test import assert_task_not_in_queue
from taskqueue.libs.helper_test import celery_worker_burst
from taskqueue.libs.helper_test import clear_all_celery_queues
from taskqueue.libs.helper_test import get_queued_tasks
from taskqueue.libs.helper_test import is_task_in_queue


def setup_celery_connection_mocks(mock_current_app):
    """Helper to setup Celery connection and channel mocks."""
    mock_conn = MagicMock()
    mock_chan = MagicMock()
    mock_current_app.connection_for_read.return_value.__enter__.return_value = mock_conn
    mock_conn.channel.return_value.__enter__.return_value = mock_chan
    return mock_conn, mock_chan


class TestHelperTest:

    @patch('taskqueue.libs.helper_test.current_app')
    def test_clear_all_celery_queues_given_multiple_queues_expect_all_purged(self, mock_current_app):
        mock_conn, mock_chan = setup_celery_connection_mocks(mock_current_app)

        mock_queue1 = MagicMock()
        mock_queue2 = MagicMock()
        mock_queue_factory1 = MagicMock(return_value=mock_queue1)
        mock_queue_factory2 = MagicMock(return_value=mock_queue2)

        mock_current_app.amqp.queues.keys.return_value = ['queue1', 'queue2']
        mock_current_app.amqp.queues = {
            'queue1': mock_queue_factory1,
            'queue2': mock_queue_factory2
        }

        clear_all_celery_queues()

        mock_queue_factory1.assert_called_once_with(mock_chan)
        mock_queue_factory2.assert_called_once_with(mock_chan)
        mock_queue1.purge.assert_called_once()
        mock_queue2.purge.assert_called_once()

    @patch('taskqueue.libs.helper_test.current_app')
    def test_clear_all_celery_queues_given_empty_queues_expect_no_purge_calls(self, mock_current_app):
        mock_conn, mock_chan = setup_celery_connection_mocks(mock_current_app)

        mock_current_app.amqp.queues.keys.return_value = []
        mock_current_app.amqp.queues = {}

        clear_all_celery_queues()

        mock_conn.channel.assert_called_once()

    @patch('taskqueue.libs.helper_test.current_app')
    def test_get_queued_tasks_given_empty_queue_expect_empty_list(self, mock_current_app):
        mock_queue = MagicMock()
        mock_queue.get.return_value = None
        mock_current_app.amqp.queues = {
            'default': MagicMock(return_value=mock_queue)}

        result = get_queued_tasks('default')

        assert result == []

    @patch('taskqueue.libs.helper_test.current_app')
    @patch('taskqueue.libs.helper_test.loads')
    def test_get_queued_tasks_given_function_executor_expect_correct_parsing(self, mock_loads, mock_current_app):
        mock_message = MagicMock()
        mock_message.headers = {
            'task': 'taskqueue.cmanager.dynamic_function_executor'}
        mock_message.body = b'mock_body'
        mock_message.content_type = 'application/json'
        mock_message.content_encoding = 'utf-8'

        mock_loads.return_value = [[], {
            'module_path': 'my.module',
            'function_name': 'my_function',
            'args': [],
            'kwargs': {}
        }]

        mock_queue = MagicMock()
        mock_queue.get.side_effect = [mock_message, None]
        mock_current_app.amqp.queues = {
            'default': MagicMock(return_value=mock_queue)}

        mock_conn = MagicMock()
        mock_chan = MagicMock()
        mock_current_app.connection_for_read.return_value.__enter__.return_value = mock_conn
        mock_conn.channel.return_value.__enter__.return_value = mock_chan

        result = get_queued_tasks('default')

        assert len(result) == 1
        assert result[0]['task_name'] == 'taskqueue.cmanager.dynamic_function_executor'
        assert result[0]['full_func_name'] == 'my.module.my_function'
        assert result[0]['args'] == []
        assert result[0]['kwargs']['module_path'] == 'my.module'
        assert result[0]['kwargs']['function_name'] == 'my_function'

    @patch('taskqueue.libs.helper_test.current_app')
    @patch('taskqueue.libs.helper_test.loads')
    def test_get_queued_tasks_given_class_method_executor_expect_correct_parsing(self, mock_loads, mock_current_app):
        mock_message = MagicMock()
        mock_message.headers = {
            'task': 'taskqueue.cmanager.dynamic_class_method_executor'}
        mock_message.body = b'mock_body'
        mock_message.content_type = 'application/json'
        mock_message.content_encoding = 'utf-8'

        mock_loads.return_value = [[], {
            'module_path': 'my.module',
            'class_name': 'MyClass',
            'method_name': 'my_method',
            'args': [],
            'kwargs': {}
        }]

        mock_queue = MagicMock()
        mock_queue.get.side_effect = [mock_message, None]
        mock_current_app.amqp.queues = {
            'default': MagicMock(return_value=mock_queue)}

        mock_conn = MagicMock()
        mock_chan = MagicMock()
        mock_current_app.connection_for_read.return_value.__enter__.return_value = mock_conn
        mock_conn.channel.return_value.__enter__.return_value = mock_chan

        result = get_queued_tasks('default')

        assert len(result) == 1
        assert result[0]['task_name'] == 'taskqueue.cmanager.dynamic_class_method_executor'
        assert result[0]['full_func_name'] == 'my.module.MyClass.my_method'
        assert result[0]['args'] == []
        assert result[0]['kwargs']['module_path'] == 'my.module'
        assert result[0]['kwargs']['class_name'] == 'MyClass'
        assert result[0]['kwargs']['method_name'] == 'my_method'

    @patch('taskqueue.libs.helper_test.get_queued_tasks')
    def test_is_task_in_queue_given_task_exists_expect_true(self, mock_get_queued_tasks):
        mock_get_queued_tasks.return_value = [
            {'full_func_name': 'my.module.my_function'},
            {'full_func_name': 'other.module.other_function'}
        ]

        result = is_task_in_queue('my.module.my_function')

        assert result is True

    @patch('taskqueue.libs.helper_test.get_queued_tasks')
    def test_is_task_in_queue_given_task_not_exists_expect_false(self, mock_get_queued_tasks):
        mock_get_queued_tasks.return_value = [
            {'full_func_name': 'other.module.other_function'}
        ]

        result = is_task_in_queue('my.module.my_function')

        assert result is False

    @patch('taskqueue.libs.helper_test.get_queued_tasks')
    def test_is_task_in_queue_given_custom_channel_expect_channel_used(self, mock_get_queued_tasks):
        mock_get_queued_tasks.return_value = [
            {'full_func_name': 'my.module.my_function'}
        ]

        result = is_task_in_queue('my.module.my_function', channel='high')

        assert result is True
        mock_get_queued_tasks.assert_called_once_with('high')

    @patch('taskqueue.libs.helper_test.is_task_in_queue')
    def test_assert_task_in_queue_given_task_exists_expect_no_exception(self, mock_is_task_in_queue):
        mock_is_task_in_queue.return_value = True

        assert_task_in_queue('my.module.my_function')

    @patch('taskqueue.libs.helper_test.is_task_in_queue')
    def test_assert_task_in_queue_given_task_not_exists_expect_assertion_error(self, mock_is_task_in_queue):
        mock_is_task_in_queue.return_value = False

        with pytest.raises(AssertionError, match="Task 'my.module.my_function' not found in queue 'default'"):
            assert_task_in_queue('my.module.my_function')

    @patch('taskqueue.libs.helper_test.is_task_in_queue')
    def test_assert_task_in_queue_given_custom_message_expect_custom_error(self, mock_is_task_in_queue):
        mock_is_task_in_queue.return_value = False

        with pytest.raises(AssertionError, match="Custom error message"):
            assert_task_in_queue('my.module.my_function',
                                 msg="Custom error message")

    @patch('taskqueue.libs.helper_test.is_task_in_queue')
    def test_assert_task_in_queue_given_custom_channel_expect_channel_used(self, mock_is_task_in_queue):
        mock_is_task_in_queue.return_value = True

        assert_task_in_queue('my.module.my_function', channel='high')

        mock_is_task_in_queue.assert_called_once_with(
            'my.module.my_function', 'high')

    @patch('taskqueue.libs.helper_test.is_task_in_queue')
    def test_assert_task_not_in_queue_given_task_not_exists_expect_no_exception(self, mock_is_task_in_queue):
        mock_is_task_in_queue.return_value = False

        assert_task_not_in_queue('my.module.my_function')

    @patch('taskqueue.libs.helper_test.is_task_in_queue')
    def test_assert_task_not_in_queue_given_task_exists_expect_assertion_error(self, mock_is_task_in_queue):
        mock_is_task_in_queue.return_value = True

        with pytest.raises(AssertionError, match="Task 'my.module.my_function' found in queue 'default'"):
            assert_task_not_in_queue('my.module.my_function')

    @patch('taskqueue.libs.helper_test.is_task_in_queue')
    def test_assert_task_not_in_queue_given_custom_message_expect_custom_error(self, mock_is_task_in_queue):
        mock_is_task_in_queue.return_value = True

        with pytest.raises(AssertionError, match="Custom error message"):
            assert_task_not_in_queue(
                'my.module.my_function', msg="Custom error message")

    @patch('taskqueue.libs.helper_test.current_app')
    @patch('taskqueue.libs.helper_test.loads')
    def test_celery_worker_burst_given_matching_function_expect_execution(self, mock_loads, mock_current_app):
        mock_task = MagicMock()
        mock_current_app.tasks = {
            'taskqueue.cmanager.dynamic_function_executor': mock_task
        }

        mock_message = MagicMock()
        mock_message.headers = {
            'task': 'taskqueue.cmanager.dynamic_function_executor'}
        mock_message.body = b'mock_body'
        mock_message.content_type = 'application/json'
        mock_message.content_encoding = 'utf-8'
        mock_message.acknowledged = False

        mock_loads.return_value = [[], {
            'module_path': 'my.module',
            'function_name': 'my_function',
            'args': [],
            'kwargs': {}
        }]

        mock_queue = MagicMock()
        mock_queue.get.side_effect = [mock_message, None]
        mock_current_app.amqp.queues = {
            'default': MagicMock(return_value=mock_queue)}

        mock_conn = MagicMock()
        mock_chan = MagicMock()
        mock_current_app.connection_for_read.return_value.__enter__.return_value = mock_conn
        mock_conn.channel.return_value.__enter__.return_value = mock_chan

        with patch('taskqueue.libs.helper_test.logger') as mock_logger:
            celery_worker_burst(['my.module.my_function'])

            mock_logger.info.assert_any_call(
                "Executing task: my.module.my_function")
            mock_logger.info.assert_any_call(
                "Successfully executed task: my.module.my_function")

        mock_message.ack.assert_called_once()
        mock_task.apply.assert_called_once()

    @patch('taskqueue.libs.helper_test.current_app')
    @patch('taskqueue.libs.helper_test.loads')
    def test_celery_worker_burst_given_non_matching_function_expect_skip(self, mock_loads, mock_current_app):
        mock_task = MagicMock()
        mock_current_app.tasks = {
            'taskqueue.cmanager.dynamic_function_executor': mock_task
        }

        mock_message = MagicMock()
        mock_message.headers = {
            'task': 'taskqueue.cmanager.dynamic_function_executor'}
        mock_message.body = b'mock_body'
        mock_message.content_type = 'application/json'
        mock_message.content_encoding = 'utf-8'
        mock_message.acknowledged = False

        mock_loads.return_value = [[], {
            'module_path': 'other.module',
            'function_name': 'other_function',
            'args': [],
            'kwargs': {}
        }]

        mock_queue = MagicMock()
        mock_queue.get.side_effect = [mock_message, None]
        mock_current_app.amqp.queues = {
            'default': MagicMock(return_value=mock_queue)}

        mock_conn = MagicMock()
        mock_chan = MagicMock()
        mock_current_app.connection_for_read.return_value.__enter__.return_value = mock_conn
        mock_conn.channel.return_value.__enter__.return_value = mock_chan

        celery_worker_burst(['my.module.my_function'])

        mock_message.ack.assert_called_once()
        mock_task.apply.assert_not_called()

    @patch('taskqueue.libs.helper_test.current_app')
    def test_celery_worker_burst_given_invalid_task_expect_warning_and_skip(self, mock_current_app):
        mock_current_app.tasks = {}

        mock_message = MagicMock()
        mock_message.headers = {'task': 'invalid.task.name'}
        mock_message.body = b'mock_body'
        mock_message.content_type = 'application/json'
        mock_message.content_encoding = 'utf-8'
        mock_message.acknowledged = False

        mock_queue = MagicMock()
        mock_queue.get.side_effect = [mock_message, None]
        mock_current_app.amqp.queues = {
            'default': MagicMock(return_value=mock_queue)}

        mock_conn = MagicMock()
        mock_chan = MagicMock()
        mock_current_app.connection_for_read.return_value.__enter__.return_value = mock_conn
        mock_conn.channel.return_value.__enter__.return_value = mock_chan

        with patch('taskqueue.libs.helper_test.logger') as mock_logger:
            celery_worker_burst(['some.function'])

            mock_logger.warning.assert_called_once_with(
                "Invalid task 'invalid.task.name'. Skipping.")
            mock_message.ack.assert_called_once()

    @patch('taskqueue.libs.helper_test.current_app')
    def test_celery_worker_burst_given_no_messages_expect_no_processing(self, mock_current_app):
        mock_queue = MagicMock()
        mock_queue.get.return_value = None
        mock_current_app.amqp.queues = {
            'default': MagicMock(return_value=mock_queue)}

        mock_conn = MagicMock()
        mock_chan = MagicMock()
        mock_current_app.connection_for_read.return_value.__enter__.return_value = mock_conn
        mock_conn.channel.return_value.__enter__.return_value = mock_chan

        celery_worker_burst(['some.function'])

        mock_queue.get.assert_called_once_with(no_ack=False)
