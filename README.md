# mono2repo
This script will extract from a monorepo a subtree and it will make it into a separate repo.

```shell
mono2repo https://github.com/getpelican/pelican.git/pelican/themes/notmyidea outputdir
```
This will create outputdir containing the original monorepo checkout and the new project.

(see https://blog.getpelican.com/namespace-plugin-migration.html for more details)
