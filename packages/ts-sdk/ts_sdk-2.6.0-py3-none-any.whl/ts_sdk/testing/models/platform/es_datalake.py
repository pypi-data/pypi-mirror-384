from unittest.mock import MagicMock

from ...util.requests import replacing
from ...util.warned import warned


@replacing("post", "/v1/datalake/searchEql")
@warned("POST /v1/datalake/searchEql is not yet fully mocked. responding with stub")
def post_search_eql(*args, **kwargs):
    response = MagicMock()
    response.status_code = 200
    response.json = lambda: {"hits": {"hits": []}}
    return response


replacements = [post_search_eql]
