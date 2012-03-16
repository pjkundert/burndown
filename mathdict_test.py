import mathdict

def test_inplace():
    md1			= mathdict.mathdict(int)
    md1["a"]            = 1

    md2			= mathdict.mathdict(int)
    md2["b"]            = 2

    md1                += md2

    assert len( md1 ) == 2
    assert md1["a"] == 1
    assert md1["b"] == 2

    md2["c"]		= 99
    md2                *= md1
    assert len( md2 ) == 3
    assert md2["a"] == 0  # key only in md1
    assert md2["b"] == 4  # key in both
    assert md2["c"] == 0  # key only in md2

    # A magical mathdict where every uninitialized value is 2.
    md2                /= mathdict.mathdict( lambda: 2 )
    assert len( md2 ) == 3
    assert md2["a"] == 0
    assert md2["b"] == 2
    assert md2["c"] == 0


def test_timedict():
    assert mathdict.timedict(int)._from_hms( "1:23" ) == 1*60*60 + 23*60
    assert mathdict.timedict(int)._from_hms( "1:23:45" ) == 1*60*60 + 23*60 + 45
    assert abs( mathdict.timedict(float)._from_hms( "1:23:45.678" )
                - ( 1*60*60 + 23*60 + 45.678 )) < .001

    assert mathdict.timedict(int)._from_hms( "876:54:32" ) == 876*60*60 + 54*60 + 32

    try: # MM limited to < 60
        assert mathdict.timedict(int)._from_hms( "1:60:56" ) == 1*60*60 + 60*60 + 56
        assert False
    except AssertionError:
        pass

    try: # SS limited to < 60
        assert mathdict.timedict(int)._from_hms( "1:23:60" ) == 1*60*60 + 23*60 + 60
        assert False
    except AssertionError:
        pass

    # automatic conversion of non-mathdict source dict items
    names		= {
        "one":          "1:00",
        "one-oh-two":	"1:02",
        "one-thirty":   "1:30",
        "two":		"2:00",
        "two-and-a-bit":"2:02:02",
        "neg-ten-ten":	"-10:10",
    }

    times		= mathdict.timedict(int)
    times              += names
    assert times["one-oh-two"] == 1*60*60 + 2*60
    assert times["neg-ten-ten"] == -(10*60*60 + 10*60)

    # Trigger reversion of a timedict (containing seconds) back to
    # plain dict (containing textual times) using the reversed
    # builtin.
    d                   = dict( reversed( times ))
    assert d["one-oh-two"] == "1:02"
    assert d["one-oh-two"] == "1:02"
    assert d["two-and-a-bit"] == "2:02:02"




    timesf		= mathdict.timedict(float)

    timesf             += {"a": "012:34:56.789"}
    timesf             += {"b": "0:00:00.12345"}
    timesf             += {"c": "0:00"}
    timesf             += {"d": "1"}
    timesf             += {"e": "-0:00:00.12345"}
    timesf             += {"f": "-1:10"}
    assert abs( timesf["a"] - (12*60*60 + 34*60 + 56.789) ) < .0001
    assert abs( timesf["e"] - -(0*60*60 + 0*60 + 0.12345) ) < .0001
    assert abs( timesf["f"] - -(1*60*60 + 10*60) ) < .0001

    d			= dict( reversed( timesf ))
    print d["a"]
    assert d["a"] == "12:34:56.789"
    assert d["b"] == "0:00:00.12345"
    assert d["c"] == "0:00"
    assert d["d"] == "1:00"
