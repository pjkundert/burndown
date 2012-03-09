#!/usr/bin/env python
"""
org-server.py	-- Provide HTTP access to project data in the supplied Git repository

    org-server.py <repo> <project> ...

api/projects

    Returns JSON describing all projects available.

api/data/<project>/<time-style>

   Returns <project> history from the org data in git, with the given time style:

       sprint           Data is aggregated for each sprint elapsed
       elapsed		Data is aggregated for periods of calendar time elapsed
       effort		Data is aggregated for periods of effort time elapsed

"""
import argparse
import cgi
import json
import string
import textwrap
import time

import git		# modules from site-packages

import mathdict		# modules local to project


def project_data( repository, projects ):
    """Given a repo name, return a dict containing a list of
    historical blobs for each project.  If the "master"" commit hasn't
    changed, we can safely return the previously cached data.

    We work back from master, and we must find a non-ambiguous path.
    In each commit, we must find a blob named <project>.org.

    (Initial commit)
    v
    o-----o-----o-----o---------------------------o-----o      OK.
                       \                         /      ^
                        o-----o-----o-----o-----o       |
                                                        master

    (Initial commit)                             (parent)
    v                                              <---
    o-----o-----o-----o-------------o-------------o-----o      BAD; Ambiguous!
                       \                         /      ^
                        o-----o-----o-----o-----o       |
                                                        master


    Collect each "name"-ed project's 'org' file git.Blobs for all of
    its historical commits into:

        project["name"] = [oldest, ..., newest]

    """

    # Obtain read-only access to the Git repo 'master' branch
    repo			= git.Repo( repository )
    assert repo.bare == False
    repo.config_reader()

    master			= repo.heads.master
    commit			= master.commit

    # See if "master" commit has changed; if not, return cached result data
    if project_data.hexsha != commit.hexsha:
        # A new "master" commit; recompute result data
        project_data.hexsha	= commit.hexsha
        project_data.result	= {}

    # See what project entries remain after removing those in cache
    remains			= set( projects ) - set( project_data.result.keys() )
    if not remains:
        return project_data.hexsha, project_data.result

    # Some project data remains to be gleaned.
    while commit:
        #'''
        print "Commit %8.8s by %-20.20s on %s" % (
            commit.hexsha, commit.author, time.strftime( "%Y-%m-%d %H:%M:%S",
                                                         time.localtime( commit.committed_date )))
        print "  %s" % ( commit.message )
        for b in commit.tree.blobs:
            print "  %8.8s: %-20s: %-50.50s" % (
                b.hexsha, b.name, repr( b.data_stream.read( 50 )))
        #'''
        for p in remains:
            try:
                b		= commit.tree/(p + ".org")
            except Exception, e:
                print "No %s.org found in commit %8.8s" %( p, commit.hexsha )
                project_data.hexsha = None	# Invalidate partial result data!
                raise
            project_data.result.setdefault( p, [] ).append( b )

        commit              = commit.parents[0] if commit.parents else None

    '''
    for p, bl in project_data.result.items():
        print "Project %s:" % ( p )
        for b in bl:
            print "  %8.8s: %-20s: %-50.50s" % (
                b.hexsha, b.name, repr( b.data_stream.read( 50 )))
    '''
    return project_data.hexsha, project_data.result

# Initial cache for project_data function
project_data.hexsha		= None
project_data.result		= None


