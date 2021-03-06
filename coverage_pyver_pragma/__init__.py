#!/usr/bin/env python3
#
#  __init__.py
"""
Plugin for `Coverage.py <https://coverage.readthedocs.io/en/coverage-5.3/>`_
to selectively ignore branches depending on the Python version.
"""  # noqa: D400
#
#  Copyright © 2020-2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
import platform
import re
import sys
from typing import TYPE_CHECKING, Any, List, NamedTuple, Pattern, Tuple, Union

# 3rd party
import coverage  # type: ignore

if TYPE_CHECKING:

	# stdlib
	from sys import _version_info as VersionInfo  # pragma: no cover (typing only)

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2020-2021 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.0.6"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = [
		"regex_main",
		"Version",
		"make_regexes",
		"PyVerPragmaPlugin",
		"make_not_exclude_regexs",
		"coverage_init",
		]

regex_main: str = re.compile(r"(?i)#\s*pragma[:\s]?\s*no\s*cover").pattern


class Version(NamedTuple):
	"""
	:class:`~typing.NamedTuple` with the same elements as :py:data:`sys.version_info`.
	"""

	major: int
	minor: int
	micro: int = 0
	releaselevel: str = ''
	serial: str = ''


def make_regexes(
		version_tuple: Union["Version", "VersionInfo", Tuple[int, ...]],
		current_platform: str,
		current_implementation: str,
		) -> List[Pattern]:
	"""
	Generates a list of regular expressions to match all valid ignores for the given Python version.

	:param version_tuple: The Python version.
	:type version_tuple: :class:`~typing.NamedTuple` with the attributes ``major`` and ``minor``
	:param current_platform:
	:param current_implementation:

	:return: List of regular expressions.
	"""

	version_tuple = Version(*version_tuple)

	if version_tuple.major == 3:
		# Python 3.X

		greater_than_versions = [str(x) for x in range(0, version_tuple.minor)]
		greater_equal_versions = [*greater_than_versions, str(version_tuple.minor)]
		less_than_versions = [str(x) for x in range(version_tuple.minor + 1, 10)]
		# Current max Python version is 3.9
		less_equal_versions = [str(version_tuple.minor), *less_than_versions]  # pragma: no cover (!Linux)
		exact_versions = [str(version_tuple.minor)]

		wrong_platforms_string = fr"(?!.*!{current_platform})"  # (?!.*Windows)(?!.*Darwin)
		wrong_implementations_string = fr"(?!.*!{current_implementation})"  # (?!.*Windows)(?!.*Darwin)
		# correct_platforms_string = r"(?=\s*(Linux)?)"

		# Add regular expressions for relevant python versions
		# We do it with re.compile to get the syntax highlighting in PyCharm
		excludes = [
				re.compile(
						fr"{regex_main}\s*\((?=\s*<py3({'|'.join(less_than_versions)})){wrong_platforms_string}{wrong_implementations_string}.*\)"
						),
				re.compile(
						fr"{regex_main}\s*\((?=\s*<=py3({'|'.join(less_equal_versions)})){wrong_platforms_string}{wrong_implementations_string}.*\)"
						),
				re.compile(
						fr"{regex_main}\s*\((?=\s*>py3({'|'.join(greater_than_versions)})){wrong_platforms_string}{wrong_implementations_string}.*\)"
						),
				re.compile(
						fr"{regex_main}\s*\((?=\s*py3({'|'.join(greater_equal_versions)})\+){wrong_platforms_string}{wrong_implementations_string}.*\)"
						),
				re.compile(
						fr"{regex_main}\s*\((?=\s*>=py3({'|'.join(greater_equal_versions)})){wrong_platforms_string}{wrong_implementations_string}.*\)"
						),
				re.compile(
						fr"{regex_main}\s*\((?=\s*py3({'|'.join(exact_versions)})){wrong_platforms_string}{wrong_implementations_string}.*\)"
						),
				re.compile(
						fr"{regex_main}\s*\((?!.*py[0-9]+){wrong_platforms_string}{wrong_implementations_string}.*\)"
						),
				]

		# print(excludes)
		return excludes

	else:
		raise ValueError("Unknown Python version.")


class PyVerPragmaPlugin(coverage.CoveragePlugin):
	"""
	Plugin for `Coverage.py <https://coverage.readthedocs.io/en/coverage-5.3/>`_
	to selectively ignore branches depending on the Python version.
	"""  # noqa: D400

	def configure(self, config: Any) -> None:
		"""
		Configure the plugin.

		:param config:
		"""

		# Coverage.py gives either a Coverage() object, or a CoverageConfig() object.
		if isinstance(config, coverage.Coverage):
			config = config.config  # pragma: no cover

		# Remove standard "pragma: no cover" regex
		if regex_main in config.exclude_list:
			config.exclude_list.remove(regex_main)

		if "pragma: no cover" in config.exclude_list:
			config.exclude_list.remove("pragma: no cover")

		excludes = make_regexes(sys.version_info, platform.system(), platform.python_implementation())
		for exc_pattern in excludes:
			config.exclude_list.append(exc_pattern.pattern)

		# Reinstate the general regex, but making sure it isn't followed by a left bracket.
		config.exclude_list += [
				p.pattern for p in make_not_exclude_regexs(platform.system(), platform.python_implementation())
				]

		# TODO: Python 4.X


def make_not_exclude_regexs(
		current_platform: str,
		current_implementation: str,
		) -> List[Pattern]:
	"""
	Generates a list of regular expressions for lines that should not be excluded.

	:param current_platform:
	:param current_implementation:
	"""

	return [
			re.compile(
					fr"{regex_main} (?!\(.*(.{{0,2}}py3\d(\+)?|!{current_platform}|!{current_implementation}).*\)).*$"
					),
			re.compile(fr"{regex_main}$"),
			]


def coverage_init(reg, options):
	"""
	Initialise the plugin.

	:param reg:
	:param options:
	"""

	reg.add_configurer(PyVerPragmaPlugin())  # pragma: no cover
