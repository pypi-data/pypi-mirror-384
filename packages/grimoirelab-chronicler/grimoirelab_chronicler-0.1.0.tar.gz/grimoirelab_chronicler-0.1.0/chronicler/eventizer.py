# -*- coding: utf-8 -*-
#
# Copyright (C) GrimoireLab Developers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import importlib
import pkgutil
import os

from collections import namedtuple
from collections.abc import Iterator, Generator
from typing import Any

from cloudevents.http import CloudEvent


Identity = namedtuple('Identity',
                      ['name', 'email', 'username'],
                      defaults=(None, None, None))


class Eventizer:
    """Abstract class to eventize data.

    Events will be generated calling to the `eventize` method.
    This method will take items produced by `perceval` and
    will convert them in GrimoireLab events.

    The class can only process items of one type. In other words,
    `git` items can't be mixed with `github` items. However,
    the same eventizer can process different categories of
    the same type. A `github` eventizer would process `issues`,
    `pull requests`, etc.

    To create your own eventizer, sub-class this class by implementing
    the method `eventize_item`. This method should have the
    logic to given a perceval item, produce the events associated to
    that item.
    """
    def eventize(self, raw_items: Iterator[dict[str, Any]]) -> Generator[CloudEvent]:
        """Generate GrimoireLab events.

        Produce events from the given list of perceval items.
        The items must be of the same type.
        """
        for raw_item in raw_items:
            yield from self.eventize_item(raw_item)

    def eventize_item(self, raw_item: dict[str, Any]) -> list[CloudEvent]:
        """Eventize a item."""
        raise NotImplementedError


def eventize(name: str, raw_items: Iterator[dict[str, Any]]) -> Generator[CloudEvent]:
    """Eventize data of a given type.

    Handy function to produce events from a set of perceval items
    of given type.
    """
    top_package_name = os.environ.get('CHRONICLER_EVENTIZERS',
                                      'chronicler.events')

    eventizers = _find_eventizers(top_package_name)

    try:
        eventizer = eventizers[name]()
    except KeyError:
        raise ValueError(f"Unknown eventizer '{name}'")

    yield from eventizer.eventize(raw_items)


def _find_eventizers(top_package_name: str) -> dict[str, type[Eventizer]]:
    """Find available eventizers.

    Look for the `Eventizer` classes under `top_package_name`
    and its sub-packages. When `top_package_name` defines a namespace,
    classes under that same namespace will be found too.

    :param top_package_name: package storing eventizer classes

    :returns: a dict with `Eventizer`
    """
    top_package = importlib.import_module(top_package_name)

    candidates = pkgutil.walk_packages(top_package.__path__,
                                       prefix=top_package.__name__ + '.')

    modules = [name for _, name, is_pkg in candidates if not is_pkg]

    return _import_eventizers(modules)


def _import_eventizers(modules):
    for module in modules:
        importlib.import_module(module)

    klasses = _find_classes(Eventizer, modules)

    eventizers = {name: kls for name, kls in klasses}

    return eventizers


def _find_classes(parent, modules):
    parents = parent.__subclasses__()

    while parents:
        kls = parents.pop()

        m = kls.__module__

        if m not in modules:
            continue

        name = m.split('.')[-1]
        parents.extend(kls.__subclasses__())

        yield name, kls


def uuid(*args):
    """Generate a UUID based on the given parameters.

    The UUID will be the SHA1 of the concatenation of the values
    from the list. The separator between these values is ':'.
    Each value must be a non-empty string, otherwise, the function
    will raise an exception.

    :param *args: list of arguments used to generate the UUID

    :returns: a universal unique identifier

    :raises ValueError: when anyone of the values is not a string,
        is empty or `None`.
    """
    import hashlib

    def check_value(v):
        if not isinstance(v, str):
            raise ValueError("%s value is not a string instance" % str(v))
        elif not v:
            raise ValueError("value cannot be None or empty")
        else:
            return v

    s = ':'.join(map(check_value, args))

    sha1 = hashlib.sha1(s.encode('utf-8', errors='surrogateescape'))
    uuid_sha1 = sha1.hexdigest()

    return uuid_sha1
