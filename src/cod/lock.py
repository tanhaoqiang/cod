# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from configparser import RawConfigParser
from contextlib import contextmanager

import solv

from .package import PackageId


def add_package(repo, vendor, pkgid, info):
    pool = repo.pool
    repodata = repo.first_repodata()

    pkgid = PackageId.from_str(pkgid)

    pkg = repo.add_solvable()
    pkg.name = pkgid.name
    pkg.evr = pkgid.evr
    pkg.arch = pkgid.arch
    pkg.vendor = vendor

    selfprovides = pool.rel2id(pkg.nameid, pkg.evrid, solv.REL_EQ)
    pkg.add_deparray(solv.SOLVABLE_PROVIDES, selfprovides)
    selfobsoletes = pool.rel2id(pkg.nameid, pkg.evrid, solv.REL_LT)
    pkg.add_deparray(solv.SOLVABLE_OBSOLETES, selfobsoletes)

    for r in info.get('requires', []):
        req = pool.str2id(r)
        pkg.add_deparray(solv.SOLVABLE_REQUIRES, req)

    for p in info.get('provides', []):
        dep = pool.str2id(p)
        pkg.add_deparray(solv.SOLVABLE_PROVIDES, dep)
        pkg.add_deparray(solv.SOLVABLE_CONFLICTS, dep)


class Lock:

    def __init__(self, path, repos):
        self.path = path
        self.profiles = {}

        self.pool = solv.Pool()
        self.repos = repos
        for name, repo in repos.items():
            self.add_repo(name, repo)

        parser = RawConfigParser(delimiters=('=',))
        try:
            f = path.open()
        except FileNotFoundError:
            pass
        else:
            with f:
                parser.read_file(f)

            for profile_name in parser.sections():
                with self(profile_name, save=False):
                    self._install(parser.items(profile_name))

        self.dirty = False

    def add_repo(self, name, repo):
        r = self.pool.add_repo(f"repo.{name}")
        repodata = r.add_repodata()
        for pkgid in repo:
            info = repo.get_info(pkgid)
            add_package(r, name, pkgid, info)
        repodata.internalize()

    def __getitem__(self, profile_name):
        packages = []
        if profile_name in self.profiles:
            for solvable in self.profiles[profile_name].solvables_iter():
                pkgid = str(PackageId.from_solvable(solvable))
                packages.append((pkgid, solvable.vendor))
        return packages

    @contextmanager
    def __call__(self, profile_name, save=True):
        if profile_name not in self.profiles:
            r = self.pool.add_repo(f"profile.{profile_name}")
            r.add_repodata()
            self.profiles[profile_name] = r

        old = self.pool.installed
        self.pool.installed = self.profiles[profile_name]
        try:
            yield
            if save:
                self.save()
        finally:
            self.pool.installed = old

    def install_provides(self, provides):
        self.pool.addfileprovides()
        self.pool.createwhatprovides()
        jobs = []
        for name in provides:
            jobs += self.pool.select(
                name,
                solv.Selection.SELECTION_PROVIDES).jobs(
                    solv.Job.SOLVER_INSTALL)
        self.install(jobs)

    def install_from_symbols(self, symbols):
        self.pool.addfileprovides()
        self.pool.createwhatprovides()
        jobs = []
        for name in symbols:
            jobs += self.pool.select(
                f"({name})",
                solv.Selection.SELECTION_PROVIDES).jobs(
                    solv.Job.SOLVER_INSTALL)
        self.install(jobs)

    def install_packages(self, packages):
        self.pool.addfileprovides()
        self.pool.createwhatprovides()
        jobs = []
        for name in packages:
            jobs += self.pool.select(
                name,
                solv.Selection.SELECTION_PROVIDES).jobs(
                    solv.Job.SOLVER_INSTALL)
        self.install(jobs)

    def install(self, jobs):
        solver = self.pool.Solver()
        problems = solver.solve(jobs)
        if problems:
            for problem in problems:
                print("Problem %d/%d:" % (problem.id, len(problems)), problem)
            exit(1)

        if solver.alternatives_count() > 0:
            print(f'Alternatives exist:')
            for alt in solver.alternatives():
                print(f" {alt}")
                for i, c in enumerate(alt.choices()):
                    print(f"  {i}: {c}")
            print('Install one of the choices to proceed')
            exit(1)

        trans = solver.transaction()
        if trans.isempty():
            return

        packages = []
        for solvable in trans.steps():
            pkgid = str(PackageId.from_solvable(solvable))
            packages.append((pkgid, solvable.vendor))

        self._install(packages)

    def _install(self, packages):
        for pkgid, name in packages:
            self.repos[name].fetch(pkgid)

        r = self.pool.installed
        for pkgid, name in packages:
            info = self.repos[name].get_info(pkgid)
            add_package(r, name, pkgid, info)
        r.first_repodata().internalize()
        self.dirty = True

    def save(self):
        if not self.dirty:
            return

        profile_names = list(self.profiles)
        profile_names.sort()

        parser = RawConfigParser(delimiters=('=',))

        for profile_name in profile_names:
            parser.add_section(profile_name)
            packages = self[profile_name]
            packages.sort()
            for pkgid, name in packages:
                parser.set(profile_name, pkgid, name)

        with self.path.open("w") as f:
            parser.write(f)

        self.dirty = False
