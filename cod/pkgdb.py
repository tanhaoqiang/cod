# Copyright (c) 2024 tanhaoqiang
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import PurePosixPath
import json
import solv

def add_pkg(repo, spec):
    pool = repo.pool
    repodata = repo.first_repodata()

    pkg = repo.add_solvable()
    pkg.name = spec['name']
    pkg.evr = "{epoch}:{version}-{release}".format(
        epoch=0,version=spec["version"],release="1")
    pkg.arch = 'noarch'

    selfprovides = pool.rel2id(pkg.nameid, pkg.evrid, solv.REL_EQ)
    pkg.add_deparray(solv.SOLVABLE_PROVIDES, selfprovides)

    for p in spec['provides']:
        pkg.add_provides(pool.Dep(p))

    for name in spec['filelist']:
        path = PurePosixPath('/') / name
        dirid = repodata.str2dir(path.parent.as_posix())
        repodata.add_dirstr(pkg.id, solv.SOLVABLE_FILELIST, dirid, path.name)

class PackageDatabase:

    def __init__(self):
        self.pool = solv.Pool()

    def add_repo(self, name, path):
        repo = self.pool.add_repo(name)
        repodata = repo.add_repodata()
        for name in path.glob("*/build/*.cod"):
            with name.open() as f:
                spec = json.load(f)
                add_pkg(repo, spec)
        repodata.internalize()

    def solve_files(self, filelist):
        self.pool.addfileprovides()
        self.pool.createwhatprovides()
        jobs = []
        for name in filelist:
            jobs += self.pool.select(
                (PurePosixPath('/') / name).as_posix(),
                solv.Selection.SELECTION_FILELIST).jobs(
                    solv.Job.SOLVER_INSTALL)

        solver = self.pool.Solver()
        problems = solver.solve(jobs)
        if problems:
            for problem in problems:
                print("Problem %d/%d:" % (problem.id, len(problems)))
                print(problem)
            return

        trans = solver.transaction()
        if trans.isempty():
            print("Nothing to do.")
        else:
            newpkgs = trans.newsolvables()
            print(newpkgs)
