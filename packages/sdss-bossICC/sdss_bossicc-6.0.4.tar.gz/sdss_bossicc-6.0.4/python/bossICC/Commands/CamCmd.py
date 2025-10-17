#!/usr/bin/env python

""" CamCmd.py -- wrap raw cam micro functions. """

from twisted.internet.defer import DeferredList

import opscore.protocols.keys as keys
import opscore.protocols.types as types
from opscore.utility.qstr import qstr

from bossICC.Commands.BaseDelegate import BaseDelegate


class IACKDelegate(BaseDelegate):
    def _individualIACKComplete(self, result, cmd, spec):
        cmd.respond('text="%s iacked."' % spec)

    def _finishIACK(self, result, cmd):
        if self.success:
            cmd.finish('text="iack(s) done"')
        else:
            cmd.fail('text="IACK failed."')

    def _failedIACK(self, result, cmd, spec):
        cmd.warn('text = "Failed to iack %s"' % spec)
        self.success = False


class RAWDelegate(BaseDelegate):
    def _tdsResponse(self, result, cmd, cam, cmd_txt):
        for ll in result:
            cmd.respond('%sRawText="%s"' % (cam, ll))
        cmd.finish()

    def _tdsResponseFail(self, result, cmd, cam, cmd_txt):
        error = result.getErrorMessage()
        msg = qstr(f"failure while running {cmd_txt} on {cam}: {error}")
        cmd.fail(f"text={msg}")


class COLDDelegate(BaseDelegate):
    def individualComplete(self, result, cam):
        self.cmd.respond('text = "Cold complete on %s."' % (cam))

    def complete(self, result):
        if self.success:
            self.cmd.finish(
                'text = "Colds complete on complete on %s."' % (self.controllers)
            )
        else:
            self.cmd.fail('text="Failed to do both colds."')

    def failed(self, result, cam):
        self.cmd.warn('text="Failed to COLD %s."' % cam)
        self.success = False


class CamCheckDelegate(BaseDelegate):
    def init(self):
        self.errors = []
        self.reached_volts = False
        self.errorValues = []

        connectedCams, allCams = self.icc.getDevLists("cam$")
        missing = allCams - connectedCams
        if missing:
            self.warnAboutMissingCams(missing)

    def warnAboutMissingCams(self, missingCams):
        self.cmd.warn(
            'text="camcheck found missing or unresponsive cameras: %s"' % (missingCams)
        )
        for cam in missingCams:
            self.errors.append(cam[0:3].upper() + "MicroNotTalking")
        self.success = False

    def individualComplete(self, results):
        errors, errorValues = results
        self.errors += errors
        self.errorValues += errorValues

    def genKeys(self):
        if self.errors:
            self.cmd.warn("; ".join(self.errorValues))
            self.cmd.warn("camCheck=" + ",".join(self.errors))
        else:
            self.cmd.inform("camCheck")

    def complete(self, result):
        self.genKeys()
        if self.success:
            self.cmd.finish("")
        else:
            self.cmd.fail('text="Failed to CAMCHECK both instruments."')

    def failed(self, result, cam):
        """Failure callback _for a single instrument.__. .complete() will be called in
        any case.
        """

        result.trap(Exception)
        self.cmd.warn('text="Failed to CAMCHECK %s, result: %s"' % (cam, result))
        self.warnAboutMissingCams([cam])


class StatDelegate(BaseDelegate):
    def __init__(self, camNames, cmd, icc, statType):
        BaseDelegate.__init__(self, camNames, cmd, icc)
        self.statType = statType

    def init(self):
        self.keys = []

    def individualComplete(self, results, cam):
        self.keys += results

    def complete(self, result):
        if len(self.keys) > 0:
            self.cmd.respond("; ".join(self.keys))
        else:
            self.cmd.inform(self.statType)
        if self.success:
            self.cmd.finish("")
        else:
            self.cmd.fail('text="Failed to %s both instruments."' % (self.statType))

    def failed(self, result, cam):
        self.cmd.warn(
            'text="Failed to %s %s, result: %s"' % (cam, self.statType, result)
        )
        self.success = False


class CamStatDelegate(BaseDelegate):
    def init(self):
        self.response = ""

    def individualComplete(self, results, cam):
        self.response += results

    def complete(self, result):
        if len(self.response) > 0:
            self.cmd.respond(self.response)
        else:
            self.cmd.inform("ln2Stat")
        if self.success:
            self.cmd.finish("")
        else:
            self.cmd.fail('text="Failed to camstat both instruments."')

    def failed(self, result, cam):
        self.cmd.warn('text="Failed to camstat %s, result: %s"' % (cam, result))
        self.success = False


