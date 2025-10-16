from typing import List, Optional


def serverless_api_endpoint(allowed_methods: Optional[List[str]]=None, body_type=None):
    """
    Decorator for serverless api endpoints

    Example:
        @serverless_api_endpoint(allowed_methods=["POST"], body_type=src.services.customer_response_v1.Message)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import jsonify
            from pydantic import ValidationError

            request = args[0]

            if request.content_type != "application/json":
                return jsonify({"errors": [{"content_type": "NOT JSON"}]}), 400

            if allowed_methods and request.method not in allowed_methods:
                return jsonify({"errors": [{"method": "NOT ALLOWED"}]}), 405

            if body_type is not None:
                try:
                    data = body_type(**request.json)
                except ValidationError as e:
                    return jsonify({"errors": e.errors()}), 400

                try:
                    result = func(request, data, **kwargs)
                except Exception as e:
                    return jsonify({"errors": [{"server": str(e)}]}), 500
            else:
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    return jsonify({"errors": [{"server": str(e)}]}), 500
            return result

        return wrapper

    return decorator
