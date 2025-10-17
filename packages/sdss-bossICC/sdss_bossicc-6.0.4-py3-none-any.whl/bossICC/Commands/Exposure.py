import logging
import time
from threading import Semaphore


class Exposure(object):
    def __init__(self, icc):
        """The exposure class is a singleton container class that holds
        persistant information regarding the exposure during different
        commands.
        """

        self.icc = icc
        self.state = "IDLE"
        self.totalTime = 0.0
        self.remainingTime = 0.0

        self.ID = 0

        self.lines = 2112
        self.pixels = 2176

        self.timers = []
        self.semaphore = Semaphore()
        self.needsRecovery = False

        self.cmd = self.icc.bcast

    def setState(self, state=None, remainingTime=0.0, totalTime=0.0, cmd=None):
        """A wrapper to set the exposure state and publish it."""

        if not cmd:
            cmd = self.cmd

        if state is not None:
            self.state = state
            self.remainingTime = remainingTime
            self.totalTime = totalTime
            self.endTime = time.time() + remainingTime
        else:
            state = self.state
            totalTime = self.totalTime
            if state == "INTEGRATING" or self.remainingTime > 0:
                remainingTime = self.endTime - time.time()
            else:
                remainingTime = self.remainingTime

        if remainingTime < 0 or remainingTime > totalTime:
            cmd.warn(
                'text="exposureState timer does not add up (remain=%0.2f total=%0.2f)"'
                % (remainingTime, totalTime)
            )
            remainingTime = totalTime

        # Crud. We actually publish elapsed and total.
        elapsedTime = totalTime - remainingTime
        status = "exposureState=%s,%0.1f,%0.1f" % (state, totalTime, elapsedTime)
        logging.info(status)

        cmd.inform(status)
