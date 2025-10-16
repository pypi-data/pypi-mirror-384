import time
from sys import getsizeof
from typing import Any, Callable, Dict, List

# end-to-end latency (ms) for all lookup related logic
LOOKUP_E2E_LATENCY = "lookup_e2e_latency_ms"
# number of lookup requests made to online store
ONLINE_STORE_REQUEST_COUNT = "online_store_request_count"
# total time spent making requests to online store provider
ONLINE_STORE_REQUEST_LATENCY = "total_online_store_request_latency_ms"
# total in-memory bytes received from responses of online store provider, upper bound on wire bytes
RESPONE_IN_MEMORY_BYTES = "total_response_in_memory_bytes"
# number of features with NaN values for request
NAN_FEATURE_COUNT = "nan_feature_count"
# number of overriden feature values for request
OVERRIDEN_FEATURE_COUNT = "overriden_feature_count"


class LookupClientMetrics:
    # metrics_dict - Dicitonary mapping metric name to values
    def __init__(self, metrics_dict: Dict[str, Any] = {}):
        self._metrics_dict = metrics_dict

    # increase value of metric, default 0 if no existing values for metrics
    def increase_metric(self, metric_name: str, amount: float):
        self._metrics_dict[metric_name] = (
            self._metrics_dict.get(metric_name, 0) + amount
        )

    def record_e2e_latency(self, request_duration_ms: float):
        self._metrics_dict[LOOKUP_E2E_LATENCY] = request_duration_ms

    # add request latency, bytes, and count to total combined value
    def record_request_metrics(
        self, request_duration_ms: float, in_memory_bytes: int, attempts: int = 1
    ):
        self.increase_metric(ONLINE_STORE_REQUEST_LATENCY, request_duration_ms)
        self.increase_metric(RESPONE_IN_MEMORY_BYTES, in_memory_bytes)
        self.increase_metric(ONLINE_STORE_REQUEST_COUNT, attempts)

    def get_metrics(self):
        return self._metrics_dict


# A wrapper to make patching in unittests easier.
def _current_time():
    return time.time()


def lookup_call_maybe_with_metrics(
    lookup_fn: Callable,
    metrics: LookupClientMetrics,
    measuring_e2e_latency: bool = False,
):
    if not metrics:
        return lookup_fn
    else:

        def lookup_fn_wrapper(*args, **kwargs):
            start_time = _current_time()
            online_store_output = lookup_fn(*args, **kwargs)
            duration_ms = (_current_time() - start_time) * 1000
            if measuring_e2e_latency:
                metrics.record_e2e_latency(duration_ms)
            else:
                # accumulates latency, response in-memory bytes, and count for each lookup request
                metrics.record_request_metrics(
                    duration_ms, getsizeof(online_store_output)
                )
            return online_store_output

        return lookup_fn_wrapper


def num_missing_feature_values(
    expected_feature_names: List[str], lookup_result: Dict[str, any]
):
    keys = lookup_result.keys()
    return len([f for f in expected_feature_names if f not in keys])
