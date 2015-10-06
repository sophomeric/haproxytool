#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# pylint: disable=superfluous-parens
#
#
# Created by: Pavlos Parissis <pavlos.parissis@gmail.com>
#
"""Manage haproxy

Usage:
    haproxytool haproxy [-D DIR ] [-a | -c | -C | -e | -i | -M | -o | -r]
    haproxytool haproxy [-D DIR ] -m METRIC [-w OPTION VALUE]
    haproxytool haproxy [-D DIR ] -w OPTION VALUE

Arguments:
    DIR     Directory path
    OPTION  Option name to set a VALUE
    VALUE   Value to set
    METRIC  Name of a metric, use '-M' to get metric names

Options:
    -a, --all                   clear all statistics counters
    -c, --clear                 clear max values of statistics counters
    -C, --maxconn               show configured maximum connection limit
    -e, --errors                show last know request and response errors
    -i, --info                  show haproxy stats
    -m, --metric                show value of a METRIC
    -M, --list-metrics          show all metrics
    -o, --options               show value of options that can be changed with
                                '-w' option
    -r, --requests              show total cumulative number of requests
                                processed by all processes
    -w, --write                 set VALUE of a haproxy OPTION
    -D DIR, --socket-dir=DIR    directory with HAProxy socket files
                                [default: /var/lib/haproxy]

"""
import sys
from docopt import docopt
from haproxyadmin import haproxy
from operator import methodcaller
from haproxyadmin.exceptions import (SocketApplicationError, CommandFailed,
                                     SocketConnectionError,
                                     SocketPermissionError)
from .utils import get_arg_option

OPTIONS = {
    'maxconn': 'setmaxconn',
    'ratelimitconn': 'setratelimitconn',
    'ratelimitsess': 'setratelimitsess',
    'ratelimitsslsess': 'setratelimitsslsess',
}


class HAProxyCommand(object):
    def __init__(self, hap, args):
        self.hap = hap
        self.args = args

    def all(self):
        self.hap.clearcounters(True)
        print("OK")

    def clear(self):
        self.hap.clearcounters()
        print("OK")

    def maxconn(self):
        print(self.hap.maxconn)

    def errors(self):
        _errors = self.hap.errors()
        for error_per_proc in _errors:
            print("Process number: {n}".format(n=error_per_proc[0]))
            for line in error_per_proc[1]:
                print(line)

    def info(self):
        _info = self.hap.info()
        for info_per_proc in _info:
            print("{c}Process {n}{c}".format(c=18 * '#',
                                             n=info_per_proc['Process_num']))
            for k, v in info_per_proc.items():
                print("{k}: {v}".format(k=k, v=v))

    def requests(self):
        print(self.hap.totalrequests)

    def options(self):
        for option in OPTIONS.keys():
            print("{opt} = {val}".format(opt=option,
                                         val=getattr(self.hap, option)))

    def write(self):
        option = self.args['OPTION']
        value = self.args['VALUE']
        if option not in OPTIONS:
            sys.exit("{opt} is not a valid option".format(opt=option))

        try:
            value = int(value)
        except ValueError:
            sys.exit("invalid input {val}, excepted number".format(val=value))

        call_method = methodcaller(OPTIONS[option], value)
        call_method(self.hap)
        print("set {opt} to {val}".format(opt=option, val=value))

    def metric(self):
        metric = self.args['METRIC']
        if metric not in haproxy.HAPROXY_METRICS:
            sys.exit("{} no valid metric".format(metric))

        print("{name} = {val}".format(name=metric, val=self.hap.metric(metric)))

    def listmetrics(self):
        for metric in haproxy.HAPROXY_METRICS:
            print(metric)


def main():
    arguments = docopt(__doc__)

    try:
        hap = haproxy.HAProxy(socket_dir=arguments['--socket-dir'])
    except (SocketApplicationError,
            SocketConnectionError,
            SocketPermissionError) as error:
        print(error, error.socket_file)
        sys.exit(1)
    except ValueError as error:
        print(error)
        sys.exit(1)

    cmd = HAProxyCommand(hap, arguments)
    method = get_arg_option(arguments)
    try:
        getattr(cmd, method)()
    except CommandFailed as error:
            sys.exit("failed with error: {err}".format(err=error))

# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()