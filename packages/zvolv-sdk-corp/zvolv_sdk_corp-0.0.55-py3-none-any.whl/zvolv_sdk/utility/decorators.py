from functools import wraps
import traceback


def enforce_pydantic_model(model_class):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for arg in args:
                if isinstance(arg, model_class):
                    break
            else:
                raise TypeError(f"Expected instance of {model_class.__name__}, got {type(arg)}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def automation_wrapper(func):
    def wrapper(client, event):
        headers = event.headers
        automation_uuid = headers['X-Nuclio-Function-Name']
        client.logger.init_execution_log(automation_uuid, event.body)
        try:
            result = func(client, event)
            client.logger.close_execution_log('success', 'Execution completed', result, None)
            return result
        except Exception as e:
            trace = traceback.format_exc()
            client.logger.close_execution_log('failure', str(e), None, trace)
            raise
    return wrapper
