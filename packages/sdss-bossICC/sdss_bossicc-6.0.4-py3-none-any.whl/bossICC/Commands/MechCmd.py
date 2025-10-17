#!/usr/bin/env python
""" MechCmd.py -- wrap specmech functions. """

from twisted.internet import reactor
from twisted.internet.defer import Deferred, DeferredList

import opscore.protocols.keys as keys
import opscore.protocols.types as types
from opscore.utility.qstr import qstr

from bossICC.Commands.BaseDelegate import BaseDelegate


def sign(x):
    return 1 if x >= 0 else -1


def motorKeys(cmd, motor_positions, motor_status):
    response = ",".join(["0x%02x" % int(m) for m in motor_status])
    cmd.respond("motorStatus=%s" % response)

    response = ",".join(["%0d" % int(m) for m in motor_positions])
    cmd.respond("motorPosition=%s" % response)


class StatusDelegate(BaseDelegate):
    """Delegate status commands to the appropriate hardware."""

    def init(self):
        self.mechs = {"sp1mech": {}}
        self.finish = True

    def individualComplete(self, status, cmd, mech):
        cmd.diag('text="Noting the status from %s."' % mech)
        if status:
            self.mechs[mech] = dict(status)
        else:
            self.mechs[mech] = {}

    def complete(self, result, cmd):
        # Prepare to merge the keywords
        shutter_status = []
        screen_status = []
        motor_status = []
        motor_positions = []
        versions = []
        slitIDs = []
        protocols = []

        for mech in ("sp1mech",):
            specName = mech[0:3]
            status = self.mechs.get(mech, {})

            # The status dict contains integers, floats, and strings as bytes
            # as they come directly from the controller and it's not easy to
            # decode them along with the other data. Here we decode only those
            # parameters that we know must be strings. The status dictionary
            # values themselves are not decoded.

            motor_positions.extend(
                status.get("motorPos", [-9999999, -9999999, -9999999])
            )
            motor_status.extend(status.get("motorStatus", [0xFF, 0xFF, 0xFF]))

            # Crap. The new specmech outputs nice keywords for screens and the shutter.
            # But we still need to generate the numeric ones. Crap.
            shutter = status.get("Shutter", b"Unknown").decode()
            shutterValues = dict(Closed=0x02, Open=0x01, Unknown=0x00)
            shutter_status.append(shutterValues[shutter])

            screens = status.get("Hartmann", [b"Unknown", b"Unknown"])
            screens0 = screens[0].decode()
            screens1 = screens[1].decode()
            screenValues = dict(Closed=0x02, Open=0x01, Unknown=0x00)
            screenMask = screenValues[screens0] | (screenValues[screens1] << 2)
            screen_status.append(screenMask)

            versions.append(status.get("Version", b"Offline").decode())
            slitIDs.append(status.get("SlitID", 0))
            protocols.append(status.get("protocol", 0))

            response = "%0.3f,%0.3f" % tuple(
                [
                    status.get(t, 0)
                    for t in ("ShutterOpenTransit", "ShutterCloseTransit")
                ]
            )
            cmd.respond("%sLastShutterTime=%s" % (specName, response))

            response = "%0.1f,%0.1f" % tuple(
                [status.get("Humid" + t, 0) for t in ("Hartmann", "CenOptics")]
            )
            cmd.respond("%sHumidity=%s" % (specName, response))

            fmt = ",".join(["%0.1f"] * 6)
            response = fmt % tuple(
                [
                    status.get("Temp" + t, 999.9)
                    for t in (
                        "Median",
                        "HartmannTop",
                        "RedCamTop",
                        "BlueCamTop",
                        "RedCamBot",
                        "BlueCamBot",
                    )
                ]
            )
            cmd.respond("%sTemp=%s" % (specName, response))

        response = ",".join(["0x%02x" % int(m) for m in motor_status])
        cmd.respond("motorStatus=%s" % response)

        response = ",".join(["%0d" % int(m) for m in motor_positions])
        cmd.respond("motorPosition=%s" % response)

        response = ",".join(["0x%02x" % m for m in shutter_status])
        cmd.respond("shutterStatus=%s" % response)

        response = ",".join(["0x%02x" % m for m in screen_status])
        cmd.respond("screenStatus=%s" % response)

        cmd.respond("slitIDs=%d" % max(slitIDs[0] - 32, 0))
        cmd.respond("specMechVersion=%s" % tuple(versions))
        cmd.respond("specMechProtocol=%s" % tuple(protocols))
        if self.finish:
            if self.success:
                cmd.finish()
            else:
                cmd.fail('text="Failed to parse status from each mech."')

    def failed(self, reason, cmd, mech):
        cmd.warn('text="Failed to gather status for %s, %s"' % (mech, reason.value))
        self.success = False