def project_data_parse( data, project, style ):
    """Return the parse org-mode project statistics data for one
    project, from the supplied data.

    Searches each blob for an org-mode table like:

    #+BEGIN: columnview :hlines 1 :id local
    | Task                                                   | Effort | CLOCKSUM |
    |--------------------------------------------------------+--------+----------|
    | * TODO Project burndown <2012-03-02 Fri>               |  22:00 |    22:00 |
    | ** DONE Display bar chart for different periods        |   2:00 |     4:00 |
    | ** NEXT Split Bar display                              |   1:00 |     6:00 |
    | ** NEXT Horizontal/Vertical Grid Lines                 |   1:00 |          |
    | ** TODO Define JSON format                             |   2:00 |          |
    | ** TODO Create org-mode/git web service                |  16:00 |    11:00 |
    | *** DONE Load Git repo                                 |   4:00 |     4:00 |
    | *** TODO Parse org-mode data                           |   4:00 |          |
    | *** DONE Create Python web server                      |   8:00 |     7:00 |
    #+END:

    From this we harvest the aggregate data, and track the
    state-changes of tasks.  We'll create a tree of task objects,
    containing roll-up statistics of all of the sub-tasks in each
    state.
    """
    class task( object ):
        def __init__( self, state, name, effort, clocksum ):
            self.subtask	= []
            self.state		= state
            self.name		= name
            self.seconds	= timedict

        def append( self, child ):
            self.subtask.append( child )

        def totals( self ):
            result		= collections.defaultdict(int)

            # Add all the subtask's results, into per-state buckets
            for s in self.subtask:
                for k, v in s.totals().items():
                    result[k]  += v

            # We now have the totals for all children.  If our own
            # totals differ from the sum of all our subtasks, they
            # must be greater -- this means that this roll-up task has
            # also accrued additional individual effort and/or
            # clocksum.  Add that, too.
            if self.

            return result

    results			= {}

    results["project"]		= project
    results["style"]		= style
    for blob in data[project]:
        tbl			=
    # WORKING HERE
    return results

def deduce_encoding( available, environ, accept=None ):
    """Deduce acceptable encoding from HTTP Accept: header:

        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8

    If it remains None (or the supplied one is unrecognized), the
    caller should fail to produce the desired content, and return an
    HTML status code 406 Not Acceptable.

    If no Accept: encoding is supplied in the environ, the default
    (first) encoding in order is used.

    We don't test a supplied 'accept' encoding against the HTTP_ACCEPT
    settings, because certain URLs have a fixed encoding.  For
    example, /some/url/blah.json always wants to return
    "application/json", regardless of whether the browser's Accept:
    header indicates it is acceptable.  We *do* however test the
    supplied 'accept' encoding against the 'available' encodings,
    because these are the only ones known to the caller.

    Otherwise, return the first acceptable encoding in 'available'.

    """
    if accept:
        # A desired encoding; make sure it is available
        accept		= accept.lower()
        if accept not in available:
            accept	= None
        return accept

    # No predefined accept encoding; deduce preferred available one.
    # Accept: may contain */*, */json, etc.  If multiple matches,
    # select the one with the highest Accept: quality value (our
    # present None starts with a quality metric of 0.0).  Test
    # available: ["application/json", "text/html"], vs. HTTP_ACCEPT
    # "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    # Since earlier matches are the for more preferred encodings,
    # later matches must *exceed* the quality metric of the earlier.
    HTTP_ACCEPT		= environ.get( "HTTP_ACCEPT", "*/*" ).lower() if environ else "*/*"
    quality		= 0.0
    for stanza in HTTP_ACCEPT.split( ',' ):
        # application/xml;q=0.9
        q		= 1.0
        for encoding in reversed( stanza.split( ';' )):
            if encoding.startswith( "q=" ):
                q	= float( encoding[2:] )
        for avail in available:
            match	= True
            for a, t in zip( avail.split( '/' ), encoding.split( '/' )):
                if a != t and t != '*':
                    match = False
            if match:
                print "Found %16s == %-16s;q=%.1f %s %-16s;q=%.1f" % (
                    avail, encoding, q,
                    '> ' if q > quality else '<=',
                    accept, quality )
                if q > quality:
                    quality	= q
                    accept	= avail
    return accept

def data_parse_stats( proj, data ):
    return {"hi": "there"}