class VoltsDelegate(BaseDelegate):
    def init(self):
        self.keys = []
        self.check = "READ"

    def individualComplete(self, results, cam):
        self.keys += results

    def complete(self, results):
        if len(self.keys) > 0:
            keysLeft = self.keys[:]
            for cam in (
                "SP1R0",
                "SP1R1",
                "SP1R",
                "SP1B2",
                "SP1B3",
                "SP1B",
                "SP2R0",
                "SP2R1",
                "SP2R",
                "SP2B2",
                "SP2B3",
                "SP2B",
            ):
                camParts = [k for k in keysLeft if k.startswith(cam)]
                if camParts:
                    self.cmd.diag("; ".join(camParts))
                for k in camParts:
                    keysLeft.remove(k)

            self.cmd.diag("; ".join(keysLeft))
        else:
            self.cmd.diag("")
        if self.success:
            self.cmd.finish("")
        else:
            self.cmd.fail('text="Failed to read volts on both cameras."')

    def failed(self, result, cam):
        self.cmd.warn('text="SHOW%sVOLTS failed on %s, %s"' % (self.check, cam, result))


class ProcedureDelegate(BaseDelegate):
    def init(self):
        self.procedure = None

    def individualComplete(self, results, cam):
        self.cmd.respond('text="%s finished on %s"' % (self.procedure, cam))

    def complete(self, results):
        if self.success:
            self.cmd.finish("")
        else:
            self.cmd.fail('text="Failed to execute script on both cameras."')

    def failed(self, result, cam):
        self.cmd.warn('text="%s failed on %s"' % (self.procedure, cam))
        self.success = False


class PhaseWaitDelegate(BaseDelegate):
    def init(self):
        self.procedure = None

    def individualComplete(self, results, cam):
        self.cmd.respond('text="PhaseMicro ready on %s"' % (cam))

    def complete(self, results):
        if self.success:
            self.cmd.finish("")
        else:
            self.cmd.fail('text="Failed wait for phase micros."')

    def failed(self, result, cam):
        self.cmd.warn(
            'text="Timeout waiting on phase micro for %s: %s"' % (cam, result.value)
        )


