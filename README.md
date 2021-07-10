# mono2repo
This module (and related script) creates a new stand alone repo out of
monorepo subtree, including all the subtree history and commits.


## Install

```shell
pip intall mono2repo

(or you can just download the mono2repo.py module)
```

## Example

This is the pelican git source tree:
```shell
https://github.com/getpelican/pelican-plugins.git
   ....
   └ summary/
    ├── Readme.rst
    └── summary.py
```
We want to extract the summary subdir and git log related entries.

### Create a new repo
Create a new repo out of the pelican summary subtree:
```shell
mono2repo init summary-extracted \
    https://github.com/getpelican/pelican-plugins.git/summary
```

### Update the repo
Update the summary-extracted with the latest summary related changes:
```
mono2repo update summary-extracted
```

(see https://blog.getpelican.com/namespace-plugin-migration.html for more details)
