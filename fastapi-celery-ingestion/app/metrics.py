from prometheus_client import Counter, Histogram

REQUESTS_TOTAL = Counter("http_requests_total", "Total HTTP requests", ["endpoint", "method", "status"])
REQUEST_LATENCY = Histogram("http_request_latency_seconds", "Request latency", ["endpoint", "method"])
