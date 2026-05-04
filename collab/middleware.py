import time


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if request.method in {'GET', 'POST', 'PUT', 'DELETE'}:
            print(
                f"method={request.method} path={request.path} "
                f"status={response.status_code} duration_ms={elapsed_ms:.2f}"
            )

        return response
