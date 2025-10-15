from unittest.mock import Mock

from wriftai._resource import Resource


class MockAPIResource(Resource):
    """Concrete subclass for testing the abstract Resource."""

    pass


def test_api_resource() -> None:
    mock_requestor = Mock()
    resource = MockAPIResource(requestor=mock_requestor)
    assert resource._requestor == mock_requestor
