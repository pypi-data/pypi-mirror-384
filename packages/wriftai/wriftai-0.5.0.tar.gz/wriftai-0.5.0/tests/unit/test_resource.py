from unittest.mock import Mock

from wriftai._resource import Resource


class MockAPIResource(Resource):
    """Concrete subclass for testing the abstract Resource."""

    pass


def test_api_resource() -> None:
    mock_api = Mock()
    resource = MockAPIResource(api=mock_api)
    assert resource._api == mock_api
