# bossICC

bossICC is the Instrument Control Computer for the BOSS spectrographs. It manages communications between other actors and the BOSS firmware, starting, stopping, and reading out exposures, moving collimators and other spectrograph mechanicals, and monitoring and managing voltages, pressures, and temperatures.

Configuration (e.g. hosts/ports/logging directories) are found in the `python/bossICC/etc/` directory. It should only be run on the `sdss5-boss-icc` virtual machine.

This product also can communicate with the engineering "benchboss" system by running `python python/bossICC/bossICC.py benchboss`.
