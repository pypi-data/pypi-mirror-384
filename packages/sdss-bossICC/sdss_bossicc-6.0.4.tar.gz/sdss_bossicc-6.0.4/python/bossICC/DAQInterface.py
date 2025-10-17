#!/usr/bin/env python
#
# A python script to communicate with the BOSS NetBurner DAQ processor
#
# The two shell variables
#        BOSS_SPECT_IP
#        BOSS_SPECT_PORT
#
# have to be set before this script can be used.Alternatively, IP and the PORT can
# be set as the 1st and 2nd command line arguments.
# A second port (BOSS_SPECT_PORT + 1) is used for the data transfer channel
#
# A (DAQ) command can be issued in the command line following IP and PORT:
#
#       Examples:   python boss_camdaq.py 192.168.1.150 6666 STATUS
#
# or interactively following a prompt when no command line argument is given.
#
#
# Note: Since we are transfering binary data (for the wordcount)
#       we need to watch the "endianess". Due to its Motorola heritage the
#       NetBurner cpu is bid endian whereas Intel PCs are little endian machines.

import logging
import os
import queue
import socket
import struct
import subprocess
import sys
import threading
import time
import traceback

import numpy as np
from astropy.io import fits

import actorcore.utility.fits

from bossICC import __version__
from bossICC.BossICC import BossGlobals


done_event = threading.Event()

#############################################################################
#
# class boss_daq
#
# Implements a proxy object to communicate with the
# BOSS DAQ hardware via two sockets. One socket is used
# for commands and status messages while the second socket
# is reserved for CCD data transfer.
#
# Layout of the Camdaq control and status registers:
#
#      DAQ Status Register (DSR)
# 		Bit		Function
# 		0		Fresh		(output register is loaded)
# 		1		Line time out
# 		2		Overflow
# 		3		Line (status of line signal)
# 		4		FSM in idle state
# 		5		Read done (Direct access mode)
# 		6		Write done (Direct access mode)
#
#
#      Global Control Register (GCR)
# 		Bit		Function
# 		0		disable line time out
# 		1		reset pixel count fifo
# 		2		clear pixel per line counter
# 		3		clear all input shift registers
# 		4		enable software test mode
# 		5		clear time out
# 		6		clear line counter
# 		7		arm
# 		8		clear total pixel count(er)
#               9		reset memory FSM
#               10		enable pattern test mode
# 		11		start pattern test
# 		11		restart pattern test
# 		13		got them... (FSM is free to reuse output register)
#               14		enable direct memory mode
#               15		not used
#
##############################################################################

##############################################################################
#
# Version History
#
# 1.2.5    KH    9/11/09        Changed output to write both formatted and unformatted
#                               images
# 1.2.6    CL    9/16/09        Lowered BLUE_POVERSCAN by 1.
# 1.2.7    CL   10/08/09        rotated formatted images by 180 deg.
# 1.2.8    JE   12/10/09        Imporved connection and error handling.
# 1.2.9    KH    2/24/10        Reduced socket timeout to 3 s, correct readout time,
#                               simulator support
# 1.2.10   KH    2/26/10        support linegate function, pferr added for fits header
# 1.2.11   KH    2/27/10        added exposure id to error message. loop command
# 1.2.12   KH    2/27/10        some message format changes. FITS checksum
# 1.2.14   CL    4/26/10        support output file compression
# 1.3.0    KH    2/23/11        support for image readback
# 1.3.1    CL    3/15/11        serialize FITS writing to avoid GIL/thread slowdowns.
# 1.3.2    CL    11/1/11        add sha1sum processing of final files
# 6.0.0    JSG   8/14/21        Convert to Python 3.
##############################################################################


