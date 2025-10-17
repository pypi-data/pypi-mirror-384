import importlib

from bossICC.Controllers import DAQController


importlib.reload(DAQController)


def sp1daq(icc, name):
    return DAQController.DAQController(icc, name, 1)
