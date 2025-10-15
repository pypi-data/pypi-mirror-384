import pytest

from tests.util import requires_grpclib  # noqa: F401


@pytest.mark.asyncio
async def test_rpc_input_message(requires_grpclib):
    from grpclib.testing import ChannelFor

    from tests.outputs.rpc_empty_input_message.rpc_empty_input_message import (
        Response,
        ServiceBase,
        ServiceStub,
        Test,
    )

    class Service(ServiceBase):
        async def read(self, test: "Test") -> "Response":
            return Response(v=42)

    async with ChannelFor([Service()]) as channel:
        client = ServiceStub(channel)

        assert (await client.read(Test())).v == 42

        # Check that we can call the method without providing the message
        assert (await client.read()).v == 42
