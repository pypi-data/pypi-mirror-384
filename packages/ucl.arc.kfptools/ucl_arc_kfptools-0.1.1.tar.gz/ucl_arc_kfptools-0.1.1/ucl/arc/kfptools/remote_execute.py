import kfp
import kfp.dsl as dsl
import logging
import inspect
from functools import wraps


def _validate_kfp_function(func):
    sig = inspect.signature(func)
    for name, param in sig.parameters.items():
        if param.annotation is inspect.Parameter.empty:
            raise TypeError(
                f"Parameter '{name}' must have a type annotation for KFP compatibility."
            )
        if not isinstance(param.annotation, type) or not issubclass(
            param.annotation, (int, float, str, bool, list, dict)
        ):
            raise TypeError(
                f"Parameter '{name}' has unsupported type '{param.annotation}' for KFP."
            )

    return_type = sig.return_annotation
    if return_type is inspect.Signature.empty:
        raise TypeError("Return type must be annotated for KFP compatibility.")
    if not isinstance(return_type, type) or not issubclass(
        return_type, (int, float, str, bool, list, dict, type(None))
    ):
        raise TypeError(f"Return type '{return_type}' is not supported by KFP.")
    return return_type


def remote_execute(*, host: str = "", namespace: str = "", timeout: int = 3600):
    def decorator(func):
        return_type = _validate_kfp_function(func)
        component_func = dsl.component(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            @dsl.pipeline(name=f"remote-function-execution-{func.__name__}")
            def dsl_pipeline():
                function_execution = component_func(*args, **kwargs)
                return function_execution.output

            dsl_pipeline.__annotations__["return"] = return_type

            client = kfp.Client(host=host, namespace=namespace)
            try:
                run = client.create_run_from_pipeline_func(
                    dsl_pipeline,
                    arguments={},
                    experiment_name="remote-function-execution",
                )
                run_id = str(run.run_id)
            except Exception as e:
                logging.error(f"Failed to create pipeline: {e}")
                raise
            try:
                run_result = client.wait_for_run_completion(run_id, timeout=timeout)
            except TimeoutError:
                logging.error("Run did not finish before timeout, terminating run")
                raise
            if run_result.state != "SUCCEEDED":
                logging.error("Run failed")
                # we should return logs here
                raise
            # we need to return the run result value here
            return run_result

        return wrapper

    return decorator
