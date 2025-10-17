#!/usr/bin/env python

""" TDSCmd.py -- wrap raw TDS functions. """

import logging
import time

from twisted.internet import reactor
from twisted.internet.defer import DeferredList

import actorcore.utility.fits as actorFits
import opscore.protocols.keys as keys
import opscore.protocols.types as types
import opscore.RO.Astro.Tm.MJDFromPyTuple as astroMJD
from opscore.utility.qstr import qstr

from bossICC import BOSSExceptions
from bossICC.Commands.BaseDelegate import BaseDelegate


class ExposureDelegate(BaseDelegate):
    def init(self):
        try:
            self.statusCmd = self.icc.commandSets.get("MechCmd", None)
        except:
            self.cmd.fail('text="cannot expose without the MechCmd package"')
        self.skipReadout = False

    # External commands
    # These must check the args against the exposure state and determine if the
    # command cannot be accepted.
    def start(self):
        """Parse the start command and determine the parameters of the exposure."""
        keywords = self.cmd.cmd.keywords
        flavor = keywords[0].name
        # Determine the integration time
        if flavor == "bias":
            itime = 0
        elif "itime" not in keywords:
            self.cmd.fail('text="Integration time not specified. i.e. itime=12"')
            self.command.exposureDelegate = None
            return
        else:
            itime = keywords["itime"].values[0]
            if itime == 0:
                self.cmd.fail('text="Integration time must be positive."')
                self.command.exposureDelegate = None
                return

        # Check if it is a focus exposure
        if "hartmann" in keywords:
            hartmann = keywords["hartmann"].values[0]
            if hartmann not in ("left", "right"):
                hartmann = None
        else:
            hartmann = None

        # Determine the cameras to be used.
        if "cams" in keywords:
            specs = [c[:3] for c in keywords["cams"].values]
        else:
            connectedCams, allCams = self.icc.getDevLists("cam$")
            specs = [dev[:3] for dev in allCams]
        specs = list(set(specs))

        # A user-specified comment to include in the header.
        if "comment" in keywords:
            headerComment = keywords["comment"].values[0]
        else:
            headerComment = None

        mechs = []
        forths = []
        daqs = []

        # From the determination of cameras calculate the hardware required.
        for spec in specs:
            for partname, partlist in (("cam", forths), ("mech", mechs), ("daq", daqs)):
                devname = spec + partname
                if devname not in self.icc.controllers:
                    if partname == "mech" and flavor in ("bias", "dark"):
                        self.cmd.warn(
                            'text="%s is not available, but we are continuing '
                            'because this is a %s"' % (devname, flavor)
                        )
                    else:
                        self.cmd.fail(
                            'text="Required device %s is not available."' % (devname)
                        )
                        return

                partlist.append(devname)

        # Make sure we have the pieces we need
        if len(specs) > len(forths):
            self.cmd.fail(
                'text="Some micros are missing! need=%scam have=%s"' % (specs, forths)
            )
            return

        # Check each camera to see if it is iacked
        iacked = True
        for f in forths:
            cam = self.icc.controllers[f]
            if not cam.iacked:
                self.cmd.error('text="%s not iacked, iack before using"' % (f))
                iacked = False
        if not iacked:
            self.cmd.fail('text="Required cameras not iacked."')
            return

        self.cmd.respond(
            'text="Hardware requirements calculated: %s."'
            % (",".join(forths + daqs + mechs))
        )

        self.window = None
        if "window" in keywords:
            y0, y1 = keywords["window"].values
            if y0 < 1 or y1 > (2 * self.icc.exposure.lines) or y0 > y1:
                self.cmd.fail(
                    'text="requested window does not lie on the '
                    'detector: %d to %d lines"' % (y0, y1)
                )
                return
            self.window = y0, y1

        self.skipReadout = "noReadout" in keywords

        # All seems well
        # grab the exposure semaphore
        if not self.icc.exposure.semaphore.acquire(blocking=False):
            # Exposure in progress, FAIL
            self.cmd.fail('text="Exposure already in progress."')
            return

        self.command.exposureDelegate = self

        # Purely for testing, force the exposure to be declared unread.
        if "testFail" in keywords:
            self.icc.exposure.needsRecovery = True

        # Store the collected arguments in the exposure singleton
        exp = self.icc.exposure
        exp.flavor = flavor
        exp.itime = itime
        exp.dirname = self.icc.filenameGen.dirname()
        exp.ID = self.icc.filenameGen.consumeNextSeqno()
        exp.cmd = self.cmd
        exp.daqs = daqs
        exp.cams = forths
        exp.mechs = mechs
        exp.hartmann = hartmann
        exp.darkStart = time.time()
        self.cmd.respond(
            'text="Exposure %s to be stored in %s"'
            % (self.icc.exposure.ID, self.icc.exposure.dirname)
        )

        # Create a list of deferreds to trigger the next phase
        dl = []

        # Prepare headers
        exp.headers = {}
        for n in (
            "shared",
            "red",
            "blue",
            "sp1",
            "sp2",
            "sp1blue",
            "sp2blue",
            "sp1red",
            "sp2red",
        ):
            exp.headers[n] = []

        if headerComment is not None:
            exp.headers["shared"].append(self._makeCard("COMMENT", headerComment))

        # Flush the ccds.
        self.flushFailed = False
        if "noflush" in keywords:
            exp.headers["shared"].append(
                self._makeCard(
                    "DIDFLUSH", False, "CCD was not flushed before integration"
                )
            )
            self.cmd.respond('text="NOT flushing the CCDs"')
            # Actually should be the end of last readout.
            self.flush_start = time.time()
            reactor.callLater(0, self._flushComplete, None)
        else:
            exp.headers["shared"].append(
                self._makeCard("DIDFLUSH", True, "CCD was flushed before integration")
            )
            self.cmd.respond('text="Flushing the CCDs"')
            if "flushproc" in keywords:
                procname = keywords["flushproc"].values[0]
                self.cmd.warn(
                    'text="over-riding builtin flush procedure with %s"' % (procname)
                )
            else:
                procname = "flush"

            self.icc.exposure.setState("FLUSHING", 13.0, 13.0)
            for cam in self.icc.exposure.cams:
                self.flush_start = time.time()
                if "/" in procname:
                    d = (
                        self.icc.controllers[cam]
                        .executePath(procname, self.cmd)
                        .addErrback(self._flushFailed, cam)
                    )
                else:
                    # we now have a separate flush for sp2
                    d = (
                        self.icc.controllers[cam]
                        .executeProc(procname + "_" + cam[:3], self.cmd)
                        .addErrback(self._flushFailed, cam)
                    )
                dl.append(d)
            if len(dl) > 0:
                DeferredList(dl).addCallback(self._flushComplete)
            else:
                reactor.callLater(0, self._flushComplete, None)

    def pause(self, cmd):
        """Pause an exposure that is currently integrating."""
        if self.icc.exposure.state != "INTEGRATING":
            cmd.fail('text="Exposure cannot be paused: not INTEGRATING."')
            return
        if self.icc.exposure.flavor in ("bias", "dark"):
            cmd.fail('text="Biases or darks would be silly to pause..."')
            return

        cmd.respond('text="Pausing the exposure..."')
        dl = []
        for spec in self.icc.exposure.mechs:
            d = self.icc.controllers[spec].sendCommand("eP", cmd, timeout=5)
            dl.append(d)

        # Report the mech status right after the shutters have been closed.
        dl.append(self.statusCmd.status(cmd, doFinish=False))

        # Pause the integration timer
        self.icc.exposure.timer.cancel()
        if len(dl) > 0:
            DeferredList(dl).addCallback(self._finishPause, cmd)
        else:
            reactor.callLater(0, self._finishPause, cmd)

    def _finishPause(self, data, cmd):
        remaining = []
        for spec in self.icc.exposure.mechs:
            remaining.append(
                self.icc.controllers[spec].cachedStatus["RemainingExpTime"]
            )

        self.remaining = max(remaining)
        # logging.info("Time elapsed = %0.3f" % elapsed)
        # logging.info("Time remaining = %0.3f" % self.remaining)
        # logging.info("Time commanded = %0.3f" % self.exposure.itime)

        self.icc.exposure.timer = None
        self.icc.exposure.setState("PAUSED", self.remaining, self.icc.exposure.itime)
        cmd.finish()

    def resume(self, cmd):
        """Resume a paused exposure."""
        if self.icc.exposure.state != "PAUSED":
            cmd.fail('text="Exposure not PAUSED"')
            return

        cmd.respond('text="Resuming the exposure..."')
        dl = []
        for spec in self.icc.exposure.mechs:
            d = self.icc.controllers[spec].sendCommand("eR", self.cmd, timeout=5)
            dl.append(d)

        # Report the mech status right after the shutters have been closed.
        dl.append(self.statusCmd.status(self.cmd, doFinish=False))

        if len(dl) > 0:
            DeferredList(dl).addCallback(self._finishResume, cmd)
        else:
            reactor.callLater(0, self._finishResume, cmd)

    def _finishResume(self, data=None, cmd=None):
        self.icc.exposure.timer = reactor.callLater(self.remaining, self.finishExposure)
        self.icc.exposure.setState(
            "INTEGRATING", self.remaining, self.icc.exposure.itime
        )

    def stop(self, cmd=None):
        """Force a running exposure to readout right away."""

        # Not totally obvious here. If we are FLUSHING, skip the read.
        state = self.icc.exposure.state
        if state in ("IDLE", "ABORTED", "PREREADING", "READING"):
            cmd.fail(
                'text="Cannot stop an exposure in the %s state."'
                % (self.icc.exposure.state)
            )
            return

        # Get the controller to close the shutter, etc.
        for m in self.icc.exposure.mechs:
            self.icc.controllers[m].stopExposure(self.icc.bcast)
        # Try and cancel the timer
        try:
            self.icc.exposure.timer.cancel()
        except:
            pass

        if state == "FLUSHING":
            cmd.warn('text="exposure was merely flushing, so we will not read it out"')
            self.icc.exposure.state = "IDLE"
            self.releaseExposure(self, doFinish=True)
        else:
            reactor.callLater(0, self.finishExposure)

        # The stop command succeeds (always?)
        if cmd:
            cmd.finish()

    def abort(self, cmd=None):
        if self.icc.exposure.state == "IDLE":
            cmd.fail('text="Cannot fail from the IDLE state."')
            return
        if self.icc.exposure.state == "READING":
            cmd.fail('text="Cannot abort exposures during readout."')
            return

        # Get the controller to close the shutter, etc.
        for m in self.icc.exposure.mechs:
            self.icc.controllers[m].stopExposure(self.icc.bcast)

        self.icc.exposure.setState("ABORTED", 0.0, 0.0)

        # Try and cancel the timer
        try:
            self.icc.exposure.timer.cancel()
        except:
            pass

        # The _exposure_ fails
        self.cmd.fail('text="exposure aborted"')

        # The abort command succeeds
        if cmd:
            cmd.finish()

    def readout(self, cmd):
        """To be called when the exposure has been aborted and a readout is needed."""

        if self.icc.exposure.state not in ("ABORTED", "LEGIBLE"):
            cmd.fail('text="Deliberate readout only allowed from aborted exposure."')
            return
        self.skipReadout = False

        # Bring the exposure command back to life, sort of. This should finish/fail the
        # readout command.
        cmd.diag(
            'text="Deliberate readout with cmd=%s and self.cmd=%s."' % (cmd, self.cmd)
        )
        self.cmd = cmd
        self.icc.exposure.cmd = cmd
        self.icc.exposure.setState("LEGIBLE", 0.0, 0.0)

        # Report the mech status
        self.statusCmd.status(self.cmd, doFinish=False)
        reactor.callLater(0, self.finishExposure)

    def recover(self, cmd):
        self.cmd = cmd
        cmd.inform("text='starting exposure recovery'")

        # Treat this readout as an entirely new exposure.
        # if not hasattr(self.icc.exposure, 'originalId'):
        #    self.icc.exposure.originalID = self.icc.exposure.ID
        if not hasattr(self.icc.exposure, "originalID"):
            self.icc.exposure.originalID = self.icc.exposure.ID
        self.icc.exposure.ID = self.icc.filenameGen.consumeNextSeqno()
        cmd.inform(
            "text='rereading exposure %d into %d'"
            % (self.icc.exposure.originalID, self.icc.exposure.ID)
        )
        self.icc.exposure.headers["shared"].append(
            self._makeCard(
                "ORIGEXP",
                self.icc.exposure.originalID,
                "This is a recovered exposure, from this EXPID",
            )
        )
        for daqname in self.icc.exposure.daqs:
            specname = daqname[:3]
            daq = self.icc.controllers[daqname]

            red_header = self._complete_header(specname, "red")
            blue_header = self._complete_header(specname, "blue")
            daq.set_fits_headers(red_header, blue_header)

        self.icc.exposure.setState(
            "READING", self.estimatedReadTime, self.estimatedReadTime
        )
        self.cmd.inform('text="Re-arming the daq..."')

        # Reset the list of failed readouts. We now lose info that we are recovering.
        self.failedReadouts = []
        dl = []
        for spec in self.icc.exposure.daqs:
            daq = self.icc.controllers[spec]

            d = daq.readout(cmd=self.cmd, expId=self.icc.exposure.ID)

            # Append the receiving thread to a list to be waited on
            dl.append(d)
            d.addErrback(self.armFailed)

        logging.info("%d : Daq armed." % (self.icc.exposure.ID))

        self.cmd.inform('text="Re-reading ..."')
        logging.info("%d : Waiting for readout to complete." % (self.icc.exposure.ID))

        # Schedule a timer to check to make sure the exposure finished
        reactor.callLater(120, self._readoutTimeout, self.icc.exposure.ID)

        # Defer the finishing of the exposure
        if len(dl) > 0:
            DeferredList(dl).addCallback(self._finishReadout)
        else:
            reactor.callLater(0, self._finishReadout, None)

        logging.info("%d : Daq ready." % (self.icc.exposure.ID))

    def status(self):
        """Republish the state."""
        self.icc.exposure.setState()

    def clear(self):
        """Clear the exposure and return it to IDLE, should always be possible."""
        try:
            self.icc.exposure.timer.cancel()
        except:
            pass
        self.icc.exposure.timer = None
        self.icc.exposure.setState("IDLE", 0.0, 0.0)

        for c in ("sp1mech", "sp2mech"):
            try:
                self.icc.controllers[c].stopExposure(self.icc.bcast)
            except:
                pass

        self.icc.exposure.semaphore.release()
        self.cmd.finish("")

    # Callbacks
    def _flushComplete(self, data):
        """Flush command has been issued, we must now wait for the phase micro."""

        dl = []
        # Report the mech status right before the exposure really starts.
        d = self.statusCmd.status(self.cmd, doFinish=False)
        dl.append(d)

        self.cmd.respond('text="Waiting for phase micro..."')
        logging.info("Waiting for phase micros...")
        for cam in self.icc.exposure.cams:
            d = (
                self.icc.controllers[cam]
                .phaseWait(cmd=self.cmd)
                .addErrback(self._flushFailed, cam)
            )
            dl.append(d)
        if len(dl) > 0:
            DeferredList(dl).addCallback(self._flushComplete2)
        else:
            reactor.callLater(0, self._flushComplete2, None)

    def _flushComplete2(self, data):
        """Just to have a place to override a failed flush."""
        if self.icc.exposure.state == "ABORTED":
            self.cmd.fail('text="Aborting exposure..."')
            return

        self.icc.exposure.darkStart = time.time()

        if self.flushFailed:
            self.cmd.fail('text="Flush failed, exposure aborted."')
            self.abort()
        else:
            self.cmd.inform("lastFlush=%d" % (time.time()))
            reactor.callLater(0, self.integrate)

    def _flushFailed(self, reason, cam):
        """Errback for anything going wrong in the flush phase."""
        if self.icc.exposure.state == "ABORTED":
            self.cmd.fail('text="Aborting exposure..."')
            return
        self.flushFailed = True
        try:
            reason.raiseException()
        except BOSSExceptions.TimeOutError:
            self.cmd.error('text="Timed out waiting for phasemicro on %s "' % cam)
        except BOSSExceptions.UndefinedCommand:
            self.cmd.error('text="Undefined command issued to %s"' % cam)
        except:
            self.cmd.error(
                'text="Error while waiting for flush to complete on %s. %s"'
                % (cam, reason.value)
            )

    def integrate(self):
        """We are ready to integrate."""
        if self.icc.exposure.state == "ABORTED":
            self.cmd.fail('text="Aborting exposure..."')
            return

        # Open shutters
        dl = []
        self.icc.exposure.startAt = time.time()

        # Configure the detectors for integration.
        # Maybe we don't need to do this for biases, but who cares?
        for spec in self.icc.exposure.cams:
            camforth = self.icc.controllers[spec]
            d = camforth.executeProc("pre-integrate_" + spec[:3], self.cmd).addErrback(
                self.readoutFailed, spec
            )
            dl.append(d)

        if self.icc.exposure.flavor not in ("bias", "dark"):
            self.cmd.respond('text="Opening the shutters."')
            for spec in self.icc.exposure.mechs:
                d = (
                    self.icc.controllers[spec]
                    .expose(
                        self.cmd,
                        self.icc.exposure.itime,
                        hartmann=self.icc.exposure.hartmann,
                    )
                    .addErrback(self._integrateFailed, spec)
                )
                dl.append(d)

            # Report the mech status as soon as the specmech exposure command finishes.
            d = self.statusCmd.status(self.cmd, doFinish=False)
            dl.append(d)
        else:
            self.cmd.respond('text="Shutters remain closed."')

        if len(dl) > 0:
            DeferredList(dl).addCallback(self._beginIntegration)
        else:
            reactor.callLater(0, self._beginIntegration)

    def _beginIntegration(self, data=None):
        # Schedule the timer
        # Move the state to integrating
        self.cmd.respond('text="Beginning integration."')
        self.icc.exposure.setState(
            "INTEGRATING", self.icc.exposure.itime, self.icc.exposure.itime
        )
        self._expstart_fits_cards()
        self.icc.exposure.timer = reactor.callLater(
            self.icc.exposure.itime, self.finishExposure
        )

    def shutterOpen(self, data, spec):
        self.cmd.respond('text="%s exposure began."' % spec)

    def _integrateFailed(self, reason, spec):
        # Failed to start exposure
        if self.icc.exposure.state == "ABORTED":
            self.cmd.fail('text="Aborting exposure..."')
            return
        self.cmd.warn('text="Failed to detect open shutter on %s."' % spec)
        self._mechCards(spec)
        self._chernoCards(spec)

    def finishExposure(self):
        """Begin the process of reading out the instrument."""
        if self.icc.exposure.state == "ABORTED":
            self.cmd.fail('text="Aborting exposure..."')
            return
        logging.info("%d : Doing a readout." % (self.icc.exposure.ID))
        dl = []
        # Check the shutter for closed status
        self.icc.exposure.setState("PREREADING", 3.0, 3.0)

        if self.icc.exposure.flavor not in ("bias", "dark"):
            self.cmd.inform('text="Waiting for shutter closed."')
            for spec in self.icc.exposure.mechs:
                d = self.icc.controllers[spec].waitForShutterState(
                    "Closed", cmd=self.cmd, poll_rate=1, timeout=3
                )
                d.addErrback(self._shutterCloseTimedOut, spec)
                dl.append(d)

        # Report the mech status as soon as the shutters are confirmed closed.
        d = self.statusCmd.status(self.cmd, doFinish=False)
        dl.append(d)

        if self.skipReadout:
            cb = self._skipReadout
        else:
            cb = self.finishExposure2

        if len(dl) > 0:
            DeferredList(dl).addCallback(cb)
        else:
            reactor.callLater(0, cb, None)

    def finishReadout(self):
        reactor.callLater(0, self.finishExposure2, None)

    def _skipReadout(self, data):
        self.icc.exposure.setState("LEGIBLE", 0.0, 0.0)
        self.cmd.finish('text="leaving exposure unread"')

    def _shutterCloseTimedOut(self, reason, mech):
        self.cmd.warn('text="Timed out waiting for shutter to close on %s."' % mech)

    def _makeFreadCmd(self, window=None):
        """Generate the readout command for out .cmd's readout window.

        Returns:
            isSubframe      - whether the readout is done with FREAD or SUBFREAD.
            nlines          - the number of quadrant rows that we will read out.
            fullframeLines  - the total number of lines in the full frame readout
            startLine       - the 0-based index of the starting line.
            skipLines       - the number of rows to skip before startLine.
            readCmd         - the micro command to readout the window.
        """

        def _estimateReadTime(nread, nskip=0, binning=1):
            lineReadTime = 26347 * 1e-6
            stupidOverhead = 3.5
            diskWriteTime = 2.5 * 1e-3  # Includes gzip -3
            return (
                stupidOverhead
                + lineReadTime * (nread + nskip / (1.0 * binning))
                + diskWriteTime * 2 * nread
            )

        if not window:
            self.estimatedReadTime = _estimateReadTime(self.icc.exposure.lines)
            return (
                False,
                self.icc.exposure.lines,
                self.icc.exposure.lines,
                0,
                0,
                "FREAD",
            )

        y0, y1 = window

        # Regions spanning the middle of the detector turn into the widest
        # section around the middle row.
        if y0 <= self.icc.exposure.lines and y1 > self.icc.exposure.lines:
            nlines = max(self.icc.exposure.lines - y0 + 1, y1 - self.icc.exposure.lines)
            y0 = self.icc.exposure.lines - nlines + 1
            y1 = self.icc.exposure.lines

        # These are in image coordinates. Hack them into quadrant coordinates.
        qY0 = (
            y0
            if y0 <= self.icc.exposure.lines
            else 2 * self.icc.exposure.lines - y0 + 1
        )
        qY1 = (
            y1
            if y1 <= self.icc.exposure.lines
            else 2 * self.icc.exposure.lines - y1 + 1
        )
        if qY0 > qY1:
            qY0, qY1 = qY1, qY0
        self.cmd.diag("text='y0,y1=%d,%d qY0,qY1=%d,%d'" % (y0, y1, qY0, qY1))

        assert (
            qY0 >= 1
            and qY1 >= 1
            and qY0 <= self.icc.exposure.lines
            and qY1 <= self.icc.exposure.lines
        )

        regions = []
        flushBinning = 10
        nread = 0
        nskip = 0

        # Possibly skip some lines first
        preSkipLines = 0
        if qY0 > 1:
            preSkipLines = int((qY0 - 1) / flushBinning)
            regions.append("1 %d %d" % (qY0 - 1, flushBinning))
            nskip += qY0 - 1

        # Readout section
        regions.append("1 %d 1" % (qY1 - qY0 + 1,))
        nread += qY1 - qY0 + 1

        # Skip the rest of the lines, if any
        if qY1 < self.icc.exposure.lines:
            hack = (self.icc.exposure.lines - qY1) + (
                self.icc.exposure.lines - qY1
            ) / flushBinning
            regions.append("1 %d %d" % (hack, flushBinning))
            nskip += self.icc.exposure.lines - qY1
        regions.append("%d SUBFREAD" % (len(regions)))

        self.estimatedReadTime = _estimateReadTime(nread, nskip, flushBinning)
        self.cmd.respond(
            "text=%s"
            % (
                qstr(
                    "preskip=%d nread=%d nskip=%d estRead=%0.2f regions are: %s"
                    % (preSkipLines, nread, nskip, self.estimatedReadTime, regions)
                )
            )
        )

        readoutCmd = " ".join(regions)
        return (
            readoutCmd,
            nread,
            self.icc.exposure.lines,
            qY0 - 1,
            preSkipLines,
            readoutCmd,
        )

    def finishExposure2(self, data):
        """Actually finish the readout process."""
        if self.icc.exposure.state == "ABORTED":
            self.cmd.fail('text="Aborting exposure..."')
            return
        dl = []
        # Get the actual exposure time
        self.icc.exposure.actualItime = {}
        for spec in self.icc.exposure.mechs:
            specname = spec[:3]
            if self.icc.exposure.flavor not in ("bias", "dark"):
                # Grab the last shutter time keyword from mech, cached should be fine
                status = self.icc.controllers[spec].cachedStatus
                actual = status["LastExpTime"]
                self.icc.exposure.actualItime[specname] = actual
                self.cmd.inform(
                    'text="Actual exposure time for %s = %0.3f"' % (specname, actual)
                )
            else:
                self.icc.exposure.actualItime[specname] = self.icc.exposure.itime

        (
            isSubframe,
            readoutLines,
            frameLines,
            startLine,
            preSkipLines,
            freadCmd,
        ) = self._makeFreadCmd(window=self.window)

        # Arm the daq
        logging.info("%d : Prepping the daq..." % (self.icc.exposure.ID))
        self.cmd.inform('text="Prepping the daq..."')
        for daqname in self.icc.exposure.daqs:
            specname = daqname[:3]
            self._expend_fits_cards(specname)
            daq = self.icc.controllers[daqname]
            try:
                daq.prepare_exposure(
                    expID=self.icc.exposure.ID,
                    lines=readoutLines,
                    pixels=self.icc.exposure.pixels,
                    direc=self.icc.exposure.dirname,
                    isSubframe=isSubframe,
                    frameLines=frameLines,
                    startLine=startLine,
                    skipLines=preSkipLines,
                    cmd=self.cmd,
                )
            except:
                self.cmd.warn(
                    "text='retrying readout prep. after DAQ connection re-established'"
                )
                daq.prepare_exposure(
                    expID=self.icc.exposure.ID,
                    lines=readoutLines,
                    pixels=self.icc.exposure.pixels,
                    direc=self.icc.exposure.dirname,
                    isSubframe=isSubframe,
                    frameLines=frameLines,
                    startLine=startLine,
                    skipLines=preSkipLines,
                    cmd=self.cmd,
                )

            red_header = self._complete_header(specname, "red")
            blue_header = self._complete_header(specname, "blue")
            daq.set_fits_headers(red_header, blue_header)

        logging.info("%d : Daq ready." % (self.icc.exposure.ID))

        # Clock the ccds
        logging.info("%d : Clocking the CCDs." % (self.icc.exposure.ID))
        # Send the full readout proc to each camera
        for spec in self.icc.exposure.cams:
            camforth = self.icc.controllers[spec]
            d = camforth.executeProc("full_" + spec[:3], self.cmd).addErrback(
                self.readoutFailed, spec
            )
            dl.append(d)
            dl.append(
                camforth.sendCommand(freadCmd, self.cmd).addErrback(
                    self.readoutFailed, spec
                )
            )

        # Arm the daq
        # self.icc.exposure.setState("READING", 65.0, 65.0)
        self.icc.exposure.setState(
            "READING", self.estimatedReadTime, self.estimatedReadTime
        )
        self.cmd.inform('text="Arming the daq..."')
        logging.info("%d : Arming the daq..." % (self.icc.exposure.ID))

        self.failedReadouts = []
        for spec in self.icc.exposure.daqs:
            daq = self.icc.controllers[spec]

            if daq.testing:
                logging.info("%d : Arming with a fill ramp." % (self.icc.exposure.ID))
                d = daq.arm(mode="fill ramp", cmd=self.cmd)
            else:
                d = daq.arm(cmd=self.cmd)
            # Append the receiving thread to a list to be waited on
            dl.append(d)
            d.addErrback(self.armFailed)

        logging.info("%d : Daq armed." % (self.icc.exposure.ID))

        self.cmd.inform('text="Reading out..."')
        logging.info("%d : Waiting for readout to complete." % (self.icc.exposure.ID))

        # Schedule a timer to check to make sure the exposure finished
        reactor.callLater(120, self._readoutTimeout, self.icc.exposure.ID)

        # Defer the finishing of the exposure
        if len(dl) > 0:
            DeferredList(dl).addCallback(self._finishReadout)
        else:
            reactor.callLater(0, self._finishReadout, None)

    def armFailed(self, x, spec):
        self.cmd.error(
            "text=%s" % (qstr("Arm or readout failed for %s: %s" % (spec, x)))
        )
        self.failedReadouts.append(spec)
        if len(self.failedReadouts) == len(self.icc.exposure.daqs):
            self.cmd.error('text="Readout failed, aborting exposure."')
            self.abort()  # ??? Really?

    def _readoutTimeout(self, expID):
        if self.icc.exposure.ID == expID and self.icc.exposure.state == "READING":
            self.needsRecovery = True
            # Reading has taken too long, abort the exposure
            self.cmd.error('text="Readout timeout expired, aborting exposure."')
            self.abort()

    def _finishReadout(self, data):
        if self.icc.exposure.state == "ABORTED":
            self.cmd.fail('text="Aborting exposure..."')
            return
        # Get the error information from the DAQ
        for dev in self.icc.exposure.daqs:
            daq = self.icc.controllers[dev]
            errors = daq.interface.camdaq_error_status()
            expID = errors["EXPID"]
            errCnt = errors["ERRCNT"]
            sErr = errors["SYNCERR"]
            pErr = errors["PIXERR"]
            pfErr = errors["PFERR"]
            response = "%sReadoutErrors=%s,%s,%s,%s,%s" % (
                dev[0:3].upper(),
                expID,
                errCnt,
                sErr,
                pErr,
                pfErr,
            )
            if errCnt > 0:
                self.cmd.warn(response)
            else:
                self.cmd.respond(response)

        # Send the set exposure OFF commands
        for spec in self.icc.exposure.daqs:
            daq = self.icc.controllers[spec]
            daq.interface.sendCommand("SET EXPOSURE OFF")
            reactor.callLater(0, daq.interface.getCommandResponse)

        self.cmd.inform(
            'text="Readout complete."; exposureId=%d' % (self.icc.exposure.ID)
        )
        logging.info("%d : Readout complete." % (self.icc.exposure.ID))

        # This is the end, close up shop
        logging.info("%d : Exposure complete." % (self.icc.exposure.ID))
        self.releaseExposure(doFinish=False)
        if self.failedReadouts:
            self.cmd.fail('text="readout for %s failed!!!!!"' % (self.failedReadouts))
        else:
            self.cmd.finish()

    def releaseExposure(self, doFinish=True):
        self.icc.exposure.timer = None
        self.icc.exposure.setState("IDLE", 0.0, 0.0)
        if self.failedReadouts or self.icc.exposure.needsRecovery:
            self.cmd.error(
                'text="!!!!!!!!! exposure needs recovery: '
                'NOT cleaning up exposureDelegate."'
            )
        else:
            self.icc.exposure.semaphore.release()
            self.command.exposureDelegate = None

        if doFinish:
            self.cmd.finish()

    def readoutFailed(self, reason, camera):
        self.cmd.error('text="Readout failed on camera %s. "' % (camera))
        self.icc.exposure.needsRecovery = True
        # self._removeSpec(camera[:3])

    # Card handlers
    def _makeCard(self, name, value, comment=""):
        try:
            return (name, value, comment)
        except:
            errStr = "failed to make %s card from %s" % (name, value)
            self.cmd.warn("text=%s" % (qstr(errStr)))
            return ("comment", errStr, "")

    def _camCards(self, specname):
        if len(specname) > 3:
            specname = specname[:3]
        self.cmd.diag('text="stuffing %s camera headers"' % (specname))

        cams = (specname + "red", specname + "blue")

        # A bit indirect, but use the actor dictionary to get some values
        # The names are enough of a wreck that I don't bother to factor things out.
        cardKeys = {
            "sp1red": {
                "LN2TEMP": "SP1R0LN2TempRead",
                "CCDTEMP": "SP1R0CCDTempRead",
                "IONPUMP": "SP1RedIonPump",
            },
            "sp1blue": {
                "LN2TEMP": "SP1B2LN2TempRead",
                "CCDTEMP": "SP1B2CCDTempRead",
                "IONPUMP": "SP1BlueIonPump",
            },
            "sp2red": {
                "LN2TEMP": "SP2R0LN2TempRead",
                "CCDTEMP": "SP2R0CCDTempRead",
                "IONPUMP": "SP2RedIonPump",
            },
            "sp2blue": {
                "LN2TEMP": "SP2B2LN2TempRead",
                "CCDTEMP": "SP2B2CCDTempRead",
                "IONPUMP": "SP2BlueIonPump",
            },
        }

        bossModel = self.icc.models["boss"].keyVarDict
        for camName in cams:
            camCards = cardKeys[camName]
            for cardName, keyName in camCards.items():
                card = actorFits.makeCardFromKey(
                    self.cmd, bossModel, keyName, cardName, cnv=float, idx=0
                )
                self.icc.exposure.headers[camName].append(card)

    def _chernoCards(self, specname):
        """Adds cherno cards."""

        default_offset = self.icc.models["cherno"].keyVarDict["default_offset"]
        offset = self.icc.models["cherno"].keyVarDict["offset"]
        astrometry_fit = self.icc.models["cherno"].keyVarDict["astrometry_fit"]

        if len(specname) > 3:
            specname = specname[:3]

        self.cmd.diag('text="stuffing %s camera headers"' % (specname))

        cams = (specname + "red", specname + "blue")

        for idx, name in enumerate(["RA", "DEC", "PA"]):
            default_ax = default_offset[idx]
            offset_ax = offset[idx]
            if (
                default_ax is None
                or offset_ax is None
                or float(default_ax) == -999.0
                or float(offset_ax) == -999.0
            ):
                full_offset = -999.0
            else:
                full_offset = float(default_ax) + float(offset_ax)

            for camName in cams:
                self.icc.exposure.headers[camName].append(
                    ("OFF" + name, full_offset, "Guider offset in " + name)
                )
        if astrometry_fit is not None and astrometry_fit[4] is not None:
            seeing = float(astrometry_fit[4])
        else:
            seeing = "?"

        for camName in cams:
            self.icc.exposure.headers[camName].append(
                ("SEEING", seeing, "Seeing from the guider [arcsec]")
            )

    def _mechCards(self, specname):
        if len(specname) > 3:
            specname = specname[:3]
        self.cmd.diag('text="stuffing %s mech headers"' % (specname))
        cards = []
        mech = self.icc.controllers.get(specname + "mech", None)
        if not mech:
            self.cmd.warn(
                'text="%s is not available -- no mech headers will be generated"'
                % (specname + "mech")
            )
            return

        status = mech.cachedStatus
        collpos = status.get("motorPos", [-9999999, -9999999, -9999999])
        for i, m in enumerate(["A", "B", "C"]):
            cards.append(
                self._makeCard(
                    "COLL" + m,
                    collpos[i],
                    "The position of the %s collimator motor" % (m),
                )
            )

        # We are trusting the exposure commands to do the right thing with the screens.
        # But we do not command the controller for non-shuttered exposures.
        if self.icc.exposure.flavor in ("bias", "dark"):
            hartmann = b", ".join(status.get("Hartmann", [b"Unknown"])).decode()
        else:
            hartmann = (
                "Out"
                if not self.icc.exposure.hartmann
                else self.icc.exposure.hartmann.capitalize()
            )
        cards.append(self._makeCard("HARTMANN", hartmann, "Hartmanns: Left,Right,Out"))

        # Shutter open & close times come at the end of the exposure. Grab the rest now.
        mechname = "MC" + specname[-1]
        statCards = (
            ("HumidHartmann", "HUMHT", -999.9, "Hartmann humidity, %"),
            ("HumidCenOptics", "HUMCO", -999.9, "Central optics humidity, %"),
            ("TempMedian", "TEMDN", -999.9, "Median temp, C"),
            ("TempHartmannTop", "THT", -999.9, "Hartmann Top Temp, C"),
            ("TempRedCamBot", "TRCB", -999.9, "Red Cam Bottom Temp, C"),
            ("TempRedCamTop", "TRCT", -999.9, "Red Cam Top Temp, C"),
            ("TempBlueCamBot", "TBCB", -999.9, "Blue Cam Bottom Temp, C"),
            ("TempBlueCamTop", "TBCT", -999.9, "Blue Cam Top Temp, C"),
        )
        for statName, cardName, defaultValue, comment in statCards:
            cardName = mechname + cardName
            val = status.get(statName, defaultValue)
            cards.append(
                self._makeCard(cardName, val, "%s mech %s" % (specname, comment))
            )

        self.icc.exposure.headers[specname].extend(cards)

        sharedCards = []
        slitID = status.get("SlitID", 0)
        if specname == "sp1":
            slitID = max(slitID - 32, 0)
        sharedCards.append(
            self._makeCard(
                "SLITID%s" % (specname[-1]),
                slitID,
                "Normalized slithead ID. sp1&2 should match.",
            )
        )
        self.icc.exposure.headers["shared"].extend(sharedCards)

    # def grabGuiderFrameName(self, cardName, comment):
    #     guiderModel = self.icc.models["guider"].keyVarDict
    #     card = actorFits.makeCardFromKey(
    #         self.cmd, guiderModel, "file", cardName, cnv=str, idx=1, comment=comment
    #     )
    #     return card

    def _expstart_fits_cards(self):
        self.icc.exposure.headers["shared"].append(
            ["FLAVOR", self.icc.exposure.flavor, "exposure type, SDSS spectro style"]
        )

        cards = []

        models = self.icc.models
        cards.extend(self._timeCards())
        cards.extend(actorFits.fpsCards(models, cmd=self.cmd))
        cards.extend(actorFits.tccCards(models, cmd=self.cmd))
        cards.extend(actorFits.apoCards(models, cmd=self.cmd))
        cards.extend(actorFits.mcpCards(models, cmd=self.cmd))

        if "test" in self.cmd.cmd.keywords:
            cards.append(["QUALITY", "test", "This is a test/engineering exposure"])
        self.icc.exposure.headers["shared"].extend(cards)

        # Fetch the mechanicals state for the integration.
        for spec in self.icc.exposure.mechs:
            self._mechCards(spec)

        # Fetch the camera state for the integration.
        for spec in self.icc.exposure.cams:
            self._camCards(spec)

        self._chernoCards(spec)

    def _timeCards(self):
        # This is wrong -- we need to unify the Filename login in
        # DAQInterface and this. Creating a shared Filename object which
        # freezes the state is probably the right thing to do.

        cards = []

        now = time.gmtime()
        mjd = astroMJD.mjdFromPyTuple(now)
        tai = mjd * 24 * 3600
        fmjd = int(mjd + 0.3)
        cards.append(self._makeCard("MJD", fmjd, "APO fMJD day at start of exposure"))
        cards.append(
            self._makeCard("TAI-BEG", tai, "MJD(TAI) seconds at start of integration")
        )

        humanDate = time.strftime("%Y-%m-%dT%H:%M:%S")
        cards.append(
            self._makeCard("DATE-OBS", humanDate, "TAI date at start of integration")
        )

        return cards

    def _expend_fits_cards(self, spec):
        """Seperate red&blue exposure are broken here."""

        specname = spec[:3]
        mech = self.icc.controllers.get(specname + "mech", None)
        if not mech:
            return
        status = mech.cachedStatus

        # We have to guess at the time between the DAQ aam() and the FREAD starting.
        darkTime = time.time() - self.icc.exposure.darkStart + 3.75
        self.icc.exposure.headers[spec].append(
            self._makeCard(
                "REQTIME", self.icc.exposure.itime, "requested exposure time"
            )
        )
        if self.icc.exposure.flavor not in ("bias", "dark"):
            self.icc.exposure.headers[spec].append(
                self._makeCard(
                    "EXPTIME",
                    self.icc.exposure.actualItime[spec],
                    "measured exposure time, s",
                )
            )
            self.icc.exposure.headers[spec].append(
                self._makeCard(
                    "SHOPETIM",
                    status.get("ShutterOpenTransit", 0.0),
                    "open shutter transit time, s",
                )
            )
            self.icc.exposure.headers[spec].append(
                self._makeCard(
                    "SHCLOTIM",
                    status.get("ShutterCloseTransit", 0.0),
                    "close shutter transit time, s",
                )
            )
        else:
            self.icc.exposure.headers[spec].append(
                self._makeCard(
                    "EXPTIME", self.icc.exposure.itime, "requested exposure time"
                )
            )
        self.icc.exposure.headers[spec].append(
            self._makeCard(
                "DARKTIME", darkTime, "time between flush end and readout start"
            )
        )

        # self.icc.exposure.headers["shared"].append(
        #     self.grabGuiderFrameName("GUIDERN", "The last guider image")
        # )

    def _complete_header(self, spec, color):
        """Generate a complete header for a single (sp1,sp2), (r,b) camera."""

        cards = list(self.icc.exposure.headers["shared"])
        cards.extend(self.icc.exposure.headers[spec])
        cards.extend(self.icc.exposure.headers[color])
        cards.extend(self.icc.exposure.headers[spec + color])

        logging.info(
            "cards for %s,%s,%s,%s: %s" % ("shared", spec, color, spec + color, cards)
        )
        return cards

    # Convenience Methods
    def _removeSpec(self, sp):
        newCams = []
        newMechs = []
        newDaqs = []
        for cam in self.icc.exposure.cams:
            if not cam.startswith(sp):
                newCams.append(cam)
        for mech in self.icc.exposure.mechs:
            if not mech.startswith(sp):
                newMechs.append(mech)
        for daq in self.icc.exposure.daqs:
            if not daq.startswith(sp):
                newDaqs.append(daq)
        self.icc.exposure.cams = newCams
        self.icc.exposure.mechs = newMechs
        self.icc.exposure.daqs = newDaqs