class ShutterDelegate(BaseDelegate):
    """Delegate shutter commands to the appropriate hardware."""

    def init(self):
        self.state = None

    def individualComplete(self, data, mech):
        self.cmd.respond('text="%s achieved state %s."' % (mech, self.state))

    def complete(self, result, command):
        self.cmd.respond('text="Shutter(s) %s "' % (self.state))
        command.status(self.cmd, doFinish=False).addCallback(self.finishCmd)

    def finishCmd(self, data):
        if self.success:
            self.cmd.finish("")
        else:
            self.cmd.fail("")

    def failed(self, reason, mech):
        self.cmd.warn('text="Failed to shutter %s on %s"' % (self.state, mech))
        self.success = False


class ScreenDelegate(BaseDelegate):
    """Delegate hartmann commands to the appropriate hardware."""

    def init(self):
        self.state = None

    def individualComplete(self, data, mech):
        self.cmd.respond('text="%s screen achieved state %s."' % (mech, self.state))

    def complete(self, result, command):
        self.cmd.respond('text="Screen(s) %s "' % (self.state))
        command.status(self.cmd, doFinish=False).addCallback(self.finishCmd)

    def finishCmd(self, data):
        if self.success:
            self.cmd.finish("")
        else:
            self.cmd.fail("")

    def failed(self, reason, mech):
        self.cmd.warn('text="Failed to screen %s on %s"' % (self.state, mech))
        self.success = False


