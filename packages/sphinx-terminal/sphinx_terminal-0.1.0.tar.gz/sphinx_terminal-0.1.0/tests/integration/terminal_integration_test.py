# This file is part of sphinx-terminal.
#
# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3, as published by the Free Software
# Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranties of MERCHANTABILITY, SATISFACTORY
# QUALITY, or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>.

import shutil
import subprocess
from pathlib import Path
from typing import cast

import bs4
import pytest


@pytest.fixture
def example_project(request) -> Path:
    project_root = request.config.rootpath
    example_dir = project_root / "tests/integration/example"

    target_dir = Path().resolve() / "example"
    shutil.copytree(example_dir, target_dir, dirs_exist_ok=True)

    return target_dir


@pytest.mark.slow
def test_hello_integration(example_project):
    build_dir = example_project / "_build"
    subprocess.check_call(
        ["sphinx-build", "-b", "html", "-W", example_project, build_dir],
    )

    index = build_dir / "index.html"

    # Rename the test output to something more meaningful
    shutil.copytree(
        build_dir, build_dir.parents[1] / ".test_output", dirs_exist_ok=True
    )
    soup = bs4.BeautifulSoup(index.read_text(), features="lxml")

    shutil.rmtree(example_project)  # Delete copied source

    # Ensure that the :copy: and :scroll: options are respected
    assert soup.find("div", {"class": "terminal copybutton scroll docutils container"})

    # Ensure that the prompt renders correctly
    prompt_html = soup.find("span", {"class": "pre"})
    assert getattr(prompt_html, "text", "") == "author@canonical:~/path$"

    # Ensure that the input command renders correctly
    input_html = soup.find("code", {"class": "command docutils literal notranslate"})
    if input_html:
        command = cast(bs4.Tag, input_html).find_all("span", {"class": "pre"})
        assert getattr(command[0], "text", "") == "echo"
        assert getattr(command[1], "text", "") == "'hello'"
    else:
        pytest.fail("Input command is not rendered in output.")

    output_html = soup.find(
        "div", {"class": "terminal-code highlight-text notranslate"}
    )
    if output_html:
        output = cast(bs4.Tag, output_html).find_next("pre")
        assert getattr(output, "text", "") == "hello\n"
    else:
        pytest.fail("Command output is not rendered in output.")
