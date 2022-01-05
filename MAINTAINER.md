## Release

### Development

#### Testing
```
# stand alone
PYTHONPATH=$(pwd) py.test -vvs tests

# end2end with a remote repo
PYTHONPATH=$(pwd) S=git@github.com:cav71/pelican-plugins.git/summary py.test -m manual -vvs tests
```

#### Coverage
```
PYTHONPATH=$(pwd) \
    py.test -vvs tests \
        --cov=mono2repo \
        --cov-report=html:build/coverage --cov-report=xml:build/coverage.xml \
        --junitxml=build/junit/junit.xml --html=build/junit/junit.html --self-contained-html
```

#### MyPy
```
PYTHONPATH=$(pwd) \
    mypy mono2repo.py \
        --no-incremental --xslt-html-report build/mypy
```

### Releases

#### Betas
Start a new beta branch:
```
git push origin $(./maintaner/release.py micro mono2repo.py)
```

#### Prod
```
git tag -m release release/A.B.C
```

