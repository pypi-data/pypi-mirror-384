# vim:set et sw=4 ts=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#
"""
Test sanitisation of --output arg
"""

import os
import pytest

from tartex.tartex import TarTeX
from tartex.utils.tar_utils import TAR_DEFAULT_COMP


@pytest.fixture
def sample_tex(monkeypatch_set_main_file, monkeypatch_mtime):
    # See explanation if conftest.py for monkeypatch
    monkeypatch_mtime("sample.tex")
    monkeypatch_set_main_file("sample.tex")
    return "sample.tex"


def test_output_default(sample_tex):
    """
    Check correct tar suffix set when output arg ext is not specified
    """
    t = TarTeX([sample_tex, "-o", "main"])
    assert t.tar_file_w_ext.name == f"main.tar.{TAR_DEFAULT_COMP}"


def test_output_nontar(sample_tex):
    """
    Check correct tar file name is set when output arg does have an extension
    but not one that matches .tar.?z

    Example: `tartex sample.tex -o main.foo.bar`
             should generate "main.foo.bar.tar.gz", not "main.foo.tar.gz"
    """
    out = "main.foo.bar"
    t = TarTeX([sample_tex, "-o", out])
    assert t.tar_file_w_ext.name == f"{out}.tar.{TAR_DEFAULT_COMP}"


def test_output_gz_eqv(sample_tex):
    """
    Check that the three kinds of output file names lead to same final tar file
    """
    common_opts = [sample_tex, "-o"]
    out = "main"
    t1 = TarTeX([*common_opts, out])
    t2 = TarTeX([*common_opts, out + ".gz"])
    t3 = TarTeX([*common_opts, out + ".tar.gz"])

    assert t1.tar_file_w_ext == t2.tar_file_w_ext
    assert t2.tar_file_w_ext == t3.tar_file_w_ext


def test_tilde_exp(sample_tex):
    """
    Check that '~' specified for output arg expands to user home
    """
    t = TarTeX([sample_tex, "-o", "~/main.tar.xz"])
    assert str(t.tar_file_w_ext) == f"{os.getenv('HOME')}/main.tar.{t.tar_ext}"
