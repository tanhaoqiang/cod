#!/usr/bin/env python3

import solv
pool = solv.Pool()
repo = pool.add_repo("repo")

repodata = repo.add_repodata()
pkg = repo.add_solvable()
pkg.name = 'example'
pkg.evr = "{epoch}:{version}-{release}".format(epoch=0,version="1.0", release="1")
pkg.arch = 'noarch'

dirid = repodata.str2dir("/usr/include")
repodata.add_dirstr(pkg.id, solv.SOLVABLE_FILELIST, dirid, "example.h")
pool.addfileprovides()
pool.createwhatprovides()
jobs = pool.select("/usr/include/example.h", solv.Selection.SELECTION_FILELIST).jobs(solv.Job.SOLVER_INSTALL)
print(jobs)

repodata.internalize()
pool.addfileprovides()
pool.createwhatprovides()
jobs = pool.select("/usr/include/example.h", solv.Selection.SELECTION_FILELIST).jobs(solv.Job.SOLVER_INSTALL)
print(jobs)
