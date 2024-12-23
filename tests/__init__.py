import unittest
from pathlib import Path
from subprocess import call

class Case(unittest.TestCase):

    def setUp(self):
        self.rootdir = Path(__file__).parent / self.directory
        for path in self.rootdir.glob("*/.cod/*.cod"):
            path.unlink()

        for path in self.rootdir.glob("*/cod.lock"):
            path.unlink()

    def assertCodOk(self, directory, *args):
        self.assertEqual(0, call(("cod",)+args, cwd=self.rootdir/directory))

    def assertCodFail(self, directory, *args):
        self.assertNotEqual(0, call(("cod",)+args, cwd=self.rootdir/directory))

class TestIncludeDependency(Case):
    directory = 'include-dependency'

    def test_build(self):
        self.assertCodOk("lib", "package")
        self.assertCodOk("bin", "build")

class TestSymbolDependency(Case):
    directory = 'symbol-dependency'

    def test_build(self):
        self.assertCodOk("include", "package")
        self.assertCodFail("bin", "build")
        self.assertCodOk("lib", "package")
        self.assertCodOk("bin", "build")

class TestIncludeTransitive(Case):
    directory = 'include-transitive'

    def test_build(self):
        self.assertCodOk("lib1", "package")
        self.assertCodOk("lib2", "package")
        self.assertCodOk("bin", "build")

class TestSymbolTransitive(Case):
    directory = 'symbol-transitive'

    def test_build(self):
        self.assertCodOk("include", "package")
        self.assertCodOk("lib1", "package")
        self.assertCodOk("lib2", "package")
        self.assertCodOk("bin", "build")

class TestIncludeAlternative(Case):
    directory = 'include-alternative'

    def test_build(self):
        self.assertCodOk("lib1", "package")
        self.assertCodOk("lib2", "package")
        self.assertCodFail("bin", "build")
        self.assertCodOk("bin", "install", "lib1")
        self.assertCodOk("bin", "build")
        self.assertCodFail("bin", "install", "lib2")

class TestSymbolAlternative(Case):
    directory = 'symbol-alternative'

    def test_build(self):
        self.assertCodOk("include", "package")
        self.assertCodOk("lib1", "package")
        self.assertCodOk("lib2", "package")
        self.assertCodFail("bin", "build")
        self.assertCodOk("bin", "install", "lib1")
        self.assertCodOk("bin", "build")
        self.assertCodFail("bin", "install", "lib2")

class TestObsolete(Case):
    directory = 'obsolete'

    def test_build(self):
        self.assertCodOk("lib1", "package")
        self.assertCodOk("lib2", "package")
        self.assertCodOk("bin", "build")
