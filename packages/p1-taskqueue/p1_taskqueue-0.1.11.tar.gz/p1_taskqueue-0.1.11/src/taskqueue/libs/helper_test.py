import logging
from typing import List

from celery import current_app
from kombu.serialization import loads

logger = logging.getLogger(__name__)


def clear_all_celery_queues():
    app = current_app
    all_queue_names = list(app.amqp.queues.keys())
    with app.connection_for_read() as conn:
        with conn.channel() as chan:
            for queue_name in all_queue_names:
                queue = app.amqp.queues[queue_name](chan)
                queue.purge()


def celery_worker_burst(include_func_names: List[str], channel: str = "default"):
    # This doesn't use celery as celery doesn't support filtering out functions
    # this use kombu to get the message from the queue and then execute the task manually
    app = current_app
    included_set = set(include_func_names)
    processed_count = 0
    executed_count = 0

    try:
        with app.connection_for_read() as conn:
            with conn.channel() as chan:
                queue = app.amqp.queues[channel](chan)

                while True:
                    message = queue.get(no_ack=False)
                    if not message:
                        break

                    processed_count += 1
                    task_name = message.headers.get("task")

                    if not task_name or task_name not in app.tasks:
                        # task is not registered in celery
                        logger.warning(
                            f"Invalid task '{task_name}'. Skipping.")
                        message.ack()
                        continue

                    try:
                        task_obj = app.tasks[task_name]
                        accept = {"application/json",
                                  "application/x-python-serialize"}
                        decoded_body = loads(
                            message.body, message.content_type, message.content_encoding, accept=accept
                        )

                        task_args = decoded_body[0] if decoded_body else []
                        task_kwargs = decoded_body[1] if len(
                            decoded_body) > 1 else {}

                        full_func_name = ""
                        if task_name.endswith("dynamic_function_executor"):
                            module_path = task_kwargs.get('module_path', '')
                            function_name = task_kwargs.get(
                                'function_name', '')
                            if module_path and function_name:
                                full_func_name = f"{module_path}.{function_name}"
                        elif task_name.endswith("dynamic_class_method_executor"):
                            module_path = task_kwargs.get('module_path', '')
                            class_name = task_kwargs.get('class_name', '')
                            method_name = task_kwargs.get('method_name', '')
                            if module_path and class_name and method_name:
                                full_func_name = f"{module_path}.{class_name}.{method_name}"

                        should_execute = full_func_name in included_set if full_func_name else False

                        if should_execute:
                            logger.info(f"Executing task: {full_func_name}")
                            message.ack()
                            task_obj.apply(args=task_args, kwargs=task_kwargs)
                            executed_count += 1
                            logger.info(
                                f"Successfully executed task: {full_func_name}")
                        else:
                            logger.info(
                                f"Skipping: {full_func_name or task_name}")
                            message.ack()

                    except Exception as e:
                        logger.error(
                            f"Failed to process task {task_name}: {type(e).__name__}: {e}")
                        if message and not message.acknowledged:
                            message.ack()

    except Exception as e:
        logger.error(
            f"Failed to connect to queue {channel}: {type(e).__name__}: {e}")


def get_queued_tasks(channel: str = "default"):
    app = current_app
    queued_tasks = []

    try:
        with app.connection_for_read() as conn:
            with conn.channel() as chan:
                queue = app.amqp.queues[channel](chan)

                while True:
                    message = queue.get(no_ack=True)
                    if not message:
                        break

                    task_name = message.headers.get("task")

                    try:
                        accept = {"application/json",
                                  "application/x-python-serialize"}
                        decoded_body = loads(
                            message.body, message.content_type, message.content_encoding, accept=accept
                        )

                        task_args = decoded_body[0] if decoded_body else []
                        task_kwargs = decoded_body[1] if len(
                            decoded_body) > 1 else {}

                        full_func_name = ""
                        if task_name and task_name.endswith("dynamic_function_executor"):
                            module_path = task_kwargs.get('module_path', '')
                            function_name = task_kwargs.get(
                                'function_name', '')
                            if module_path and function_name:
                                full_func_name = f"{module_path}.{function_name}"
                        elif task_name and task_name.endswith("dynamic_class_method_executor"):
                            module_path = task_kwargs.get('module_path', '')
                            class_name = task_kwargs.get('class_name', '')
                            method_name = task_kwargs.get('method_name', '')
                            if module_path and class_name and method_name:
                                full_func_name = f"{module_path}.{class_name}.{method_name}"

                        queued_tasks.append({
                            'task_name': task_name,
                            'full_func_name': full_func_name,
                            'args': task_args,
                            'kwargs': task_kwargs,
                            'headers': message.headers
                        })

                    except Exception as e:
                        logger.warning(f"Failed to decode message: {e}")
                        continue

    except Exception as e:
        logger.error(
            f"Failed to get queued tasks from queue {channel}: {type(e).__name__}: {e}")

    return queued_tasks


def is_task_in_queue(expected_func_name: str, channel: str = "default"):
    queued_tasks = get_queued_tasks(channel)
    for task in queued_tasks:
        if task['full_func_name'] == expected_func_name:
            return True
    logger.info(
        f"Task {expected_func_name} not found in queue {channel}. Queued tasks: {[task['full_func_name'] for task in queued_tasks]}")
    return False


def assert_task_in_queue(expected_func_name: str, channel: str = "default", msg: str = None):
    if not is_task_in_queue(expected_func_name, channel):
        error_msg = msg or f"Task '{expected_func_name}' not found in queue '{channel}'"
        raise AssertionError(error_msg)


def assert_task_not_in_queue(expected_func_name: str, channel: str = "default", msg: str = None):
    if is_task_in_queue(expected_func_name, channel):
        error_msg = msg or f"Task '{expected_func_name}' found in queue '{channel}'"
        raise AssertionError(error_msg)
