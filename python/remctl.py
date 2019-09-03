# Python interface to remctl.
#
# This is the high-level interface that most Python programs that use remctl
# should be using.  It's a Python wrapper around the _remctl C module, which
# exposes exactly the libremctl API.
#
# Original implementation by Thomas L. Kula <kula@tproa.net>
# Copyright 2014, 2019 Russ Allbery <eagle@eyrie.org>
# Copyright 2008, 2011-2012
#     The Board of Trustees of the Leland Stanford Junior University
# Copyright 2008 Thomas L. Kula <kula@tproa.net>
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted, provided
# that the above copyright notice appear in all copies and that both that
# copyright notice and this permission notice appear in supporting
# documentation, and that the name of Thomas L. Kula not be used in
# advertising or publicity pertaining to distribution of the software without
# specific, written prior permission. Thomas L. Kula makes no representations
# about the suitability of this software for any purpose.  It is provided "as
# is" without express or implied warranty.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
# There is no SPDX-License-Identifier registered for this license.

"""Interface to remctl.

   This module is an interface to remctl, a client/server
   protocol for running single commands on a remote host
   using Kerberos v5 authentication.
"""

VERSION = "3.16"

import _remctl

# Exception classes.


class RemctlError(Exception):
    """The underlying remctl library has returned an error."""

    pass


class RemctlProtocolError(RemctlError):
    """A remctl protocol error occurred.

    This exception is only used with the remctl.remctl() simple interface;
    for the full interface, errors are returned as a regular output token.
    """

    pass


class RemctlNotOpenedError(RemctlError):
    """No open connection to a server."""

    pass


# Simple interface.


class RemctlSimpleResult:
    """An object holding the results from the simple interface."""

    def __init__(self):
        self.stdout = None
        self.stderr = None
        self.status = None


def remctl(host, port=None, principal=None, command=[]):
    """Simple interface to remctl.

    Connect to HOST on PORT, using PRINCIPAL as the server principal for
    authentication, and issue COMMAND.  Returns the result as a
    RemctlSimpleResult object, which has three attributes.  stdout holds the
    complete standard output, stderr holds the complete standard error, and
    status holds the exit status.
    """
    if port == None:
        port = 0
    else:
        try:
            port = int(port)
        except ValueError:
            raise TypeError("port must be a number: " + repr(port))
    if (port < 0) or (port > 65535):
        raise ValueError("invalid port number: " + repr(port))
    if isinstance(command, (basestring, bool, int, float)):
        raise TypeError("command must be a sequence or iterator")

    # Convert the command to a list of strings.
    mycommand = []
    for item in command:
        mycommand.append(str(item))
    if len(mycommand) < 1:
        raise ValueError("command must not be empty")

    # At this point, things should be sane.  Call the low-level interface.
    output = _remctl.remctl(host, port, principal, mycommand)
    if output[0] != None:
        raise RemctlProtocolError(output[0])
    result = RemctlSimpleResult()
    setattr(result, "stdout", output[1])
    setattr(result, "stderr", output[2])
    setattr(result, "status", output[3])
    return result


# Complex interface.


class Remctl:
    def __init__(self, host=None, port=None, principal=None):
        self.r = _remctl.remctl_new()
        self.opened = False

        if host != None:
            self.open(host, port, principal)

    def set_ccache(self, ccache):
        if not _remctl.remctl_set_ccache(self.r, ccache):
            raise RemctlError(self.error())

    def set_source_ip(self, source):
        if not _remctl.remctl_set_source_ip(self.r, source):
            raise RemctlError(self.error())

    def set_timeout(self, timeout):
        if not _remctl.remctl_set_timeout(self.r, timeout):
            raise RemctlError(self.error())

    def open(self, host, port=None, principal=None):
        if port == None:
            port = 0
        else:
            try:
                port = int(port)
            except ValueError:
                raise TypeError("port must be a number: " + repr(port))
        if (port < 0) or (port > 65535):
            raise ValueError("invalid port number: " + repr(port))

        # At this point, things should be sane.  Call the low-level interface.
        if not _remctl.remctl_open(self.r, host, port, principal):
            raise RemctlError(self.error())
        self.opened = True

    def command(self, comm):
        commlist = []
        if not self.opened:
            raise RemctlNotOpenedError("no currently open connection")
        if isinstance(comm, (basestring, bool, int, float)):
            raise TypeError("command must be a sequence or iterator")

        # Convert the command to a list of strings.
        for item in comm:
            commlist.append(str(item))
        if len(commlist) < 1:
            raise ValueError("command must not be empty")

        # At this point, things should be sane.  Call the low-level interface.
        if not _remctl.remctl_commandv(self.r, commlist):
            raise RemctlError(self.error())

    def output(self):
        if not self.opened:
            raise RemctlNotOpenedError("no currently open connection")
        output = _remctl.remctl_output(self.r)
        if len(output) == 0:
            raise RemctlError(self.error())
        return output

    def noop(self):
        if not self.opened:
            raise RemctlNotOpenedError("no currently open connection")
        if not _remctl.remctl_noop(self.r):
            raise RemctlError(self.error())

    def close(self):
        del self.r
        self.r = None
        self.opened = False

    def error(self):
        if self.r == None:
            # We do this instead of throwing an exception so that callers
            # don't have to handle an exception when they are trying to find
            # out why an exception occured.
            return "no currently open connection"
        return _remctl.remctl_error(self.r)
