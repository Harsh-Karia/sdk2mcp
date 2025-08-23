import requests
import inspect

print([name for name, obj in inspect.getmembers(requests) if inspect.isfunction(obj)])