import sys

from twisted.internet import protocol, reactor
from twisted.protocols import basic


class CamForthProtocol(basic.LineReceiver):
    def lineReceived(self, line):
        pass

    def dataReceived(self, data):
        print("Raw Data = ", data.decode())
        if not data[-1] == b"\x00":
            self.transport.write(data)
        else:
            print("Line Received.")
            resp = b"  ok\x0D\x00\x0A"
            self.transport.write(resp)

        print("Raw data echoed.")


class CamForthSimulator(protocol.ServerFactory):
    protocol = CamForthProtocol


reactor.listenTCP(int(sys.argv[1]), CamForthSimulator())
reactor.run()
