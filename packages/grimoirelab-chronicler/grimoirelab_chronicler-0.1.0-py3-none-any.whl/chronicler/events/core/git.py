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

import logging
import re

from typing import Any, Generator

from cloudevents.http import CloudEvent
from grimoirelab_toolkit.identities import generate_uuid

from ...eventizer import Eventizer, uuid, Identity

GIT_EVENT_COMMIT = "org.grimoirelab.events.git.commit"
GIT_EVENT_MERGE_COMMIT = "org.grimoirelab.events.git.merge"
GIT_EVENT_ACTION_ADDED = "org.grimoirelab.events.git.file.added"
GIT_EVENT_ACTION_MODIFIED = "org.grimoirelab.events.git.file.modified"
GIT_EVENT_ACTION_DELETED = "org.grimoirelab.events.git.file.deleted"
GIT_EVENT_ACTION_REPLACED = "org.grimoirelab.events.git.file.replaced"
GIT_EVENT_ACTION_COPIED = "org.grimoirelab.events.git.file.copied"
GIT_EVENT_ACTION_TYPE_CHANGED = "org.grimoirelab.events.git.file.typechanged"

GIT_EVENT_COMMIT_AUTHORED_BY = "org.grimoirelab.events.git.commit.authored_by"
GIT_EVENT_COMMIT_COMMITTED_BY = "org.grimoirelab.events.git.commit.committed_by"
GIT_EVENT_COMMIT_ACKED_BY = "org.grimoirelab.events.git.commit.acked_by"
GIT_EVENT_COMMIT_CO_AUTHORED_BY = "org.grimoirelab.events.git.commit.co_authored_by"
GIT_EVENT_COMMIT_HELPED_BY = "org.grimoirelab.events.git.commit.helped_by"
GIT_EVENT_COMMIT_MENTORED_BY = "org.grimoirelab.events.git.commit.mentored_by"
GIT_EVENT_COMMIT_REPORTED_BY = "org.grimoirelab.events.git.commit.reported_by"
GIT_EVENT_COMMIT_REVIEWED_BY = "org.grimoirelab.events.git.commit.reviewed_by"
GIT_EVENT_COMMIT_SIGNED_OFF_BY = "org.grimoirelab.events.git.commit.signed_off_by"
GIT_EVENT_COMMIT_SUGGESTED_BY = "org.grimoirelab.events.git.commit.suggested_by"
GIT_EVENT_COMMIT_TESTED_BY = "org.grimoirelab.events.git.commit.tested_by"

COMMIT_TRAILERS = {
    "Acked-by": GIT_EVENT_COMMIT_ACKED_BY,
    "Co-authored-by": GIT_EVENT_COMMIT_CO_AUTHORED_BY,
    "Helped-by": GIT_EVENT_COMMIT_HELPED_BY,
    "Mentored-by": GIT_EVENT_COMMIT_MENTORED_BY,
    "Reported-by": GIT_EVENT_COMMIT_REPORTED_BY,
    "Reviewed-by": GIT_EVENT_COMMIT_REVIEWED_BY,
    "Signed-off-by": GIT_EVENT_COMMIT_SIGNED_OFF_BY,
    "Suggested-by": GIT_EVENT_COMMIT_SUGGESTED_BY,
    "Tested-by": GIT_EVENT_COMMIT_TESTED_BY,
}

# Pair programming regex. Some matching examples are:
#   - John Smith, John Doe and Jane Rae <pairprogramming@example.com>
#   - John Smith, John Doe & Jane Rae <pairprogramming@example>
#   - John Smith and John Doe <pairpogramming@example>
GIT_AUTHORS_REGEX = re.compile(
    r"(?P<first_authors>.+?)\s+(?:[aA][nN][dD]|&|\+)\s+(?P<last_author>.+?)\s+<(?P<email>[^>]+)>"
)

logger = logging.getLogger(__name__)