def http_exception( framework, status, message ):
    """Return an exception appropriate for the given web framework,
    encoding the HTTP status code and message provided.
    """
    if framework and framework.__name__ == "web":
        if status == 404:
            return framework.NotFound( message )

        if status == 406:
            class NotAcceptable( framework.NotAcceptable ):
                def __init__(self, message):
                    self.message = '; '.join( [self.message, message] )
                    framework.NotAcceptable.__init__(self)
            return NotAcceptable( message )

    elif framework and framework.__name__ == "itty":
        if status == 404:
            return framework.NotFound( message )

        if status == 406:
            class NotAcceptable( itty.RequestError ):
                status  = 406
            return NotAcceptable( message )

    return Exception( "%d %s" % ( status, message ))


def projects_request( repository, project,
                      queries=None, environ=None, accept=None,
                      framework=None ):
    """Render a projects requests in the accepted form.  If an accept
    encoding is supplied, us it.  Otherwise, detect it from the
    environ's' "HTTP_ACCEPT"; default to "text/html".

        repository	-- A Git repository path
        project		-- A list of 1 or more project names
        queries		-- URL query options dictionary (or None)
        environ		-- HTTP request environment (headers)
        accept		-- A forced MIME encoding (eg. application/json).
        framework	-- The web framework module being used
    """
    accept		= deduce_encoding( [ "application/json", "text/html" ],
                                           environ=environ, accept=accept )

    hexsha, data	= project_data( repository, project )
    # TODO: Deduce available graph styles from data (eg. see if sprint specified)
    styles		= [ "sprint", "elapsed", "effort" ]

    content		= [
        {
            "project":	name,
            "styles":	styles,
        }
        for name in data.keys()
    ]

    if accept == "application/json":
        # JSON
        response		= json.dumps( content, indent=4 )

    elif accept == "text/html":
        # HTML5.  Yes, this minimal markup is cross-browser standards
        # compliant (including the unquoted attributes!)
        html			= """\
                                  <!doctype html>
                                  <meta charset=utf-8>
                                  <title>%(title)s</title>""" % {
                                      "title":	"Projects",
                                  }
        # Dump any request query options
        if queries:
            html               += """
                                  <pre>"""
            for query, value in queries.items():
                html           += """
                                    %(query)-16.16s %(value)s""" % {
                                      "query":	str( query ) + ":",
                                      "value":	value
                                  }
            html               += """
                                  </pre>"""

        # And display the available projects, and styles with URLs
        # linking to project data
        for proj in content:
            html               += """
                                  <div class=project>%(project)s:""" % proj
            for style in proj["styles"]:
                one		= {
                    "project":	proj["project"],
                    "style":	style,
                }
                one["url"]	= cgi.escape( "/api/data/%(project)s/%(style)s" % one,
                                              quote=True )
                html           += """
                                    <div class=projectlink><a href="%(url)s">%(style)s</a></div>""" % one

        response	= textwrap.dedent( html )

    else:
        # Invalid encoding requested.  Return appropriate 406 Not Acceptable
        message		=  "Invalid encoding: %s, for Accept: %s" % (
            accept, environ.get( "HTTP_ACCEPT", "*.*" ))
        raise http_exception( framework, 406, message )

    # Return the content-type we've agreed to produce, and the result.
    return accept, response


