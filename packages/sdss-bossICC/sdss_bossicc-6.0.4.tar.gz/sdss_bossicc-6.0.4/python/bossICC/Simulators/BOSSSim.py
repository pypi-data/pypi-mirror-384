from time import time as time

from twisted.conch.telnet import StatefulTelnetProtocol
from twisted.internet import protocol, reactor


class CamForthSimulator(StatefulTelnetProtocol):
    def connectionMade(self):
        print("CamForth connected.")
        print(self)
        self.start = None

    def lineReceived(self, line):
        """Just echo it back in forth speak."""

        line = line.decode()
        response = ""
        if "FREAD" in line:
            self.start = time()
            response = "<" + line[:-1] + " ok> ok"
        elif self.start and time() - self.start < 5:
            response = "PHASEMICRO BUSY"
        elif len(line) > 1:
            response = "<" + line[:-1] + " ok> ok"
        else:
            response = " ok"
        print(response)
        reactor.callLater(0.2, self.sendLine, response)


class CamForthFactory(protocol.ServerFactory):
    protocol = CamForthSimulator


reactor.listenTCP(5001, CamForthFactory())
# reactor.listenTCP(5002, CamForthFactory())
reactor.run()
