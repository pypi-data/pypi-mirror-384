"""Module containing tests for the abllib.fuzzy module"""

from abllib import fuzzy

# pylint: disable=protected-access, unidiomatic-typecheck

def test_all():
    """Ensure that fuzzy.match_all works at all"""

    target = "fox"
    inputs = ["the slow white rat", "the quick brown fox", "different saying with many words"]

    results = fuzzy.match_all(target, inputs)
    assert len(results) == 1
    assert results[0].value == "the quick brown fox"
    assert results[0].index == 1
    assert results[0].inner_index is None

    target = "the"
    inputs = ["the slow white rat", "the quick brown fox", "different saying with many words"]

    results = fuzzy.match_all(target, inputs)
    assert len(results) == 2
    assert results[0].value == "the slow white rat"
    assert results[0].index == 0
    assert results[0].inner_index is None
    assert results[1].value == "the quick brown fox"
    assert results[1].index == 1
    assert results[1].inner_index is None

def test_all_fuzzy():
    """Ensure that fuzzy.match_all applies fuzzy logic"""

    target = "diferent"
    inputs = ["the slow white rat", "the quick brown fox", "different saying with many words"]

    # pylint: disable-next=use-implicit-booleaness-not-comparison
    assert len(fuzzy.match_all(target, inputs, 0)) == 0
    assert len(fuzzy.match_all(target, inputs, 1)) == 1
    assert len(fuzzy.match_all(target, inputs, 8)) == 1

def test_all_tuple():
    """Ensure that fuzzy.match_all handles tuple candidates correctly"""

    target = "diferent"
    inputs = [
        ("the slow white rat", "this sentence is diferent"),
        ("the quick brown fox", "something else"),
        "different saying with many words"
    ]

    m = fuzzy.match_all(target, inputs)

    # pylint: disable-next=use-implicit-booleaness-not-comparison
    assert len(m) == 2
    assert m[0].value == ("the slow white rat", "this sentence is diferent")
    assert m[1].value == "different saying with many words"

def test_all_matchresult():
    """Ensure that fuzzy.match_all asigns correct values to MatchResult"""

    target = "diferent"
    inputs = [
        ("the slow white rat", "this sentence is diferent"),
        ("the quick brown fox", "something else"),
        "different saying with many words"
    ]

    m = fuzzy.match_all(target, inputs)

    # pylint: disable-next=use-implicit-booleaness-not-comparison
    assert len(m) == 2
    assert m[0].index == 0
    assert m[0].value == ("the slow white rat", "this sentence is diferent")
    assert m[0].inner_index == 1

def test_closest():
    """Ensure that fuzzy.match_closest works at all"""

    target = "fox"
    inputs = ["the slow white rat", "the quick brown fox", "different saying with many words"]

    result = fuzzy.match_closest(target, inputs, 0)
    assert result.value == "the quick brown fox"
    assert result.index == 1
    assert result.inner_index is None

    target = "the"
    inputs = ["the slow white rat", "the quick brown fox", "different saying with many words"]

    result = fuzzy.match_closest(target, inputs, 0)
    assert result.value == "the slow white rat"
    assert result.index == 0
    assert result.inner_index is None

def test_closest_fuzzy():
    """Ensure that fuzzy.match_closest applies fuzzy logic"""

    target = "diferent"
    inputs = ["the slow white rat", "the quick brown fox", "different saying with many words"]

    assert fuzzy.match_closest(target, inputs, 0).value is None
    assert fuzzy.match_closest(target, inputs, 1).value == "different saying with many words"
    assert fuzzy.match_closest(target, inputs, 8).value == "different saying with many words"

    target = "diferent wth wors"
    inputs = ["the slow white rat", "the quick brown fox", "different saying with many words"]

    assert fuzzy.match_closest(target, inputs, 0).value is None
    assert fuzzy.match_closest(target, inputs, 1).value == "different saying with many words"
    assert fuzzy.match_closest(target, inputs, 8).value == "different saying with many words"

def test_closest_tuple():
    """Ensure that fuzzy.match_closest handles candidate tuples correctly"""

    target = "diferent"
    inputs = [
        ("the slow white rat", "this sentence is diferent"),
        ("the quick brown fox", "something else"),
        "different saying with many words"
    ]

    m = fuzzy.match_closest(target, inputs)

    assert m.value == ("the slow white rat", "this sentence is diferent")
    assert m.score == 0.25

def test_closest_matchresult():
    """Ensure that fuzzy.match_closest asigns correct values to MatchResult"""

    target = "diferent"
    inputs = [
        ("the slow white rat", "this sentence is diferent"),
        ("the quick brown fox", "something else"),
        "different saying with many words"
    ]

    m = fuzzy.match_closest(target, inputs)

    # pylint: disable-next=use-implicit-booleaness-not-comparison
    assert m.index == 0
    assert m.value == ("the slow white rat", "this sentence is diferent")
    assert m.inner_index == 1

def test_similarity():
    """Ensure that the similarity calculation works as expected"""

    similarity = fuzzy.similarity
    assert callable(similarity)
    assert type(similarity("test", "test")) == float

    assert similarity("fox", "the quick fox") == 0.33
    assert similarity("foy", "the quick fox") == 0.22

    # ensure single words also work
    assert similarity("fox", "fox") == 1
    assert similarity("dog", "dawg") == 0.5

    # only allow for an edit_distance of up to (len(word) // 3) + 1
    assert similarity("hoy", "the quick fox") == 0.11
    assert similarity("hay", "the quick fox") == 0.0

    assert similarity("sentence sentence",
                      "sentence candidate") == 0.5
    assert similarity("sentence sentence sentence",
                      "sentence candidate candidate") == 0.33
    assert similarity("fox",
                      "the quick fox") == 0.33
    assert similarity("sentence sen ntence",
                      "sentence sentence candidate") == 0.58
    assert similarity("this is a pretty pretty long target",
                      "a long pretty sentence is given as") == 0.57
    assert similarity("this is a pretty pretty long target sentence sentence sentence",
                     "a long pretty sentence is given as a candidate candidate") == 0.5
    assert similarity("first first second",
                      "first secon") == 0.61
    assert similarity("sentene word sentnc",
                      "se sen sent sente sentence") == 0.18

def test_similarity_same_words():
    """Ensure that passing many identical words return the correct score"""

    similarity = fuzzy.similarity
    assert similarity("word word word word word word word",
                      "wor word word word word word word") == 0.97
    assert similarity("word word word word word word word",
                      "word word word wor word word word") == 0.97
    assert similarity("word word word word word word word",
                      "word word word word word wor word") == 0.97
    assert similarity("word word word word word word word",
                      "word word word word word word wor") == 0.97
    assert similarity("word word wor word word word word",
                      "word word word word word word word") == 0.97
    assert similarity("wor word word word word word word",
                      "word word word word word word word") == 0.97
    assert similarity("word word word word word word wor",
                      "word word word word word word word") == 0.97

def test_similarity_swappable():
    """Ensure that swapping the arguments for similarity calculation returns the same score"""

    similarity = fuzzy.similarity
    assert similarity("hoy", "the quick fox") == similarity("the quick fox", "hoy")
    assert similarity("sentence sen ntence", "sentence sentence candidate") \
           == similarity("sentence sentence candidate", "sentence sen ntence")
