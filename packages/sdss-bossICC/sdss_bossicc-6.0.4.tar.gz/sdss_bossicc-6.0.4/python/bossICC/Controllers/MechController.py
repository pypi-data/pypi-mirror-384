from twisted.internet import reactor
from twisted.internet.defer import Deferred

from opscore.utility.qstr import qstr

from bossICC.Controllers import BaseController, MechProtocol
from bossICC.Controllers.BaseFactory import BaseFactory


# The replies from the protocol are always bytes. Integers and floats are
# evaluated but the rest remains bytes and we send it so to the command.
# byte strings are decoded only before outputting to the users.


class MechFactory(BaseFactory):
    protocol = MechProtocol.MechProtocol


class MechController(BaseController.BaseController):
    factory_class = MechFactory

    def __init__(self, icc, name, debug=1):
        BaseController.BaseController.__init__(self, icc, name, debug)
        self.mechProtocol = 3
        self.cachedStatus = {}

    def ping(self, cmd=None):
        d = Deferred()
        status_deferred = self.status(cmd)
        status_deferred.addCallback(self._pingComplete, d, cmd)
        status_deferred.addErrback(self._pingFailed, d, cmd)
        return d

    def _pingComplete(self, data, d, cmd):
        reactor.callLater(0, d.callback, data["Version"])

    def _pingFailed(self, reason, d, cmd):
        reactor.callLater(0, d.errback, reason)

    def iack(self, cmd):
        # '!' acknowledges a mech reboot. Non-status commands fail until this
        # is issued. no-op if reboot already was acknowledged.
        return self.sendCommand("!", cmd, timeout=1)

    def status(self, cmd, ntries=3, ntry=0, d=None):
        if d is None:
            d = Deferred()

        if ntry > ntries:
            # Too many tries
            reactor.callLater(
                0, d.errback, Exception("Failed to properly parse status.")
            )
            return d

        status_deferred = self.sendCommand("sa", cmd, timeout=10)
        status_deferred.addCallback(self._statusComplete, d, cmd, ntry)
        status_deferred.addErrback(self._statusFailed, d, cmd, ntries, ntry)

        return d

    def _statusUpdate(self, data, d, cmd, ntry):
        status = {}
        status["protocol"] = self.mechProtocol
        for line in data:
            if len(line) > 1:
                line = line.lstrip(" \t")
                line = line.rstrip(" \t\r\n\0")
                items = line.split(" ")
                if len(items[1:]) > 1:
                    status[items[0]] = items[1:]
                elif len(items) > 1:
                    status[items[0]] = items[1]

    def _statusComplete(self, data, d, cmd, ntry):
        """The one and only routine which parses, validates,
        and converts raw specmech status output.

        Args:
           data    - the specmech 's'tatus output as a list of lines.
           d       - a Deferred to "call"
           cmd     - the cmd we are operating for.
           ntry    - the number of times we have tried to get valid 's'tatus. Passed on.

        Fills in the .cachedStatus dictionary, with renamed, validated, and typed
        values. This dict also contains the raw 's'tatus keys and values.
        """

        status = {}
        status["protocol"] = self.mechProtocol
        for line in data:
            if len(line) > 1:
                line = line.lstrip(b" \t")
                line = line.rstrip(b" \t\r\n\0")
                items = line.split(b" ")
                if len(items[1:]) > 1:
                    status[items[0].decode()] = items[1:]
                elif len(items) > 1:
                    status[items[0].decode()] = items[1]

        # Validate the status
        statusIsOK = True

        # Validate Motor Data
        # Grab converted versions of the motor position and status
        # MotorInitialized TRUE TRUE TRUE"
        # MotorStatus 133 133 133"
        # MotorMeasPos 5 0 1"

        try:
            raw = status.get("MotorMeasPos")
            vals = list(map(int, raw))
            status["motorPos"] = vals
        except:
            cmd.warn(
                "text=%s" % (qstr("value for motor positions was bad: %s" % (raw)))
            )
            status["motorPos"] = (-9999999, -9999999, -9999999)
            statusIsOK = False

        try:
            raw = status.get("MotorStatus")
            vals = list(map(int, raw))
            status["motorStatus"] = vals
        except:
            cmd.warn("text=%s" % (qstr("value for motor status was bad: %s" % (raw))))
            status["motorStatus"] = (0xFF, 0xFF, 0xFF)
            statusIsOK = False

        # The following are simply type-converted in place, if possible:
        # SpectroID 2
        # SlitID 17
        # DesiredExpTime 0.00
        # RemainingExpTime 0.00
        # LastExpTime 0.00
        # ShutterOpenTransit 0.00
        # ShutterCloseTransit 0.00
        # HumidHartmann 25.1 0x
        # HumidCenOptics 14.0 0x
        # TempMedian 4.2
        # TempHartmannTop 5.0 (0x)
        # TempRedCamBot 4.6 (0x)
        # TempRedCamTop 3.9 (0x)
        # TempBlueCamBot 4.2 (0x)
        # TempBlueCamTop 4.3 (0x)
        for name in ("SpectroID", "SlitID"):
            try:
                cnv = int(status[name])
            except:
                cmd.warn(
                    'text="Failed to convert %s=%s to int."'
                    % (name, status.get(name, "noValue"))
                )
                cnv = -1
            status[name] = cnv

        for name in (
            "HumidHartmann",
            "HumidCenOptics",
            "TempHartmannTop",
            "TempRedCamBot",
            "TempRedCamTop",
            "TempBlueCamBot",
            "TempBlueCamTop",
            "TempMedian",
            "DesiredExpTime",
            "RemainingExpTime",
            "LastExpTime",
            "ShutterOpenTransit",
            "ShutterCloseTransit",
        ):
            try:
                val = status[name]
                if type(val) == list:
                    val = val[0].decode()
                cnv = float(val)
            except:
                cmd.warn(
                    'text="Failed to convert %s=%s to float."'
                    % (name, status.get(name, "noValue"))
                )
                cnv = -9999.9
            status[name] = cnv

        # The following are left unmolested and unimproved:
        # Version 3.0.0b1
        # Air On
        # AD 27455 1094
        # ExpState Idle
        # BootAcknowledged No
        # Shutter Closed
        # Hartmann Closed Closed

        cmd.respond('text="Response parsed."')
        if statusIsOK:
            # We are done call the callbacks
            self.cachedStatus = status
            reactor.callLater(0, d.callback, status)
        else:
            # Try again
            reactor.callLater(0, self.status, cmd, ntry=ntry + 1, d=d)

    def _statusFailed(self, reason, d, cmd, ntries, ntry):
        # Try again
        cmd.warn(
            'text="Failed to parse %s status, trying again (%d of %d): %s"'
            % (self.name, ntry, ntries, reason.value)
        )
        reactor.callLater(0, self.status, cmd, False, ntry=ntry + 1, d=d)

    def expose(self, cmd, itime, hartmann=None):
        if hartmann is None:
            return self.sendCommand("eo%0.3f" % (itime), cmd, timeout=4)
        elif hartmann == "left":
            return self.sendCommand("el%0.3f" % (itime), cmd, timeout=4)
        elif hartmann == "right":
            return self.sendCommand("er%0.3f" % (itime), cmd, timeout=4)

    def openShutter(self, cmd):
        return self.sendCommand("xso", cmd)

    def closeShutter(self, cmd):
        return self.sendCommand("xsc", cmd)

    def stopExposure(self, cmd):
        return self.sendCommand("eS", cmd)

    def waitForShutterState(self, state, cmd=None, poll_rate=1, timeout=10):
        return self._waitForStatusValue(
            "Shutter", state, cmd=cmd, poll_rate=poll_rate, timeout=timeout
        )

    def waitForScreenState(self, state, cmd=None, poll_rate=1, timeout=10):
        return self._waitForStatusValue(
            "Hartmann", state, cmd=cmd, poll_rate=poll_rate, timeout=timeout
        )

    def _waitForStatusValue(self, key, value, cmd=None, poll_rate=1, timeout=10):
        d = Deferred()
        status = self.status(cmd)
        status.addCallback(
            self._waitForStatusComplete, cmd, key, value, poll_rate, timeout, d, 0
        )
        status.addErrback(
            self._waitForStatusFailed, cmd, key, value, poll_rate, timeout, d, 0
        )
        return d

    def _waitForStatusComplete(
        self, status, cmd, key, value, poll_rate, timeout, d, tries
    ):
        print(status[key])
        if status[key] == value:
            reactor.callLater(0, d.callback, status[key])
            return
        else:
            if tries >= timeout:
                # Timedout
                reactor.callLater(
                    0, d.errback, Exception("Timed out waiting for shutter.")
                )
                return
            else:
                # Schedule another check
                reactor.callLater(
                    0,
                    self._callStatusLater,
                    cmd,
                    key,
                    value,
                    poll_rate,
                    timeout,
                    d,
                    tries,
                )

    def _waitForStatusFailed(
        self, reason, cmd, key, value, poll_rate, timeout, d, tries
    ):
        if tries > timeout:
            # Timedout
            reactor.callLater(0, d.errback, Exception("Timed out waiting for shutter."))
            return
        else:
            # Schedule another check
            reactor.callLater(
                0,
                self._callStatusLater,
                cmd,
                key,
                value,
                poll_rate,
                timeout,
                d,
                tries + poll_rate,
            )

    def _callStatusLater(self, cmd, key, value, poll_rate, timeout, d, tries):
        status = self.status(cmd)
        status.addCallback(
            self._waitForStatusComplete,
            cmd,
            key,
            value,
            poll_rate,
            timeout,
            d,
            tries + poll_rate,
        )
        status.addErrback(
            self._waitForStatusFailed,
            cmd,
            key,
            value,
            poll_rate,
            timeout,
            d,
            tries + poll_rate,
        )
        return status

    def screen(self, action, cmd=None):
        """Command a hartmann screen move.

        Args:
            action   - which screens should be put in the beam.
                       'left', 'right', 'out', 'both'
            cmd      - the controlling Command.
        """

        if action == "left":
            cmdTxt = "xhl"
        elif action == "right":
            cmdTxt = "xhr"
        elif action in ("both", "closed"):
            cmdTxt = "xhc"
        elif action in ("none", "open", "out"):
            cmdTxt = "xho"

        return self.sendCommand(cmdTxt, cmd)

    def moveMotor(self, name, ticks, cmd=None):
        moves = [0, 0, 0]
        names = dict(a=0, b=1, c=2)

        moves[names[name]] = ticks
        return self.moveMotors(*moves, cmd=cmd)

    def _moveDone(self, data, d, cmd):
        cmd.respond("text='move done'")
        return

    def _moveFailed(self, data, d, cmd):
        cmd.warn("text='move failed; ignoring'")
        return

    def moveMotors(self, a, b, c, cmd=None):
        # The internal timeout for motion commands is 5s.
        d = self.sendCommand("mr %d %d %d" % (a, b, c), cmd, timeout=8)
        d.addCallback(self._moveDone, d, cmd)
        d.addErrback(self._moveFailed, d, cmd)

        return d

    def moveMotorA(self, ticks):
        return self.moveMotors(ticks, 0, 0)

    def moveMotorB(self, ticks):
        return self.moveMotors(0, ticks, 0)

    def moveMotorC(self, ticks):
        return self.moveMotors(0, 0, ticks)

    def zeroMotors(self, cmd):
        return self.sendCommand("mz", cmd)

    def pistonCollimator(self, ticks, cmd=None):
        return self.moveMotors(ticks, ticks, ticks, cmd=cmd)


if __name__ == "__main__":
    reactor.connectTCP("localhost", 7000, MechFactory())
    reactor.run()
