import importlib.metadata as md
import zz_tools

def test_version_matches_metadata():
    assert zz_tools.__version__ == md.version("zz-tools")
