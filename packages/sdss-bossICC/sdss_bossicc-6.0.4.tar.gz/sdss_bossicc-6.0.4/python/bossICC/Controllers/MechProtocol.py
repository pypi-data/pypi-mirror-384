import logging

from twisted.internet import reactor

from opscore.utility.qstr import qstr

from bossICC import BOSSExceptions
from bossICC.Controllers.BaseProtocol import BaseProtocol


class MechProtocol(BaseProtocol):
    timeout = 5

    def lineReceived(self, line):
        """Line received from the camera.
        This is where the bulk of the message parsing takes place.

        self.buf is a buffer of lines that correspond to a single response.
        self.d is the deferred object to be fired when the response is complete
        self.d.raw is the raw command that was sent down to the micro
        self.d.cmd is the command object for returning text

        When parsing is complete either fire the callback or errback depending
        self.d.callback(self.buf)
        self.d.errback(Exception('Information regarding the error'))
        """

        line = line.rstrip(b"\r")  # DON'T DECODE! Some values are byte-encoded numbers.
        if self.d is None:
            self.factory.controller.icc.bcast.warn(
                "text=%s"
                % (
                    qstr(
                        "Unsolicited message from %s: %s"
                        % (self.factory.controller.name, line)
                    )
                )
            )
            return

        # Gobble echo
        if self.buf is None:
            if not line.strip().startswith(self.d.raw):
                self.d.cmd.warn(
                    'text="Mech %s failed to echo command."'
                    % (self.factory.controller.name)
                )
                reactor.callLater(
                    0,
                    self.d.errback,
                    Exception(
                        "Mech %s failed to echo command."
                        % (self.factory.controller.name)
                    ),
                )
                try:
                    self.d.timer.cancel()
                except:
                    logging.info('text="Failed to cancel timeout timer."')
                self.d = None
                self.scheduleNext()

                return
            else:
                self.buf = []
        elif line != b"OK":
            # Push off the timeout and append line to response buffer
            self.buf.append(line)

        self.d.timer.delay(self.d.timeout)
        logging.info("%r: %r" % (self.factory.controller.name, line))
        if b"OK" in line:
            self.d.cmd.diag(
                'text="Completed message from %s"' % (self.factory.controller.name)
            )
            reactor.callLater(0, self.d.callback, self.buf)
        elif line.startswith(b"Failed"):
            self.d.cmd.warn(
                "text=%s"
                % (qstr("Failure from %s: %s" % (self.factory.controller.name, line)))
            )
            reactor.callLater(0, self.d.errback, Exception(line))
        else:
            return

        try:
            self.d.timer.cancel()
        except:
            logging.info('text="Failed to cancel timeout timer."')
        self.d = None
        self.scheduleNext()

    def commandTimedOut(self, d, cmd):
        response = 'text="Command %s to %s timed out"' % (
            d.raw.decode(),
            self.factory.controller.name,
        )
        reactor.callLater(0, d.errback, BOSSExceptions.TimeOutError())
        logging.info(response)
        if d.cmd:
            d.cmd.warn(response)
