import json
import re
import textwrap

import orgserver
from mathdict import *

def test_best_fit():
    x, y, s			= orgserver.best_fit( [(0,0), (1,1), (2,2)] )
    assert abs( y -  0.0 ) < 0.0001
    assert abs( s -  1.0 ) < 0.0001
    x, y, s			= orgserver.best_fit( [(1,1), (2,2)] )
    assert abs( y -  0.0 ) < 0.0001
    assert abs( s -  1.0 ) < 0.0001
    x, y, s			= orgserver.best_fit( [(0,-1), (1,0), (2,1), (3,2), (4,3)] )
    assert abs( y - -1.0 ) < 0.0001
    assert abs( s -  1.0 ) < 0.0001
    x, y, s			= orgserver.best_fit( [(0,1)] )
    assert str( s ) == "inf"
    assert str( y ) == "nan"


def test_task():
    t1 = orgserver.task( "TODO", "Project burndown <2012-03-02 Fri>",
                         [("Effort", "22:00"), ("CLOCKSUM", "24:00")] )
    print t1.data
    print t1.data
    print dict(reversed( t1.data ))
    print t1.display()

    t1.add( orgserver.task( "DONE", "Display bar chart for different periods",
                            [("Effort", "2:00"), ("CLOCKSUM", "4:00")] ))
    t1.add( orgserver.task( "NEXT", "Split Bar display",
                            [("Effort", "1:00"), ("CLOCKSUM", "6:00")] ))
    t1.add( orgserver.task( "NEXT", "Horizontal/Vertical Grid Lines",
                            [("Effort", "1:00")] ))
    t1.add( orgserver.task( "TODO", "Define JSON format",
                            [("Effort", "2:00" )] ))
    t2 = orgserver.task( "TODO", "Create org-mode/git web service",
                         [("Effort", "16:00"), ("CLOCKSUM", "11:00")] )
    t1.add( t2 )
    t2.add( orgserver.task( "DONE", "Load Git repo",
                            [("Effort", "4:00"), ("CLOCKSUM", "4:00")] ))
    t2.add( orgserver.task( "TODO", "Parse org-mode data",
                            [("Effort", "4:00")] ))
    t2.add( orgserver.task( "DONE", "Create Python web server",
                            [("Effort", "8:00"), ("CLOCKSUM", "7:00")] ))

    print t1.display()


    print json.dumps( t1.totals(), indent=4 )
    #print repr( t1.totals() )

def test_task_parse():


    refirst			= re.compile( r"\s* \| \s* ( \*+ ) \s* ( \w+ )", re.VERBOSE )
    assert refirst.match( "| * TODO" ) != None

    raw				= textwrap.dedent( """\
        #+BEGIN: columnview :hlines 1 :id local
        | Task                                                   | Effort | CLOCKSUM |
        |--------------------------------------------------------+--------+----------|
        | * TODO Project burndown <2012-03-02 Fri>               |  22:00 |    24:00 |
        | ** DONE Display bar chart for different periods        |   2:00 |     4:00 |
        | ** NEXT Split Bar display                              |   1:00 |     6:00 |
        | ** NEXT Horizontal/Vertical Grid Lines                 |   1:00 |          |
        | ** TODO Define JSON format                             |   2:00 |          |
        | ** TODO Create org-mode/git web service                |  16:00 |    11:00 |
        | *** DONE Load Git repo                                 |   4:00 |     4:00 |
        | *** TODO Parse org-mode data                           |   4:00 |          |
        | *** DONE Create Python web server                      |   8:00 |     7:00 |
        #+END:
        """)

    t1				= orgserver.parse_task_heirarchy( iter( raw.split( "\n" )))
    print t1.display()
