"""Module containing tests for the abllib.fs module"""

import os
import pathlib

import pytest

from abllib import fs

# pylint: disable=missing-class-docstring

def test_absolute():
    """Ensure that fs.absolute works as expected"""

    assert callable(fs.absolute)
    assert fs.absolute(os.getcwd()) == os.getcwd().replace("c:\\", "C:\\")
    assert fs.absolute("test.txt") == os.path.join(_uppercase_path(os.getcwd()), "test.txt")
    assert fs.absolute("subdir", "another", "test.txt") \
           == os.path.join(_uppercase_path(os.getcwd()), "subdir", "another", "test.txt")
    assert fs.absolute("subdir", pathlib.Path("another"), "test.txt") \
           == os.path.join(_uppercase_path(os.getcwd()), "subdir", "another", "test.txt")
    assert fs.absolute("subdir", "..", "test.txt") == os.path.join(_uppercase_path(os.getcwd()), "test.txt")

    with pytest.raises(TypeError):
        fs.absolute(None)
    with pytest.raises(TypeError):
        fs.absolute(1)
    with pytest.raises(TypeError):
        fs.absolute("one", "two", 3)
    with pytest.raises(ValueError):
        fs.absolute()

def _uppercase_path(path: str) -> str:
    if path.startswith("/"):
        return path

    first = path[0]
    first = first.upper()
    return first + path[1:]

def test_sanitize():
    """Ensure that fs.sanitize works as expected"""

    assert callable(fs.sanitize)
    assert fs.sanitize("title") == "title"
    assert fs.sanitize("myimage.jpeg") == "myimage.jpeg"
    assert fs.sanitize("myfilename.txt") == "myfilename.txt"

    # spaces
    assert fs.sanitize("this is a normal sentence") == "this_is_a_normal_sentence"
    assert fs.sanitize("the sentence ends.") == "the_sentence_ends."

    # punctuation marks
    assert fs.sanitize("This sentence gets converted..txt") == "This_sentence_gets_converted.txt"
    assert fs.sanitize("the sentence ends..txt") == "the_sentence_ends.txt"
    assert fs.sanitize("sure?") == "sure"
    assert fs.sanitize("sure!") == "sure"
    assert fs.sanitize("I'm sure. Are you?") == "Im_sure_Are_you"

    # long sentences
    # pylint: disable-next=line-too-long
    assert fs.sanitize("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus venenatis aliquet turpis, ac laoreet mauris fermentum eu. Suspendisse luctus a ante sit amet vehicula. Vestibulum aliquet non dui at efficitur. Donec fermentum nulla sit amet eros viverra accumsan. Sed et tortor sit amet diam tempor condimentum sed ut erat. Curabitur cursus dignissim tincidunt.") == "Lorem_ipsum_dolor_sit_amet_consectetur_adipiscing_elit_Vivamus_venenatis_aliquet_turpis_ac_laoreet_mauris_fermentum_eu_Suspendisse_luctus_a_ante_sit_amet_vehicula_Vestibulum_aliquet_non_dui_at_efficitur_Donec_fermentum_nulla_sit_amet_eros_viverra_accumsan_Sed_et_tortor_sit_amet_diam_tempor_condimentum_sed_ut_erat_Curabitur_cursus_dignissim_tincidunt."

    # newlines
    assert fs.sanitize("first line\nnext line") == "first_line_next_line"
    assert fs.sanitize("first line \nnext line") == "first_line_next_line"

    # special characters
    assert fs.sanitize("special' char/act\\ers ar|e i*gnor;ed") == "special_char_act_ers_ar_e_ignor_ed"

    # german Umlaute
    assert fs.sanitize("Äpfel") == "Apfel"
    assert fs.sanitize("Die grüne Böschung") == "Die_grune_Boschung"
    assert fs.sanitize("Straße") == "Strasse"

    # japanese characters
    assert fs.sanitize("ハウルの動く城") == "hauru_no_ugoku_shiro"
    assert fs.sanitize("葬送のフリーレン      ") == "sousou_no_furiiren"
    assert fs.sanitize("こんにちは World!") == "konnichiha_World"
    assert fs.sanitize("Hello 世界!") == "Hello_sekai"

    # pykakasi is optional
    mod = fs.filename.pykakasi
    fs.filename.pykakasi = None
    assert fs.sanitize("ハウルの動く城") == ""
    assert fs.sanitize("葬送のフリーレン      ") == ""
    assert fs.sanitize("こんにちは World!") == "_World"
    assert fs.sanitize("Hello 世界!") == "Hello_"
    fs.filename.pykakasi = mod

    # mixed sentences
    assert fs.sanitize("最初の文。The second sentence.") == "saisho_no_bun_The_second_sentence."
    assert fs.sanitize("最初の文。The second sentence..txt") == "saisho_no_bun_The_second_sentence.txt"