class CamCmd(object):
    """Wrap spXcam functions."""

    def __init__(self, icc):
        self.icc = icc

        self.keys = keys.KeysDictionary(
            "boss_cam",
            (1, 1),
            keys.Key(
                "cams",
                types.Enum("sp1cam", "sp2cam"),
                help="list of cameras (sp1cam,sp2cam) to use",
            ),
            keys.Key("proc", types.String(), help="a procedure to run"),
            keys.Key("path", types.String(), help="the filename of a procedure to run"),
        )
        self.vocab = (
            ("sp1cam", "@raw", self.sp1cam_cmd),
            ("sp2cam", "@raw", self.sp2cam_cmd),
            ("camProcedure", "[<cams>] [<proc>] [<path>]", self.cam_procedure),
            ("camCheck", "", self.camcheck),
            ("camStat", "", self.camstat),
            ("camRead", "", self.camread),
            ("camBias", "", self.cambias),
            ("camNom", "", self.camnom),
            ("ln2stat", "", self.ln2stat),
            ("specstat", "", self.specstat),
            ("coldReboot", "[force] [<cams>]", self.coldReboot),
            ("iack", "[<cams>]", self.iack),
            ("ackErrors", "[<cams>]", self.ackErrors),
            ("phaseWait", "[<cams>]", self.phaseWait),
        )

    def getCamList(self, cmd):
        if "cams" in cmd.cmd.keywords:
            cams = cmd.cmd.keywords["cams"].values
        else:
            cams = []
            for device in list(self.icc.controllers.keys()):
                if device.endswith("cam"):
                    cams.append(device)
        return cams

    def iack(self, cmd):
        """Initialize the camera controllers, including setting appropriate
        temperatures, voltages, etc.
        """

        camNames = self.getCamList(cmd)
        dl = []
        delegate = IACKDelegate(camNames, cmd, self.icc)
        for camName in camNames:
            cam = self.icc.controllers[camName]
            specname = camName[:3].lower()
            cmd.respond(
                'text="Performing iack initialization of %s (%s)."'
                % (specname, camName)
            )
            d = cam.iack(cmd=cmd)
            d.addCallback(delegate._individualIACKComplete, cmd, camName)
            d.addErrback(delegate._failedIACK, cmd, camName)
            dl.append(d)
        dl = DeferredList(dl, fireOnOneErrback=True).addCallback(
            delegate._finishIACK, cmd
        )
        return dl

    def ackErrors(self, cmd):
        """Clear sticky and latched BOSS errors on one or both spectrographs."""

        camNames = self.getCamList(cmd)
        dl = []
        for camName in camNames:
            cam = self.icc.controllers[camName]
            ack = cam.ackErrors(cmd, clearLatched=True)
            dl.append(ack)
        dl = DeferredList(dl).addCallback(self.camcheck, cmd)
        return dl

    def coldReboot(self, cmd):
        """WARNING: Performs a cold reboot of the camera controllers.

        WARNING: you must issue 'boss iack' after this to get the controllers
        into the correct state.

        """

        camNames = self.getCamList(cmd)
        force = "force" in cmd.cmd.keywords
        if not force:
            cams_str = ",".join(camNames)
            cmd.fail(
                'text="coldReboot will only reboot BOSS cameras if you '
                f"specify 'force'. Would have rebooted {cams_str}."
            )
            return

        dl = []
        delegate = COLDDelegate(camNames, cmd, self.icc)
        for camName in camNames:
            cam = self.icc.controllers[camName]
            specname = camName[:3].lower()
            cmd.warn('text="Performing cold reboot of %s (%s)."' % (specname, camName))
            cold = cam.sendCommand("COLD", cmd, timeout=4)
            cold.addCallback(delegate.individualComplete, cam).addErrback(
                delegate.failed, cam, camName
            )
            dl.append(cold)
        dl = DeferredList(dl).addCallback(delegate.complete)

    def camcheck(self, cmd):
        """Performs the CAMCHECK command on both of the camForths and
        reports the keywords to the ICC.

        The CAMCHECK command queries the camera controllers for anything that is out of
        spec. This will return any voltages that are outside of the tolerances and will
        also report other conditions that need immediate attention.
        """

        # if self.icc.exposure and self.icc.exposure.state in ('FLUSHING', 'READING'):
        #    cmd.fail('text="I do not want to run CAMCHECK during a readout."')
        #    return

        camNames = self.getCamList(cmd)
        delegate = CamCheckDelegate(camNames, cmd, self.icc)
        dl = []
        for dev in camNames:
            cmd.diag('text="Performing camcheck on %s."' % (dev))
            cc = self.icc.controllers[dev].camcheck(cmd)
            cc.addCallback(delegate.individualComplete).addErrback(delegate.failed, dev)
            dl.append(cc)
        dl = DeferredList(dl, fireOnOneErrback=True).addCallback(delegate.complete)

    def ln2stat(self, cmd):
        """Performs the LN2STAT command on the camForths and reports the results.

        The LN2STAT commands the camForth to list information pertinent to the operation
        of the N2 dewars.
        """

        dl = []
        camNames = self.getCamList(cmd)
        delegate = StatDelegate(camNames, cmd, self.icc, "ln2stat")
        for dev in camNames:
            cam = self.icc.controllers[dev]
            d = (
                cam.ln2stat(cmd)
                .addCallback(delegate.individualComplete, dev)
                .addErrback(delegate.failed, dev)
            )
            dl.append(d)
        DeferredList(dl).addCallback(delegate.complete)

    def specstat(self, cmd):
        """Performs the SPEC2STAT command on the camForths and reports the results.

        The SPECSTAT commands the camForth to list information about the temperatures,
        ion pumps, and heater voltages.
        """

        dl = []
        camNames = self.getCamList(cmd)
        delegate = StatDelegate(camNames, cmd, self.icc, "specStat")
        for dev in camNames:
            cam = self.icc.controllers[dev]
            d = (
                cam.envstat(cmd)
                .addCallback(delegate.individualComplete, dev)
                .addErrback(delegate.failed, dev)
            )
            dl.append(d)
        DeferredList(dl).addCallback(delegate.complete)

    def camstat(self, cmd):
        """Performs the CAMSTAT command on the camForths and reports the results. The
        CAMSTAT command lists all pertinant status information of the camForth
        controllers.
        """

        camNames = self.getCamList(cmd)
        delegate = CamStatDelegate(camNames, cmd, self.icc)
        dl = []
        for dev in camNames:
            cam = self.icc.controllers[dev]
            cc = cam.camstat(cmd)
            cc.addCallback(delegate.individualComplete, dev).addErrback(
                delegate.failed, dev
            )
            dl.append(cc)
        dl = DeferredList(dl).addCallback(delegate.complete)
        return dl

    def camread(self, cmd, doFinish=True):
        """Performs CAMREADVOLTS on the camForths and reports the results converted from
        the 8-bit values to a float. CAMREADVOLTS lists all of the actually meausured
        volatges of the camera. The values read directly from the camera are in the form
        of an 8 bit integer, they must be then convertated into a floating point
        voltage.
        """

        self.camVolts(cmd, "READ")

    def cambias(self, cmd):
        """Performs CAMBIASVOLTS on the camForths and reports the results converted from
        the 8-bit values to a float. CAMBIASVOLTS lists all of the bias volatges of the
        camera. The values read directly from the camera are in the form of an 8 bit
        integer, they must be then convertated into a floating point voltage.
        """

        self.camVolts(cmd, "BIAS")

    def camnom(self, cmd):
        """Performs CAMNOMVOLTS on the camForths and reports the results converted from
        the 8-bit values to a float. CAMNOMVOLTS lists all of the nominal volatges of
        the camera. The values read directly from the camera are in the form of an 8 bit
        integer, they must be then convertated into a floating point voltage.
        """

        self.camVolts(cmd, "NOM")

    def camVolts(self, cmd, check):
        """Do the actual voltage query on the camForths. check is either 'READ', 'BIAS',
        or 'NOM'.
        """

        camNames = self.getCamList(cmd)
        dl = []
        delegate = VoltsDelegate(camNames, cmd, self.icc)
        delegate.check = check
        for cam in camNames:
            dev = self.icc.controllers[cam]
            d = (
                dev.voltsCheck(cmd, check)
                .addCallback(delegate.individualComplete, cam)
                .addErrback(delegate.failed, dev)
            )
            dl.append(d)
        DeferredList(dl).addCallback(delegate.complete)

    def get_voltages(self, check):
        """Return the voltages of a given type

        Returns:
           dict of tuples, where the dict is the camera name (sp1/2) and the
              tuples are converted (name, value) pairs.
        """

        vdict = {}
        for dev in list(self.icc.controllers.keys()):
            if dev.endswith("cam"):
                cam = self.icc.controllers[dev]
                device_name = dev[:3].upper()
                results = cam.send_command("SHOW%sVOLTS" % check)
                keys = []
                for line in results.split("\n"):
                    name, value = self._read_voltage_line(line)
                    if name:
                        keys.append("%s=%s" % (name, value))
                vdict[device_name.lower()] = keys

        return vdict

    def sp1cam_cmd(self, cmd):
        """Pass a raw command through to sp1cam."""
        self.tds_cmd("sp1cam", cmd)

    def sp2cam_cmd(self, cmd):
        """Pass a raw command through to sp2cam"""
        self.tds_cmd("sp2cam", cmd)

    def tds_cmd(self, cam, cmd):
        """Send a raw TDS command unmolested to the TDS micro."""

        # TDS commands might be horrible Forth junk with single double quotes, etc.,
        # so ignore any Command parsing.
        # Well, uppercase the commmand...

        cmd_txt = cmd.cmd.keywords["raw"].values[0]
        cmd_txt = cmd_txt.upper()
        cmd.respond('text="Sending raw command %s to %s"' % (cmd_txt, cam))
        delegate = RAWDelegate((cam,), cmd, self.icc)
        self.icc.controllers[cam].sendCommand(cmd_txt, cmd).addCallback(
            delegate._tdsResponse, cmd, cam, cmd_txt
        ).addErrback(delegate._tdsResponseFail, cmd, cam, cmd_txt)

    def cam_procedure(self, cmd):
        """Execute a list of commands on the camera controller.

        Examples of these files can be found in the CamProcedures directory of the boss
        ICC. These procedures contain the complicated list of commands that must be
        issued to the camera to execute a proper flush, blue read, or red read. A file
        path can also be passed to run custom procedures.
        """

        camNames = self.getCamList(cmd)
        dl = []
        delegate = ProcedureDelegate(camNames, cmd, self.icc)

        if "proc" in cmd.cmd.keywords:
            proc = cmd.cmd.keywords["proc"].values[0]
            delegate.procedure = proc
            for cam in camNames:
                cmd.diag('text="Performing %s read on %s."' % (proc, cam))
                d = (
                    self.icc.controllers[cam]
                    .executeProc(proc, cmd=cmd)
                    .addCallback(delegate.individualComplete, cam)
                    .addErrback(delegate.failed, cam)
                )
                dl.append(d)
        elif "path" in cmd.cmd.keywords:
            path = cmd.cmd.keywords["path"].values[0]
            delegate.procedure = path
            for cam in camNames:
                cmd.diag('text="Performing %s on %s."' % (path, cam))
                d = (
                    self.icc.controllers[cam]
                    ._executePath(path, cmd=cmd)
                    .addCallback(delegate.individualComplete, cam)
                    .addErrback(delegate.failed, cam)
                )
                dl.append(d)
        else:
            cmd.fail('text="Must specify a procedure file to execute."')
            return

        DeferredList(dl).addCallback(delegate.complete)

    def phaseWait(self, cmd):
        """Wait for the phase micro to become available and post a message
        when ready or timed out.
        """

        camNames = self.getCamList(cmd)
        dl = []
        delegate = PhaseWaitDelegate(camNames, cmd, self.icc)
        for cam in camNames:
            cmd.diag('text="Waiting on %s phase micro."' % cam)
            d = (
                self.icc.controllers[cam]
                .phaseWait(cmd)
                .addCallback(delegate.individualComplete, cam)
                .addErrback(delegate.failed, cam)
            )
            dl.append(d)
        DeferredList(dl).addCallback(delegate.complete)
