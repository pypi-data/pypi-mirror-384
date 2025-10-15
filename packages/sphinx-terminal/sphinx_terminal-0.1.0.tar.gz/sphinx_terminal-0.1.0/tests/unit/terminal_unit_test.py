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

import pytest
from docutils import nodes
from sphinx import addnodes


@pytest.mark.parametrize(
    "fake_terminal_directive",
    [{"options": {"input": "echo 'hello'"}, "content": ["\nhello\n"]}],
    indirect=True,
)
def test_terminal_directive(fake_terminal_directive):
    expected = nodes.container()
    expected["classes"] = "terminal"

    highlight = addnodes.highlightlang()
    highlight["force"] = "False"
    highlight["lang"] = "text"
    highlight["linenothreshold"] = "10000"
    expected.append(highlight)

    input_container = nodes.container()
    input_container["classes"] = "input"

    prompt_container = nodes.container()
    prompt_container["classes"] = "prompt"
    prompt_text = nodes.literal(text="user@host:~$ ")
    prompt_container.append(prompt_text)
    input_container.append(prompt_container)

    command = nodes.literal(text="echo 'hello'")
    command["classes"] = "command"
    input_container.append(command)
    expected.append(input_container)

    output_block = nodes.literal_block(text="\nhello\n")
    output_block["classes"] = "terminal-code"
    output_block["xml:space"] = "preserve"
    expected.append(output_block)

    actual = fake_terminal_directive.run()[0]

    assert str(expected) == str(actual)


@pytest.mark.parametrize(
    "fake_terminal_directive",
    [
        {
            "options": {
                "user": "author",
                "host": "canonical",
                "dir": "~/path",
                "input": "echo 'hello'",
            },
            "content": ["\nhello\n"],
        }
    ],
    indirect=True,
)
def test_terminal_directive_prompt(fake_terminal_directive):
    expected = nodes.container()
    expected["classes"] = "terminal"

    highlight = addnodes.highlightlang()
    highlight["force"] = "False"
    highlight["lang"] = "text"
    highlight["linenothreshold"] = "10000"
    expected.append(highlight)

    input_container = nodes.container()
    input_container["classes"] = "input"

    prompt_container = nodes.container()
    prompt_container["classes"] = "prompt"
    prompt_text = nodes.literal(text="author@canonical:~/path$ ")
    prompt_container.append(prompt_text)
    input_container.append(prompt_container)

    command = nodes.literal(text="echo 'hello'")
    command["classes"] = "command"
    input_container.append(command)
    expected.append(input_container)

    output_block = nodes.literal_block(text="\nhello\n")
    output_block["classes"] = "terminal-code"
    output_block["xml:space"] = "preserve"
    expected.append(output_block)

    actual = fake_terminal_directive.run()[0]

    assert str(expected) == str(actual)


@pytest.mark.parametrize(
    "fake_terminal_directive",
    [
        {
            "options": {
                "copy": None,
                "scroll": None,
                "input": "echo 'hello'",
            },
            "content": ["\nhello\n"],
        }
    ],
    indirect=True,
)
def test_terminal_copy_scroll(fake_terminal_directive):
    expected = nodes.container()
    expected["classes"] = "terminal copybutton scroll"

    highlight = addnodes.highlightlang()
    highlight["force"] = "False"
    highlight["lang"] = "text"
    highlight["linenothreshold"] = "10000"
    expected.append(highlight)

    input_container = nodes.container()
    input_container["classes"] = "input"

    prompt_container = nodes.container()
    prompt_container["classes"] = "prompt"
    prompt_text = nodes.literal(text="user@host:~$ ")
    prompt_container.append(prompt_text)
    input_container.append(prompt_container)

    command = nodes.literal(text="echo 'hello'")
    command["classes"] = "command"
    input_container.append(command)
    expected.append(input_container)

    output_block = nodes.literal_block(text="\nhello\n")
    output_block["classes"] = "terminal-code"
    output_block["xml:space"] = "preserve"
    expected.append(output_block)

    actual = fake_terminal_directive.run()[0]

    assert str(expected) == str(actual)


@pytest.mark.parametrize(
    "fake_terminal_directive",
    [
        {
            "options": {"input": "echo 'hello'", "class": ["test"]},
            "content": ["\nhello\n"],
        }
    ],
    indirect=True,
)
def test_terminal_class_option(fake_terminal_directive):
    expected = nodes.container()
    expected["classes"] = "terminal test"

    highlight = addnodes.highlightlang()
    highlight["force"] = "False"
    highlight["lang"] = "text"
    highlight["linenothreshold"] = "10000"
    expected.append(highlight)

    input_container = nodes.container()
    input_container["classes"] = "input"

    prompt_container = nodes.container()
    prompt_container["classes"] = "prompt"
    prompt_text = nodes.literal(text="user@host:~$ ")
    prompt_container.append(prompt_text)
    input_container.append(prompt_container)

    command = nodes.literal(text="echo 'hello'")
    command["classes"] = "command"
    input_container.append(command)
    expected.append(input_container)

    output_block = nodes.literal_block(text="\nhello\n")
    output_block["classes"] = "terminal-code"
    output_block["xml:space"] = "preserve"
    expected.append(output_block)

    actual = fake_terminal_directive.run()[0]

    assert str(expected) == str(actual)