class boss_daq:
    BOSS_VERSION = __version__

    BLUE_EXTEND = 50
    BLUE_POVERSCAN = 77  # adjusted by Craig.#
    BLUE_LOVERSCAN = 56
    RED_EXTEND = 7
    RED_POVERSCAN = 111  # adjusted by Craig
    RED_LOVERSCAN = 48

    def __init__(self, host, port, name, debug=False, spectro=1):
        self.host = host
        self.port = port
        self.name = name
        self.spectrograph = spectro
        self.data_port = port + 1
        self.sock = None
        self.data_sock = None
        self.status = "Idle"
        self.debug_flag = debug
        self.command = ""
        self.loop_count = 1
        self.stop = threading.Event()  # Synchronization
        self.complete = threading.Event()
        self.armed = threading.Event()
        self.stop.clear()
        self.complete.clear()
        self.armed.clear()
        self.callback = None
        self.errback = None
        self.receiver_thread = None
        self.simulator_status = False

        self.writer_queue = queue.Queue()
        self.writer_thread = threading.Thread(
            target=fitsWriter, args=(self.writer_queue,)
        )
        self.writer_thread.daemon = True
        self.writer_thread.start()

        # configuration information (returned from Netburner for each exposure)
        self.printline = 0
        self.number_of_lines = 0
        self.number_of_pixels = 0
        self.total = 0
        self.exposureID = 0
        self.error_count = 0
        self.sync_error_count = 0
        self.pix_error_count = 0
        self.sync_error_lines = []
        self.pix_error_lines = []
        self.pframe_error = 0

        self.current_line = 0  # Variables for read-out status
        self.current_pixel = 0
        self.remaining_bytes = 0

        # Variables to control subframe reading.
        self.isSubframe = False
        self.frameLines = 2112  # KH was 0   # Rows in full frame.
        self.startLine = 0  # KH was 1# Row in readout to keep.
        self.skipLines = 0  # Rows to discard before keeping.

        self.start_time = None
        self.end_time = None

        self.timeout = 10.0  # used for command loop
        self.daq_timeout = (
            7  # used for data transfer from Netburner. Allow nnn time outs
        )

        self.fname = "sdR"
        self.directory = "./"
        self.red_io = True
        self.blue_io = True
        self.format = "ON"
        self.compressOutput = True
        self.syncOutput = (
            False  # Whether to NOT defer the file writes to a background thread.
        )
        self.cmd = None

        self.red_header = []
        self.blue_header = []

        self.camdaq_version = ""
        self.fpga_version = ""

        self.check_for_message_threshold = 100

        # Create socket and connect #
        logging.debug("%s: __init__ connection", (self.name))
        self.sock = self.reconnect(self.port)
        if self.sendCommand("VERSION") >= 0:
            response = self.getCommandResponse()
            if response is None:
                raise Exception
            myTokens = response.split(":")
            for field in myTokens:
                if field.startswith("CAMDAQ"):
                    self.camdaq_version = field.split("=")[1]
                if field.startswith("FPGA"):
                    self.fpga_version = field.split("=")[1]

        # Create data socket and adjust some options #
        self.data_sock = self.reconnect(self.data_port)

        self.status = "Connected"

    def __del__(self):
        self.writer_queue.put(None)

    ######################################################
    #
    # Some utility functions
    #
    ######################################################
    def reconnect(self, port):
        # Create data socket and adjust some options #
        if self.debug_flag:
            logging.debug(
                "Connecting to data link on host %s, port %d" % (self.host, port)
            )
        try:
            # Use create_connection(), which allows connect()-only timeouts.
            s = socket.create_connection((self.host, port), 4.0)
            if self.debug_flag:
                logging.debug("%s: Connected." % (self.name))
        except Exception as x:
            logging.error("ERROR in reconnect: %s" % str(x))
            raise
        s.settimeout(self.timeout)
        return s

    def readout(self, cmd=None, expid=None, errback=None):
        """Configure the system for an image readback. Call arm and return.

        During readback the pixel count fifo (# of pixels per line) is not used.
        It is assumed that every line contains the correct number of pixels.
        """

        self.cmd = cmd
        self.errback = errback

        if expid is not None:
            self.sendCommand("set expid %d" % int(expid))
        # Set romode to 4, turn on exposure and set direct mode to on
        self.execute_command("set romode 4")
        self.execute_command("set exposure on")
        self.execute_command("set directmode on")
        self.execute_command("fsm arm off")

        # Arm readout - this will start immediately
        self.execute_command("arm")

    def simulator(self, param):
        self.execute_command("set simulator %s" % param)
        if self.camdaq_status()["SIMULATOR"] == 1:
            self.simulator_status = True
        else:
            self.simulator_status = False

    def setWindow(self, isSubframe, frameLines, startLine, skipLines):
        """Set the readout window, for when the micro sends a subframe.

        Args:
          isSubframe    - True if the readout is from a SUBFREAD command. Note
                          that this is not the same as whether we are reading a full
                          frame, since SUBFREAD never sends overscan rows.
          frameLines    - the number of lines in the full frame. This is the vertical
                          size of the final image.
          startLine     - index of the starting line. 0-based.
          skipLines     - number of lines to discard before startLine.
        """

        self.isSubframe = isSubframe
        self.frameLines = frameLines
        self.startLine = startLine
        self.skipLines = skipLines

        # Flag that the writes should be synchronous.
        # This should be a completely independant flag -- CPL
        self.syncOutput = isSubframe

    def arm(self, mode="", cmd=None, errback=None):
        self.cmd = cmd
        if not self.armed.isSet():
            self.errback = errback
            if self.debug_flag:
                logging.info("%s: Starting receiver!" % (self.name))
            if self.data_sock is None:
                self.data_sock = self.reconnect(self.data_port)
                logging.info("%s: reconnecting data sock" % (self.name))
            self.receiver_thread = threading.Thread(
                target=self.async_receiveImage, args=(self.data_sock, None)
            )
            if isinstance(self.complete, threading.Event):
                self.complete.clear()
            if isinstance(self.stop, threading.Event):
                self.stop.clear()
            if isinstance(self.armed, threading.Event):
                self.armed.set()
            self.receiver_thread.daemon = True
            self.receiver_thread.start()
            retcode = self.sendCommand("ARM %s" % mode)
            if retcode < 0:
                if cmd is not None:
                    pass
                logging.info("ERROR in ARM command %s" % repr(retcode))
            return self.getCommandResponse()
        else:
            return "Already armed"

    def syncarm(self, mode="", cmd=None):
        self.cmd = cmd
        if not self.armed.isSet():
            if self.debug_flag:
                logging.debug("%s: Calling receiver!" % (self.name))
            if isinstance(self.complete, threading.Event):
                self.complete.clear()
            if isinstance(self.stop, threading.Event):
                self.stop.clear()
            if isinstance(self.armed, threading.Event):
                self.armed.set()
            retcode = self.sendCommand("SYNCARM %s" % mode)
            if retcode < 0:
                logging.info(
                    "%s: ERROR in SYNCARM command %s" % (self.name, repr(retcode))
                )
            response = self.getCommandResponse()
            if response.find("ACCEPTED") != -1:
                if self.sock is None:
                    self.sock = self.reconnect(self.port)
                self.receiveImage(self.sock, None)
                return "Done"
            else:
                return response
        else:
            return "Already armed"

    def receiving(self):
        if self.receiver_thread:
            return self.receiver_thread.isAlive()
        else:
            return False

    def receiver_status(self):
        status = {}
        status["Running"] = self.receiving()
        status["Complete"] = self.complete.isSet()
        status["Stop"] = self.stop.isSet()
        status["Armed"] = self.armed.isSet()
        status["Lines"] = self.number_of_lines
        status["Pixels"] = self.number_of_pixels
        status["Total"] = self.total
        status["Current_Line"] = self.current_line
        status["Current_Pixel"] = self.current_pixel
        status["Exposure"] = self.exposureID
        status["Remaining"] = self.remaining_bytes
        status["Start"] = self.start_time
        status["End"] = self.end_time
        status["File"] = self.fname
        status["Dir"] = self.directory
        return status

    def daq_status(self):
        status = {}
        status["Name"] = self.name
        status["Status"] = self.status
        status["Timeout"] = self.timeout
        status["Host"] = self.host
        status["Port"] = self.port
        status["Debug"] = self.debug_flag
        status["Version"] = boss_daq.BOSS_VERSION
        status["Red_IO"] = self.red_io
        status["Blue_IO"] = self.blue_io
        status["Format"] = self.format
        status["Red_Include"] = bool(self.red_header)
        status["Blue_Include"] = bool(self.blue_header)
        status["Red_Header"] = self.red_header
        status["Blue_Header"] = self.blue_header
        return status

    def set_debug_flag(self):
        self.debug_flag = True

    def clear_debug_flag(self):
        self.debug_flag = False

    def image_complete_event(self, complete=None):
        if complete is not None:
            if isinstance(complete, threading.Event):
                self.complete = complete
        return self.complete

    def abort(self):
        retcode = self.sendCommand("ABORT")
        if retcode < 0:
            return "ERROR in ABORT command %s" % repr(retcode)
        response = self.getCommandResponse()
        self.stop.set()
        return response

    def stop_event(self, stop=None):
        if stop is not None:
            if isinstance(stop, threading.Event):
                self.stop = stop
        return self.stop

    def armed_event(self, armed=None):
        if armed is not None:
            if isinstance(armed, threading.Event):
                self.armed = armed
        return self.armed

    def image_complete_callback(self, callback=None):
        if callback is not None:
            if callback == "None":
                self.callback = None
            else:
                self.callback = callback
        return self.callback

    def fits_format(self, f=None):
        if f is not None:
            self.format = f
        return self.format

    def set_fits_headers(self, red_header, blue_header):
        self.red_header = red_header
        self.blue_header = blue_header

    def output(self, r=None, b=None):
        if r is not None:
            self.red_io = r
        if b is not None:
            self.blue_io = b
        return (self.red_io, self.blue_io)

    def appname(self, name=None):
        if name is not None:
            self.name = name
        return self.name

    def filename(self, fname=None):
        if fname is not None:
            self.fname = fname
        return self.fname

    def direct(self, d=None):
        if d is not None:
            self.directory = d
        return self.directory

    def last_command(self):
        return self.command

    def readout_time(self):
        if self.start_time is None or self.end_time is None:
            return -1
        return self.end_time - self.start_time

    def executeCommand(self, command):
        self.sendCommand(command)
        return self.getCommandResponse()

    def kickstart_simulator(self):
        print("Simulator Kickstart.")
        self.executeCommand("expose 1")
        self.executeCommand("expose 0")
        self.executeCommand("expose 2")
        self.executeCommand("expose 0")

    # Initialize CamDAQ for readout
    def camdaq_init(self, id=1):
        if self.sendCommand("SET DEBUG 0") < 0:
            return False
        if self.sendCommand("CLEAR") < 0:
            return False
        if self.sendCommand("SET READOUTMODE ON") < 0:
            return False
        if self.sendCommand("SET EXPID %d" % id) < 0:
            return False
        if self.sendCommand("SET ROMODE 0") < 0:
            return False
        return True
        pass

    # Initialize CamDAQ for testmode readout
    def camdaq_init_testmode(self, id=1, romode=2):
        if self.sendCommand("SET DEBUG 1") < 0:
            return False
        if self.sendCommand("CLEAR") < 0:
            return False
        if self.sendCommand("SET TESTMODE ON") < 0:
            return False
        if self.sendCommand("SET EXPID %d" % id) < 0:
            return False
        if self.sendCommand("SET ROMODE %d" % romode) < 0:
            return False
        return True

    # Collect status information from camdaq micro

    def camdaq_error_status(self):
        status = {}
        status["EXPID"] = self.exposureID
        status["ERRCNT"] = self.error_count
        status["SYNCERR"] = self.sync_error_count
        status["PIXERR"] = self.pix_error_count
        status["PFERR"] = self.pframe_error
        status["SLINES"] = "".join(self.sync_error_lines)
        status["PLINES"] = "".join(self.pix_error_lines)
        return status

    def camdaq_status(self):
        status = {}
        # Get Status
        if self.sendCommand("STATUS") >= 0:
            response = self.getCommandResponse()
            # Analyse message string
            myTokens = response.split(":")
            for field in myTokens:
                if field.startswith("TRANSFER"):
                    status["TRANSFER"] = field.split("=")[1]
                if field.startswith("LINES"):
                    status["LINES"] = int(field.split("=")[1])
                if field.startswith("PIXELS"):
                    status["PIXELS"] = int(field.split("=")[1])
                if field.startswith("CURRENTLINE"):
                    status["CURRENTLINE"] = int(field.split("=")[1])
                if field.startswith("CURRENTPIXEL"):
                    status["CURRENTPIXEL"] = int(field.split("=")[1])
                if field.startswith("SENT"):
                    status["SENT"] = int(field.split("=")[1])
                if field.startswith("ID"):
                    status["EXPID"] = int(field.split("=")[1])

        # Get X Status
        if self.sendCommand("X") >= 0:
            response = self.getCommandResponse()
            # Analyse message string
            myTokens = response.split(":")
            for field in myTokens:
                if field.startswith("GSR"):
                    status["GSR"] = int(field.split("=")[1])
                if field.startswith("RSR"):
                    status["RSR"] = int(field.split("=")[1])
                if field.startswith("DSR"):
                    status["DSR"] = int(field.split("=")[1])
                if field.startswith("PIXCNTFIFO"):
                    status["PIXCNTFIFO"] = int(field.split("=")[1])
                if field.startswith("LINECNT"):
                    status["LINECNT"] = int(field.split("=")[1])
                if field.startswith("TOTALPIX"):
                    status["TOTALPIX"] = int(field.split("=")[1])

        # Get Flags
        if self.sendCommand("FLAGS") >= 0:
            response = self.getCommandResponse()
            # Analyse message string
            myTokens = response.split(":")
            for field in myTokens:
                if field.startswith("ARMED"):
                    status["ARMED"] = int(field.split("=")[1])
                if field.startswith("TEST"):
                    status["TEST"] = int(field.split("=")[1])
                if field.startswith("DIRECT"):
                    status["DIRECT"] = int(field.split("=")[1])
                if field.startswith("ROMODE"):
                    status["ROMODE"] = int(field.split("=")[1])
                if field.startswith("DEBUG"):
                    status["DEBUG"] = int(field.split("=")[1])
                if field.startswith("ABORT"):
                    status["ABORT"] = int(field.split("=")[1])
                if field.startswith("COMPLETE"):
                    status["COMPLETE"] = int(field.split("=")[1])
                if field.startswith("PCC"):
                    status["POWERCYCLE"] = int(field.split("=")[1])
                if field.startswith("SIMULATOR"):
                    status["SIMULATOR"] = int(field.split("=")[1])

        # Get Version
        if self.sendCommand("VERSION") >= 0:
            response = self.getCommandResponse()
            # Analyse message string
            myTokens = response.split(":")
            for field in myTokens:
                if field.startswith("CAMDAQ"):
                    status["CAMDAQ"] = field.split("=")[1]
                if field.startswith("FPGA"):
                    status["FPGA"] = int(field.split("=")[1])

        return status

    def exit(self):
        self.stop.set()
        if self.data_sock is not None:
            self.data_sock.close()
        self.data_sock = None
        if self.sock is not None:
            self.sock.close()
        self.sock = None

    def disconnect(self):
        self.sendCommand("DISCONNECT")
        self.stop.set()
        if self.data_sock is not None:
            self.data_sock.close()
        self.data_sock = None
        if self.sock is not None:
            self.sock.close()
        self.sock = None

    def reset(self):
        self.stop.set()
        self.sendCommand("RESET")
        if self.data_sock is not None:
            self.data_sock.close()
        self.data_sock = None
        if self.sock is not None:
            self.sock.close()
        self.sock = None

    ######################################################
    #
    # Receive pixel data from the server and writes fits file
    # Uses class variables for the data socket, number of lines
    # and number of pixels, total_pixels and the exposureID
    #
    # Events are used for synchronization purposes
    #      stop           (threading.Event -> abort if set)
    #      complete       (threading.Event -> set when image is complete)
    #
    #      callback       function to be called when image is complete
    #
    # This subroutine does not return until the image is complete and saved to disk
    # or an error has occured
    #
    ######################################################

    def async_receiveImage(self, s, dummy):
        try:
            if self.data_sock is None:
                self.data_sock = self.reconnect(self.data_port)
        except Exception as x:
            logging.error(
                "%s: Cannot reconnect to data socket in async_receiveImage. "
                "Transfer aborted. Message: %s" % (self.name, str(x))
            )
            self.armed.clear()
            self.status = "STOPPED"
            if self.data_sock is not None:
                self.data_sock.close()
            if self.errback:
                self.errback(x)
            return
        try:
            self.receiveImage(self.data_sock, dummy)
        except Exception as x:
            logging.error(
                "%s: Exception in receiveImage. Transfer aborted. Message: %s"
                % (self.name, str(x))
            )
            print(traceback.format_exc())
            self.armed.clear()
            self.status = "STOPPED"
            if self.data_sock is not None:
                self.data_sock.close()
            self.data_sock = None
            if self.errback:
                self.errback(x)
            return

    def receiveImage(self, s, dummy):
        self.error_count = 0
        self.pframe_error = 0
        self.sync_error_count = 0
        self.pix_error_count = 0
        self.sync_error_lines = []
        self.pix_error_lines = []
        self.printline = 0
        kickStart = False

        # Are we getting pixel data? Wait for the exposure header.
        while 1:
            if self.stop.isSet():
                self.armed.clear()
                if self.debug_flag:
                    logging.info("%s: ReceiveImage: Got stop event" % (self.name))
                self.stop.clear()
                self.status = "STOPPED"
                return

            try:
                response = str(self.getResponse(s))
            except Exception as x:
                logging.error(
                    "%s: Exception in receiveImage. Transfer Aborted. Message: %s"
                    % (self.name, str(x))
                )
                self.armed.clear()
                raise
            if response.find("EXPOSURE") != -1:
                # Analyse message string
                myTokens = response.split(":")
                for field in myTokens:
                    if field.startswith("EXPOSURE"):
                        self.exposureID = int(field.split("=")[1])
                    if field.startswith("PIXCOUNT"):
                        self.total = int(field.split("=")[1])
                    if field.startswith("LINES"):
                        self.number_of_lines = int(field.split("=")[1])
                    if field.startswith("PIXPERLINE"):
                        self.number_of_pixels = int(field.split("=")[1])

                if self.debug_flag:
                    logging.info(
                        "%s: Exposure ID %d, total pixel count %d, "
                        "Lines %d, Pixels per line %d"
                        % (
                            self.name,
                            self.exposureID,
                            self.total,
                            self.number_of_lines,
                            self.number_of_pixels,
                        )
                    )
                else:
                    logging.info(
                        "%s: ID=%d:TOTPIXCNT=%d"
                        % (self.name, self.exposureID, self.total)
                    )
                break
            else:
                if self.debug_flag:
                    logging.info(
                        "%s: ReceiveImage: Received incorrect response: %r"
                        % (self.name, response[:40])
                    )

        if not self.armed.isSet():  # are we armed?
            self.status = "ERROR"
            return

        # setup and make a local copy of the ccd data
        self.complete.clear()
        self.current_line = 0
        self.current_pixel = 0
        ccd = np.zeros(
            (2 * self.frameLines, 2 * self.number_of_pixels), dtype=np.uint16
        )
        R0 = np.zeros((self.frameLines, self.number_of_pixels), dtype=np.uint16)
        R1 = np.zeros((self.frameLines, self.number_of_pixels), dtype=np.uint16)
        R2 = np.zeros((self.frameLines, self.number_of_pixels), dtype=np.uint16)
        R3 = np.zeros((self.frameLines, self.number_of_pixels), dtype=np.uint16)
        B0 = np.zeros((self.frameLines, self.number_of_pixels), dtype=np.uint16)
        B1 = np.zeros((self.frameLines, self.number_of_pixels), dtype=np.uint16)
        B2 = np.zeros((self.frameLines, self.number_of_pixels), dtype=np.uint16)
        B3 = np.zeros((self.frameLines, self.number_of_pixels), dtype=np.uint16)

        # Now loop until we have all pixels. Each pixels is 2 bytes
        self.remaining_bytes = self.total * 2
        abort_transfer = 0

        # Loop until we have received the complete image
        logging.debug(
            "%s: Waiting for first line of exposure %d" % (self.name, self.exposureID)
        )
        if self.simulator_status:
            kickStart = True
            s.settimeout(10.0)  # overwrite timeout when using the simulator
        else:
            s.settimeout(self.timeout)
        catchStart = True
        while self.remaining_bytes > 0 and abort_transfer == 0:
            self.status = "Receiving"
            self.current_pixel = 0
            got_lineheader = 0
            got_waiting = 0
            while got_lineheader == 0:  # First we need a line header
                responsePieces = []
                missingLength = 4  # get word count for line header
                wc = b""
                timeouts = self.daq_timeout
                while missingLength > 0:
                    if (
                        self.stop.isSet()
                    ):  # Check for stop events from controlling thread
                        self.status = "STOPPED"
                        self.stop.clear()
                        self.armed.clear()
                        return
                    try:
                        next_chunk = s.recv(missingLength)
                        if len(next_chunk) == 0:
                            logging.error(
                                "%s: recv returns zero length string "
                                "in receiveImage (1)." % (self.name)
                            )
                            raise socket.error("Invalid response from Netburner.")
                        wc += next_chunk
                        missingLength -= len(wc)
                        if catchStart:
                            self.start_time = time.time()
                            catchStart = False

                        # TEST BLAMMO
                        if (
                            False
                            and self.name == "sp2daq"
                            and (int(time.time()) % 10) == 0
                        ):
                            logging.error("%s: Craig is causing trouble" % (self.name))
                            raise RuntimeError("Craig is making me blow up")
                    except Exception as xx:
                        if str(xx) == "timed out":
                            if kickStart:  # Kick simulator electronics
                                kickStart = False
                                self.kickstart_simulator()
                                s.settimeout(self.timeout)
                                continue
                            else:
                                timeouts -= 1
                                if timeouts >= 0:
                                    continue
                        logging.info(
                            "%s: Cannot obtain line header wc (data). Message: %s"
                            % (self.name, str(xx))
                        )
                        self.status = "ERROR"
                        self.armed.clear()
                        raise

                length = struct.unpack("i", wc[::-1])[0]
                missingLength = length

                # Read rest of line header message
                while missingLength > 0:
                    if self.stop.isSet():
                        self.status = "STOPPED"
                        self.stop.clear()
                        self.armed.clear()
                        return
                    next_chunk = s.recv(
                        missingLength
                    )  # no special timeout handling - data should be there already
                    if len(next_chunk) == 0:
                        logging.error(
                            "%s: recv returns zero length string in receiveImage (2)."
                            % (self.name)
                        )
                        raise socket.error("Invalid response from Netburner.")
                    responsePieces.append(next_chunk.decode())
                    missingLength -= len(next_chunk)

                lastResponse = " ".join(responsePieces)
                if (
                    self.debug_flag
                    and self.skipLines > 0
                    and (
                        self.current_line % 100 == 0
                        or self.current_line == self.number_of_lines - 1
                    )
                ):
                    logging.info(
                        "%s: Received line header with  %d bytes: %s"
                        % (self.name, int(length), lastResponse)
                    )

                # Analyze message - check for status updates
                myTokens = lastResponse.split(":")
                for field in myTokens:
                    if field.startswith("ABORT"):
                        logging.info(
                            "%s: Received ABORT Message: %s" % (self.name, lastResponse)
                        )
                        abort_transfer = 1
                        break
                    elif field.startswith("WAITING"):
                        logging.info("%s: Waiting: %s" % (self.name, lastResponse))
                        got_waiting = 1
                    elif field.startswith("LINE"):
                        received_count = int(field.split("=")[1])
                        # Check if line counter matches
                        if received_count != self.current_line:
                            self.error_count += 1
                            self.sync_error_count += 1
                            if len(self.sync_error_lines) < 10:
                                self.sync_error_lines.append(
                                    str(self.current_line) + ","
                                )
                        got_lineheader = 1  # got line header -> read to move on
                    elif field.startswith("PIXCNT"):
                        try:
                            actual_pixels = int(field.split("=")[1])
                        except:
                            actual_pixels = -1
                        # Check if number of pixels matches
                        if actual_pixels != self.number_of_pixels:
                            self.error_count += 1
                            self.pix_error_count += 1
                            if len(self.pix_error_lines) < 10:
                                self.pix_error_lines.append(
                                    str(self.current_line) + ","
                                )
                if self.current_line == self.printline:
                    logging.info("%s: Last Response: %s" % (self.name, lastResponse))
                    self.printline += 500
                if abort_transfer == 1:
                    break
                if got_waiting == 1:
                    got_waiting = 0
                    continue

            if abort_transfer == 1:
                break  # end transfer
            #
            # Now read the pixel data wc
            #
            line = b""
            self.current_pixel = 0
            continue_transfer = 0
            abort_transfer = 0
            while self.current_pixel < self.number_of_pixels:
                missingLength = 4  # get word count
                wc = b""
                timeouts = self.daq_timeout
                while missingLength > 0:
                    if self.stop.isSet():
                        self.status = "STOPPED"
                        self.stop.clear()
                        self.armed.clear()
                        return
                    try:
                        next_chunk = s.recv(missingLength)
                        if len(next_chunk) == 0:
                            logging.error(
                                "%s: recv returns zero length string in "
                                "receiveImage (3)." % (self.name)
                            )
                            raise socket.error("Invalid response from Netburner.")
                        wc += next_chunk
                        missingLength -= len(wc)
                    except Exception as xx:
                        if str(xx) == "timed out":
                            timeouts -= 1
                            if timeouts >= 0:
                                continue
                        logging.error(
                            "Cannot obtain pixel data wc data (Line %d, Pixel %d) %s"
                            % (self.current_line, self.current_pixel, str(xx))
                        )
                        self.status = "ERROR"
                        self.armed.clear()
                        raise

                length = struct.unpack("i", wc[::-1])[0]
                missingLength = length
                if length < self.check_for_message_threshold:
                    test_this = 1
                else:
                    test_this = 0
                #
                # Loop in case recv returns before message is complete
                #
                timeouts = self.daq_timeout
                while missingLength > 0:
                    try:
                        if self.stop.isSet():
                            self.status = "STOPPED"
                            self.stop.clear()
                            self.armed.clear()
                            return
                        pixelbytes = s.recv(missingLength)
                        if len(pixelbytes) == 0:
                            logging.error(
                                "%s: recv returns zero length string in receiveImage."
                                % (self.name)
                            )
                            raise socket.error("Invalid response from Netburner.")
                    except Exception as xx:
                        if str(xx) == "timed out":
                            timeouts -= 1
                            if timeouts >= 0:
                                continue
                        logging.info(
                            "%s: Error reading pixel bytes. Message: %s"
                            % (self.name, str(xx))
                        )
                        self.status = "ERROR"
                        self.armed.clear()
                        raise

                    if test_this:
                        if pixelbytes.find(b"ABORT") != -1:
                            logging.info(
                                "%s: Received ABORT Message: %s"
                                % (self.name, pixelbytes.decode())
                            )
                            abort_transfer = 1
                            break
                        elif pixelbytes.find(b"WAITING") != -1:
                            logging.info(
                                "%s: Waiting: %s" % (self.name, pixelbytes.decode())
                            )
                            continue_transfer = 1
                            break
                        test_this = 0

                    line += pixelbytes  # got some data
                    missingLength -= len(pixelbytes)

                if continue_transfer:
                    continue  # wait for next message

                if abort_transfer == 1:
                    break  # end transfer

                self.remaining_bytes -= length
                self.current_pixel += length / 16

            if abort_transfer == 1:
                break  # end transfer

            if len(line) != 34816:
                logging.info(
                    "%s: Last Line %d with %d pixels"
                    % (self.name, self.current_line, len(line))
                )

            # Discard any SUBFREAD binned rows before the readout region.
            if self.skipLines > 0:
                self.skipLines -= 1
                continue

            # Process the line,convert string to array and reshape
            # use this for little endian   aline = np.fromstring(line,dtype=np.int16)
            # use this for big endian      aline = np.fromstring(line,dtype='>H')
            aline = np.fromstring(line, dtype=">H")
            ampsline = np.reshape(aline, (-1, 8))
            if self.debug_flag and (self.current_line == 0):
                logging.info(
                    "%s: Pixel 0 for amp0: %d (%x)"
                    % (self.name, ampsline[0, 0], ampsline[0, 0])
                )
                logging.info(
                    "%s: Pixel 0 for amp1: %d (%x)"
                    % (self.name, ampsline[0, 1], ampsline[0, 1])
                )
                logging.info(
                    "%s: Pixel 0 for amp2: %d (%x)"
                    % (self.name, ampsline[0, 2], ampsline[0, 2])
                )
                logging.info(
                    "%s: Pixel 0 for amp3: %d (%x)"
                    % (self.name, ampsline[0, 3], ampsline[0, 3])
                )
                logging.info(
                    "%s: Pixel 0 for amp4: %d (%x)"
                    % (self.name, ampsline[0, 4], ampsline[0, 4])
                )
                logging.info(
                    "%s: Pixel 0 for amp5: %d (%x)"
                    % (self.name, ampsline[0, 5], ampsline[0, 5])
                )
                logging.info(
                    "%s: Pixel 0 for amp6: %d (%x)"
                    % (self.name, ampsline[0, 6], ampsline[0, 6])
                )
                logging.info(
                    "%s: Pixel 0 for amp7: %d (%x)"
                    % (self.name, ampsline[0, 7], ampsline[0, 7])
                )

            # Naming convention:
            #                     R2 | R3         B2 | B3
            #                     -------         -------
            #                     R0 | R1         B0 | B1
            #
            # Connector Pin - CCD Amp assignments
            # Pin/Bit 0    B1
            # Pin/Bit 1    B0
            # Pin/Bit 2    B2
            # Pin/Bit 3    B3
            # Pin/Bit 4    R3
            # Pin/Bit 5    R1
            # Pin/Bit 6    R2
            # Pin/Bit 7    R0
            #
            # Note that if the micro is sending subframed data:
            #   - the full line width is sent, so we leave that alone.
            #   - the subframe starts at a given row, so we need to offset by that
            #       amount.

            # fmt: off

            # Amplifier B1 (correct line, pixels have to be reversed (right side read out))
            B1[self.current_line + self.startLine, 0 : self.number_of_pixels] = ampsline[::-1, 0]
            # Amplifier B0 (pixel and lines are already in the correct order)
            B0[self.current_line + self.startLine, 0 : self.number_of_pixels] = ampsline[:, 1]
            # Amplifier B2 (line is counted from top, pixels correct)
            B2[self.frameLines - (self.current_line + self.startLine) - 1, 0 : self.number_of_pixels] = ampsline[:, 2]   #
            # Amplifier B3 (line is counted from top, pixels have to be reversed (right side read out))
            B3[self.frameLines - (self.current_line + self.startLine) - 1, 0 : self.number_of_pixels] = ampsline[::-1, 3]

            # Amplifier R3 (line is counted from top, pixels have to be reversed (right side read out))
            R3[self.frameLines - (self.current_line + self.startLine) - 1, 0 : self.number_of_pixels] = ampsline[::-1, 4]
            # Amplifier R1 (correct line, pixels have to be reversed (right side read out))
            R1[self.current_line + self.startLine, 0 : self.number_of_pixels] = ampsline[::-1, 5]
            # Amplifier R2 (line is counted from top, pixels correct)
            R2[self.frameLines - (self.current_line + self.startLine) - 1, 0 : self.number_of_pixels] = ampsline[:, 6]
            # Amplifier R0 (pixel and lines are already in the correct order)
            R0[self.current_line + self.startLine, 0 : self.number_of_pixels] = ampsline[:, 7]

            # fmt: on

            # get ready for the next line
            self.current_line += 1

        # We received a complete image
        self.end_time = time.time()
        self.status = "SAVING"
        if self.stop.isSet() or abort_transfer == 1:
            if self.debug_flag:
                logging.info(
                    "%s: Transfer for exposure %d was aborted after %d "
                    "pixels and %f seconds."
                    % (
                        self.name,
                        self.exposureID,
                        self.total,
                        (self.end_time - self.start_time),
                    )
                )
            if abort_transfer == 1:
                self.status = "ABORT"
            else:
                self.status = "STOPPED"
            self.stop.clear()
            self.armed.clear()
            return

        logging.info(
            "%s: Receiving %d pixels for exposure %d took %f seconds."
            % (
                self.name,
                self.total,
                self.exposureID,
                (self.end_time - self.start_time),
            )
        )

        # Check if read and write counter on the DA board have the correct values
        time.sleep(0.1)
        fsm_result = self.execute_command("fsm")
        logging.debug(
            "%s: Check read and write address counters: %s" % (self.name, fsm_result)
        )
        parts = fsm_result.split(":")
        for i in parts:
            pieces = i.split("=")
            if pieces[0] == "RCNT":
                # Allow  nominal value and nominal value + 1 as long as the
                #   camera sends the extra line
                if (
                    int(pieces[-1]) != self.total / 8
                    and int(pieces[-1]) != self.total / 8 + 1
                ):
                    logging.error(
                        "%s: Exposure %d: Incorrect value for %s address counter. "
                        "Should be %d. Is %s."
                        % (
                            self.name,
                            self.exposureID,
                            pieces[0],
                            self.total / 8,
                            pieces[-1],
                        )
                    )
                    self.error_count += 1
                    self.pframe_error = 1
            elif pieces[0] == "WCNT":
                # Allow  nominal value and nominal value + extra line of pixels as
                #   long as the camera sends the extra line
                if (
                    int(pieces[-1]) != self.total / 8
                    and int(pieces[1]) != self.total / 8 + self.number_of_pixels
                ):
                    logging.error(
                        "%s: Exposure %d: Incorrect value for %s address counter. "
                        "Should be %d. Is %s."
                        % (
                            self.name,
                            self.exposureID,
                            pieces[0],
                            self.total / 8,
                            pieces[-1],
                        )
                    )
                    self.error_count += 1
                    self.pframe_error = 1
            elif pieces[0] == "EXTRA":
                # Allow  nominal value and a full line as long as
                #   the camera sends the extra line
                if int(pieces[-1]) != 0 and int(pieces[-1]) != self.number_of_pixels:
                    logging.error(
                        "%s: Exposure %d: Received extra pframe clocks. Count: %s"
                        % (self.name, self.exposureID, pieces[-1])
                    )
                    self.error_count += 1
                    self.pframe_error = int(pieces[-1])

        # arrange full CCD array. If format is not set write out raw data,
        # otherwise move overscan lines and pixels to the edge
        # a few definitions to improve readability of the code
        lines = self.frameLines
        pix = self.number_of_pixels
        pover = boss_daq.RED_POVERSCAN
        lover = boss_daq.RED_LOVERSCAN

        # self.format controls whether formatted ("ON"), unformatted ("OFF")
        # or both ("BOTH") images are written to disk

        if self.format == "OFF":
            format_ctrl = (False,)
        elif self.format == "BOTH":
            format_ctrl = (True, False)
        else:
            format_ctrl = (True,)
        for output_formatted in format_ctrl:
            try:
                if output_formatted:
                    fullFilename = "%s-r%d-%08d.fit" % (
                        self.filename(),
                        self.spectrograph,
                        self.exposureID,
                    )
                else:
                    if self.filename() == "sdR":
                        fn = "sdU"
                    else:
                        fn = self.filename() + "-raw"
                    fullFilename = "%s-r%d-%08d.fit" % (
                        fn,
                        self.spectrograph,
                        self.exposureID,
                    )

                # fmt: off

                if output_formatted:
                    # Copy pixel data from amplifier R0
                    ccd[0:lover, 0:pover] = R0[lines - lover:lines, pix - pover:pix]          # move line, pixel overscan
                    ccd[0:lover, pover:pix] = R0[lines - lover:lines, 0:pix - pover]          # move line overscan
                    ccd[lover:lines, 0:pover] = R0[0:lines - lover, pix - pover:pix]          # move pixel overscan
                    ccd[lover:lines, pover:pix] = R0[0:lines - lover, 0:pix - pover]          # move pixel data
                    # Copy pixel data from amplifier R1
                    ccd[0:lover, 2 * pix - pover:2 * pix] = R1[lines - lover:lines, 0:pover]  # move line, pixel overscan
                    ccd[0:lover, pix:2 * pix - pover] = R1[lines - lover:lines, pover:pix]    # move line overscan
                    ccd[lover:lines, 2 * pix - pover:2 * pix] = R1[0:lines - lover, 0:pover]  # move pixel overscan
                    ccd[lover:lines, pix:2 * pix - pover] = R1[0:lines - lover, pover:pix]    # move pixel data
                    # Copy pixel data from amplifier R2
                    ccd[2 * lines - lover:2 * lines, 0:pover] = R2[0:lover, pix - pover:pix]    # move line, pixel overscan
                    ccd[2 * lines - lover:2 * lines, pover:pix] = R2[0:lover, 0:pix - pover]    # move line overscan
                    ccd[lines:2 * lines - lover, 0:pover] = R2[lover:lines, pix - pover:pix]    # move pixel overscan
                    ccd[lines:2 * lines - lover, pover:pix] = R2[lover:lines, 0:pix - pover]    # move pixel data
                    # Copy pixel data from amplifier R3
                    ccd[2 * lines - lover:2 * lines, 2 * pix - pover:2 * pix] = R3[0:lover, 0:pover]    # move line, pixel overscan
                    ccd[2 * lines - lover:2 * lines, pix:2 * pix - pover] = R3[0:lover, pover:pix]      # move line overscan
                    ccd[lines:2 * lines - lover, 2 * pix - pover:2 * pix] = R3[lover:lines, 0:pover]    # move pixel overscan
                    ccd[lines:2 * lines - lover, pix:2 * pix - pover] = R3[lover:lines, pover:pix]      # move pixel data
                else:
                    ccd[0:lines, 0:pix] = R0
                    ccd[0:lines, pix:2 * pix] = R1
                    ccd[lines:2 * lines, 0:pix] = R2
                    ccd[lines:2 * lines, pix:2 * pix] = R3

                # fmt: on

                # Rotate image by 180 degrees.
                ccd = np.fliplr(np.flipud(ccd))

                hdu = fits.PrimaryHDU(data=ccd.copy())
                hdu.header["TELESCOP"] = "SDSS 2-5m"
                hdu.header["FILENAME"] = fullFilename
                hdu.header["CAMERAS"] = "r" + str(self.spectrograph)
                hdu.header["EXPOSURE"] = self.exposureID
                hdu.header["V_BOSS"] = (
                    boss_daq.BOSS_VERSION,
                    "Active version of the BOSS ICC",
                )

                hdu.header["CAMDAQ"] = self.camdaq_version + ":" + self.fpga_version

                hdu.header["SUBFRAME"] = (
                    self.isSubframe if self.isSubframe else "",
                    "the subframe readout command",
                )

                if self.isSubframe:
                    hdu.header["SUBFROW1"] = (
                        self.startLine + 1,
                        "first row of subframe readout",
                    )
                    hdu.header["SUBFROWN"] = (
                        self.startLine + self.number_of_lines,
                        "last row of subframe readout",
                    )

                if self.error_count == 0:
                    hdu.header["ERRCNT"] = "NONE"
                else:
                    hdu.header["ERRCNT"] = "%d" % self.error_count
                if self.sync_error_count == 0:
                    hdu.header["SYNCERR"] = "NONE"
                else:
                    hdu.header["SYNCERR"] = "%d" % self.sync_error_count
                if len(self.sync_error_lines) == 0:
                    hdu.header["SLINES"] = "NONE"
                else:
                    hdu.header["SLINES"] = "%s" % "".join(self.sync_error_lines)
                if self.pix_error_count == 0:
                    hdu.header["PIXERR"] = "NONE"
                else:
                    hdu.header["PIXERR"] = "%d" % self.pix_error_count
                if len(self.pix_error_lines) == 0:
                    hdu.header["PLINES"] = "NONE"
                else:
                    hdu.header["PLINES"] = "%s" % "".join(self.pix_error_lines)
                if self.pframe_error == 0:
                    hdu.header["PFERR"] = "NONE"
                else:
                    hdu.header["PFERR"] = "%d" % self.pframe_error

                # Include additional keywords from ICC and reset include flag
                # for next exposure

                for card in self.red_header:
                    try:
                        name, value, comment = card
                    except Exception:
                        name = "comment"
                        value = "failed to make card from %s" % (card)
                        comment = ""
                    try:
                        hdu.header[name] = (value, comment)
                    except Exception as e:
                        logging.error(
                            "%s: Completely failed to write a fits card for %s: %s"
                            % (self.name, card, e)
                        )

                if self.red_io:
                    # Fix for #1006, where subframed hartmanns are
                    #   not available to process soon enough.
                    if self.syncOutput:
                        if self.cmd is not None:
                            self.cmd.inform('text="writing red images directly"')
                        else:
                            logging.info("writing red images directly")
                        writeSingleFITS(
                            hdu,
                            self.directory,
                            fullFilename,
                            self.cmd,
                            self.compressOutput,
                        )
                    else:
                        if self.cmd is not None:
                            self.cmd.inform('text="submitting red to writing thread"')
                        else:
                            logging.info("submitting red to writing thread")
                        self.writer_queue.put(
                            (
                                hdu,
                                self.directory,
                                fullFilename,
                                BossGlobals.bcast,
                                self.compressOutput,
                            ),
                        )

            except Exception as xx:
                logging.error(
                    "%s: PyFITS FileIO (Red) error: %s" % (self.name, str(xx))
                )
                raise

        # end for output_formatted

        self.red_header = []

        # arrange full CCD array. If format is not set write out raw data,
        # otherwise move overscan lines and pixels to the edge
        # a few definitions to improve readability of the code
        lines = self.frameLines
        pix = self.number_of_pixels
        pover = boss_daq.BLUE_POVERSCAN
        lover = boss_daq.BLUE_LOVERSCAN

        # For the time being we write each image twice - formatted and unformatted
        for output_formatted in format_ctrl:
            try:
                if output_formatted:
                    fullFilename = "%s-b%d-%08d.fit" % (
                        self.filename(),
                        self.spectrograph,
                        self.exposureID,
                    )
                else:
                    if self.filename() == "sdR":
                        fn = "sdU"
                    else:
                        fn = self.filename() + "-raw"
                    fullFilename = "%s-b%d-%08d.fit" % (
                        fn,
                        self.spectrograph,
                        self.exposureID,
                    )

                # fmt: off

                if output_formatted:
                    # Copy pixel data from amplifier B0
                    ccd[0:lover, 0:pover] = B0[lines - lover:lines, pix - pover:pix]            # move line, pixel overscan
                    ccd[0:lover, pover:pix] = B0[lines - lover:lines, 0:pix - pover]            # move line overscan
                    ccd[lover:lines, 0:pover] = B0[0:lines - lover, pix - pover:pix]            # move pixel overscan
                    ccd[lover:lines, pover:pix] = B0[0:lines - lover, 0:pix - pover]            # move pixel data
                    # Copy pixel data from amplifier B1
                    ccd[0:lover, 2 * pix - pover:2 * pix] = B1[lines - lover:lines, 0:pover]    # move line, pixel overscan
                    ccd[0:lover, pix:2 * pix - pover] = B1[lines - lover:lines, pover:pix]      # move line overscan
                    ccd[lover:lines, 2 * pix - pover:2 * pix] = B1[0:lines - lover, 0:pover]    # move pixel overscan
                    ccd[lover:lines, pix:2 * pix - pover] = B1[0:lines - lover, pover:pix]      # move pixel data
                    # Copy pixel data from amplifier B2
                    ccd[2 * lines - lover:2 * lines, 0:pover] = B2[0:lover, pix - pover:pix]    # move line, pixel overscan
                    ccd[2 * lines - lover:2 * lines, pover:pix] = B2[0:lover, 0:pix - pover]    # move line overscan
                    ccd[lines:2 * lines - lover, 0:pover] = B2[lover:lines, pix - pover:pix]    # move pixel overscan
                    ccd[lines:2 * lines - lover, pover:pix] = B2[lover:lines, 0:pix - pover]    # move pixel data
                    # Copy pixel data from amplifier B3
                    ccd[2 * lines - lover:2 * lines, 2 * pix - pover:2 * pix] = B3[0:lover, 0:pover]    # move line, pixel overscan
                    ccd[2 * lines - lover:2 * lines, pix:2 * pix - pover] = B3[0:lover, pover:pix]      # move line overscan
                    ccd[lines:2 * lines - lover, 2 * pix - pover:2 * pix] = B3[lover:lines, 0:pover]    # move pixel overscan
                    ccd[lines:2 * lines - lover, pix:2 * pix - pover] = B3[lover:lines, pover:pix]      # move pixel data
                else:
                    ccd[0:lines, 0:pix] = B0
                    ccd[0:lines, pix:2 * pix] = B1
                    ccd[lines:2 * lines, 0:pix] = B2
                    ccd[lines:2 * lines, pix:2 * pix] = B3

                # fmt: on

                # Rotate image by 180 degrees.
                ccd = np.fliplr(np.flipud(ccd))

                hdu = fits.PrimaryHDU(data=ccd.copy())
                hdu.header["TELESCOP"] = "SDSS 2-5m"
                hdu.header["FILENAME"] = fullFilename
                hdu.header["CAMERAS"] = "b" + str(self.spectrograph)
                hdu.header["EXPOSURE"] = self.exposureID
                hdu.header["V_BOSS"] = (
                    boss_daq.BOSS_VERSION,
                    "Active version of the BOSS ICC",
                )
                hdu.header["CAMDAQ"] = self.camdaq_version + ":" + self.fpga_version
                hdu.header["SUBFRAME"] = (
                    self.isSubframe if self.isSubframe else "",
                    "the subframe readout command",
                )

                if self.isSubframe:
                    hdu.header["SUBFROW1"] = (
                        self.startLine + 1,
                        "first row of subframe readout",
                    )
                    hdu.header["SUBFROWN"] = (
                        self.startLine + self.number_of_lines,
                        "last row of subframe readout",
                    )

                if self.error_count == 0:
                    hdu.header["ERRCNT"] = "NONE"
                else:
                    hdu.header["ERRCNT"] = "%d" % self.error_count
                if self.sync_error_count == 0:
                    hdu.header["SYNCERR"] = "NONE"
                else:
                    hdu.header["SYNCERR"] = "%d" % self.sync_error_count
                if len(self.sync_error_lines) == 0:
                    hdu.header["SLINES"] = "NONE"
                else:
                    hdu.header["SLINES"] = "%s" % "".join(self.sync_error_lines)
                if self.pix_error_count == 0:
                    hdu.header["PIXERR"] = "NONE"
                else:
                    hdu.header["PIXERR"] = "%d" % self.pix_error_count
                if len(self.pix_error_lines) == 0:
                    hdu.header["PLINES"] = "NONE"
                else:
                    hdu.header["PLINES"] = "%s" % "".join(self.pix_error_lines)
                if self.pframe_error == 0:
                    hdu.header["PFERR"] = "NONE"
                else:
                    hdu.header["PFERR"] = "%d" % self.pframe_error

                # Include additional keywords from ICC
                #   (and reset include flag for next exposure)
                for card in self.blue_header:
                    try:
                        name, value, comment = card
                    except Exception:
                        name = "comment"
                        value = "failed to make card from %s" % (card)
                        comment = ""

                    try:
                        hdu.header[name] = (value, comment)
                    except Exception as e:
                        logging.error(
                            "%s: Completely failed to write a fits card for %s: %s"
                            % (self.name, card, e)
                        )

                if self.blue_io:
                    # Fix for #1006, where subframed hartmanns
                    #   are not available to process soon enough.
                    if self.syncOutput:
                        if self.cmd is not None:
                            self.cmd.inform('text="writing blue images directly"')
                        else:
                            logging.info("writing blue images directly")
                        writeSingleFITS(
                            hdu,
                            self.directory,
                            fullFilename,
                            self.cmd,
                            self.compressOutput,
                        )
                    else:
                        if self.cmd is not None:
                            self.cmd.inform('text="submitting blue to writing thread"')
                        else:
                            logging.info("submitting blue to writing thread")
                        self.writer_queue.put(
                            (
                                hdu,
                                self.directory,
                                fullFilename,
                                BossGlobals.bcast,
                                self.compressOutput,
                            ),
                        )
            except Exception as xx:
                logging.error("%s: PyFITS FileIO (Blue) error: " + (self.name, str(xx)))

        #
        # end for output_formatted
        #
        self.blue_header = []
        self.status = "DONE"
        if self.callback:
            self.callback()
        self.armed.clear()
        if self.debug_flag:
            logging.info(
                "%s: receiveImage complete. Error count: %d"
                % (self.name, self.error_count)
            )
        if isinstance(self.complete, threading.Event):
            self.complete.set()
        logging.info(
            "%s: DEBUG: Done.  Error count: %d" % (self.name, self.error_count)
        )
        return

    ######################################################
    #
    # Sends a command to the server
    #      cmd is the command string
    #
    # returns 0 if okay, 1 if reconnected and -1 if error
    #
    ######################################################

    def sendCommand(self, cmd):
        self.command = cmd
        if self.sock is None:
            self.sock = self.reconnect(self.port)
        try:
            if self.debug_flag:
                logging.debug("%s: Sending %s to daq" % (self.name, cmd))
            self.sock.sendall(
                struct.pack("i", socket.htonl(len(self.command)))
                + self.command.upper().encode()
            )
        except Exception as x:
            logging.error(
                "%s: Cannot send command %s. Message: %s" % (self.name, cmd, str(x))
            )
            if self.sock is not None:
                self.sock.close()
            self.sock = None
            if self.data_sock is not None:
                self.data_sock.close()
            self.data_sock = None
            raise
        return 0

    def getCommandResponse(self):
        if self.sock is None:
            self.sock = self.reconnect(self.port)
        try:
            return self.getResponse(self.sock)
        except Exception as x:
            if self.sock is not None:
                self.sock.close()
            self.sock = None
            logging.error(
                "%s: Cannot get response from command socket. Message: %s"
                % (self.name, str(x))
            )
            if str(x).find("Netburner") != -1:
                logging.error("%s: Resetting Data Sock" % (self.name))
                if self.data_sock is not None:
                    self.data_sock.close()
                self.data_sock = None
            raise

    def getResponse(self, sock):
        """Get a response from the server.

        sock is the socket to be used to receive the response. Returns the response.
        """

        response = b""
        missingLength = 4  # get word count
        wc = b""
        wc_partial = b""
        timeouts = self.daq_timeout
        while missingLength > 0:
            try:
                wc_partial = sock.recv(missingLength)
            except Exception as xx:
                if str(xx) == "timed out":
                    logging.info(
                        "%s: timed out (%d left) last=%r full=%r"
                        % (self.name, timeouts, wc_partial, wc)
                    )
                    timeouts -= 1
                    if timeouts >= 0:
                        continue
                logging.info(
                    "%s: Error reading pixel bytes. Message: %s" % (self.name, str(xx))
                )
                self.status = "ERROR"
                self.armed.clear()
                raise
            if len(wc_partial) == 0:
                logging.error(
                    "%s: recv returns zero length string in getResponse (1)."
                    % (self.name)
                )
                raise socket.error("Invalid response from Netburner.")
            wc += wc_partial
            missingLength -= len(wc)
        length = struct.unpack("i", wc[::-1])[0]
        missingLength = length
        while missingLength > 0:
            responsePiece = sock.recv(missingLength)
            if len(responsePiece) == 0:
                logging.error(
                    "%s: recv returns zero length string in getResponse (2)."
                    % (self.name)
                )
                raise socket.error("Invalid response from Netburner.")
            missingLength -= len(responsePiece)
            response += responsePiece
        # scrub the response
        response.replace(b"\0", b"")
        response = response.decode()
        if self.debug_flag:
            logging.info("%s: Received response: %s" % (self.name, response))
        return response

    def append_response(self, response, msg):
        if msg:
            response += msg + "\n"
            logging.info("%s: %s" % (self.name, msg))
        return response

    def execute_command(self, command):
        """Handle a command line instruction."""
        return_resp = ""
        # DAQ   Get the DAQ status
        if command.upper().startswith("DAQ"):
            status = self.daq_status()
            return_resp = self.append_response(
                return_resp, "DAQ Status: %s" % repr(status)
            )
        # RECEIVER   Get the image receiver status
        elif command.upper().startswith("RECEIVER"):
            status = self.receiver_status()
            return_resp = self.append_response(
                return_resp, "Receiver Status: %s" % repr(status)
            )
        # STOP  (not fully functional)
        elif command.upper().startswith("STOP"):
            try:
                self.abort()
                return_resp = self.append_response(return_resp, "Stop requested")
            except:
                return_resp = self.append_response(return_resp, "Cannot set stop event")
        # DEBUG Set debug_flag on the host/python side
        elif command.upper().startswith("DEBUG"):
            if command.upper().find("OFF") != -1:
                self.clear_debug_flag()
                return_resp = self.append_response(return_resp, "debug_flag cleared")
            else:
                self.set_debug_flag()
                return_resp = self.append_response(return_resp, "debug_flag set")
        # DISCONNECT
        elif command.upper().startswith("DISCONNECT"):
            self.disconnect()
            return_resp = self.append_response(return_resp, "netburner disconnected")
        # EXIT
        elif command.upper().startswith("EXIT"):
            self.exit()
            return_resp = self.append_response(return_resp, "Done")
        # NAME  Set/get the application name
        elif command.upper().startswith("NAME"):
            myTokens = command.split(" ")
            if len(myTokens) > 1:
                return_resp = self.append_response(
                    return_resp,
                    "DAQ Controller name set to %s"
                    % str(self.appname(name=myTokens[1])),
                )
            else:
                return_resp = self.append_response(
                    return_resp, "Current DAQ Controller name: %s" % str(self.appname())
                )
        # FILE  Specify the output file name.
        # expID and name will be appended.
        # fits is the extension
        elif command.upper().startswith("FILE"):
            myTokens = command.split(" ")
            if len(myTokens) > 1:
                return_resp = self.append_response(
                    return_resp,
                    "Image file set to %s" % str(self.filename(fname=myTokens[1])),
                )
            else:
                return_resp = self.append_response(
                    return_resp, "Current image file: %s" % str(self.filename())
                )
        # OUTPUT  Configure which output file (if any) is written
        elif command.upper().startswith("OUTPUT"):
            myTokens = command.split(" ")
            if len(myTokens) > 1:
                if myTokens[1].upper().find("R") != -1:
                    red = True
                else:
                    red = False
                if myTokens[1].upper().find("B") != -1:
                    blue = True
                else:
                    blue = False
                self.output(r=red, b=blue)
            return_resp = self.append_response(
                return_resp,
                "Image files to be written (red, blue): %s" % repr(self.output()),
            )
        # FORMAT  Configure output fits format
        elif command.upper().startswith("FORMAT"):
            myTokens = command.split(" ")
            if len(myTokens) > 1:
                if myTokens[1].upper().find("RAW") != -1:
                    format = "OFF"
                elif myTokens[1].upper().find("OFF") != -1:
                    format = "OFF"
                elif myTokens[1].upper().find("FALSE") != -1:
                    format = "OFF"
                elif myTokens[1].upper().find("BOTH") != -1:
                    format = "BOTH"
                else:
                    format = "ON"
            else:
                format = "ON"
            self.fits_format(f=format)
            return_resp = self.append_response(
                return_resp, "Image fits format set to: %s" % repr(self.fits_format())
            )
        # HEADER  Include additional header words
        elif command.upper().startswith("HEADER"):
            fh = {"OBSERVER": "Klaus", "OBSERVAT": "APO"}
            myTokens = command.split(" ")
            if len(myTokens) > 1 and (
                myTokens[1].upper().find("R") != -1
                or myTokens[1].upper().find("B") != -1
            ):
                self.fits_header(include=True, camera=myTokens[1], header=fh)
                return_resp = self.append_response(
                    return_resp, "Additional fits header keywords will be included."
                )
            else:
                self.fits_header(include=False)
                return_resp = self.append_response(
                    return_resp, "No additional fits header keywords will be included."
                )
        # INIT  Configure CamDAQ for readout
        elif command.upper().startswith("INIT"):
            if command.upper().startswith("INITTEST"):
                myTokens = command.split(" ")
                if len(myTokens) > 1:
                    id = int(myTokens[1])
                    if len(myTokens) > 2:
                        romode = int(myTokens[2])
                    else:
                        romode = 2
                else:
                    id = 1
                    romode = 2
                if not self.camdaq_init_testmode(id, romode):
                    return_resp = self.append_response(
                        return_resp, "ERROR initializing CamDAQ"
                    )
                else:
                    return_resp = self.append_response(
                        return_resp, "CamDAQ initialized for read out (test mode)"
                    )
            else:
                myTokens = command.split(" ")
                if len(myTokens) > 1:
                    id = int(myTokens[1])
                else:
                    id = 1
                if not self.camdaq_init(id):
                    return_resp = self.append_response(
                        return_resp, "ERROR initializing CamDAQ"
                    )
                else:
                    return_resp = self.append_response(
                        return_resp, "CamDAQ initialized for read out"
                    )

        # DIR   Set path for output file
        elif command.upper().startswith("DIRECTORY"):
            myTokens = command.split(" ")
            if len(myTokens) > 1:
                return_resp = self.append_response(
                    return_resp,
                    "Image directory set to %s" % str(self.direct(d=myTokens[1])),
                )
            else:
                return_resp = self.append_response(
                    return_resp, "Current image directory: %s" % str(self.direct())
                )

        # CALLBACK   Set callback function (must be in main namespace)
        elif command.upper().startswith("CALLBACK"):
            myTokens = command.split(" ")
            if len(myTokens) > 1:
                if myTokens[1] != "None":
                    cb = myTokens[1]
                else:
                    cb = "None"
                self.image_complete_callback(callback=cb)
            else:
                if self.image_complete_callback():
                    return_resp = self.append_response(
                        return_resp,
                        "Current callback function: %s"
                        % str(self.image_complete_callback().__name__),
                    )
                else:
                    return_resp = self.append_response(
                        return_resp, "Current callback function: None"
                    )

        # ROTIME  Print last read out time
        elif command.upper().startswith("ROTIME"):
            return_resp = self.append_response(
                return_resp, "Last read out time: %d" % self.readout_time()
            )

        # GETRESPONSE  Force a call to getResonse to reset synchronization
        # elif command.upper().startswith("GETRESPONSE"):
        #     return_resp = self.append_response(
        #         return_resp,
        #         "Get Response: %s" % myBoss.getCommandResponse(myBoss.sock),
        #     )

        # SIMULATOR   turn simulator on or off; return status
        elif command.upper().startswith("SIMULATOR"):
            param = command.upper().partition(" ")[2]
            if param != "":
                self.simulator(param)
            if self.simulator_status:
                return_resp = self.append_response(return_resp, "Simulator is enabled")
            else:
                return_resp = self.append_response(return_resp, "Simulator is disabled")

        # CAMDAQ  Print CamDAQ status (status + x + flags) and errors
        elif command.upper().startswith("CAMDAQ"):
            if command.upper().find("ERROR") != -1:
                return_resp = self.append_response(
                    return_resp,
                    "CAMDAQ Error Status: %s" % repr(self.camdaq_error_status()),
                )
            else:
                return_resp = self.append_response(
                    return_resp, "CAMDAQ Status: %s" % repr(self.camdaq_status())
                )

        # LOOP  Set loop count for wait arm command
        elif command.upper().find("LOOP") != -1:
            count = command.upper().partition(" ")[2]
            if count != "":
                self.loop_count = int(count)
            return_resp = self.append_response(
                return_resp, "Loop Count set to %d" % self.loop_count
            )

        # ARM   Get ready for image data, use receiver thread (arm) or
        #   a direct call (syncarm)
        elif command.upper().find("ARM") != -1 and command.upper().find("FSM") == -1:
            mode = command.upper().partition(" ")[2]  # everything after the first space
            return_resp = self.append_response(return_resp, "Mode: %s" % mode)
            if command.upper().startswith("SYNC"):
                for i in range(self.loop_count):
                    return_resp = self.append_response(
                        return_resp, "Arming CamDAQ %s " % self.appname()
                    )
                    response = self.syncarm(mode)
                    if response == "Done":
                        status = self.receiver_status()
                        return_resp = self.append_response(
                            return_resp,
                            "Image %d with %d pixels complete. "
                            "Read out time %d seconds."
                            % (
                                status["Exposure"],
                                status["Total"],
                                self.readout_time(),
                            ),
                        )
                    else:
                        return_resp = self.append_response(
                            return_resp, "ERROR in syncarm: %s" % response
                        )

            elif command.upper().startswith("WAIT"):
                for i in range(self.loop_count):
                    return_resp = self.append_response(return_resp, "Getting Ready")
                    retcode = self.sendCommand("set exposure on")
                    if retcode < 0:
                        continue  # go to next loop (if any) and try again
                    return_resp = self.append_response(
                        return_resp, "Received Response: %s" % self.getCommandResponse()
                    )
                    return_resp = self.append_response(
                        return_resp, "Arming CamDAQ %s " % self.appname()
                    )
                    response = self.arm(mode)
                    if response.find("ACCEPTED") != -1:
                        while not self.image_complete_event().isSet():
                            time.sleep(1)
                        status = self.receiver_status()
                        return_resp = self.append_response(
                            return_resp,
                            "Image %d with %d pixels complete. "
                            "Read out time %d seconds."
                            % (
                                status["Exposure"],
                                status["Total"],
                                self.readout_time(),
                            ),
                        )
                    else:
                        return_resp = self.append_response(
                            return_resp, "ERROR in waitarm: %s" % response
                        )
                    retcode = self.sendCommand("set exposure off")
                    if retcode < 0:
                        continue  # go to next loop (if any) and try again
                    return_resp = self.append_response(
                        return_resp, "Received Response: %s" % self.getCommandResponse()
                    )
            else:
                return_resp = self.append_response(
                    return_resp, "Arming CamDAQ %s " % self.appname()
                )
                response = self.arm(mode)
                if response.find("ACCEPTED") == -1:
                    return_resp = self.append_response(
                        return_resp, "ERROR in arm: %s" % response
                    )
        else:
            # Send command to netburner
            self.sendCommand(command.upper())
            return_resp = self.append_response(return_resp, self.getCommandResponse())

        return return_resp


