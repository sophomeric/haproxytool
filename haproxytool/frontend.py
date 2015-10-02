#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# pylint: disable=superfluous-parens
#
#
# Created by: Pavlos Parissis <pavlos.parissis@gmail.com>
#
"""Manage frontends

Usage:
    haproxytool frontend [-D DIR ] (-r | -s | -o | -e | -d | -t | -p | -i) [NAME...]
    haproxytool frontend [-D DIR ] -w OPTION VALUE [NAME...]
    haproxytool frontend [-D DIR ] (-l | -M)
    haproxytool frontend [-D DIR ] -m METRIC [NAME...]

Arguments:
    DIR     Directory path
    VALUE   Value to set
    OPTION  Setting name
    METRIC  Name of a metric, use '-M' to get metric names

Options:
    -h, --help                show this screen
    -e, --enable              enable frontend
    -d, --disable             disable frontend
    -t, --shutdown            shutdown frontend
    -r, --requests            show requests
    -p, --process             show process number
    -i, --iid                 show proxy ID number
    -s, --status              show status
    -o, --options             show value of options that can be changed with
                              '-w' option
    -m, --metric              show value of a metric
    -M, --list-metrics        show all metrics
    -l, --list                show all frontends
    -w, --write               change a frontend option
    -D DIR, --socket-dir=DIR  directory with HAProxy socket files
                              [default: /var/lib/haproxy]

"""
import sys
from docopt import docopt
from haproxyadmin import haproxy, exceptions
from operator import methodcaller
from haproxyadmin.exceptions import (SocketApplicationError,
                                     SocketConnectionError,
                                     SocketPermissionError)
from .utils import get_arg_option


class FrontendCommand(object):
    def __init__(self, hap, args):
        self.hap = hap
        self.args = args
        self.frontends = self.build_frontend_list(args['NAME'])

    def build_frontend_list(self, names=None):
        frontends = []
        if not names:
            for frontend in self.hap.frontends():
                frontends.append(frontend)
        else:
            for name in names:
                try:
                    frontends.append(self.hap.frontend(name))
                except ValueError:
                    print("{} was not found".format(name))

        return frontends

    def list(self):
        for frontend in self.frontends:
            print("{}".format(frontend.name))

    def status(self):
        for frontend in self.frontends:
            print("{} {}".format(frontend.name, frontend.status))

    def requests(self):
        for frontend in self.frontends:
            print("{} {}".format(frontend.name, frontend.requests))

    def iid(self):
        for frontend in self.frontends:
            print("{} {}".format(frontend.name, frontend.iid))

    def process(self):
        for frontend in self.frontends:
            print("{} {}".format(frontend.name, frontend.process_nb))

    def options(self):
        for frontend in self.frontends:
            print("{} maxconn={}".format(frontend.name, frontend.maxconn))

    def enable(self):
        for frontend in self.frontends:
            try:
                frontend.enable()
                print("{} enabled".format(frontend.name))
            except exceptions.CommandFailed as error:
                print("{} failed to be enabled:{}".format(frontend.name,
                                                          error))

    def disable(self):
        for frontend in self.frontends:
            try:
                frontend.disable()
                print("{} disabled".format(frontend.name))
            except exceptions.CommandFailed as error:
                print("{} failed to be disabled:{}".format(frontend.name,
                                                           error))

    def shutdown(self):
        for frontend in self.frontends:
            try:
                frontend.shutdown()
                print("{} shutdown".format(frontend.name))
            except exceptions.CommandFailed as error:
                print("{} failed to be shutdown:{}".format(frontend.name,
                                                           error))

    def write(self):
        setting = self.args['OPTION']
        value = self.args['VALUE']
        try:
            value = int(value)
            call_method = methodcaller('setmaxconn', value, die=False)
            for frontend in self.frontends:
                if call_method(frontend):
                    print("{} set {} to {}".format(frontend.name,
                                                   setting,
                                                   value))
                else:
                    print("{} failed to set maxconn on {}".format(frontend.name,
                                                                  value))
        except ValueError:
            sys.exit("You need to pass a number, got {}".format(value))

    def metric(self):
        metric = self.args['METRIC']
        if metric not in haproxy.FRONTEND_METRICS:
            sys.exit("{} no valid metric".format(metric))

        for frontend in self.frontends:
            print("{} {}".format(frontend.name, frontend.metric(metric)))

    def listmetrics(self):
        for metric in haproxy.FRONTEND_METRICS:
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

    cmd = FrontendCommand(hap, arguments)
    method = get_arg_option(arguments)
    getattr(cmd, method)()

# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
