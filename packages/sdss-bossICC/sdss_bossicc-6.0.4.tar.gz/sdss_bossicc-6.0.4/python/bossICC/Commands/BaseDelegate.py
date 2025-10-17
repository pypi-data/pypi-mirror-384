class BaseDelegate(object):
    def __init__(self, controllers, cmd, icc):
        self.cmd = cmd
        self.controllers = controllers
        self.icc = icc
        self.success = True
        self.init()

    def init(self):
        pass