def fitsWriter(q):
    logging.warn("starting fitsWriter thread (%d live)" % (threading.active_count()))
    while True:
        item = q.get()
        logging.warn("fitsWriter got: %r" % (item,))
        if not item:
            break

        # I tried forking each write off in its own thread to parallelize two writes at
        # a time, but that actually slows things down. GIL? Dunno.
        # The 2.6 process-forking module appears to work and lets the gzips, etc.
        # run together. But it occasionally hangs.
        #
        # t = multiprocessing.Process(target=writeFITS, args=item)
        # t.daemon = True
        # t.start()

        writeFITS(*item)

    logging.warn("fitsWriter closing down! (%d live)" % (threading.active_count()))


fitsLock = threading.Lock()


def writeSingleFITS(*args):
    """writeFITS wrapper to serialize pyfits.writeto()s --
    they slow down horribly when threaded together.
    """

    with fitsLock:
        writeFITS(*args)


def writeFITS(hdu, directory, filename, cmd, doCompress=False):
    """write an image to FITS. Handles optional compression.

    Args:
        hdu       - a pyfits HDU or HDUList
        filename  - the full filename, not including the path.
        cmd       - a cmd to chat to.
    """

    anyWritten = False
    outName = "XXX-%s" % (filename)
    mjd = os.path.split(directory)[-1]
    try:
        outName = actorcore.utility.fits.writeFits(
            cmd,
            hdu,
            directory,
            filename,
            doCompress=doCompress,
            chmod=0o444,
            checksum=True,
            caller="BOSS",
        )
        anyWritten = True
    except Exception:
        # fits.writefits already logged it.
        # Just move on, as we'll try to write a local unzipped version later.
        pass

    # Per PR #1470, add a line to the $MJD.sha1sum file. Note that we could get
    # the in-memory sha1 by writing the compressed FITS file to a cStringIO object and
    # calling hashlib.sha1(str).hexdigest() on it.
    if anyWritten:
        ret = subprocess.call(
            "cd %s; sha1sum %s >> %s.sha1sum"
            % (os.path.dirname(outName), os.path.basename(outName), mjd),
            shell=True,
        )
        if ret:
            if cmd is not None:
                cmd.warn(
                    'text="FAILED to generate SHA checksum for BOSS file %s. ret=%d"'
                    % (outName, ret)
                )
            else:
                logging.warn(
                    "FAILED to generate SHA checksum for BOSS file %s. ret=%d"
                    % (outName, ret)
                )
        else:
            if cmd is not None:
                cmd.inform('text="wrote sha1sum for %s"' % (outName))

    # JSG: commenting thit for now since it's not clear what's for.
    # localOutName = "XXX-%s" % (filename)
    # try:
    #     # Save the file uncompressed in a local directory. Some external
    #     # process needs to thin this.
    #     localDir = os.path.join("/export/home/boss/data", mjd)
    #     try:
    #         os.mkdir(localDir)
    #     except OSError as e:
    #         if e.strerror == "File exists":
    #             pass
    #         else:
    #             raise
    #     except:
    #         raise

    #     # KH added for none ICC debugging
    #     if not os.path.isdir(localDir):
    #         localDir = ""

    #     localOutName = os.path.join(localDir, filename)

    #     logging.info("Writing local copy %s" % (localOutName))
    #     hdu.writeto(localOutName, checksum=True)
    #     logging.info("wrote local copy %s" % (localOutName))
    #     if cmd is not None:
    #         cmd.inform('text="wrote local copy %s"' % (localOutName))
    #     anyWritten = True
    # except Exception as e:
    #     if cmd is not None:
    #         cmd.warn(
    #             'text="FAILED to write local BOSS file copy %s: %s"' % (localOutName, e)
    #         )
    #     else:
    #         logging.warn(
    #             "FAILED to write local BOSS file copy %s: %s" % (localOutName, e)
    #         )

    if not anyWritten:
        for i in range(10):
            if cmd is not None:
                cmd.warn(
                    'text="FAILED to write _either_ BOSS file for: %s !!!!!!!! '
                    'STOP observing and fix this!!!!"' % (filename)
                )
            else:
                logging.warn(
                    "FAILED to write _either_ BOSS file for: %s !!!!!!!! "
                    "STOP observing and fix this!!!!" % (filename)
                )

    del hdu


