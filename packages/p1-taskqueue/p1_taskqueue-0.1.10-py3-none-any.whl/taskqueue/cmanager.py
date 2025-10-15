import importlib
import inspect
import logging
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import Tuple

from celery import shared_task
from celery.exceptions import Reject

# Setup logger
logger = logging.getLogger(__name__)

# Enqueue operation type constants
K_ENQUEUE_OP_TYPE_ENQUEUE = 'enqueue'
K_ENQUEUE_OP_TYPE_ENQUEUE_AT = 'enqueue_at'
K_ENQUEUE_OP_TYPE_ENQUEUE_IN = 'enqueue_in'

K_MAX_RETRY_COUNT = 3
K_DEFAULT_RETRY_COUNTDOWN = 10


def _is_class_method(func: Any) -> bool:
    return inspect.ismethod(func) or (
        hasattr(func, "__self__") and getattr(func, "__self__") is not None
    )


def taskqueue_class(cls):
    """Decorator to automatically capture init arguments for taskqueue."""
    original_init = cls.__init__
    
    def wrapped_init(self, *args, **kwargs):
        self._taskqueue_init_args = list(args)
        self._taskqueue_init_kwargs = dict(kwargs)
        original_init(self, *args, **kwargs)
    
    cls.__init__ = wrapped_init
    return cls


def _extract_init_args_from_instance(instance: Any) -> Tuple[list, dict]:
    """Extract init arguments from instance."""
    init_args = getattr(instance, '_taskqueue_init_args', [])
    init_kwargs = getattr(instance, '_taskqueue_init_kwargs', {})
    return init_args, init_kwargs


