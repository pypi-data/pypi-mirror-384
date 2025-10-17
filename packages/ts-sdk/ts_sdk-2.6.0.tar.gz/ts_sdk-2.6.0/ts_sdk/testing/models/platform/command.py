from ...util import random
from ...util.requests import replacing, responses
from ...util.warned import warned


@replacing("get", "/v1/commands")
@warned("GET /v1/commands is not yet fully mocked. responding with stub")
def get_command(*args, **kwargs):
    print("warning: GET /v1/commands is not yet fully mocked. responding with stub")
    return responses.json({"id": random.string()})


@replacing("post", "/v1/commands")
@warned("POST /v1/commands is not yet fully mocked. responding with stub")
def post_command(*args, **kwargs):
    return responses.json({"status": "SUCCESS", "responseBody": None})


replacements = [get_command, post_command]
