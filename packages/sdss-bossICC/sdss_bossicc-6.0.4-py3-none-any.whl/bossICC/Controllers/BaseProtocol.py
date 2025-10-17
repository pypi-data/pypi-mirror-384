import logging
from queue import Empty, Queue

from twisted.conch.telnet import StatefulTelnetProtocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred, DeferredList

from opscore.utility.qstr import qstr


class BaseProtocol(StatefulTelnetProtocol):
    """Incomplete subclass of all the protocols.

    BaseProtocol is a twisted telnet client that handles the
    asyncronous sending of commands.

    The BaseProtocol takes raw commands that are to be sent to
    the controllers and queues them up and defers them. The sendCommand
    method handles this and returns a defered object which can then be
    attached with a callback and/or an error back.

    The protocol then schedules a method to pop a raw
    command off of that queue and send it to the micro.
    The protocol waits for a response. The subclasser of
    BaseProtocol overrides receiveLine(self,line) to check the incoming
    data. The incoming data can then be determined to be good or not.
    This is on the subclass to decide. Inside of receive line the code
    then calls self.scheduleNext() which will have the reactor core
    pop the next command the next time around the loop. An example
    receiveLine would be:

    def receiveLine(self,line):
        if line == "WIN":
            self.d.callback(line)
        elif line == "FAIL":
            self.d.errback(line)
        self.scheduleNext()

    """

    timeout = 5

    def connectionMade(self):
        """Set up any connection specific variables."""
        self.buf = None  # Buffer for incoming lines
        self.d = None
        self.q = Queue()  # Queue for deferreds
        self.iacked = False  # Not IACKED
        self._nextTimer = None  # Deferred sendNextTimer
        self.factory.tool = self  # Give the factory a reference
        self.factory.controller.icc.bcast.respond(
            'text="Controller %s connected."' % (self.factory.controller.name)
        )
        self.factory.controller.init(self.factory.controller.icc.bcast)

    def connectionLost(self, reason):
        self.factory.controller.icc.bcast.warn(
            'text="Controller %s disconnected."' % (self.factory.controller.name)
        )
        self.factory.controller.icc.bcast.warn(
            'text="%s removed from available hardware."'
            % (self.factory.controller.name)
        )
        try:
            del self.factory.controller.icc.controllers[self.factory.controller.name]
        except:
            pass

    def connectionFailed(self, reason):
        self.factory.controller.icc.bcast.warn(
            'text="Controller %s connection failed. reason: %s"'
            % (self.factory.controller.name, reason)
        )

    def sendCommand(self, raw, cmd=None, timeout=1):
        """Defer the command and pop the deferal on a queue."""
        # Create a deferred object
        d = Deferred()
        d.raw = raw.encode()
        d.cmd = cmd
        d.timeout = timeout
        empty = self.q.empty()
        self.q.put(d)
        if empty:
            self.scheduleNext()
        return d

    def sendCommandList(self, raws, cmd=None, timeout=timeout):
        """Send a list of commands to the controllers

        Arguments
        raws -- A list of raw command strings.
        cmd -- Command object, used for logging

        Returns
        dlist -- A DeferredList that can be used to receive
                a callback when all commands have run.
        """
        dlist = []
        for raw in raws:
            # Send a command to the controller
            d = self.sendCommand(raw, cmd=cmd, timeout=timeout)
            # Append the deffered to a list
            dlist.append(d)
        # Create a deffered list, will not trigger until all commands
        # have finished.
        dlist = DeferredList(dlist)
        return dlist

    def _sendNextCommand(self):
        """Get the next command from the queue and do it."""
        # None the nextTimer
        self._nextTimer = None
        # If there is a current command
        if self.d is not None:
            return
        # Try to pop one of the Queue
        try:
            d = self.q.get(block=False)
        except Empty:
            # If there is nothing, go home
            return
        # Save the deferal for later
        self.d = d
        d.timer = reactor.callLater(d.timeout, self.commandTimedOut, d, d.cmd)
        # Clear the response buffer
        self.buf = None
        # Write the command
        logging.info("%s > %r" % (self.factory.controller.name, d.raw))
        if d.cmd:
            decoded = d.raw.decode()
            msg = qstr("Sending %s to %s" % (decoded, self.factory.controller.name))
            d.cmd.diag(f"text={msg}")
        self.sendLine(d.raw)

    def commandTimedOut(self, d, cmd):
        raise NotImplementedError()

    def scheduleNext(self):
        """Prevents more than one callLater from being scheduled."""
        if not self._nextTimer:
            self._nextTimer = reactor.callLater(0, self._sendNextCommand)

    def iack(self):
        """IACK the instrument."""
        raise NotImplementedError()

    def lineReceived(self, data):
        """Receive data and buffer it, determine if it is good or not."""
        raise NotImplementedError()
