"""U6: ``BlockedHostError`` is a subclass of micawber's ``ProviderException`` so
callers already catching provider errors keep working.

Utility requirement. Visible to the agent.
"""
from micawber.exceptions import ProviderException
from micawber.guarded import BlockedHostError


def test_blocked_host_error_is_provider_exception():
    assert issubclass(BlockedHostError, ProviderException)
