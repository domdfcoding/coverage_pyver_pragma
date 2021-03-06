# stdlib
import platform
import sys

# this package
from coverage_pyver_pragma import PyVerPragmaPlugin, make_not_exclude_regexs, make_regexes, regex_main


class MockConfig:

	def __init__(self):
		self.exclude_list = [regex_main]


def test_plugin():
	mock_config = MockConfig()
	PyVerPragmaPlugin().configure(mock_config)

	assert mock_config.exclude_list == [
			p.pattern for p in make_regexes(sys.version_info, platform.system(), platform.python_implementation())
			] + [p.pattern for p in make_not_exclude_regexs(platform.system(), platform.python_implementation())]
