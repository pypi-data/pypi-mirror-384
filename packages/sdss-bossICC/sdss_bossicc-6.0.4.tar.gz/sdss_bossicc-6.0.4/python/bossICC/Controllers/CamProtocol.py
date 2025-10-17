import logging

from twisted.internet import reactor

from opscore.utility.qstr import qstr

from bossICC import BOSSExceptions

from . import BaseProtocol


class CamProtocol(BaseProtocol.BaseProtocol):
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
        logging.info("%s < %r" % (self.factory.controller.name, line))
        if self.d is None:
            self.factory.controller.icc.bcast.warn(
                'text="Unsolicited message from %s, %s"'
                % (self.factory.controller.name, line)
            )
            return

        if b"COLD" in self.d.raw:
            # This is a cold command, look for the proper thing
            if line.startswith(b"TDS2020"):
                line += b"ok"

        # check echo
        if self.buf is None:
            if not line.startswith(self.d.raw):
                errText = "text=%s" % (
                    qstr(
                        "Cam %s failed to echo command; returned ::%s::"
                        % (self.factory.controller.name, line)
                    )
                )
                self.d.cmd.warn(errText)
                self.d.errback(Exception(errText))
                try:
                    self.d.timer.cancel()
                except:
                    logging.info('text="Failed to cancel timeout timer."')
                self.d = None
                self.scheduleNext()
                return
            else:
                line = line[len(self.d.raw) :].strip()
                self.buf = []
                if line:
                    self.buf.append(line)
        else:
            # HACK: the controller replies with keywords that are prefixed with its
            # spectrograph (SP1 or SP2). In September 2025 we installed the SP2
            # controller with the SP1 cameras. This hack changes SP2 to SP1 in the
            # response from the camera controller (the mech and DAQ do not include
            # spectrohraph-specific prefixes in their replies).
            if line.startswith(b"SP2"):
                line = b"SP1" + line[3:]

            # Push off the timeout and append line to response buffer
            self.buf.append(line)

        try:
            self.d.timer.delay(self.d.timeout)
        except:
            self.d.cmd.warn(
                'text="Failed to extend fired timeout on %s"'
                % self.factory.controller.name
            )
            reactor.callLater(
                0, self.d.errback, Exception("Something is wrong with the timeout.")
            )
            line = b""

        if line.strip().endswith(b"ok"):
            self.d.cmd.diag(
                'text="Completed message from %s"' % (self.factory.controller.name)
            )
            if b"PHASEMICRO BUSY" in line:
                reactor.callLater(0, self.d.errback, BOSSExceptions.PhaseMicroBusy())
            else:
                reactor.callLater(0, self.d.callback, self.buf)
        elif b"UNDEFINED" in line:
            errText = qstr(
                "Cam %s received an undefined command: %s (%s)"
                % (self.factory.controller.name, self.d.raw, line)
            )
            self.d.cmd.warn("txt=%s" % (errText))
            reactor.callLater(
                0, self.d.errback, BOSSExceptions.UndefinedCommand(errText)
            )
        elif line.endswith(b" - EMPTY STK"):
            errText = qstr("Cam %s stack empty" % (self.factory.controller.name))
            self.d.cmd.warn("txt=%s" % (errText))
            reactor.callLater(
                0, self.d.errback, BOSSExceptions.UndefinedCommand(errText)
            )
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

        def TimeOutCallback():
            raise BOSSExceptions.TimeOutError(response)

        reactor.callLater(0, d.errback, TimeOutCallback)
        d.cmd.warn(response)
        logging.info(response)
