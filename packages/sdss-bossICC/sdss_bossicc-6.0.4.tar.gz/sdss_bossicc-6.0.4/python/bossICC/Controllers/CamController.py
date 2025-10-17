# flake8: noqa W605

import os
import re
import time

from twisted.internet import reactor
from twisted.internet.defer import Deferred

from opscore.utility.qstr import qstr

from bossICC import BOSSExceptions, CamForthTranslations

from . import BaseController, CamProtocol
from .BaseFactory import BaseFactory


# The replies from the protocol are always bytes but the data we send
# back to the command has already been decoded/evaluated. This is different
# from the mech in which we keep everything either evaluated or bytes.


class CamFactory(BaseFactory):
    protocol = CamProtocol.CamProtocol


class CamController(BaseController.BaseController):
    factory_class = CamFactory

    def init(self, cmd):
        self.latchedErrors = {}
        self.camcheck(cmd, report=True).addCallback(self._finishInit, cmd)

    def ping(self, cmd):
        return self.sendCommand("PING", cmd=cmd, timeout=3)

    def _finishInit(self, results, cmd):
        if not self.iacked:
            cmd.warn('text="Controller %s not iacked"' % self.name)
            return
        cmd.respond('text="Controller %s iacked and ready."' % self.name)

    def _camCheckAfterIack(self, data, cmd):
        # I can't figure out how to chain this so that the cmd
        # does not finish/fail before the camcheck is done.
        self.camcheck(self.icc.bcast, report=True)

    def iack(self, cmd=None):
        if not cmd:
            cmd = self.icc.bcast
        cmd.respond('text="IACKing %s"' % self.name)
        return self.executeProc("iack_" + self.name[:3], cmd=cmd).addCallback(
            self._iackComplete, cmd
        )

    def _iackComplete(self, data, cmd):
        cmd.respond('text="IACK complete on %s."' % (self.name))
        reactor.callLater(0, self._camCheckAfterIack, None, cmd)

    def camcheck(self, cmd, report=False):
        """Perform camcheck, call callback with errors and errorvalues."""
        d = Deferred()
        self.sendCommand("CAMCHECK", cmd, timeout=5).addCallback(
            self._camcheckComplete, cmd, d, commandName="CAMCHECK", report=report
        ).addErrback(self._camcheckFailed, cmd, d)
        return d

    def _fixupPhaseBoot(self, cmd, line):
        """Turn '? PHASEMICRO BUSY' into 'BUSY'"""

        keyword, value = line.split(None, 1)
        if value == "? PHASEMICRO BUSY":
            return "BUSY"
        else:
            cmd.warn(
                "text=%s"
                % (
                    qstr(
                        "unexpected value for the CAMSTAT PHASE_BOOT keyword: %s"
                        % (value)
                    )
                )
            )
            return qstr(value)

    def _camcheckComplete(self, results, cmd, d, commandName="UNKNOWN", report=False):
        errors = []
        errorValues = []
        cam = self.name
        cmd.respond('text="Parsing %s from %s"' % (commandName, self.name))
        iacked = True
        clearableErrors = []
        for line in results:
            tokens = line.split()
            if b"UNACKNOWLEDGED" in line:
                if iacked:
                    cmd.warn(
                        'text="Camcheck discovered unacknowledged state for %s, '
                        'which will need to be iacked"' % (self.name)
                    )
                iacked = False
            if len(tokens) > 0:
                tk_uni = tokens[0].decode()
                if tk_uni in CamForthTranslations.keyword_translations:
                    # Do the translations
                    keyName = CamForthTranslations.keyword_translations[tk_uni]
                    keyword = "%s%s" % (cam[:3].upper(), keyName)
                    errors.append(keyword)
                    if len(tokens) > 1 and tokens[1][0:1] != b"#":
                        errorValues.append("%s=%s" % (keyword, tokens[1].decode()))
                    if keyName in (
                        "FillFault",
                        "LN2Empty",
                        "RedIonPump",
                        "BlueIonPump",
                    ):
                        clearableErrors.append(keyName)
                        latchedName = keyword + "Latched"
                        if latchedName not in self.latchedErrors:
                            self.latchedErrors[latchedName] = time.time()
                            cmd.warn(
                                'text="first noticed clearable error (%s) on %s (%s)"'
                                % (keyName, cam[:3], clearableErrors)
                            )
                else:
                    keyword, value = self._readVoltageLine(line, cmd)
                    if keyword and value:
                        errors.append("%s" % keyword)
                        errorValues.append("%s=%s" % (keyword, value))
                    elif keyword != "":
                        # keyword == "" signals lines to silently ignore.
                        cmd.warn(
                            'text="Failed to parse or convert camcheck '
                            'line as a voltage: %s"' % (line)
                        )

        self.iacked = iacked

        for latchedName, latchedError in list(self.latchedErrors.items()):
            errors.append(latchedName)
            errorValues.append("%s=%s" % (latchedName, latchedError))

        cmd.respond('text="Parsed CAMCHECK on %s"' % self.name)
        if report:
            if errorValues:
                cmd.warn("; ".join(errorValues))
            for err in errorValues:
                cmd.warn("camCheckAlert=" + (",".join(err.split("="))))

            if errors:
                cmd.warn("camCheck=" + ",".join(errors))
            else:
                cmd.inform("camCheck=")
        if clearableErrors:
            reactor.callLater(0, self.ackErrors, self.icc.bcast)

        d.callback([errors, errorValues])

    def _camcheckFailed(self, results, cmd, d):
        results.trap(BOSSExceptions.TimeOutError, Exception)
        # d.errback(Exception("Failed on camcheck %s, %s" % (self.name,results)))
        cmd.warn('text="Failed on camcheck %s, %s"' % (self.name, results.__class__))
        d.errback(Exception("Failed on camcheck %s, %s" % (self.name, results)))
        return results

    def ackErrors(self, cmd, clearLatched=False):
        d = Deferred()
        cmd.warn(
            'text="Clearing %s errors on %s"'
            % ("sticky and latched" if clearLatched else "sticky", self.name)
        )
        self.sendCommand(
            "CLEAREMPTY CLEARFFAULT 0 REDIPERRCTR ! 0 BLUIPERRCTR !", cmd, timeout=4
        ).addCallback(self._ackErrorsComplete, cmd, d, clearLatched).addErrback(
            self._ackErrorsFailed, cmd, d
        )
        return d

    def _ackErrorsComplete(self, results, cmd, d, clearLatched):
        if clearLatched:
            self.latchedErrors = {}
            cmd.inform('text="Cleared sticky and latched errors on %s"' % (self.name))
        else:
            cmd.inform('text="Cleared sticky errors on %s"' % (self.name))

        d.callback(results)

    def _ackErrorsFailed(self, reason, cmd, d):
        cmd.warn('text="Failed to clear errors %s"' % reason)
        d.errback(reason)
        return reason

    def ln2stat(self, cmd):
        d = Deferred()
        self.sendCommand("LN2STAT", cmd, timeout=4).addCallback(
            self._ln2statComplete,
            cmd,
            d,
        ).addErrback(
            self._ln2statFailed,
            cmd,
            d,
        )
        return d

    def _ln2statComplete(self, results, cmd, d):
        keys = []
        clearableErrors = []
        for line in results:
            if len(line) == 0:
                continue
            try:
                tokens = line.split()
                keyword = tokens[0].decode()
                value = tokens[1].decode()
                if keyword in CamForthTranslations.keyword_translations:
                    response = "%s%s=%s" % (
                        self.name,
                        CamForthTranslations.keyword_translations[keyword],
                        value.split("_")[0],
                    )
                    keys.append(response)
                    if keyword in ("FillFault"):
                        clearableErrors.append(keyword)
                        latchedName = keyword + "Latched"
                        if latchedName not in self.latchedErrors:
                            self.latchedErrors[latchedName] = time.time()
                            cmd.warn(
                                'text="first noticed clearable error (%s) on (%s)"'
                                % (keyword, clearableErrors)
                            )
                    elif keyword in ("LN2Empty",):
                        pass
            except:
                # We should enumerate unknown strings rather than pass on them.
                pass

        if clearableErrors:
            reactor.callLater(0, self.ackErrors, self.icc.bcast)
        # But let camcheck actually _report_ the latched errors.

        d.callback(keys)

    def _ln2statFailed(self, reason, cmd, d):
        cmd.warn("Failed to call ln2stat: %s" % reason)
        d.errback(reason)

    def envstat(self, cmd):
        d = Deferred()
        self.sendCommand("SPECSTAT LN2STAT", cmd, timeout=4).addCallback(
            self._envstatComplete, cmd, d
        ).addErrback(self._envstatFailed, cmd, d)
        return d

    def _envstatComplete(self, results, cmd, d):
        """
        Parse the results of SPECSTAT and LN2STAT.
        results should look something like the following (exact values differ):

        2NDARY_DEWAR_PRESS    10  # PSI GAUGE
        RED_ION_PUMP_LOGP -6.86
        BLUE_ION_PUMP_LOGP -6.69

        SP1R0  LN2TEMP   91.4K
        CCD_TEMP:  DAC SET AT 153 =    0.98 V = -120 C  MEASURED  -119.6C
        HEATER_VOLTS     6.05 V

        SP1B2  LN2TEMP   89.8K
        CCD_TEMP:  DAC SET AT 127 =   -0.04 V = -100 C  MEASURED   -99.6C
        HEATER_VOLTS     8.06 V

        LN2_FILL      ON
        FILLTIME      120_MINUTES
        NEXT_FILL     118_MINUTES

        2NDARY_DEWAR_PRESS    10  # PSI GAUGE
        NORM_RETRIG   3
        FILL_MODE     COLD
        WARM_FILLTIME 15_MINUTES
        WARM_FILLS    2
        WARM_RETRIG   10
        FILLFAULT     NO
        EMPTY_TRIGGER NO
        AUTOFILL_ON 1 2
        LN2_EMPTY
         ok

        """
        keys = []

        cam = "X0"
        for line in results:
            line = line.strip().decode()
            # these are safe to ignore.
            # LN2_EMPTY with a value after it would be used later in the
            # keyword translations below.
            if line == "" or line == "ok" or line == "LN2_EMPTY":
                continue

            try:
                tokens = line.split()
                keyword = tokens[0]
                value = tokens[1]
                if value == "LN2TEMP":
                    m = re.search("^SP([12])([BR]).*", keyword)
                    # cmd.warn('text="ln2temp %s:%s:%s"' % (keyword,value,m))
                    if m:
                        cam = m.group(2) + m.group(1)
                elif keyword == "CCD_TEMP:":
                    m = re.search(
                        "CCD_TEMP:\s+DAC SET AT [^=]+=[^=]+=\s*([0-9-]+).*"
                        "MEASURED\s+([0-9-]+).*",
                        line,
                    )
                    cmd.warn(
                        'text="CCD_TEMP: %s %s"' % (cam, m.groups() if m else None)
                    )
                    if False and m:
                        keys.append("%s%s=%s" % (cam, "CCDTempSetpoint", m.groups(1)))
                        keys.append("%s%s=%s" % (cam, "CCDTemp", m.groups(2)))
                elif keyword in CamForthTranslations.keyword_translations:
                    response = "%s%s=%s" % (
                        self.name,
                        CamForthTranslations.keyword_translations[keyword],
                        value.split("_")[0],
                    )
                    keys.append(response)
            except Exception as e:
                cmd.warn('text="failed to handle micro output: %s (%s)"' % (line, e))

        d.callback(keys)

    def _envstatFailed(self, reason, cmd, d):
        cmd.warn("Failed to call specstat: %s" % reason)
        d.errback(reason)

    def camstat(self, cmd):
        d = Deferred()
        self.sendCommand("CAMSTAT", cmd, timeout=4).addCallback(
            self._camstatComplete, cmd, d
        ).addErrback(self._camstatFailed, cmd, d)
        return d

    def _camstatComplete(self, results, cmd, d):
        cmd.respond('text="Performing camstat on %s."' % (self.name))
        response = ""
        for line in results:
            if len(line) > 0:
                line = line.decode()
                try:
                    keyword, value = line.split()[:2]
                    if value.count("=") > 0:
                        value = value.split("=")[-1]
                    if keyword == "PHASE_BOOT" and value == "?":
                        value = self._fixupPhaseBoot(cmd, line)
                    response += "%s%s=%s;" % (
                        self.name[:3].upper(),
                        CamForthTranslations.keyword_translations[keyword],
                        value,
                    )
                except:
                    pass
        d.callback(response)

    def _camstatFailed(self, reason, cmd, d):
        d.errback(reason)

    def showReadVolts(self, cmd):
        return self.voltsCheck(cmd, "READ")

    def showBiasVolts(self, cmd):
        return self.voltsCheck(cmd, "BIAS")

    def showNomVolts(self, cmd):
        return self.voltsCheck(cmd, "NOM")

    def voltsCheck(self, cmd, check):
        d = Deferred()
        self.sendCommand("SHOW%sVOLTS" % check, cmd).addCallback(
            self._voltsCheck, cmd, check, d
        ).addErrback(d.errback)
        return d

    def _voltsCheck(self, results, cmd, check, d):
        keys = []
        for line in results:
            name, value = self._readVoltageLine(line, cmd)
            if name:
                keys.append("%s=%s" % (name, value))
        d.callback(keys)

    def _readVoltageLine(self, line, cmd):
        """Parse a "voltage" line, from camcheck or showXvolts.

        Args:
             line   - one of several forms of micro output. Sorry.

        Returns:
           name, val

           where:
            name = "" if the line should be ignored
            name = None if the line is in error
            name is otherwise translated per CamForthVoltages

            val is translated per CamForthVoltages

        """
        line = line.strip()

        if (
            len(line) == 0
            or line[0:1] == b"#"
            or line.find(b"NONE") >= 0
            or line == b"ok"
        ):
            return "", ""

        try:
            line = line[: line.index(b"#")].strip()
        except:
            pass

        try:
            tokens = line.split()
            board, name, kind = tokens[0].split(b"_")
            spec = board[:3].decode()

            if tokens[0] == b"2NDARY_DEWAR_PRESS":
                key = tokens[0]
            else:
                key = board[3:] + b"_" + name
            value = int(tokens[1].strip(b"*"))
        except:
            key = tokens[0]

        # Decode now
        key = key.decode()

        if key in CamForthTranslations.voltage_translations:
            if CamForthTranslations.voltage_translations[key] is None:
                # Signal that we are deliberately ignoring the value.
                return "", ""
            (
                board_name,
                boss_name,
                vscl8,
                du8z,
                vscl10,
                du10z,
            ) = CamForthTranslations.voltage_translations[key]
            voltage = vscl10 * (value - du10z) / 512.0
            # 8-bit DAC setting translations (See ticket #919)
            kind = kind.decode()
            if kind == "BIAS":
                voltage = vscl8 * (value - du8z) / 256.0
            full_name = "%s%s%s%s" % (spec, board_name, boss_name, kind.capitalize())
            return full_name, "%.3f" % (voltage)
        elif key in CamForthTranslations.keyword_translations:
            full_name = "%s%s" % (
                self.name[:3].upper(),
                CamForthTranslations.keyword_translations[key],
            )
            if len(tokens) > 1 and tokens[1][0:1] != b"#":
                return full_name, tokens[1].decode()
            else:
                cmd.warn(
                    'text="Failed to handle voltage %s, line: %s"' % (tokens[0], line)
                )
                return None, None
        else:
            cmd.warn('text="Failed to handle voltage line: %s"' % (line))
            return None, None

    def phaseWait(self, cmd, timeout=60):
        """Start a pinging process that continues until timeout or the micro is free."""
        self.phase_defer = Deferred()
        self.phase_start = time.time()
        self.phase_timeout = timeout
        self._sendPing(cmd)
        return self.phase_defer

    def _sendPing(self, cmd):
        self.sendCommand("PING", cmd, timeout=3).addCallback(
            self.phase_defer.callback
        ).addErrback(self._phaseBusy, cmd)

    def _phaseBusy(self, error, cmd):
        try:
            # raise the exception to see what it is
            error.raiseException()
        except BOSSExceptions.PhaseMicroBusy:
            # Phase micro is busy, schedule a timer to try again
            elapsed = time.time() - self.phase_start
            if elapsed < self.phase_timeout:
                reactor.callLater(0.25, self._sendPing, cmd)
            else:
                # We have timed out
                reactor.callLater(
                    0,
                    self.phase_defer.errback,
                    BOSSExceptions.TimeOutError(
                        "Timedout out waiting for micro. %.2f" % elapsed
                    ),
                )
        except:
            # Actual error
            reactor.callLater(0, self.phase_defer.errback, error.value)

    def executeProc(self, proc, cmd=None):
        """Returns a deferred."""
        if not cmd:
            cmd = self.icc.bcast
        this_dir = os.path.realpath(os.path.dirname(__file__))
        path = os.path.join(this_dir, "..", "etc", "CamProcedures", proc)
        return self._executePath(path, cmd=cmd)

    def _executePath(self, path, cmd=None):
        """Returns a deferred."""
        if not cmd:
            cmd = self.icc.bcast
        if not os.path.exists(path):
            d = Deferred()
            reactor.callLater(
                0, d.errback, Exception("Procedure does not exist at %s." % path)
            )
            return d
        proc = open(path)
        lines = []
        for line in proc:
            line = line.strip("\r\n ")
            if len(line) == 0 or line.startswith("#"):
                continue
            lines.append(line)
        return self.sendCommandList(lines, cmd, timeout=4 * len(lines))