class MotorDelegate(BaseDelegate):
    """Delegate collimator motor commands to the appropriate hardware."""

    def init(self):
        self.names = ("a", "b", "c")
        self.setTarget(None, None, False, [0, 0, 0])
        self.failed = False

    def setTarget(self, mech, mechCmd, absMove, targetPos, carryOn=False):
        """Define the target position.

        Args:
          mech       - 'sp1' or 'sp2'
          mechCmd    -
          absMove    - whether the target position is absolute or relative
          targetPos  - steps
          carryOn    ? if True, ignore individual axis failures are keep trying to move
                       until all are stopped.
        """

        self.targetPos = targetPos
        self.absMove = absMove
        self.mech = mech
        self.mechCmd = mechCmd
        self.carryOn = carryOn

    def execute(self):
        """Execute the move that the delegate was created for."""

        if self.mech is None:
            self.cmd.fail('text="No mech specified."')
            return

        self.controller = self.icc.controllers.get(self.mech, None)
        if not self.controller:
            self.cmd.error('text="No controller for %s"' % (self.mech))
            self.cmd.fail("")
            return

        # Fire off the position query; the callback does all the work.
        self.getMotorPos(self.cmd, self.mech).addCallback(self._startMove)

    def getMotorPos(self, cmd, mechName):
        """Broadcast motor positions"""
        d = Deferred()
        mech = self.icc.controllers.get(mechName, None)
        if mech:
            status = mech.status(cmd)
            status.addCallback(self._finishMotorPos, mech, d)
        else:
            # this shouldn't ever happen: controllers.get would except first.
            raise RuntimeError("hell")
        return d

    def _finishMotorPos(self, mstatus, mech, d):
        reactor.callLater(0, d.callback, (mstatus["motorPos"], mstatus["motorStatus"]))

    def _startMove(self, data):
        """Get starting motor position and translate move to absolute units."""

        startPos, startStatus = data

        self.lastPos = startPos
        if not self.absMove:
            self.targetPos = [sum(m) for m in zip(startPos, self.targetPos)]
        self.lastReq = [None, None, None]

        distance = [m[1] - m[0] for m in zip(startPos, self.targetPos)]

        # Number of moves (clipped to <= 1000 steps) each axis can run.
        self.stepsLeft = [int(abs(d) / 1000) + 4 for d in distance]

        self.cmd.diag(
            'text="moving %s from %s to %s (abs=%s)"'
            % (self.mech, startPos, self.targetPos, self.absMove)
        )
        reactor.callLater(0, self._doMove, data)

    def _doMove(self, data):
        """Given new reported positions, generate the next piece of the move."""

        if self.failed:
            self.cmd.fail("Motor moved failed, command failed.")
            return

        positions, status = data

        reqLeft = [m[0] - m[1] for m in zip(self.targetPos, positions)]

        self.cmd.respond('text="motors at %s"' % (positions))
        self.cmd.respond('text="remaining move: %s"' % (reqLeft))

        for motorId in range(3):
            name = self.names[motorId]

            left = reqLeft[motorId]
            lastMove = positions[motorId] - self.lastPos[motorId]
            lastReq = self.lastReq[motorId]

            # Pass along any older vetoes.
            self.cmd.diag(
                'text="%s(%d): at=%s left=%s lastPos=%s lastReq=%s lastMove=%s"'
                % (
                    name,
                    motorId,
                    positions[motorId],
                    left,
                    self.lastPos[motorId],
                    lastReq,
                    lastMove,
                )
            )
            if lastReq == 0:
                reqLeft[motorId] = 0
                left = 0

            # Close enough?
            if abs(left) <= 8:
                self.cmd.diag('text="%s declared done at %d"' % (name, left))
                reqLeft[motorId] = 0

            # Hit limit switch?
            elif status[motorId] & 0x02:
                self.cmd.warn(
                    'text="%s actuator hit a limit!!!!! requested=%s; moved=%s)"'
                    % (name, lastReq, lastMove)
                )
                reqLeft[motorId] = 0
                if not self.carryOn:
                    self.moveFailed("limit hit", name)
                    return

            # Reversed by some significant amount? Note that the motor controller
            # reverses by 4000 steps after a limit is hit.
            elif lastReq and lastMove * lastReq < -1000:
                self.cmd.warn(
                    'text="reversed %s (requested=%s; moved=%s): probably hit a limit!"'
                    % (name, lastReq, lastMove)
                )
                reqLeft[motorId] = 0
                if not self.carryOn:
                    self.moveFailed("actuator reversed direction", name)
                    return

            # Taking too long to get there?
            elif self.stepsLeft[motorId] <= 0:
                self.cmd.warn(
                    'text="stopped %s move -- too many tries. requested=%s moved=%s "'
                    % (name, lastReq, lastMove)
                )
                reqLeft[motorId] = 0

            # Did not move as expected?
            # Stopped?
            # Can we tell if we _hit_ home?
            else:
                reqLeft[motorId] = left

            self.stepsLeft[motorId] -= 1

        dl = []
        if any(reqLeft):
            reqs = [0, 0, 0]
            for motorId in range(3):
                req = reqLeft[motorId]
                if abs(req) > 1000:
                    req = 1000 * sign(req)
                reqs[motorId] = req

            self.lastReq = reqs
            self.lastPos = positions
            self.cmd.diag('text="%s"' % (("Moving %s motors %s") % (self.mech, reqs)))
            d = self.controller.moveMotors(*reqs, cmd=self.cmd)
            d.addErrback(self.moveFailed, "motors")
            dl.append(d)
            dl.append(self.getMotorPos(self.cmd, self.mech).addCallback(self._doMove))
            return dl
        else:
            # Moves are done
            # Finish up with a status check
            self.mechCmd.status(self.cmd)

    def moveFailed(self, reason, motorName):
        self.failed = True
        self.cmd.fail(
            'text="Motor move on (%s %s) failed or did not finish: %s"'
            % (self.mech, motorName, reason)
        )

        # Finish up with a status check
        self.mechCmd.status(self.icc.bcast)


class ZeroDelegate(BaseDelegate):
    """Delegate motor zeroing commands to the appropriate hardware."""

    def init(self):
        pass

    def individualComplete(self, data, mech):
        self.cmd.respond('text="%s motors zeroed."' % mech)
        return

    def complete(self, data, command):
        self.cmd.respond('text="Motors zeroed."')
        command.status(self.cmd, doFinish=False).addCallback(self.finish)

    def finish(self, data):
        if self.success:
            self.cmd.finish("")
        else:
            self.cmd.fail('text="Failed to zero both motors."')

    def failed(self, reason, mech):
        self.cmd.warn('text="Failed to zero %s, %s"' % (mech, reason.value))
        self.success = False


