#!/usr/bin/env python

""" PingCmd.py -- wrap 'ping' functions. """

from twisted.internet import reactor
from twisted.internet.defer import DeferredList

import opscore.protocols.keys as keys
import opscore.protocols.types as types

from bossICC.Commands.BaseDelegate import BaseDelegate


class PingDelegate(BaseDelegate):
    def init(self):
        self.doFinish = True

    def individualComplete(self, response, controller):
        self.cmd.inform('text="%s: OK"' % controller)

    def failed(self, reason, controller):
        self.cmd.warn('text="%s: DEAD"' % controller)
        self.success = False

    def complete(self, data):
        if not self.doFinish:
            return
        if self.success:
            self.cmd.finish("")
        else:
            self.cmd.fail('text="Ping failed on one or more devices."')


class PingCmd(object):
    """Wrap 'dis ping' and friends."""

    def __init__(self, icc):
        self.icc = icc

        self.keys = keys.KeysDictionary(
            "boss_ping", (1, 1), keys.Key("devices", types.String() * (1,))
        )
        self.vocab = (("ping", "[<devices>]", self.pingCmd),)

    def pingCmd(self, cmd, doFinish=True):
        """Top-level "dis ping" command handler.
        Query all the controllers for liveness/happiness.
        """

        if "devices" in cmd.cmd.keywords:
            devices = cmd.cmd.keywords["devices"].values
        else:
            devices = list(self.icc.controllers.keys())  # Only ping those listed
        delegate = PingDelegate(devices, cmd, self.icc)
        delegate.doFinish = doFinish

        dl = []
        for device in devices:
            if device == "icc":
                cmd.respond('text="ICC : OK"')
            else:
                d = self.icc.controllers[device].ping(cmd)
                d.addCallback(delegate.individualComplete, device)
                d.addErrback(delegate.failed, device)
                dl.append(d)
        if len(dl) > 0:
            DeferredList(dl).addCallback(delegate.complete)
        else:
            reactor.callLater(0, delegate.complete, None)
