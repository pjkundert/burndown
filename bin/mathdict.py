import collections

class mathdict( collections.defaultdict ):
    """A dictionary type that contains values, and which responds to
    arithmetic operators in a sensible way.  For example, adding two
    mathdict objects together adds together corresponding components;
    any missing components are assigned the default value.
    """
    def __init__( self, default_factory=int ):
        collections.defaultdict.__init__( self, default_factory )

    #
    # self <op>= rhs
    # self <op>  rhs	-- Not Implemented
    # lhs  <op>= self	-- Not Implemented
    #
    # Perform operation, returning self containing result.  Note that
    # any operator that raises an exception (eg. self /= rhs, where
    # rhs contains keys that do not (yet) exist in self), is likely to
    # destroy the consistency of (partially update) self!  Supports:
    #
    #         <mathdict> <op>= ("key", value)
    #         <mathdict> <op>= <matchdict>
    #         <mathdict> <op>= <dict>
    #
    # All operators (not just *= and /=) must produce new rhs items
    # for any keys in self that don't exist in rhs, because we can't
    # assume that the default_factory produces a "zero" value.  We'll
    # do this *first*, because these operations are most likely to be
    # fatal (eg. in /=, producing a ZeroDivision exception), so by
    # performing one first, we won't corrupt self.
    #
    # When accessing a plain dict on the rhs, we iterate over the rhs
    # dict item's tuples, and process them recursively.  This allows a
    # derived class to specially process raw source tuples
    # (eg. specially parsing the value components into appropriate
    # numeric form)

    def __iadd__( self, rhs ):
        """<mathdict> += [<mathdict>, (k,v)]"""
        if isinstance( rhs, tuple ):
            self[rhs[0]]       += rhs[1]
            return self
        elif isinstance( rhs, mathdict ):
            for k in self.keys():
                if k not in rhs:
                    self[k]    += rhs.default_factory()
            for k, v in rhs.iteritems():
                self[k]        += v
            return self
        elif isinstance( rhs, dict ):
            for i in rhs.iteritems():
                self           += i
            return self
        raise NotImplementedError()
    def __add__( self, rhs ):
        """<mathdict> + <mathdict>"""
        if isinstance( rhs, mathdict ):
            res			= self.__class__(self.default_factory)
            res                += self
            res                += rhs
            return res
        raise NotImplementedError()
    def __radd__( self, lhs ):
        """? += <mathdict> -- Not Implemented"""

    def __isub__( self, rhs ):
        """<mathdict> -= [<mathdict>, (k,v)]"""
        if isinstance( rhs, tuple ):
            self[rhs[0]]       -= rhs[1]
            return self
        elif isinstance( rhs, mathdict ):
            for k in self.keys():
                if k not in rhs:
                    self[k]    -= rhs.default_factory()
            for k, v in rhs.iteritems():
                self[k]        -= v
            return self
        elif isinstance( rhs, dict ):
            for i in rhs.iteritems():
                self           -= i
            return self
        raise NotImplementedError()
    def __sub__( self, rhs ):
        """<mathdict> - <mathdict>"""
        if isinstance( rhs, mathdict ):
            res			= self.__class__(self.default_factory)
            res                += self
            res                -= rhs
            return res
        raise NotImplementedError()
    def __rsub__( self, lhs ):
        """? -= <mathdict> -- Not Implemented"""

    def __imul__( self, rhs ):
        """<mathdict> *= [<mathdict>, (k,v)]"""
        if isinstance( rhs, tuple ):
            self[rhs[0]]       *= rhs[1]
            return self
        elif isinstance( rhs, mathdict ):
            for k in self.keys():
                if k not in rhs:
                    self[k]    *= rhs.default_factory()
            for k, v in rhs.iteritems():
                self[k]        *= v
            return self
        elif isinstance( rhs, dict ):
            for i in rhs.iteritems():
                self           *= i
            return self
        raise NotImplementedError()
    def __mul__( self, rhs ):
        """<mathdict> * <mathdict>"""
        if isinstance( rhs, mathdict ):
            res			= self.__class__(self.default_factory)
            res                += self
            res                *= rhs
            return res
        raise NotImplementedError()
    def __rmul__( self, lhs ):
        """? *= <mathdict> -- Not Implemented"""

    def __idiv__( self, rhs ):
        """<mathdict> /= [<mathdict>, (k,v)]"""
        if isinstance( rhs, tuple ):
            self[rhs[0]]       /= rhs[1]
            return self
        elif isinstance( rhs, mathdict ):
            for k in self.keys():
                if k not in rhs:
                    self[k]    /= rhs.default_factory()
            for k, v in rhs.iteritems():
                self[k]        /= v
            return self
        elif isinstance( rhs, dict ):
            for i in rhs.iteritems():
                self           /= i
            return self
        raise NotImplementedError()
    def __mul__( self, rhs ):
        """<mathdict> / <mathdict>"""
        if isinstance( rhs, mathdict ):
            res			= self.__class__(self.default_factory)
            res                += self
            res                /= rhs
            return res
        raise NotImplementedError()
    def __rdiv__( self, lhs ):
        """? /= <mathdict> -- Not Implemented"""


class timedict( mathdict ):
    """Deals in times, in the form:

        ("key", "H[:MM[:SS[.s]]]]")

    and converts these values into seconds, optionally including
    fractional seconds if the underlying mathdict deals in floats.
    Parses:

      H
      H:MM
      H:MM:SS[.s]

    """

    def _from_hms( self, timespec ):
        multiplier		= 60 * 60
        seconds			= 0

        for segment in timespec.split( ":" ):
            assert multiplier >= 1  # If reaches 0, too many segments!
            if segment:
                value		= self.default_factory( segment )
            else:
                # Handles: "", "0:", ":00"; empty segments ==> 0
                value		= self.default_factory()
            if multiplier      <= 60:
                assert value < 60
            seconds    += value * multiplier
            multiplier         /= 60
        return seconds

    def _into_hms( self, seconds ):
        multiplier		= 60 * 60
        timespec                = []

        timespec.append( "%d" % ( seconds / ( 60*60 )))
        seconds                %= 60*60
        timespec.append( "%02d" % ( seconds / 60 ))
        seconds                %= 60
        if seconds:
            timespec.append( "%02d" % ( seconds ))
            seconds            %= 1
            if seconds:
                # Must be float, now < 1.0; turns 0.123000 into .123
                timespec[-1]   += ("%f" % ( seconds )).strip( "0" )
        return ":".join( timespec )

    def __iadd__( self, rhs ):
        """Handles:

            <timedict> += ( key, "HH:MM" )

        tuples specially; passes everything else along to mathdict.
        For "adding" regular dicts full of textual timespecs to a
        timedict.  Depends on the fact that mathdict.__iadd__ from a
        plain dict recursively triggers __iadd__ for each dict tuple,
        finding this code in the derived class.
        """
        if isinstance( rhs, tuple ) and isinstance( rhs[1], basestring ):
            self[rhs[0]]       += self._from_hms( rhs[1] )
            return self
        return mathdict.__iadd__( self, rhs ) # Otherwise, base mathdict handles

    def __reversed__( self ):
        """Returns an iterator over sorted (key, value) data, reverted
        back into "HH:MM[:SS[.s]" form.
        """
        return ( (k, self._into_hms( self[k] )) for k in sorted( self.keys()) )