def data_request( repository, project, path,
                  queries=None, environ=None, accept=None,
                  framework=None ):
    """Return the project data specified by path:

           <project>[/<style>]

    We'll parse the historical org-mode data, and cache it based on the
    """
    accept		= deduce_encoding( [ "application/json", "text/html" ],
                                           environ=environ, accept=accept )

    # Confirm that project name and (optional) style are valid.
    # Default to "effort" style, because it gives us the best
    # information: based on the actual amount of effort applied, what
    # is the remaining effort that will be required to complete the
    # project.
    proj, style		= None, None
    hexsha, data	= None, None
    try:
        terms		= path.split( "/" )
        assert 1 <= len( terms ) <= 2
        proj		= terms[0]

        try:
            hexsha, data	= project_data( repository, [ proj ])
        except Exception, e:
            raise http_exception( framework, 500,
                                  "Project data bad: %s" % ( e.message ))
        if proj not in data.keys():
            raise http_exception( framework, 404, "Unknown project: %s" % ( proj ))
        if len( terms ) > 1:
            style	= terms[1]
            if style not in [ "sprint", "elapsed", "effort" ]:
                raise Exception( "Unknown style for project '%s': %s" % ( proj, style ))
        else:
            style	= "effort"
    except Exception, e:
        # Invalid project/style requested.  Return 404 Not Found
        raise http_exception( framework, 404, e.message )

    # hexsha updated, data[proj] available.  Check that our cached
    # data still valid and/or exists, and collect if not.
    if data_request.hexsha != hexsha:
        data_request_hexsha	= hexsha
        data_request.cache	= {}
    stats		= data_request.cache.get( proj, None )
    if not stats:
        stats           = project_data_parse( data, proj )
        data_request.cache[proj]= stats

    response		= None
    if accept == "application/json":
        response	= json.dumps( stats )

    elif accept == "text/html":
        pass

    else:
        # Invalid encoding requested.  Return appropriate 406 Not Acceptable
        message		=  "Invalid encoding: %s, for Accept: %s" % (
            accept, environ.get( "HTTP_ACCEPT", "*.*" ))
        raise http_exception( framework, 406, message )

    return accept, response

# Initial cache for data_request function
data_request.hexsha	= None
data_request.cache	= None