def _split_function_and_queue_kwargs(kwargs: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    # To prevent confusion whether a kwargs is for function or queue kwargs(i.e celery options and on_commit),
    # ignore confusing kwargs while give warning
    supported_queue_keys = {"channel", "retry", "on_commit", "job_timeout"}
    ignored_non_function_keys = {
        "queue", "countdown", "eta", "expires", "priority", "task_id", "routing_key",
        "serializer", "compression", "headers", "link", "link_error", "retry_policy",
        "shadow", "time_limit", "soft_time_limit", "reply_to", "group_id", "chord", "chain",
        "result_ttl", "failure_ttl", "ttl", "depends_on", "at_front", "meta", "retry_count",
    }

    queue_kwargs: Dict[str, Any] = {}
    func_kwargs: Dict[str, Any] = {}

    for key, value in kwargs.items():
        if key in supported_queue_keys:
            queue_kwargs[key] = value
        elif key in ignored_non_function_keys:
            logger.warning(
                f"[CManager] Unsupported celery args detected: {key}. Ignored.")
            continue
        else:
            func_kwargs[key] = value

    return func_kwargs, queue_kwargs


def _build_dynamic_task_call(func: Any, *args: Any, **func_kwargs: Any) -> Tuple[str, list, dict]:
    if _is_class_method(func):
        instance = getattr(func, "__self__")
        klass = instance.__class__
        module_path = klass.__module__
        class_name = klass.__name__
        method_name = func.__name__
        
        init_args, init_kwargs = _extract_init_args_from_instance(instance)
        
        task_name = "taskqueue.cmanager.dynamic_class_method_executor"
        task_args = []
        task_kwargs: Dict[str, Any] = {
            "module_path": module_path,
            "class_name": class_name,
            "method_name": method_name,
            "args": list(args),
            "kwargs": dict(func_kwargs),
            "init_args": init_args,
            "init_kwargs": init_kwargs,
        }
        return task_name, task_args, task_kwargs

    module_path = getattr(func, "__module__", None)
    function_name = getattr(func, "__name__", None)
    if not module_path or not function_name:
        raise ValueError(
            "Unsupported callable type for Celery enqueue. Provide a module-level function or a class method.")

    task_name = "taskqueue.cmanager.dynamic_function_executor"
    task_args = []
    task_kwargs = {
        "module_path": module_path,
        "function_name": function_name,
        "args": list(args),
        "kwargs": dict(func_kwargs),
    }
    return task_name, task_args, task_kwargs


class CManager:

    def __init__(self) -> None:
        pass

    def _get_celery_app(self):
        """Get the auto-configured Celery app instance."""
        # Use taskqueue's built-in auto-configured celery app
        from .celery_app import celery_app
        return celery_app

    def enqueue(self, *args: Any, **kwargs: Any) -> None:
        self._enqueue_op(
            *args, enqueue_op_type=K_ENQUEUE_OP_TYPE_ENQUEUE, **kwargs)

    def enqueue_at(self, *args: Any, **kwargs: Any) -> None:
        self._enqueue_op(
            *args, enqueue_op_type=K_ENQUEUE_OP_TYPE_ENQUEUE_AT, **kwargs)

    def enqueue_in(self, *args: Any, **kwargs: Any) -> None:
        self._enqueue_op(
            *args, enqueue_op_type=K_ENQUEUE_OP_TYPE_ENQUEUE_IN, **kwargs)

    def _enqueue_op(self, *args: Any, **kwargs: Any) -> None:
        on_commit = kwargs.pop('on_commit', False)
        if on_commit:
            try:
                from django.db import transaction
                transaction.on_commit(
                    lambda: self._enqueue_op_base(*args, **kwargs))
            except ImportError:
                raise RuntimeError(
                    "Django is not installed. Please install Django to use on_commit.")
        else:
            self._enqueue_op_base(*args, **kwargs)

    def _enqueue_op_base(self, *args: Any, **kwargs: Any) -> None:
        enqueue_op_type = kwargs.pop(
            'enqueue_op_type', K_ENQUEUE_OP_TYPE_ENQUEUE)

        try:
            if enqueue_op_type == K_ENQUEUE_OP_TYPE_ENQUEUE:
                if not args:
                    raise ValueError(
                        "enqueue requires a callable as the first positional argument")
                func = args[0]
                func_args = args[1:]

            elif enqueue_op_type == K_ENQUEUE_OP_TYPE_ENQUEUE_AT:
                if len(args) < 2:
                    raise ValueError(
                        "enqueue_at requires (eta_datetime, func, *func_args)")
                eta: datetime = args[0]
                func = args[1]
                func_args = args[2:]

            elif enqueue_op_type == K_ENQUEUE_OP_TYPE_ENQUEUE_IN:
                if len(args) < 2:
                    raise ValueError(
                        "enqueue_in requires (countdown_delta, func, *func_args)")
                delta: timedelta = args[0]
                func = args[1]
                func_args = args[2:]
            else:
                raise ValueError(
                    f"Unknown enqueue operation type: {enqueue_op_type}")

            func_kwargs, queue_kwargs = _split_function_and_queue_kwargs(
                kwargs)

            if enqueue_op_type == K_ENQUEUE_OP_TYPE_ENQUEUE_AT:
                queue_kwargs = dict(queue_kwargs)
                queue_kwargs["eta"] = eta
            elif enqueue_op_type == K_ENQUEUE_OP_TYPE_ENQUEUE_IN:
                queue_kwargs = dict(queue_kwargs)
                queue_kwargs["countdown"] = int(delta.total_seconds())

            task_name, task_args, task_kwargs = _build_dynamic_task_call(
                func, *func_args, **func_kwargs)

            task_id = self._send_task(task_name, task_args,
                                      task_kwargs, queue_kwargs)

            logger.info('[_enqueue_op_base %s] Submit Celery Task SUCCESS, task_name: %s args: %s, kwargs: %s, task_id: %s' % (
                enqueue_op_type, task_name, task_args, task_kwargs, task_id))

        except Exception as e:
            logger.exception('[_enqueue_op_base %s] Submit Celery Task FAILED, error: %s, args: %s, kwargs: %s' % (
                enqueue_op_type, str(e), args, kwargs))
            raise e

    def _send_task(self, task_name: str, task_args: list, task_kwargs: dict, queue_kwargs: Dict[str, Any]) -> str:
        celery_app = self._get_celery_app()

        queue_name = queue_kwargs.pop("channel", None)
        job_timeout = queue_kwargs.pop("job_timeout", None)
        retry_policy = queue_kwargs.pop("retry", None)

        send_opts: Dict[str, Any] = {}
        if queue_name:
            send_opts["queue"] = queue_name
        if job_timeout is not None:
            send_opts["time_limit"] = job_timeout
        if "countdown" in queue_kwargs:
            send_opts["countdown"] = queue_kwargs["countdown"]
        if "eta" in queue_kwargs:
            send_opts["eta"] = queue_kwargs["eta"]

        task_kwargs_with_retry = dict(task_kwargs)
        if retry_policy is None:
            task_kwargs_with_retry["retry"] = {
                "max_retries": K_MAX_RETRY_COUNT, "countdown": K_DEFAULT_RETRY_COUNTDOWN}
        else:
            task_kwargs_with_retry["retry"] = retry_policy

        task = celery_app.send_task(task_name, args=task_args,
                                    kwargs=task_kwargs_with_retry, **send_opts)
        return str(task.id)


cm = CManager()


# Dynamic task executors - handle function and class method execution
@shared_task(bind=True, max_retries=K_MAX_RETRY_COUNT)
def dynamic_function_executor(self, module_path=None, function_name=None, args=None, kwargs=None, retry=None):
    job_id = self.request.id
    try:
        module = importlib.import_module(module_path)
        function = getattr(module, function_name)
        args = args or []
        kwargs = kwargs or {}
        logger.info(
            f"[TaskQueue] Executing dynamic function: {function_name} with args: {args} and kwargs: {kwargs}, job_id: {job_id}")
        function(*args, **kwargs)
        logger.info(
            f"[TaskQueue] Dynamic function execution completed successfully, function_name: {function_name}, args: {args}, kwargs: {kwargs}, job_id: {job_id}")
        return None
    except Exception as e:
        logger.exception(
            f"[TaskQueue] Error executing dynamic function: {function_name} with args: {args} and kwargs: {kwargs}, error_class: {e.__class__.__name__}, error: {e}, job_id: {job_id}")
        current_retries = getattr(self.request, 'retries', 0) or 0
        max_retries = self.max_retries or K_MAX_RETRY_COUNT
        if isinstance(retry, dict) and 'max_retries' in retry:
            max_retries = retry['max_retries']

        if current_retries >= max_retries:
            raise Reject(str(e), requeue=False)

        countdown = K_DEFAULT_RETRY_COUNTDOWN
        if isinstance(retry, dict) and 'countdown' in retry:
            countdown = retry['countdown']

        raise self.retry(exc=e, countdown=countdown, max_retries=max_retries)


@shared_task(bind=True, max_retries=K_MAX_RETRY_COUNT)
def dynamic_class_method_executor(self, module_path=None, class_name=None, method_name=None, args=None, kwargs=None, init_args=None, init_kwargs=None, retry=None):
    job_id = self.request.id
    try:
        module = importlib.import_module(module_path)
        class_obj = getattr(module, class_name)
        init_args = init_args or []
        init_kwargs = init_kwargs or {}
        instance = class_obj(*init_args, **init_kwargs)
        method = getattr(instance, method_name)
        args = args or []
        kwargs = kwargs or {}
        logger.info(
            f"[TaskQueue] Executing dynamic class method: {method_name} with args: {args} and kwargs: {kwargs}, job_id: {job_id}")
        method(*args, **kwargs)
        logger.info(
            f"[TaskQueue] Dynamic class method execution completed successfully, method_name: {method_name}, args: {args}, kwargs: {kwargs}, job_id: {job_id}")
        return None
    except Exception as e:
        logger.exception(
            f"[TaskQueue] Error executing dynamic class method: {method_name} with args: {args} and kwargs: {kwargs}, error_class: {e.__class__.__name__}, error: {e}, job_id: {job_id}")
        current_retries = getattr(self.request, 'retries', 0) or 0
        max_retries = self.max_retries or K_MAX_RETRY_COUNT
        if isinstance(retry, dict) and 'max_retries' in retry:
            max_retries = retry['max_retries']

        if current_retries >= max_retries:
            raise Reject(str(e), requeue=False)

        countdown = K_DEFAULT_RETRY_COUNTDOWN
        if isinstance(retry, dict) and 'countdown' in retry:
            countdown = retry['countdown']

        raise self.retry(exc=e, countdown=countdown, max_retries=max_retries)