class IackDelegate(BaseDelegate):
    """Delegate reboot acknowledge commands to the appropriate hardware."""

    def init(self):
        pass

    def individualComplete(self, data, mech):
        self.cmd.respond('text="%s iacked."' % mech)
        return

    def complete(self, data, command):
        self.cmd.respond('text="Controllers iacked."')
        command.status(self.cmd, doFinish=False).addCallback(self.finish)

    def finish(self, data):
        if self.success:
            self.cmd.finish("")
        else:
            self.cmd.fail('text="Failed to iack some controller."')

    def failed(self, reason, mech):
        self.cmd.warn('text="Failed to iack %s, %s"' % (mech, reason.value))
        self.success = False


class MechCmd(object):
    """Commands to manipulate the mechs"""

    def __init__(self, icc):
        self.icc = icc

        self.keys = keys.KeysDictionary(
            "boss_mech",
            (1, 1),
            keys.Key("spec", types.Enum("sp1"), help="the name of a spectrograph"),
            keys.Key("motor", types.String() * (1, 3), help="list of motor names"),
            keys.Key("a", types.Int(), help="the number of ticks to move actuator A"),
            keys.Key("b", types.Int(), help="the number of ticks to move actuator B"),
            keys.Key("c", types.Int(), help="the number of ticks to move actuator C"),
            keys.Key(
                "piston",
                types.Int(),
                help="the number of ticks to move actuators A,B, and C",
            ),
            keys.Key("ticks", types.Int(), help="the number of ticks to move"),
        )

        self.vocab = (
            ("openShutter", "[<spec>]", self.openShutter),
            ("closeShutter", "[<spec>]", self.closeShutter),
            ("hartmann", "@(left|right|out|both) [<spec>]", self.screen),
            (
                "moveColl",
                "<spec> [<a>] [<b>] [<c>] [<piston>] [@(abs)] [@(home)] [@(carryOn)]",
                self.moveColl,
            ),
            ("zeroMotors", "[<spec>]", self.zeroMotors),
            ("mechStatus", "", self.status),
            ("mechIack", "[<spec>]", self.iack),
        )

    def testStatus(self, cmd, doFinish=True):
        """Parse the status of each conected mech and report it in keyword form."""

        status = {}
        for mechname in ("sp1mech",):
            mech = self.icc.controllers.get(mechname, None)
            if mech:
                status[mechname] = mech.fullStatus(cmd)
                keys = list(status[mechname].keys())
                keys.sort()
                for k in keys:
                    cmd.diag(
                        "text=%s"
                        % (qstr("%s.%s: %s" % (mechname, k, status[mechname][k])))
                    )

        if doFinish:
            cmd.finish("")

    def status(self, cmd, doFinish=True):
        """Parse the status of each conected mech and report it in keyword form."""
        dl = []
        delegate = StatusDelegate(("sp1mech",), cmd, self.icc)
        delegate.finish = doFinish
        for mechname in ("sp1mech",):
            mech = self.icc.controllers.get(mechname, None)
            if mech:
                status = mech.status(cmd).addErrback(delegate.failed, cmd, mechname)
                status.addCallback(delegate.individualComplete, cmd, mechname)
                dl.append(status)

        return DeferredList(dl).addCallback(delegate.complete, cmd)

    ############################################################
    # Shutter Commands                                         #
    ############################################################
    def openShutter(self, cmd):
        """Open the shutter."""
        self._shutterCommand("open", cmd)

    def closeShutter(self, cmd):
        """Close the shutter."""
        self._shutterCommand("close", cmd)

    def _shutterCommand(self, action, cmd):
        mechs = self.specs_for_cmd(cmd)
        if not mechs:
            return

        delegate = ShutterDelegate(mechs, cmd, self.icc)

        for mech in mechs:
            cmd.respond('text="Performing %s on %s"' % (action, mechs))
            if action == "open":
                shutter = self.icc.controllers[mech].openShutter(cmd)
                state = "Open"
            else:
                shutter = self.icc.controllers[mech].closeShutter(cmd)
                state = "Closed"
            shutter.addErrback(delegate.failed, mech)

        delegate.state = state
        dl = []
        for mech in mechs:
            cmd.respond('text="Waiting for %s to be  %s"' % (mech, state))
            wait = self.icc.controllers[mech].waitForShutterState(state, cmd)
            wait.addCallback(delegate.individualComplete, mech)
            wait.addErrback(delegate.failed, mech)
            dl.append(wait)
        DeferredList(dl).addCallback(delegate.complete, self)

    ############################################################
    # Screen Commands                                          #
    ############################################################
    def screen(self, cmd):
        """
        Move the hartmann left, right or out.
        Note that this is mostly an engineering command:
           boss exposure hartmann=left/right handles the hartmanns for exposures.
        """

        specs = self.specs_for_cmd(cmd)
        try:
            command = cmd.cmd.keywords[0].name
            assert command in ("left", "right", "both", "out")
        except:
            cmd.warn('text="hartmann [left|right|out|both]"')
            specs = ()
        dl = []
        delegate = ScreenDelegate(specs, cmd, self.icc)
        for spec in specs:
            delegate.state = command
            d = self.icc.controllers[spec].screen(command, cmd)
            d.addCallback(delegate.individualComplete, spec)
            d.addErrback(delegate.failed, spec)
            dl.append(d)
        DeferredList(dl).addCallback(delegate.complete, self)

    ############################################################
    # Motor Commands                                           #
    ############################################################
    def moveColl(self, cmd):
        """Adjust the position of the colimator motors.
        Arguments:
            specs=sp1,sp2 - Which mech to use.
            a,b,c         - one or motor commands, in ticks.
              or
            piston=ticks
            abs           - if true, go to absolute position.
        """

        cmdKeys = cmd.cmd.keywords
        specs = self.specs_for_cmd(cmd)

        if len(specs) != 1:
            cmd.fail('text="exactly one spectrograph must be specified')
            return

        absMove = "abs" in cmdKeys
        goHome = "home" in cmdKeys
        carryOn = "carryOn" in cmdKeys
        piston = cmdKeys["piston"].values[0] if "piston" in cmdKeys else None

        a = cmdKeys["a"].values[0] if "a" in cmdKeys else 0
        b = cmdKeys["b"].values[0] if "b" in cmdKeys else 0
        c = cmdKeys["c"].values[0] if "c" in cmdKeys else 0

        if not (piston or a or b or c or goHome):
            cmd.fail('text="No motion specified"')
            return

        if piston and (a or b or c) and goHome:
            cmd.fail(
                'text="Either piston or home or one or '
                'more of a,b,c must be specified."'
            )
            return

        if goHome:
            piston = -50000
        if piston:
            a = b = c = piston

        delegate = MotorDelegate(specs, cmd, self.icc)
        delegate.setTarget(
            specs[0], self, absMove, [a, b, c], carryOn=(carryOn or goHome)
        )
        delegate.execute()

    def zeroMotors(self, cmd):
        """Declare that the current position of the collimator motors is 0,0,0."""
        dl = []

        specs = self.specs_for_cmd(cmd)
        delegate = ZeroDelegate(specs, cmd, self.icc)
        if not specs:
            return
        for spec in specs:
            cmd.respond('text="%s"' % ("Zeroing motors on %s" % (spec)))
            d = self.icc.controllers[spec].zeroMotors(cmd)
            d.addCallback(delegate.individualComplete, spec)
            d.addErrback(delegate.failed, spec)
            dl.append(d)

        DeferredList(dl).addCallback(delegate.complete, self)

    def iack(self, cmd):
        """Acknowledge a specmech reboot."""
        dl = []

        specs = self.specs_for_cmd(cmd)
        if not specs:
            return

        delegate = IackDelegate(specs, cmd, self.icc)
        for spec in specs:
            cmd.respond('text="%s"' % ("iacking %s" % (spec)))
            d = self.icc.controllers[spec].iack(cmd)
            d.addCallback(delegate.individualComplete, spec)
            d.addErrback(delegate.failed, spec)
            dl.append(d)

        DeferredList(dl).addCallback(delegate.complete, self)

    ############################################################
    # Helper Commands                                          #
    ############################################################
    def specs_for_cmd(self, cmd):
        try:
            specs = cmd.cmd.keywords["spec"].values
            for spec in specs:
                assert spec == "sp1" or spec == "sp2"
        except KeyError:
            specs = ["sp1"]
        except:
            cmd.fail('text = "Invalid spec specified."')
            return
        specs = [sp + "mech" for sp in specs]
        return specs
