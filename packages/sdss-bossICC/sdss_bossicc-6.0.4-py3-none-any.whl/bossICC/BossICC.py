#!/usr/bin/env python

"""The instrument control computer for the BOSS spectrographs and associated bits."""

import logging
import os
import re
import sys
import time
import types

import click
from twisted.internet import reactor

import actorcore.ICC
import opscore
from sdsstools.daemonizer import DaemonGroup

from bossICC import FilenameGen, __version__
from bossICC.Commands.Exposure import Exposure


BossGlobals = types.SimpleNamespace()


class BossICC(actorcore.ICC.ICC):
    def __init__(
        self,
        name,
        productName="bossICC",
        configFile=None,
        makeCmdrConnection=True,
    ):
        actorcore.ICC.ICC.__init__(
            self,
            name,
            configFile=configFile,
            productName=productName,
            makeCmdrConnection=makeCmdrConnection,
        )

        self.version = __version__

        # Connections are the external devices we I/O from/to.
        self.allControllers = ("sp1mech", "sp1cam", "sp1daq")
        self.controllers = {}

        # Just for debugging
        self.activeCmd = None

        # The one and only exposure we can have active.
        self.exposure = Exposure(self)

        self.shutdown = False

        try:
            rootDir = self.config[self.name]["imagedir"]
        except:
            rootDir = "/data/spectro"
        seqnoFile = os.path.join(rootDir, "nextExposureNumber")

        def namesFunc(rootDir, seqno):
            names = []
            for c in "r1", "b1":
                names.append(os.path.join(rootDir, "sdR-%s-%08d.fit" % (c, seqno)))
            return tuple(names)

        self.filenameGen = FilenameGen.FilenameGen(
            rootDir, seqnoFile, namesFunc=namesFunc
        )
        self.filenameGen.setup()

        self.models = {}

        BossGlobals.bcast = self.bcast
        self.firstConnection = False

    def commandFailed(self, cmd):
        """Called when a command failed."""
        pass

    def connectionMade(self):
        if self.firstConnection is False:
            logging.info("Attaching all controllers...")
            self.attachAllControllers()
            self.firstConnection = True

            reactor.callLater(10, self.status_check)
            reactor.callLater(15, self.complete_check)
            reactor.callLater(40, self.list_voltages_check)

    def complete_check(self):
        """Perform the periodic total status report of the system."""

        # This is a good point to create the models. When the model is created it
        # sends multiple getFor= to the keys actor. If this happens in __init__()
        # the cmdr connection to the hub hasn't have had a chance to succeed and those
        # getFor commands are lost. At this point the connection must have happened.
        for actor in ["mcp", "tcc", "apo", "boss", "jaeger", "cherno"]:
            if actor not in self.models:
                self.models[actor] = opscore.actor.model.Model(actor)

        self.bcast.respond("aliveAt=%d" % (time.time()))
        self.callCommand("camNom")
        self.callCommand("camBias")
        self.callCommand("camStat")
        self.callCommand("iccStatus")
        self.callCommand("ln2stat")
        reactor.callLater(self.config[self.name]["camstatDelay"], self.complete_check)

    def status_check(self):
        """Perform the periodic total status report of the system."""

        self.bcast.respond("aliveAt=%d" % (time.time()))
        self.callCommand("camCheck")
        reactor.callLater(self.config[self.name]["camcheckDelay"], self.status_check)

    def list_voltages_check(self):
        """Generate voltage listings."""

        self.callCommand("camRead")
        vldelay = self.config[self.name]["voltageListDelay"]
        reactor.callLater(vldelay, self.list_voltages_check)

    def getDevLists(self, devRE=None):
        """Return lists of all defined and all connected controllers."""

        controllers = self.config[self.name]["controllers"]
        controllers = set(map(str, controllers))
        connected = set(self.controllers.keys())

        if devRE:
            controllers = set([dev for dev in controllers if re.search(devRE, dev)])
            connected = set([dev for dev in connected if re.search(devRE, dev)])

        return connected, controllers


LOG_FILE = os.path.join(
    os.environ.get("ACTOR_DAEMON_LOG_DIR", "$HOME/logs"),
    "bossICC/bossICC.log",
)


@click.group(cls=DaemonGroup, prog="bossICC-actor", log_file=LOG_FILE)
@click.option("--bench", is_flag=True, help="Run benchboss.")
def run_actor(bench=False):
    """Runs bossICC."""

    sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 1)

    logging.getLogger("dispatch").setLevel(40)
    logging.getLogger("cmdr").setLevel(20)

    bossICC = BossICC("benchboss") if bench else BossICC("boss")
    bossICC.run()


if __name__ == "__main__":
    run_actor()
