from os.path import dirname, abspath

endpoint = "annotations/"


def load_tests(loader, tests, pattern):
    return loader.discover(start_dir=dirname(abspath(__file__)), pattern=pattern)
