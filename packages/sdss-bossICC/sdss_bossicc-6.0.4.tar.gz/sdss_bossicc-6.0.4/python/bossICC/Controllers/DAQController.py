import logging

from twisted.internet import reactor
from twisted.internet.defer import Deferred

from opscore.utility.qstr import qstr

from bossICC import DAQInterface


class DAQController(object):
    def __init__(self, icc, name, spectroID, debug=1):
        """docstring for %s"""
        self.name = name
        self.icc = icc
        self.spectroID = spectroID
        self.host = self.icc.config[self.name]["host"]
        self.port = self.icc.config[self.name]["port"]
        self.debug = self.icc.config[self.name]["debug"]

        if self.icc.config[self.name]["mode"] == "test":
            self.testing = True
        else:
            self.testing = False

    def failedToStart(self, e):
        self.icc.bcast.warn(
            'text="failed to start DAQ %s, disconnecting myself, %s"' % (self.name, e)
        )
        del self.icc.controllers[self.name]

    def start(self):
        """Get things started."""
        d = Deferred()
        self.reset().addCallback(self.connect, d).addErrback(self.failedToStart)
        return d

    def connect(self, results, d):
        if self.testing:
            logging.info("Initializing camdaq in test mode.")
            self.interface.camdaq_init_testmode()
            self.interface.sendCommand("SET ROMODE 0")
            self.interface.getCommandResponse()
        else:
            logging.info("Initializing camdaq in normal mode.")
            self.interface.camdaq_init()

        try:
            timeout = self.icc.config[self.name]["timeout"]
            self.interface.sendCommand("TIMEOUT SET %s" % (timeout))
            self.interface.getCommandResponse()

            self.interface.sendCommand("TIMEOUT CLEAR")
            self.interface.getCommandResponse()

            self.interface.sendCommand("TIMEOUT ENABLE")
            self.interface.getCommandResponse()
        except Exception as xx:
            reactor.callLater(0, d.errback, xx)
            return

        reactor.callLater(0, d.callback, [])

    def reset(self, cmd=None):
        d = Deferred()
        try:
            self.interface = DAQInterface.boss_daq(
                self.host,
                self.port,
                self.name,
                spectro=self.spectroID,
                debug=self.debug,
            )
            self.interface.sendCommand("RESET")
            self.interface.exit()
            del self.interface

        except Exception as xx:
            reactor.callLater(0, d.errback, xx)
            return d
        reactor.callLater(6, self._finishReset, d, cmd)
        return d

    def _finishReset(self, d, cmd=None):
        try:
            self.interface = DAQInterface.boss_daq(
                self.host,
                self.port,
                self.name,
                spectro=self.spectroID,
                debug=self.debug,
            )
        except Exception as xx:
            reactor.callLater(0, d.errback, xx)
            return
        reactor.callLater(0, d.callback, [])

    def prepare_exposure(
        self,
        expID=None,
        lines=None,
        pixels=None,
        direc=None,
        isSubframe=False,
        frameLines=None,
        startLine=None,
        skipLines=0,
        cmd=None,
    ):
        if cmd:
            cmd.diag('text="initializing daq, just cuz"')
        self.interface.camdaq_init()

        self.interface.setWindow(isSubframe, frameLines, startLine, skipLines)
        if expID:
            self.interface.executeCommand("SET EXPID %d" % (expID))
        if lines:
            self.interface.executeCommand("SET LINES %d" % (lines))
        if pixels:
            self.interface.executeCommand("SET PIXELS %d" % (pixels))
        if direc:
            self.interface.direct(d=direc)

        # ON: quadrants flipped and organized. OFF: raw camera image. Or BOTH
        try:
            format = self.icc.config[self.icc.name]["format"]
        except:
            format = "ON"
        self.interface.fits_format(format)

        # Optionally zero fill the memory buffer. This takes a while, oddly, so
        # is not on by default.
        zeroFill = False
        try:
            zeroFill = bool(self.icc.config[self.name]["zeroFill"])
        except:
            pass
        if zeroFill:
            if cmd:
                cmd.inform('text="zero-filling DAQ buffers"')
            self.interface.execute_command("set testmode on")
            self.interface.execute_command("fill value 0")
            self.interface.execute_command("set testmode off")
            self.interface.execute_command("set romode 0")

        self.interface.executeCommand("SET EXPOSURE ON")

    def set_fits_headers(self, red_header, blue_header):
        self.interface.set_fits_headers(red_header, blue_header)

    def arm(self, mode="", cmd=None, errback=None):
        d = Deferred()
        self.interface.image_complete_callback(callback=self._imageComplete)
        self.arm_cmd = cmd
        self.arm_d = d
        self.interface.arm(mode=mode, cmd=cmd, errback=self._imageFailed)
        return d

    def readout(self, expId=None, cmd=None, errback=None):
        d = Deferred()
        self.interface.image_complete_callback(callback=self._imageComplete)
        self.arm_cmd = cmd
        self.arm_d = d
        self.interface.readout(cmd=cmd, expid=expId, errback=self._imageFailed)
        return d

    def _imageComplete(self):
        self.arm_cmd.respond('text="%s readout complete"' % (self.name))
        reactor.callFromThread(self.arm_d.callback, None)

    def _imageFailed(self, x):
        self.arm_cmd.error(
            "text=%s"
            % (qstr("%s readout failed: %s (%s)." % (self.name, x, self.arm_d.errback)))
        )
        reactor.callFromThread(self.arm_d.errback, x, self.name)

    def handle_command(self, command):
        if command.upper() == "RESET":
            self.reset()
            return "We are back."
        else:
            return self.interface.execute_command(command)

    def syncarm(self):
        self.interface.syncarm()

    def ping(self, cmd):
        d = Deferred()
        if not hasattr(self, "interface") or not self.interface:
            result = "DISCONNECTED"
            reactor.callLater(0, d.errback, Exception("DISCONNECTED"))
            return d

        self.interface.sendCommand("x")
        response = self.interface.getCommandResponse()
        if len(response) > 0:
            result = "OK"
            reactor.callLater(0, d.callback, result)
        else:
            result = "DEAD"
            reactor.callLater(0, d.errback, Exception("DEAD"))
        return d

    def stop(self):
        """docstring for stop"""
        try:
            self.interface.exit()
        except:
            pass
