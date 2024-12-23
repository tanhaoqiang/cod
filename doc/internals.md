# Internals

## List export symbols in .a archive

.a archive starts with `"!<arch>\n"`

each file inside an archive prepended with ar_hdr

```c
struct ar_hdr
{
  char ar_name[16];		/* Name of this member.  */
  char ar_date[12];		/* File mtime.  */                      
  char ar_uid[6];		/* Owner uid; printed as decimal.  */
  char ar_gid[6];		/* Owner gid; printed as decimal.  */
  char ar_mode[8];		/* File mode, printed as octal.   */
  char ar_size[10];		/* File size, printed as decimal.  */
  char ar_fmag[2];		/* Should contain ARFMAG.  */
};
```

the first file in the archive may be an armap. For example

```
┌─────────┬─────────────────────────────── N: number of symbols
│         │ ┌─────────┬─────────────────── N * offset to ar_hdr
│         │ │         │ ┌───────────────┬─ N * name of symbol (C string)
│         │ │         │ │               │
00 00 00 01 00 00 00 52 68 65 6c 6c 6f 00 
                        h  e  l  l  o
```

## Add package to libsolv repo

the following code would print `[]`

```python
import solv
pool = solv.Pool()
repo = pool.add_repo("repo")

pkg = repo.add_solvable()
pkg.name = 'example'
pkg.evr = "{epoch}:{version}-{release}".format(epoch=0,version="1.0", release="1")

pool.createwhatprovides() # will segfault without this line
jobs = pool.select(pkg.name, solv.Selection.SELECTION_PROVIDES).jobs(solv.Job.SOLVER_INSTALL)
print(jobs)
```

Each package should provide itself

```python
pkg.add_deparray(solv.SOLVABLE_PROVIDES, pool.rel2id(pkg.nameid, pkg.evrid, solv.REL_EQ))
pool.createwhatprovides() # required if new provides added
jobs = pool.select(pkg.name, solv.Selection.SELECTION_PROVIDES).jobs(solv.Job.SOLVER_INSTALL)
print(jobs)
```

## Add filelist to libsolv repo

the following code would print `[]`

```python
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
```

`repodata.internalize()` must be called if new filelist added

```python
repodata.internalize()
pool.addfileprovides()
pool.createwhatprovides()
jobs = pool.select("/usr/include/example.h", solv.Selection.SELECTION_FILELIST).jobs(solv.Job.SOLVER_INSTALL)
print(jobs)
```

## Detect header

https://gcc.gnu.org/onlinedocs/gcc/Preprocessor-Options.html

`-MM` would exclude all found system headers

`-MG` would generate dependency rather than raising an error, if a header file not found.

for example, we have `a.c` and an empty file `b.h`

```c
#include <stdio.h>
#include "b.h"
#include "c.h"

int
main() {
}
```

`gcc -MM -MG a.c` would print

```makefile
a.o: a.c b.h c.h
```

`zig cc` also support these flags.

```makefile
a.o: a.c b.h c.h
```

Unfortunately, `gcc -nostdinc -MM -MG a.c` would complain

```
a.c:1:19: error: no include path in which to search for stdio.h
```

However, `zig cc -MM -MG -target x86_64-freestanding a.c` is fine

```makefile
a.o: a.c stdio.h b.h c.h
```

## Detect undefined symbol

for example, we have `c.c`

```c
void f();

int
main() {
  f();
}
```

`zig cc` would print

```
ld.lld: error: undefined symbol: f
```

undefined symbol `g` in `d.c`

```c
void g();

void
f() {
}

void
h() {
  g();
}
```

undefined symbol `j` in `e.c`

```
void j();

void
i() {
  j();
}
```

create archive file

```
zig cc -c -o d.o d.c
zig cc -c -o e.o e.c
zig ar rcs lib.a d.o e.o
```

`zig cc c.c lib.a` would only print

```
ld.lld: error: undefined symbol: g
```
