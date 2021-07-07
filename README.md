# mono2repo
This module (and script) will create a new stand alone repo out of
monorepo subtree, including all the subtree history and commits.

## Example

### Create a new repo
Create a new repo out of the pelican summary subtree:
```shell
mono2repo init summary-extracted \\
    https://github.com/getpelican/pelican-plugins.git/summary
```

### Update the repo
Update the summary-extracted with the latest summary related changes:
```
mono2repo update summary-extracted
```

(see https://blog.getpelican.com/namespace-plugin-migration.html for more details)
