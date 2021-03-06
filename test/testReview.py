import sys
import testGrape
import os

if not ".." in sys.path:
    sys.path.insert(0, "..")
from vine import grapeMenu


class TestReview(testGrape.TestGrape):
    def testReview(self):
        os.chdir(self.repo)
        args = ["review", "--test", "--user=user", "--proj=proj1", "--repo=repo1"]
        try:
            ret = grapeMenu.menu().applyMenuChoice("review", args, globalArgs=["-v"])
        except SystemExit:
            self.fail("grape-review failed with output %s" % self.output.getvalue())
        contents = self.output.getvalue()
        self.assertTrue(ret)
