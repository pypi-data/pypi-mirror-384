#! /usr/bin/env python3

################################################################################
""" Docker interface for Thingy

    Copyright (C) 2017 John Skilleter

    Note that this:
        * Only implements functions required by docker-purge
        * Only has basic error checking, in that it raises DockerError
          for any error returned by the external docker command.
"""
################################################################################

import thingy.run as run

################################################################################

class DockerError(Exception):
    """ Exception for dockery things """

    pass

################################################################################

def instances(all=False):
    """ Return a list of all current Docker instances """

    cmd = ['docker', 'ps', '-q']

    if all:
        cmd.append('-a')

    instances_list = []
    try:
        for result in run.run(cmd):
            instances_list.append(result)
    except run.RunError as exc:
        raise DockerError(exc)

    return instances_list

################################################################################

def stop(instance, force=False):
    """ Stop the specified Docker instance """

    # TODO: force option not implemented

    try:
        run.run(['docker', 'stop', instance], output=True)
    except run.RunError as exc:
        raise DockerError(exc)

################################################################################

def rm(instance, force=False):
    """ Remove the specified instance """

    cmd = ['docker', 'rm']

    if force:
        cmd.append('--force')

    cmd.append(instance)

    try:
        run.run(cmd, output=True)
    except run.RunError as exc:
        raise DockerError(exc)

################################################################################

def images():
    """ Return a list of all current Docker images """

    try:
        for result in run.run(['docker', 'images', '-q']):
            yield result
    except run.RunError as exc:
        raise DockerError(exc)

################################################################################

def rmi(image, force=False):
    """ Remove the specified image """

    cmd = ['docker', 'rmi']
    if force:
        cmd.append('--force')

    cmd.append(image)

    try:
        run.run(cmd, foreground=True)
    except run.RunError as exc:
        raise DockerError(exc)
