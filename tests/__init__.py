# Copyright (c) 2024-2025 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

import unittest
from pathlib import Path
from subprocess import call
from shutil import rmtree

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

class TestIncludeAsm(Case):
    directory = 'include-asm'

    def test_build(self):
        self.assertCodOk("lib1", "package")
        self.assertCodOk("bin", "build", "-a", "aarch64")
        self.assertCodFail("bin", "build", "-a", "x86_64")
        self.assertCodOk("lib2", "package")
        self.assertCodOk("bin", "build", "-a", "x86_64")

class TestSymbolAsm(Case):
    directory = 'symbol-asm'

    def test_build(self):
        self.assertCodOk("include", "package")
        self.assertCodOk("lib1", "package")
        self.assertCodOk("bin", "build", "-a", "aarch64")
        self.assertCodFail("bin", "build", "-a", "x86_64")
        self.assertCodOk("lib2", "package")
        self.assertCodOk("bin", "build", "-a", "x86_64")

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

class TestBuildFlags(Case):
    directory = 'build-flags'

    def test_build(self):
        self.assertCodFail("lib", "build")
        self.assertCodOk("lib", "build", "-p", "debug")
        self.assertCodOk("lib", "build", "-p", "debug_noarch")
        self.assertCodFail("lib", "build", "-p", "debug_arch", "-a", "aarch64")
        self.assertCodOk("lib", "build", "-p", "debug_arch", "-a", "x86_64")

class TestExportFlags(Case):
    directory = 'export-flags'

    def test_build(self):
        self.assertCodOk("lib1", "package")
        self.assertCodOk("lib", "build")
        self.assertCodOk("lib", "install", "lib1")
        self.assertCodFail("lib", "build")

class TestSingleArch(Case):
    directory = 'single-arch'

    def test_build(self):
        self.assertCodOk("lib1", "build") # x86_64
        self.assertCodOk("lib2", "build") # aarch64

class TestMultipleObjects(Case):
    directory = 'multiple-objects'

    def test_build(self):
        self.assertCodOk("lib", "build")

class TestI686Target(Case):
    directory = 'i686-target'

    def test_build(self):
        self.assertCodOk("lib", "build")

class TestLinkerScript(Case):
    directory = 'linker-script'

    def test_build(self):
        self.assertCodOk("bin", "build")
        self.assertCodFail("bin", "build", "-p", "debug")
        self.assertCodFail("bin", "build", "-p", "debug_noarch")
        self.assertCodFail("bin", "build", "-p", "debug_arch", "-a", "aarch64")
        self.assertCodOk("bin", "build", "-p", "debug_arch", "-a", "x86_64")
        self.assertCodOk("lib", "package")
        self.assertCodOk("bin", "install", "lib")
        self.assertCodFail("bin", "build")

class TestAssembly(Case):
    directory = 'assembly'

    def test_build(self):
        self.assertCodOk("bin", "build")

class TestLibProfile(Case):
    directory = 'lib-profile'

    def test_build(self):
        self.assertCodOk("lib", "package")
        self.assertCodFail("lib", "build")
        self.assertCodOk("bin", "build")

class TestObjcopy(Case):
    directory = 'objcopy'

    def test_build(self):
        for path in self.rootdir.glob("bin/.cod/*/bin/oc.bin"):
            path.unlink()
        self.assertCodOk("bin", "build")
        self.assertNotEqual(list(self.rootdir.glob("bin/.cod/*/bin/oc.bin")), [])

class TestObjconv(Case):
    directory = 'objconv'

    def test_build(self):
        self.assertCodOk("lib", "package")
        self.assertCodOk("bin", "build", "-a", "i686")
        self.assertCodOk("bin", "build", "-a", "x86_64")
        with (self.rootdir / "bin/.cod/dev.i686/bin/oc.bin").open("rb") as f:
            bin32 = f.read()
        with (self.rootdir / "bin/.cod/dev.x86_64/bin/oc.bin").open("rb") as f:
            bin64 = f.read()
        self.assertEqual(bin32, bin64)

class TestProjectFlags(Case):
    directory = 'project-flags'

    def test_build(self):
        self.assertCodFail("lib", "build")

class TestProjectLocalRepo(Case):
    directory = 'project-local-repo'

    def test_build(self):
        self.assertCodOk("lib", "package")
        self.assertCodOk("bin", "build")

        rmtree(self.rootdir / "lib" / ".cod")
        rmtree(self.rootdir / "bin" / ".cod")

        self.assertCodOk("bin", "build")
