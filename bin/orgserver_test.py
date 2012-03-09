import orgserver
from mathdict import *

def test_task():
    t1			= org-server.task( "TODO", "Project burndown <2012-03-02 Fri>",
                                           [("Effort", "22:00"), ("CLOCKSUM", "24:00")] )
