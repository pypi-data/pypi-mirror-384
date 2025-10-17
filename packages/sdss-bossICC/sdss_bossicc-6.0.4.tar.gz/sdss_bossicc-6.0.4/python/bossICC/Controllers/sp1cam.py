import importlib

from bossICC.Controllers import CamController


importlib.reload(CamController)


def sp1cam(icc, name):
    return CamController.CamController(icc, name)