# Utility/helper functions


# Get host, port and command information from command line and/or shell variables.
# Will force exit if HOST or PORT are not set.
# A command line command is optional.
def getArguments():
    if len(sys.argv) >= 3:
        HOST = sys.argv[1]
        PORT = int(sys.argv[2])
    else:
        HOST = os.getenv("BOSS_SPECT_IP")
        PORT = os.getenv("BOSS_SPECT_PORT")

    if HOST is None:
        print(
            "Use command line arguments or set BOSS_SPEC1_IP before using this script"
        )
        sys.exit()
    if PORT is None:
        print(
            "Use command line arguments or set BOSS_SPEC1_PORT before using this script"
        )
        sys.exit()

    port = int(PORT)

    #
    # Scan for additional command line argument
    #
    cmd = ""
    if len(sys.argv) > 3:
        for i in range(3, len(sys.argv)):
            if len(cmd) == 0:
                cmd = sys.argv[i].upper()
            else:
                cmd = cmd + " " + sys.argv[i].upper()

    return HOST, port, cmd


def test_callback():
    print("We report the completion of the last image acquisition")


def pixel_test_callback():
    global done_event
    print("In callback setting done event.")
    done_event.set()


########################################################
#
# CLI Client to exercise/test CamDAQ system
#
########################################################


