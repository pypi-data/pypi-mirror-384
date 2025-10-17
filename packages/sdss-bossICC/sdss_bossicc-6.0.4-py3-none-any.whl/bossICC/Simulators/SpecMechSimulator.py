import sys
from threading import Timer
from time import time

from twisted.internet import protocol, reactor
from twisted.protocols import basic


def shut_left():
    SpecMechSimulator.shutters["l"] = False


def shut_right():
    SpecMechSimulator.shutters["r"] = False


def shut_main():
    SpecMechSimulator.shutters["s"] = False


def end_exposure():
    shut_main()
    shut_right()
    shut_left()


class SpecMechProtocol(basic.LineReceiver):
    def lineReceived(self, line):
        try:
            self.doCmd(line)
        except:
            print(sys.exc_info())
            self.transport.write(b"Failed {Could not parse command.}\r\n")
            self.transport.write(b"OK\r\x00\n")

    def doCmd(self, line):
        global shut_right, shut_left, shut_main
        if len(line) == 0:
            return
        print(line)
        self.transport.write(line + b"\r\n")
        if line[0] == b"?":
            self.transport.write(b"""""")
        elif line[0] == b"A":
            self.factory.exposuretime = int(line[1])
        elif line[0] == b"c":
            if line[1] == b"b":
                self.factory.shutters["s"] = True
                self.factory.shutters["l"] = True
            elif line[1] == b"l":
                self.factory.shutters["l"] = False
                self.factory.shutters["r"] = True
            elif line[1] == b"r":
                self.factory.shutters["r"] = False
                self.factory.shutters["l"] = True
            else:
                self.factory.shutters[line[1]] = False
        elif line[0] == b"l":
            self.factory.left_screen = True
            Timer(int(line[1]), shut_left).start()
        elif line[0] == b"m":
            self.factory.motors[line[1]] += int(line[2:])
        elif line[0] == b"o":
            if line[1] == b"b":
                self.factory.shutters["s"] = True
                self.factory.shutters["l"] = True
            elif line[1] == b"l":
                self.factory.shutters["l"] = True
                self.factory.shutters["r"] = False
            elif line[1] == b"r":
                self.factory.shutters["r"] = True
                self.factory.shutters["l"] = False
            else:
                self.factory.shutters[line[1]] = True
        elif line[0] == b"P":
            if not self.factory.exposing:
                self.transport.write(b"Failed {No exposure.}\r\n")
            else:
                self.factory.paused = True
                self.factory.shutters["s"] = False
                self.factory.exposing = False
        elif line[0] == b"p":
            self.factory.piston += int(line[1:])
        elif line[0] == b"R":
            if not self.factory.paused:
                self.transport.write(b"Failed {Exposure not paused.}\r\n")
            else:
                self.factory.shutters["s"] = True
                self.factory.exposing = True
        elif line[0] == b"r":
            self.factory.shutters["r"] = True
            Timer(int(line[1]), shut_right).start()
        elif line[0] == b"S":
            for s in list(self.factory.shutters.keys()):
                self.factory.shutters[s] = False
            self.factory.last_exp_time = time.time() - self.factory.exposure_start
        elif line[0:2] == b"sa":
            status = b"""Version 3.0.1\r\nBootAcknowledged Yes\r\nSpectroID 1\r\nSlitID 38\r\nAir On\r\nExpState Idle\r\nShutter Closed\r\nHartmann Closed Closed\r\nDesiredExpTime 30.00\r\nRemainingExpTime 0.00\r\nLastExpTime 30.84\r\nShutterOpenTransit .72\r\nShutterCloseTransit .57\r\nMotorInitialized TRUE TRUE TRUE\r\nMotorStatus 133 133 133\r\nMotorMeasPos 32933 33469 33466\r\nHumidHartmann 10.3 0x\r\nHumidCenOptics 9.3 0x\r\nTempMedian 7.3\r\nTempHartmannTop 8.1 (0x)\r\nTempRedCamBot 7.1 (0x)\r\nTempRedCamTop 7.4 (0x)\r\nTempBlueCamBot 7.3 (0x)\r\nTempBlueCamTop 7.0 (0x)\r\nAD 1837 1294\r\n"""  # noqa
            self.transport.write(status)
        elif line[0] == b"z":
            for m in list(self.factory.motors.keys()):
                self.factory.motors[m] = 0
        elif line[0] == b"e":
            if self.factory.exposing:
                self.transport.write(b"Failed {Already exposing.}\r\n")
            else:
                for s in list(self.factory.shutters.keys()):
                    self.factory.shutters[s] = True
                self.factory.exposing = True
                self.factory.exp_timer = Timer(int(line[1]), end_exposure)
                self.factory.exp_timer.start()

        else:
            self.transport.write(b"Failed { Unknown Command}\r\n")

        self.transport.write(b"OK\r\x00\n")


class SpecMechSimulator(protocol.ServerFactory):
    protocol = SpecMechProtocol
    exposuretime = 200
    shutters = {}
    shutters["s"] = False
    shutters["l"] = True
    shutters["r"] = False
    motors = {}
    motors["a"] = 0
    motors["b"] = 0
    motors["c"] = 0
    exposing = False
    paused = False
    piston = 0
    last_exp_time = 0
    exposure_start = 0


reactor.listenTCP(int(sys.argv[1]), SpecMechSimulator())
reactor.run()
