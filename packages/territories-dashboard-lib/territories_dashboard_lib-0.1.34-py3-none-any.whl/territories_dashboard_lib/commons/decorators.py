import functools
from typing import get_origin

from django.http import HttpResponse
from pydantic import ValidationError


def use_payload(payload_class):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.method != "GET":
                raise NotImplementedError
            data = {}
            for field_name, field in payload_class.model_fields.items():
                url_name = field.alias if field.alias else field_name
                is_list_field = get_origin(field.annotation) is list
                url_value = (
                    request.GET.getlist(url_name)
                    if is_list_field
                    else request.GET.get(url_name)
                )
                if url_value is not None:
                    data[url_name] = url_value
            try:
                payload = payload_class.model_validate(data)
            except ValidationError as e:
                return HttpResponse(
                    e.json(), headers={"content_type": "application/json"}, status=400
                )

            return func(request, *args, payload=payload, **kwargs)

        return wrapper

    return decorator
