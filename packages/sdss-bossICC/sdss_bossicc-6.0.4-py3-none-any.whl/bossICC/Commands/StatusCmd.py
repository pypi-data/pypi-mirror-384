#!/usr/bin/env python
""" StatusCmd.py -- wrap 'status' functions. """


class StatusCmd(object):
    """Wrap the various BOSS ICC status messages."""

    def __init__(self, icc):
        self.icc = icc

        self.keys = {}
        self.vocab = (
            ("status", "", self.status),
            ("iccStatus", "", self.iccStatus),
        )

    def status(self, cmd, doFinish=True):
        """Refresh all available status and keywords (ICC, DAQ, mech)."""
        self.iccStatus(cmd, doFinish=False)
        mechCmd = self.icc.commandSets.get("MechCmd", None)
        if mechCmd:
            mechCmd.status(cmd, doFinish=True)

    def iccStatus(self, cmd, doFinish=True):
        """Query the status of the ICC."""

        self.icc.sendVersionKey(cmd)
        self.icc.exposure.setState(cmd=cmd)

        cmd.inform(
            'text="controller names = %s"' % (sorted(self.icc.controllers.keys()))
        )

        sp2daq = "sp2daq" in list(self.icc.controllers.keys())
        sp1daq = ("sp1daq" in list(self.icc.controllers.keys())) << 1
        sp2mech = ("sp2mech" in list(self.icc.controllers.keys())) << 2
        sp1mech = ("sp1mech" in list(self.icc.controllers.keys())) << 3
        sp2cam = ("sp2cam" in list(self.icc.controllers.keys())) << 4
        sp1cam = ("sp1cam" in list(self.icc.controllers.keys())) << 5
        hardware_status = sp1cam | sp2cam | sp1mech | sp2mech | sp1daq | sp2daq
        cmd.respond("hardwareStatus=%s" % hex(hardware_status))
        if doFinish:
            cmd.finish("")