class ExposureCmd(object):
    def __init__(self, icc):
        self.icc = icc

        self.keys = keys.KeysDictionary(
            "boss_exposure",
            (1, 1),
            keys.Key(
                "itime",
                types.Float() * (1, 2),
                help="the exposure time(s) for the (red,blue) cameras",
            ),
            keys.Key(
                "flushproc",
                types.String(),
                help="CamProcedure to use when flushing",
            ),
            keys.Key(
                "fullproc",
                types.String(),
                help="CamProcedure to use when reading",
            ),
            keys.Key(
                "comment",
                types.String(),
                help="comment for the exposure",
            ),
            keys.Key(
                "cams",
                types.Enum("sp1cam", "sp2cam"),
                help="list of cameras (sp1cam,sp2cam) to use",
            ),
            keys.Key(
                "hartmann",
                types.Enum("left", "right"),
                help="type of hartmann exposure to take.",
            ),
            keys.Key(
                "window",
                types.Int() * 2,
                help="y0,y1 readout window",
            ),
        )
        self.vocab = (
            (
                "exposure",
                "@(bias) [<itime>] [<cams>] [<comment>] [<flushproc>] [<fullproc>] "
                "[test] [<window>] [noflush] [testFail]",
                self.exposure,
            ),
            (
                "exposure",
                "@(dark|arc|flat|science) <itime> [<cams>] [<comment>] [<flushproc>] "
                "[<fullproc>] [<hartmann>] [test] [<window>] [noflush] [noreadout]",
                self.exposure,
            ),
            (
                "exposure",
                "@(pause|resume|stop|abort|readout|status|clear|recover)",
                self.exposure,
            ),
            (
                "clearExposure",
                "",
                self.clearExposure,
            ),
            (
                "testCards",
                "",
                self.testCards,
            ),
        )

        self.exposureDelegate = None

    def exposure(self, cmd):
        """
        Either create an exposure or modify the current exposure.
        """
        # Parse and validate the arguments

        flavor = cmd.cmd.keywords[0].name
        assert flavor in (
            "bias",
            "dark",
            "arc",
            "flat",
            "science",
            "pause",
            "resume",
            "stop",
            "abort",
            "readout",
            "adjust",
            "extend",
            "status",
            "clear",
            "recover",
        )

        # Switch over the flavor and check the state to see if the transition is valid
        if flavor in ("dark", "arc", "flat", "science", "bias"):
            if self.exposureDelegate:
                cmd.fail(
                    "text=\"exposure already in progress! Do a 'boss clearExposure' if "
                    'you want to kill and or clear it."'
                )
                return

            exposureDelegate = ExposureDelegate([], cmd, self.icc)
            exposureDelegate.command = self
            exposureDelegate.start()
        elif self.exposureDelegate is None:
            # Exposure hasn't been started, refuse all other commands
            cmd.fail('text="No exposure to act on."')
            return
        elif flavor == "pause":
            self.exposureDelegate.pause(cmd)
        elif flavor == "resume":
            self.exposureDelegate.resume(cmd)
        elif flavor == "stop":
            self.exposureDelegate.stop(cmd=cmd)
        elif flavor == "abort":
            self.exposureDelegate.abort(cmd=cmd)
        elif flavor == "readout":
            self.exposureDelegate.readout(cmd)
        elif flavor == "extend":
            self.exposureDelegate.extend()
        elif flavor == "status":
            self.exposureDelegate.status()
        elif flavor == "clear":
            self.exposureDelegate.clear()
        elif flavor == "recover":
            self.exposureDelegate.recover(cmd)
        else:
            cmd.fail("text='unknown exposure command: %s'" % (cmd.cmd))

    def testCards(self, cmd):
        """Check the fits header output, comming from several different header cards."""
        cards = {}
        cards["apo"] = actorFits.apoCards(self.icc.models, cmd=cmd)
        cards["mcp"] = actorFits.mcpCards(self.icc.models, cmd=cmd)
        cards["tcc"] = actorFits.tccCards(self.icc.models, cmd=cmd)
        cards["fps"] = actorFits.fpsCards(self.icc.models, cmd=cmd)

        for actor in cards:
            text = "would add %s " % actor
            for c in cards[actor]:
                cmd.warn('text="' + text + 'card %s,%s,%s"' % c)

        cmd.finish()

    def clearExposure(self, cmd, doFinish=True):
        """
        Clear the currently active exposure. LOSES ALL DATA!
        WARNING: This will cause loss of all data related to this exposure!
        """
        if self.exposureDelegate:
            self.exposureDelegate.clear()
            self.exposureDelegate = None

        if self.icc.exposure.cmd != self.icc.bcast and self.icc.exposure.cmd.alive:
            self.icc.exposure.cmd.fail('text="cleared active exposure....')
        self.icc.exposure.needsRecovery = False
        self.icc.exposure.cmd = self.icc.bcast
        self.icc.exposure.setState("IDLE", 0.0, 0.0)
        self.icc.exposure.semaphore.release()
        if doFinish:
            cmd.finish("")
