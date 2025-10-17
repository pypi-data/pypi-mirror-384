from twisted.conch.telnet import TelnetTransport
from twisted.internet.protocol import ClientFactory


class BaseFactory(ClientFactory):
    protocol = None

    def __init__(self):
        if not self.protocol:
            raise NotImplementedError()

    def buildProtocol(self, addr):
        cam = TelnetTransport(self.protocol)
        cam.factory = self
        return cam
