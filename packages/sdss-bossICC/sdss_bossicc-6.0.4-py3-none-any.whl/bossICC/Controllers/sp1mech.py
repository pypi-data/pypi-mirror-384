import importlib

from bossICC.Controllers import MechController


importlib.reload(MechController)


def sp1mech(icc, name):
    return MechController.MechController(icc, name)
