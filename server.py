#!/usr/bin/env python

import SimpleHTTPServer
import SocketServer

port = 8000

class JSONHandler( SimpleHTTPServer.SimpleHTTPRequestHandler ):
    def guess_type(self, path):
        """Anything in the .../api/ returns JSON. """
        print self.path
        if self.path.startswith("/api/"):
            return "application/json";
        return SimpleHTTPServer.SimpleHTTPRequestHandler.guess_type(self, path)
        #return super(JSONHandler, self).guess_type(path)

httpd = SocketServer.TCPServer(("",port), JSONHandler)
httpd.serve_forever()