if __name__ == "__main__":

    # Parse args
    parser			= argparse.ArgumentParser(
        description = "Provide HTTP access to project data in the supplied Git repository",
        epilog = "" )

    parser.add_argument( '-s', '--server',
                         default="web.py", help="Webserver framework to use (web.py, itty)" )
    parser.add_argument( '-a', '--address',
                         default="0.0.0.0", help="Default interface[:port] to bind to (default: all, port 80)")
    parser.add_argument( 'repository', nargs=1 )
    parser.add_argument( 'project', nargs="+" )
    args			= parser.parse_args()

    # Deduce interface:port to bind, and correct types
    address			= args.address.split(':')
    assert 1 <= len( address ) <= 2
    address			= ( str( address[0] ),
                                    int( address[1] ) if len( address ) > 1 else 80 )

    # Implement the various Web Servers
    if args.server == "web.py":
        """The web.py webserver.

        When invoked using:

            curl -vo - --header "Accept: application/json" http://localhost:8080/api/projects.json?foo=bar

        the web.ctx available to the handler class' GET method looks
        like this:

        <ThreadedDict {
            'status':           '200 OK',
            'realhome':         u'http://localhost:8080',
            'homedomain':	u'http://localhost:8080',
            'protocol':         u'http',
            'app_stack':        [<web.application.application instance at 0x1015806c8>],
            'ip':               u'127.0.0.1',
            'fullpath':         u'/api/projects.json?foo=bar',
            'headers':          [],
            'host':             u'localhost:8080',
            # ('env' duplicates 'environ' dict)
            'environ': {
                'ACTUAL_SERVER_PROTOCOL': 'HTTP/1.1',
                'HTTP_ACCEPT':          'application/json',
                'HTTP_HOST':            'localhost:8080',
                'HTTP_USER_AGENT':      'curl/7.21.4 (universal-apple-darwin11.0) libcurl/7.21.4 OpenSSL/0.9.8r zlib/1.2.5',
                'PATH_INFO':            '/api/projects.json',
                'QUERY_STRING':         'foo=bar',
                'REMOTE_ADDR':		'127.0.0.1',
                'REMOTE_PORT':          '64328',
                'REQUEST_METHOD':       'GET',
                'REQUEST_URI':          '/api/projects.json?foo=bar',
                'SCRIPT_NAME':          '',
                'SERVER_NAME':          'localhost',
                'SERVER_PORT':          '8080',
                'SERVER_PROTOCOL':      'HTTP/1.1',
                'SERVER_SOFTWARE':	'CherryPy/3.2.0 Server',
                'wsgi.errors':		<open file '<stderr>', mode 'w' at 0x100f0a270>,
                'wsgi.input':           <web.wsgiserver.KnownLengthRFile object at 0x1015f4450>,
                'wsgi.multiprocess':    False
                'wsgi.multithread':     True,
                'wsgi.run_once':	False,
                'wsgi.url_scheme':       'http',
                'wsgi.version':		(1, 0),
            },
            'home':		u'http://localhost:8080',
            'homepath':         u'',
            'output':           u'',
            'path':		u'/api/projects.json',
            'query':            u'?foo=bar',
            'method':		u'GET'
        }>

        When invoked from Chrome, it is very similar (differences outlined below):

        <ThreadedDict {
            ...
            'environ': {
                ...
                'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'HTTP_ACCEPT_CHARSET': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'HTTP_ACCEPT_ENCODING': 'gzip,deflate,sdch'
                'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.8',
                'HTTP_CACHE_CONTROL': 'max-age=0',
                'HTTP_CONNECTION': 'keep-alive',
                'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
                ...
            },
            ...
        }>

        """

        import web
        urls			= (
            "/api/projects.json",		"projects",
            "/api/projects",			"projects",
            "/api/data/(.*)",			"data",		# Passes remainder as argument
        )

        class projects:
            def GET( self ):
                """Deduce accept encoding from Accept: header, or
                force JSON if .json path was explicitly requested.
                """
                environ		= web.ctx.environ
                queries		= web.input()
                accept		= None
                if environ.get( "PATH_INFO", "" ).endswith( ".json" ):
                    accept	= "application/json"

                # Always returns a content-type and response.  If an
                # exception is raised, it should be an appropriate one
                # from the supplied framework to carry a meaningful
                # HTTP status code.  Otherwise, a generic 500 Server
                # Error will be produced.
                content, response = projects_request( args.repository[0], args.project,
                                                      queries=queries, environ=environ,
                                                      accept=accept, framework=web )
                web.header( "Content-Type", content )
                return response

        class data:
            def GET( self, path ):
                environ		= web.ctx.environ
                queries		= web.input()
                accept		= None
                if path.endswith( ".json" ):
                    accept	= "application/json"
                    path	= path[:-5] # Clip off .json

                content, response = data_request( args.repository[0], args.project, path,
                                                    queries=queries, environ=environ,
                                                    accept=accept, framework=web )
                web.header( "Content-Type", content )
                return response

        # Get the required classes from the local namespace.
        # The iface:port must always passed on argv[1] to use
        # app.run(), so use lower-level interface.
        app			= web.application( urls, locals() )
        web.httpserver.runsimple( app.wsgifunc(), address )

    elif args.server == "itty":
        """The itty webserver is a very small Python native webserver
        that recognizes the "Accept: " header, and allows different
        implementations to be triggered for each "Accept: ...""
        type, for each HTTP URL.

        The request passed to each index function contains the Query
        options, available as a dict from request.<method>
        (eg. request.GET), and the request environment is available in
        request._environ (contains *both* the shell environment, as
        well as the HTTP request environment):
        {
            'Apple_PubSub_Socket_Render': '/tmp/launch-OVKXKk/Render',
            'Apple_Ubiquity_Message':   '/tmp/launch-dbg33P/Apple_Ubiquity_Message',
            'COLUMNS':                  '112',
            'COMMAND_MODE':		'unix2003',
            'COM_GOOGLE_CHROME_FRAMEWORK_SERVICE_PROCESS/USERS/LAVERNE/LIBRARY/APPLICATION_SUPPORT/GOOGLE/CHROME_SOCKET': '/tmp/launch-6Lanzn/ServiceProcessSocket',
            'CONTENT_LENGTH':		'',
            'CONTENT_TYPE':		'text/plain',
            'DISPLAY':			'/tmp/launch-5qBefz/org.x:0',
            'EMACS':                    't',
            'GATEWAY_INTERFACE':        'CGI/1.1',
            'GIT_PS1_SHOWDIRTYSTATE':   '1',
            'GIT_PS1_SHOWUNTRACKEDFILES': '1',
            'GIT_PS1_SHOWUPSTREAM':     'auto',
            'HOME':                     '/Users/laverne',
            'HTTP_ACCEPT':              'application/json',
            'HTTP_HOST':                'localhost:8080',
            'HTTP_USER_AGENT':          'curl/7.21.4 (universal-apple-darwin11.0) libcurl/7.21.4 OpenSSL/0.9.8r zlib/1.2.5',
            'INSIDE_EMACS':             't',
            'ITERM_PROFILE':            'Default',
            'ITERM_SESSION_ID':         'w0t0p0',
            'LANG':                     'en_CA.UTF-8',
            'LOGNAME':                  'laverne',
            'PATH':                     '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/usr/X11/bin:/usr/local/git/bin',
            'PATH_INFO':                '/api/projects.json',
            'PWD':                      '/Users/laverne/src/burndown/bin',
            'PYTHONPATH':               '/usr/local/lib/python2.7/site-packages',
            'QUERY_STRING':             'foo=bar',
            'REMOTE_ADDR':              '127.0.0.1',
            'REMOTE_HOST':              '1.0.0.127.in-addr.arpa',
            'REQUEST_METHOD':           'GET',
            'SCRIPT_NAME':              '',
            'SERVER_NAME':              '1.0.0.127.in-addr.arpa',
            'SERVER_PORT':              '8080',
            'SERVER_PROTOCOL':          'HTTP/1.1',
            'SERVER_SOFTWARE':          'WSGIServer/0.1 Python/2.7.1',
            'SHELL':                    '/bin/bash',
            'SHLVL':                    '2',
            'SSH_AUTH_SOCK':            '/tmp/launch-anCnoA/Listeners',
            'STY':                      '39661.ttys000.macpro',
            'TERM':			'dumb',
            'TERMCAP':                  '',
            'TERM_PROGRAM':             'iTerm.app',
            'TMPDIR':                   '/var/folders/vm/sbw2f_2d3ps_rx7y85pf8rwc0000gn/T/',
            'USER':                     'laverne',
            'VERSIONER_PYTHON_PREFER_32_BIT': 'no',
            'VERSIONER_PYTHON_VERSION': '2.7',
            'WINDOW':                   '0',
            '_':                        '/Users/laverne/src/burndown/bin/org-server.py',
            '__CF_USER_TEXT_ENCODING':	'0x1F5:0:0',
            'wsgi.errors':              <open file '<stderr>', mode 'w' at 0x105f2f270>,
            'wsgi.file_wrapper': <class wsgiref.util.FileWrapper at 0x1064ba050>,
            'wsgi.input': <socket._fileobject object at 0x106488bd0>,
            'wsgi.multiprocess':        False,
            'wsgi.multithread': True,
            'wsgi.run_once': False,
            'wsgi.url_scheme': 'http',
            'wsgi.version': (1, 0),
        }
        """
        import itty

        #     Instead of just returning the response directly and
        # taking the default headers, encode the supplied
        # Content-Type.
        @itty.get( "/api/projects" )
        def index( request ):
            """
            Responds according to content of Accept: header.
            """
            queries		= request.GET
            environ		= request._environ
            content, response	= projects_request( args.repository[0], args.project,
                                                    queries=queries, environ=environ,
                                                    framework=itty )
            return itty.Response( response, headers=[("Content-Type", content)])

        @itty.get( "/api/projects.json" )
        def index( request ):
            """
            Explcit .json; forces JSON, regardless of Accept: header.
            """
            queries		= request.GET
            environ		= request._environ
            content, response	= projects_request( args.repository[0], args.project,
                                                    queries=queries, environ=environ,
                                                    accept="application/json", framework=itty )
            return itty.Response( response, headers=[("Content-Type", content)])

        itty.run_itty( host=address[0], port=address[1] )

    else:
        raise Exception("Unknown Web Server framework: %s" % ( args.server ))