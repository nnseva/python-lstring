
def load_tests(loader, tests, pattern):
	# Allow running the whole suite via: python -m unittest tests
	return loader.discover(start_dir=__path__[0], pattern=pattern or "test*.py")
