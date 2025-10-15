import time
from unittest import TestCase

from openmodule.models.base import OpenModuleModel
from openmodule.rpc import RPCClient
from openmodule_test.rpc import MockRPCClient


class Request(OpenModuleModel):
    data: str


class Response(OpenModuleModel):
    res: str


class MockRPCClientTest(TestCase):
    def setUp(self) -> None:
        self.client = MockRPCClient(callbacks={("channel", "db"): self.callback, ("channel", "timeout"): self.timeout},
                                    responses={("channel", "res"): Response(res="res")})

    def callback(self, req: Request, _):
        """
        test callback
        """
        return Response(res=req.data)

    def timeout(self, req: Request, _):
        time.sleep(10)

    def test_results(self):
        self.assertEqual(self.client.rpc("channel", "db", Request(data="test"), Response).res, "test")
        self.assertEqual(self.client.rpc("channel", "res", Request(data="test"), Response).res, "res")
        with self.assertRaises(RPCClient.TimeoutError):
            self.client.rpc("channel2", "res", Request(data="test"), Response)
        self.assertEqual(self.client.last_request[("channel2", "res")], Request(data="test"))
        with self.assertRaises(RPCClient.TimeoutError):
            self.client.rpc("channel", "timeout", Request(data="test"), Response)
