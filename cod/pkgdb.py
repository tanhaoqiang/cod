# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import PurePosixPath
import json
import solv

def add_pkg(repo, path, spec, vendor):
    pool = repo.pool
    repodata = repo.first_repodata()

    pkg = repo.add_solvable()
    pkg.name = spec['name']
    pkg.evr = "{epoch}:{version}-{release}".format(
        epoch=0,version=spec["version"],release="1")
    pkg.arch = 'noarch'
    pkg.vendor = vendor

    selfprovides = pool.rel2id(pkg.nameid, pkg.evrid, solv.REL_EQ)
    pkg.add_deparray(solv.SOLVABLE_PROVIDES, selfprovides)

    for p in spec['provides']:
        dep = pool.str2id(p)
        pkg.add_deparray(solv.SOLVABLE_PROVIDES, dep)
        pkg.add_deparray(solv.SOLVABLE_CONFLICTS, dep)

    repodata.set_location(pkg.id, 0, path.as_posix())

    for name in spec['filelist']:
        dep = pool.str2id(f"<{name}>")
        pkg.add_deparray(solv.SOLVABLE_PROVIDES, dep)
        pkg.add_deparray(solv.SOLVABLE_CONFLICTS, dep)

        path = PurePosixPath('/') / name
        dirid = repodata.str2dir(path.parent.as_posix())
        repodata.add_dirstr(pkg.id, solv.SOLVABLE_FILELIST, dirid, path.name)

class PackageDatabase:

    def __init__(self, path, repos):
        self.pool = solv.Pool()
        self.repos = repos
        for name, p in repos.items():
            self.add_repo(name, p)

        repo = self.pool.add_repo("installed")
        repo.appdata = path
        repodata = repo.add_repodata()

        try:
            f = (path / ".installed").open()
        except FileNotFoundError:
            pass
        else:
            with f:
                installed = json.load(f)

            for name, p in installed:
                with (repos[name] / p).open() as f:
                    spec = json.load(f)
                    add_pkg(repo, PurePosixPath(p), spec, name)

        self.pool.installed = repo
        repodata.internalize()

    def add_repo(self, name, path):
        repo = self.pool.add_repo(name)
        repo.appdata = path
        repodata = repo.add_repodata()
        for name in path.glob("*/build/*.cod"):
            with name.open() as f:
                spec = json.load(f)
                add_pkg(repo, name.relative_to(path), spec, repo.name)
        repodata.internalize()

    def _get_installed(self):
        return [[solvable.vendor,solvable.lookup_location()[0]]
                for solvable in self.pool.installed.solvables_iter()]

    def get_installed(self):
        return [(self.repos[vendor]/path) for vendor, path in self._get_installed()]

    def install_from_filelist(self, filelist):
        self.pool.addfileprovides()
        self.pool.createwhatprovides()
        jobs = []
        for name in filelist:
            # jobs += self.pool.select(
            #     (PurePosixPath('/') / name).as_posix(),
            #     solv.Selection.SELECTION_FILELIST).jobs(
            #         solv.Job.SOLVER_INSTALL)
            jobs += self.pool.select(
                f"<{name}>",
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

        installed = self.pool.installed

        for solvable in trans.steps():
            repo_path = solvable.repo.appdata
            path, _ = solvable.lookup_location()

            with (repo_path / path).open() as f:
                spec = json.load(f)
                add_pkg(installed, PurePosixPath(path), spec, solvable.vendor)

        repodata = installed.first_repodata()
        repodata.internalize()

        installed.appdata.mkdir(exist_ok=True)
        with (installed.appdata / ".installed").open("w") as f:
            json.dump(self._get_installed(), f)
