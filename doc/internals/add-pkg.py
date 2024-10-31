#!/usr/bin/env python3

import solv
pool = solv.Pool()
repo = pool.add_repo("repo")

pkg = repo.add_solvable()
pkg.name = 'example'
pkg.evr = "{epoch}:{version}-{release}".format(epoch=0,version="1.0", release="1")
pkg.arch = 'noarch'

pool.createwhatprovides()
jobs = pool.select(pkg.name, solv.Selection.SELECTION_PROVIDES).jobs(solv.Job.SOLVER_INSTALL)
print(jobs)

pkg.add_deparray(solv.SOLVABLE_PROVIDES, pool.rel2id(pkg.nameid, pkg.evrid, solv.REL_EQ))
pool.createwhatprovides()
jobs = pool.select(pkg.name, solv.Selection.SELECTION_PROVIDES).jobs(solv.Job.SOLVER_INSTALL)
print(jobs)
