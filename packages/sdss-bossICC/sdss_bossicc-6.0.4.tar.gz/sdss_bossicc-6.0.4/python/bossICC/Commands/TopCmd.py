#!/usr/bin/env python

""" TopCmd.py -- wrap top-level ICC functions. """

import logging
import sys

from twisted.internet import reactor, task

import opscore.protocols.keys as keys
import opscore.protocols.types as types
from opscore.utility.qstr import qstr
from opscore.utility.tback import tback
from sdsstools import read_yaml_file

from bossICC.Commands.BaseDelegate import BaseDelegate


class RAWDelegate(BaseDelegate):
    def _response(self, result, cmd, cam, cmd_txt):
        for ll in result:
            cmd.respond('%sRawText="%s"' % (cam, ll))
        cmd.finish()

    def _responseFail(self, result, cmd, cam, cmd_txt):
        cmd.fail(
            'text="Unable to send command (%s) to %s. output=%s"'
            % (cmd_txt, cam, result.value)
        )


class TopCmd(object):
    """Wrap top-level BOSS ICC funtions (spX raw, reload, debug)"""

    def __init__(self, icc):
        self.icc = icc

        self.keys = keys.KeysDictionary(
            "boss_top",
            (1, 1),
            keys.Key(
                "cmdfile",
                types.String() * (1, None),
                help="the name of a command file to load",
            ),
            keys.Key(
                "controllers",
                types.String() * (1, None),
                help="the names of 1 or more controllers to load",
            ),
        )

        self.vocab = (
            ("sp1mech", "@raw", self.sp1mech_raw),
            ("sp2mech", "@raw", self.sp2mech_raw),
            ("sp1daq", "@raw", self.sp1daq_raw),
            ("sp2daq", "@raw", self.sp2daq_raw),
            ("reinit", "", self.reinitialize),
            ("re", "", self.reloadExposure),
            ("reloadCommands", "[<cmdfile>]", self.reloadCommands),
            ("reloadControllers", "[<controllers>]", self.reloadControllers),
            ("disconnectControllers", "[<controllers>]", self.disconnectControllers),
            ("dbg", "@raw", self.dbg),
            ("dbgStmt", "@raw", self.dbgStmt),
        )

    def dbg(self, cmd):
        """Execute a raw command, returning the output results."""

        cmd_txt = cmd.cmd.keywords["raw"].values[0]
        cmd.respond('text="Executing raw command %s"' % (cmd_txt))

        try:
            exec("ret = %s" % (cmd_txt))
            cmd.respond('text="returned: %r' % (ret))  # type: ignore  # noqa
            cmd.finish("")
        except Exception as e:
            cmd.fail('text="error: %r' % (e))

    def dbgStmt(self, cmd):
        """Execute a raw command, ignoring the output results."""
        cmd_txt = cmd.cmd.keywords["raw"].values[0]
        cmd.respond('text="Executing raw command %s"' % (cmd_txt))
        try:
            exec("%s" % (cmd_txt))
            cmd.respond('text="OK')
            cmd.finish("")
        except Exception as e:
            cmd.fail('text="error: %r' % (e))

    #######################################################################
    #   sp1mech raw=TEXT
    #   sp2mech raw=TEXT
    #   sp1cam raw=TEXT
    #   sp2cam raw=TEXT
    #     Send raw commands down to the actual controllers. The text after
    #   the "raw=" is sent through unmolested.
    #       Returns:
    #          sp1mechText, sp2mechText, sp1camText, sp2camText
    #######################################################################
    def sp1mech_raw(self, cmd, doLower=False):
        """Pass a raw command through to sp1cam."""
        self.raw_cmd("sp1mech", cmd, doLower=False)

    def sp2mech_raw(self, cmd):
        """Pass a raw command through to sp2cam."""
        self.raw_cmd("sp2mech", cmd, doLower=False)

    def raw_cmd(self, cam, cmd, doLower=True):
        """Send a raw TDS command unmolested to the TDS micro."""

        # TDS commands might be horrible Forth junk with single double quotes, etc.,
        # so ignore any Command parsing.
        # Well, uppercase the commmand...
        #
        cmd_txt = cmd.cmd.keywords["raw"].values[0]
        if doLower:
            cmd_txt = cmd_txt.lower()
        cmd.respond('text="Sending raw command %s to %s"' % (cmd_txt, cam))
        delegate = RAWDelegate((cam,), cmd, self.icc)
        self.icc.controllers[cam].sendCommand(cmd_txt, cmd).addCallback(
            delegate._response, cmd, cam, cmd_txt
        ).addErrback(delegate._responseFail, cmd, cam, cmd_txt)
        cmd.respond('text="Waiting for response from spec mech."')

    def sp1daq_raw(self, cmd):
        """Send the sp1daq controller a raw command."""
        try:
            daq = self.icc.controllers["sp1daq"]
            cmdStr = cmd.cmd.keywords["raw"].values[0].strip("\"'")

            retStr = daq.handle_command(cmdStr)
            cmd.respond("text=%s" % (qstr(retStr)))
        except Exception as e:
            print(tback("sp1daq", e))
            cmd.warn('text="Failed in sending raw command to sp1daq: %s "' % (e))
        cmd.finish("")

    def sp2daq_raw(self, cmd):
        """Send the sp2daq controller a raw command."""
        try:
            daq = self.icc.controllers["sp2daq"]
            cmdStr = cmd.cmd.keywords["raw"].values[0].strip("\"'")

            retStr = daq.handle_command(cmdStr)
            cmd.respond("text=%s" % (qstr(retStr)))
        except Exception as e:
            print(tback("sp2daq", e))
            cmd.warn('text="Failed in sending raw command to sp2daq: %s "' % (e))
        cmd.finish("")

    def reloadExposure(self, cmd):
        """Reload the exposure command."""
        cmd.respond('text="Reloading exposure command."')
        self.icc.attachCmdSet("ExposureCmd")
        cmd.respond('text="Reload command completed."')
        cmd.finish("")

    def init(self, cmd):
        """Initialize by reloading the camera controllers."""
        self.reloadControllers(cmd, doFinish=False)

    def reloadCommands(self, cmd):
        """Reload the command modules from source.
        Arguments:
        cmds - A list of commands to reload.
        """
        if "cmds" in cmd.cmd.keywords:
            # Load the specified
            commands = cmd.cmd.keywords["cmds"].values
            for command in commands:
                cmd.respond('text="Attaching %s."' % (command))
                self.icc.attachCmdSet(command)
        else:
            # Load all
            cmd.respond('text="Attaching all command sets."')
            self.icc.attachAllCmdSets()
        cmd.finish("")

    def reloadControllers(self, cmd, doFinish=True):
        """Reload all, or a comma-separated list,
        of controller objects (e.g. spXcam,spXmech,spXdaq).
        """

        if "controllers" in cmd.cmd.keywords:
            controllers = cmd.cmd.keywords["controllers"].values
        else:
            controllers = self.icc.config[self.icc.name]["controllers"]
        controllers = list(map(str, controllers))

        # Nasty nasty nasty:
        # We want to do a .stop() and .start() on each connected controller. But .stop()
        # executed through a deferred, so we have let the reactor chain them.
        # We are not passing Deferreds up, so I'll just sleep a bit for now.
        # Which is WRONG and BROKEN.
        connected = [c for c in controllers if c in self.icc.controllers]
        if connected:
            for controller in connected:
                try:
                    cmd.respond('text="Disconnecting %s..."' % controller)
                    self.icc.controllers[controller].stop()
                    del self.icc.controllers[controller]
                except Exception as e:
                    cmd.warn(
                        'text="Unable to disconnect controller %s: %s. "'
                        % (controller, e)
                    )
            cmd.inform(
                'text="pausing to let the controllers disconnect themselves...."'
            )

        task.deferLater(
            reactor,
            (2.0 if connected else 0.0),
            self.connectControllers,
            cmd,
            controllers,
            doFinish,
        )

    def connectControllers(self, cmd, controllers, doFinish):
        cmd.respond('text="Reloading %s controllers..."' % controllers)
        for controller in controllers:
            try:
                cmd.respond('text="Attaching %s..."' % controller)
                self.icc.attachController(controller)
            except Exception as e:
                cmd.warn(
                    'text="Unable to attach controller %s: %s. "' % (controller, e)
                )

        if doFinish:
            cmd.finish("")

    def disconnectControllers(self, cmd):
        """Disconnect comma-separated list of controller objects
        (e.g. spXcam,spXmech,spXdaq).
        """

        if "controllers" in cmd.cmd.keywords:
            controllers = cmd.cmd.keywords["controllers"].values
            cmd.respond('text="Disconnecting %s controllers..."' % controllers)
            for controller in controllers:
                try:
                    controller = str(controller)
                    cmd.respond('text="Disconnecting %s..."' % controller)
                    self.icc.controllers[controller].stop()
                    del self.icc.controllers[controller]
                    cmd.respond('text="%s disconnected."' % controller)
                except Exception as e:
                    cmd.warn(
                        'text="Unable to disconnect controller %s: %s. "'
                        % (controller, e)
                    )
        else:
            cmd.fail('text="Must specify a controller to disconnect."')
        cmd.finish("")

    def reloadConfiguration(self, cmd):
        """Reload the boss.yaml file."""
        cmd.respond('text="Reparsing the configuration file."')
        logging.warn("reading config file %s", self.icc.configFile)
        self.icc.config = read_yaml_file(self.icc.configFile)
        cmd.finish("")

    def reinitialize(self, arg):
        """Make every attempt to reinitialize the system, by stopping and
        starting all devices and iccs.
        """

        if "devices" in arg.cmd.keywords:
            devices = arg.cmd.keywords["devices"].values
        else:
            devices = list(self.icc.controllers.keys())
        if "icc" in devices:
            devices = list(self.icc.controllers.keys())
        arg.respond('text="All devices = %s"' % (list(self.icc.controllers.keys())))
        arg.respond('text="Reconnecting the following devices: %s."' % (devices))
        for device in devices:
            try:
                arg.respond('text="Stopping %s."' % (device))
                logging.info("Stopping %s." % (device))
                self.icc.controllers[device].stop()
                arg.respond('text="Starting %s."' % (device))
                logging.info("Starting %s." % (device))
                self.icc.controllers[device].start()
                logging.info("%s restarted." % (device))
                arg.respond('text="%s restarted."' % (device))
            except:
                print(sys.exc_info())
                arg.warn('text="%s could not be reinitialized."' % (device))
        arg.finish("")
