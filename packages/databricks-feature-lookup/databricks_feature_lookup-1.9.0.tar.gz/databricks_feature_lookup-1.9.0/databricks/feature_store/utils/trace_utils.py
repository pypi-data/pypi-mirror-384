import os
from functools import wraps

import mlflow
from mlflow.entities import SpanType
from packaging import version

ENABLE_FEATURE_TRACING = "ENABLE_FEATURE_TRACING"


def is_feature_tracing_enabled() -> bool:
    # environment variables stored as string, rather than boolean
    # MLflow tracing is only available after Mlflow 2.14.0
    current_mlflow_version = version.parse(mlflow.__version__)
    minimum_mlflow_version = version.parse("2.14.0")
    return (
        os.getenv(ENABLE_FEATURE_TRACING) != "false"
        and current_mlflow_version >= minimum_mlflow_version
    )


def trace_latency(span_name: str):
    """
    A decorator for simple tracing. Any method decorated by this decorator
    will add a span with the given name. Compared with the official mlflow.trace,
    this version does not record method inputs or outputs.
    """

    def decorator(func):
        if is_feature_tracing_enabled():
            # Apply mlflow.trace directly if tracing is enabled
            return mlflow.trace(name=span_name, span_type=SpanType.RETRIEVER)(func)
        else:
            # Otherwise, return the original function unchanged
            return func

    return decorator