def boss_client():
    global done_event

    # get command line (and environment) arguments
    HOST, port, cmd = getArguments()

    # set logging level
    logging.basicConfig(level=logging.DEBUG)

    # create a boss daq instance, choose sp1
    myBoss = boss_daq(HOST, port, "sp1")

    #  Start of Command Loop
    abortFlag = 0
    while abortFlag == 0:
        command = ""
        if len(cmd) == 0:
            try:
                command = input("Enter command: ")
            except KeyboardInterrupt:
                sys.exit()
        else:
            command = cmd
        if len(command) == 0:
            continue
        # Quit
        if command.upper() == "QUIT":
            abortFlag = 1
            myBoss.disconnect()
            sys.exit()
            break
        if command.upper().find("PTEST") != -1:
            myBoss.simulator("ON")  # execute_command("set simulator on")
            done_event.clear()
            myBoss.direct("/n/des/boss/pixel_test")
            myBoss.execute_command("set expid %s" % str(command.upper().split(" ")[-1]))
            myBoss.fits_format("OFF")
            myBoss.image_complete_callback(callback=pixel_test_callback)
            while 1:
                print("Preparing next exposure")
                done_event.clear()
                myBoss.execute_command("set testmode on")
                myBoss.execute_command("fill value 0")
                myBoss.execute_command("set testmode off")
                myBoss.execute_command("set romode 0")
                myBoss.execute_command("set exposure on")
                myBoss.execute_command("arm")
                print("...waiting")
                done_event.wait(120)
                if not done_event.is_set():
                    print("timeout waiting for done. trying to continue.")
                myBoss.execute_command("set exposure off")
                print("... got done event. Wait 5 seconds")
                time.sleep(5)
        elif command.upper().find("LOOP") != -1:
            pieces = command.upper().split(" ")
            if len(pieces) < 3:
                print("Usage: loop <expid> < count>")
                return
            expid = int(pieces[1])
            count = int(pieces[2])
            myBoss.simulator("ON")  # execute_command("set simulator on")
            myBoss.direct("/n/des/boss/pixel_test")
            myBoss.execute_command("set expid %d" % expid)
            myBoss.execute_command("set romode 0")
            myBoss.execute_command("set exposure on")
            myBoss.execute_command("loop %d" % count)
            myBoss.execute_command("wait arm")
        # RESET Force Netburner reboot and create a new boss_daq instance
        elif command.upper() == "RESET":
            try:
                myBoss.reset()
                time.sleep(5)
                logging.info("Netburner is back from RESET")
            except Exception as msg:
                logging.error("Cannot send RESET command. Message: %s" % str(msg))
        elif command.upper().startswith("READOUT"):
            pieces = command.split()
            try:
                expid = int(pieces[1])
            except:
                expid = None
            myBoss.readout(expid)
            print("Readout of DAQ memory started.")
        elif command.upper() == "REBOOT":
            try:
                remember_name = myBoss.name
                rsock = socket.socket()
                rsock.connect((HOST, port + 2))
                rsock.send(b"RESET")
                rsock.close()
                time.sleep(5)
                del myBoss
                myBoss = boss_daq(HOST, port, remember_name)
                logging.info("%s: We are back from REBOOT" % (myBoss.name))
            except Exception as msg:
                logging.error("Cannot force reboot. Message: %s" % str(msg))
        else:
            try:
                myBoss.execute_command(command)
            except Exception as msg:
                logging.error(
                    "Cannot execute command %s. Message: %s" % (command, str(msg))
                )

        if len(cmd) != 0:
            break  # exit if there was a command line arg.

    # End of while loop
    myBoss.disconnect()


# End of boss_client()

if __name__ == "__main__":
    try:
        boss_client()
    except Exception as x:
        print("Unhandled Exception in boss_client. Message: ", x)
        print("Good Bye.")
