import unittest
from test import test_support

import pexpect


class CommandCoverage(unittest.TestCase):
    """Each of the following tests starts a new instance of the shared variable engine."""

    def setUp(self):
        self.boss = pexpect.spawn("telnet localhost 9999")
        self.boss.expect("yourUserNum=[0-9]*")
        self.prompt = ["[0-9]* [0-9] :.*", "[0-9]* [0-9] f.*"]

    def testConnection(self):
        self.boss.send("ping\n")

    def testOpenShutter(self):
        self.boss.send("open_shutter\n")

    def testCloseShutter(self):
        self.boss.send("close_shutter\n")

    def testCloseShutter1(self):
        self.boss.send("close_shutter sp1\n")

    def testCloseShutter2(self):
        self.boss.send("close_shutter sp2\n")

    def testOpenShutter1(self):
        self.boss.send("open_shutter sp1\n")

    def testOpenShutter2(self):
        self.boss.send("open_shutter sp2\n")

    def testOpenLeftScreen(self):
        self.boss.send("open_left_screen\n")

    def testOpenLeftScreen1(self):
        self.boss.send("open_left_screen sp1\n")

    def testOpenLeftScreen2(self):
        self.boss.send("open_left_screen sp2\n")

    def testOpenRightScreen(self):
        self.boss.send("open_right_screen\n")

    def testOpenRightScreen1(self):
        self.boss.send("open_right_screen sp1\n")

    def testOpenRightScreen2(self):
        self.boss.send("open_right_screen sp2\n")

    def tearDown(self):
        def fail():
            self.fail("BOSS returned failed.")

        def not_fail():
            pass

        result = self.boss.expect(self.prompt)
        case = {0: not_fail, 1: fail}[result]()
        self.boss.send("\x1d\x0d")
        self.boss.expect("telnet", timeout=2)
        self.boss.send("q")


def test_main():
    test_support.run_unittest(CommandCoverage)


if __name__ == "__main__":
    test_main()
