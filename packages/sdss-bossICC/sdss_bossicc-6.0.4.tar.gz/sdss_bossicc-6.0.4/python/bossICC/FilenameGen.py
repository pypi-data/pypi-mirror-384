import os.path
import threading
import time

import opscore.RO.Astro.Tm.MJDFromPyTuple as astroMJD


class FilenameGen(object):
    def __init__(self, rootDir, seqnoFile, filePrefix="test", namesFunc=None):
        """ """

        self.rootDir = rootDir
        self.seqnoFile = seqnoFile
        self.filePrefix = filePrefix
        self.namesFunc = namesFunc if namesFunc else self.defaultNamesFunc

        self.simRoot = None
        self.simSeqno = None

        self.seqnoFileLock = threading.Lock()

    def setup(self, rootDir=None, seqnoFile=None, seqno=1):
        """If necessary, create directories and sequence files."""

        if not rootDir:
            rootDir = self.rootDir
        if not seqnoFile:
            seqnoFile = self.seqnoFile

        if not os.path.isdir(rootDir):
            os.makedirs(rootDir)

        if not os.access(seqnoFile, os.F_OK):
            seqFile = open(seqnoFile, "w")
            seqFile.write("%d\n" % (seqno))

    def defaultNamesFunc(self, rootDir, seqno):
        """Returns a list of filenames."""
        filename = os.path.join(rootDir, "%s-%04d.fits" % (self.filePrefix, seqno))
        return (filename,)

    def genFilename(self, root, seqno):
        filename = os.path.join(root, "%s-%04d.fits" % (self.filePrefix, seqno))
        return filename

    def consumeNextSeqno(self):
        """Return the next free sequence number."""

        with self.seqnoFileLock:
            try:
                sf = open(self.seqnoFile, "r")
                seq = sf.readline()
                seq = seq.strip()
                seqno = int(seq)
            except Exception as e:
                raise RuntimeError(
                    "could not read sequence integer from %s: %s" % (self.seqnoFile, e)
                )

            nextSeqno = seqno + 1
            try:
                sf = open(self.seqnoFile, "w")
                sf.write("%d\n" % (nextSeqno))
                sf.truncate()
                sf.close()
            except Exception as e:
                raise RuntimeError(
                    "could not WRITE sequence integer to %s: %s" % (self.seqnoFile, e)
                )

        return nextSeqno

    def dirname(self):
        """Return the next directory to use."""

        mjd = astroMJD.mjdFromPyTuple(time.gmtime())
        fmjd = str(int(mjd + 0.3))

        dataDir = os.path.join(self.rootDir, fmjd)
        if not os.path.isdir(dataDir):
            # cmd.respond('text="creating new directory %s"' % (dataDir))
            os.mkdir(dataDir, 0o0755)

        return dataDir

    def genNextRealPath(self, cmd):
        """Return the next filename to use."""

        dataDir = self.dirname()
        seqno = self.consumeNextSeqno()
        imgFiles = self.namesFunc(dataDir, seqno)

        return imgFiles

    def genNextSimPath(self, cmd):
        """Return the next filename to use."""

        filenames = self.namesFunc(self.simRoot, self.simSeqno)
        self.simSeqno += 1

        return filenames if os.path.isfile(filenames[0]) else None

    def getNextPath(self, cmd):
        if self.simRoot:
            return self.genNextSimPath(cmd)
        else:
            return self.genNextRealPath(cmd)


def test1():
    gen = FilenameGen("/tmp", "testSeq")
    gen.setup()
