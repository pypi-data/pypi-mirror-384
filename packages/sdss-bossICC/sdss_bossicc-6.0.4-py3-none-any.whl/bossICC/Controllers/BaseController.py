import sys

from twisted.internet import reactor
from twisted.internet.defer import Deferred


class BaseController(object):
    def __init__(self, icc, name, debug=1):
        self.icc = icc
        self.name = name
        self.debug = debug
        self.iacked = True

    def start(self):
        try:
            # Create the client factory
            self.factory = self.factory_class()
            self.factory.controller = self
            # Get the connection information
            host = self.icc.config[self.name]["host"]
            port = self.icc.config[self.name]["port"]
            # Connect the factory to the reactor
            reactor.callLater(2, self._connect, host, port, self.factory)
            # self._connect(host,port,self.factory)
        except Exception as e:
            self.icc.bcast.warn(
                'text="failed to start controller %s: %s"' % (self.name, e)
            )

    def _connect(self, host, port, factory):
        self.connector = reactor.connectTCP(host, port, factory)

    def init(self, cmd):
        pass

    def stop(self):
        # Disconnect the factory
        if self.connector:
            self.connector.disconnect()

    def ping(self):
        raise NotImplementedError()

    def sendCommand(self, raw, cmd, timeout=3):
        """Try to send a command to the protocol.

        If it is not connected call the errback.
        """

        # raw is unicode. Do not convert to bytes here. That happens in BaseProtocol.
        try:
            return self.factory.tool.sendCommand(raw, cmd, timeout=timeout)
        except:
            d = Deferred()
            reactor.callLater(0, d.errback, sys.exc_info())
            return d

    def sendCommandList(self, raws, cmd, timeout=3):
        """Try to send a command to the protocol.

        If it is not connected call the errback.
        """

        try:
            return self.factory.tool.sendCommandList(raws, cmd, timeout=timeout)
        except:
            d = Deferred()
            reactor.callLater(0, d.errback, sys.exc_info()[0])
            return d