class GitEventizer(Eventizer):
    """Eventize git commits"""

    def eventize_item(self, raw_item: dict[str, Any]) -> list[CloudEvent]:
        events = []

        item_uuid = raw_item.get('uuid', None)

        if not item_uuid:
            raise ValueError("'uuid' attribute not found on item.")
        if raw_item['backend_name'].lower() != 'git':
            raise ValueError(f"Item {item_uuid} is not a 'git' item.")
        if raw_item['category'] != 'commit':
            raise ValueError(f"Invalid category '{raw_item['category']}' for '{item_uuid}' item.")

        if 'Merge' in raw_item['data']:
            event_type = GIT_EVENT_MERGE_COMMIT
        else:
            event_type = GIT_EVENT_COMMIT

        attributes = {
            "id": item_uuid,
            "type": event_type,
            "source": raw_item['origin'],
            "time": raw_item['updated_on'],
        }

        event = CloudEvent(attributes, raw_item['data'])
        events.append(event)

        action_events = self._eventize_commit_actions(event,
                                                      raw_item['data']['files'])

        events.extend(action_events)

        identities_events = self._eventize_commit_identities(event,
                                                             raw_item)

        events.extend(identities_events)

        return events

    def _eventize_commit_actions(self, parent_event: CloudEvent, raw_files_data):

        events = []

        for file_data in raw_files_data:
            actions = file_data.get('action', None)

            if not actions and parent_event['type'] == GIT_EVENT_COMMIT:
                raise ValueError(f"No action for commit event {parent_event['id']}")
            elif not actions:
                continue

            if parent_event['type'] == GIT_EVENT_COMMIT:
                action_event = self._process_action(parent_event['source'],
                                                    parent_event['time'],
                                                    parent_event['id'], actions, file_data)
                events.append(action_event)
            else:
                prev_merge_action = None
                for action in actions:
                    if action == prev_merge_action:
                        continue

                    action_event = self._process_action(parent_event['source'],
                                                        parent_event['time'],
                                                        parent_event['id'], action, file_data)
                    events.append(action_event)
                    prev_merge_action = action
        return events

    def _process_action(self, source, time, event_uuid, action, file_data):
        if action == 'A':
            event_type = GIT_EVENT_ACTION_ADDED
        elif action == 'M':
            event_type = GIT_EVENT_ACTION_MODIFIED
        elif action == 'D':
            event_type = GIT_EVENT_ACTION_DELETED
        elif action.startswith('R'):
            event_type = GIT_EVENT_ACTION_REPLACED
        elif action.startswith('C'):
            event_type = GIT_EVENT_ACTION_COPIED
        elif action.startswith('T'):
            event_type = GIT_EVENT_ACTION_TYPE_CHANGED
        else:
            raise ValueError(f"No valid action: {action}")

        id_args = [event_uuid, file_data['file'], action]
        if 'newfile' in file_data:
            id_args.append(file_data['newfile'])

        event_id = uuid(*id_args)

        data = {
            "filename": file_data['file'],
            "modes": file_data['modes'],
            "indexes": file_data['indexes'],
            "similarity": action[1:] if action in ('R', 'C') else None,
            "new_filename": file_data.get('newfile', None),
            "added_lines": file_data.get('added', None),
            "deleted_lines": file_data.get('removed', None)
        }

        attributes = {
            "id": event_id,
            "linked_event": event_uuid,
            "type": event_type,
            "source": source,
            "time": time,
        }

        event = CloudEvent(attributes, data)

        return event

    def _eventize_commit_identities(self, parent_event: CloudEvent, raw_item: dict[str, Any]) -> list[CloudEvent]:
        """Eventize commit identities from a git commit item."""

        events = []

        authors = self._parse_authors(raw_item["data"]["Author"])
        identity_events = self._process_identities(parent_event['source'],
                                                   parent_event['time'],
                                                   parent_event['id'],
                                                   GIT_EVENT_COMMIT_AUTHORED_BY,
                                                   authors)
        events.extend(identity_events)

        committers = self._parse_authors(raw_item["data"]["Commit"])
        identity_events = self._process_identities(parent_event['source'],
                                                   parent_event['time'],
                                                   parent_event['id'],
                                                   GIT_EVENT_COMMIT_COMMITTED_BY,
                                                   committers)
        events.extend(identity_events)

        for trailer, event_type in COMMIT_TRAILERS.items():
            signers = raw_item["data"].get(trailer, [])
            identity_events = self._process_identities(parent_event['source'],
                                                       parent_event['time'],
                                                       parent_event['id'],
                                                       event_type,
                                                       signers)
            events.extend(identity_events)

        return events

    def _process_identities(
        self,
        source: str,
        time: str,
        event_uuid: str,
        event_type: str,
        raw_identities: list[str]
    ) -> Generator[CloudEvent, None, None]:
        """Obtain identity events from a list of identities.

        :param source: data source of the event
        :param time: time of the event
        :param event_uuid: UUID of the parent event
        :param event_type: type of the identity event
        :param raw_identities: list of strings with the identities information

        :returns: generator of CloudEvent with the identity information
        """
        for raw_identity in raw_identities:
            try:
                identity = self._parse_identity(raw_identity)
                identity_id = generate_uuid(source="git",
                                            email=identity.email,
                                            name=identity.name,
                                            username=identity.username)
            except ValueError as e:
                logger.warning(f"Cannot generate UUID for identity '{raw_identity}' "
                               f"in event '{event_uuid}': {e}. Skipping.")
                continue

            role = event_type.split('.')[-1]
            event_id = uuid(event_uuid, role, identity_id)

            data = {
                "source": "git",
                "name": identity.name,
                "username": identity.username,
                "email": identity.email,
                "role": role,
                "uuid": identity_id,
            }

            attributes = {
                "id": event_id,
                "linked_event": event_uuid,
                "type": event_type,
                "source": source,
                "time": time,
            }

            yield CloudEvent(attributes, data)

    @staticmethod
    def _parse_authors(authors: str) -> list[str]:
        """Parse a list of authors from a string."""

        m = GIT_AUTHORS_REGEX.match(authors)
        if m:
            authors = m.group("first_authors").split(",")
            authors = [author.strip() for author in authors]
            authors += [m.group("last_author")]
            authors += [f"<{m.group('email')}>"]
            return authors
        else:
            return [authors]

    @staticmethod
    def _parse_identity(git_author: str) -> Identity:
        """Extract identity information from a Git author string."""

        fields = git_author.split("<")
        name = fields[0]
        name = name.strip()
        if not name:
            name = None
        email = None
        if len(fields) > 1:
            email = git_author.split("<")[1][:-1]

        return Identity(email=email, name=name)
