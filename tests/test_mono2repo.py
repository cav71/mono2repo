import pytest
import mono2repo


@pytest.mark.parametrize("uri, expected", [
    ("ow", ValueError()),
    ("https://a.domain.org/some/repo.git/adir/asubdir",
        ("https://a.domain.org/some/repo.git", "adir/asubdir",),),
])
def test_split_source(uri, expected):
    if isinstance(expected, Exception):
        pytest.raises(expected.__class__, mono2repo.split_source, uri)
    else:
        found = mono2repo.split_source(uri)
        assert expected == found
