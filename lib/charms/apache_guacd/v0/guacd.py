# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Guacd library.

This library allows the integration with Apache Guacd charm. Is is published as part of the
[davigar15-apache-guacd]((https://charmhub.io/davigar15-apache-guacd) charm.

The charm that requires guacd should include the following content in its metadata.yaml:

```yaml
# ...
requires:
    guacd:
        interface: guacd
        limit: 1
# ...
```

A typical example of including this library might be:

```python
# ...
from ops.framework import StoredState
from charms.davigar15_apache_guacd.v0.guacd import GuacdEvents, GuacdRequires

class SomeApplication(CharmBase):
  on = GuacdEvents()
  _stored = StoredState()

  def __init__(self, *args):
    # ...
    self.guacd = GuacdRequires(self, self._stored)
    self.framework.observe(self.on.guacd_changed, self._guacd_changed)
    # ...

  def _guacd_changed(self, _):
    guacd_hostname = self.guacd.hostname
    guacd_port = self.guacd.port
    # ...
```
"""


import socket
from ipaddress import IPv4Address
from typing import Optional

from ops.charm import CharmEvents, RelationEvent
from ops.framework import EventBase, EventSource, Object

# The unique Charmhub library identifier, never change it
LIBID = "49a97420b5ce4b45b493d48ec74867b8"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 1


def pod_ip() -> Optional[IPv4Address]:
    """Pod's IP address."""
    fqdn = socket.getfqdn()
    return IPv4Address(socket.gethostbyname(fqdn))


class GuacdChangedEvent(EventBase):
    """Event to announce a change in the Guacd service."""


class GuacdEvents(CharmEvents):
    """Guacd Events."""

    guacd_changed = EventSource(GuacdChangedEvent)


class GuacdRequires(Object):
    """Requires-side of the guacd interface."""

    def __init__(self, charm, _stored, relation_name="guacd"):
        super().__init__(charm, relation_name)
        self.relation_name = relation_name
        self.charm = charm
        self._stored = _stored
        self._stored.set_default(guacd_hostname=None, guacd_port=None)
        self.framework.observe(
            charm.on[self.relation_name].relation_changed, self._on_relation_changed
        )

    @property
    def hostname(self):
        """Guacd hostname."""
        return self._stored.guacd_hostname

    @property
    def port(self):
        """Guacd port."""
        return self._stored.guacd_port

    def _on_relation_changed(self, event: RelationEvent):
        if event.app in event.relation.data:
            hostname = event.relation.data[event.app].get("hostname")
            port = event.relation.data[event.app].get("port")
            stored_updated = False
            if hostname and hostname != self._stored.guacd_hostname:
                self._stored.guacd_hostname = hostname
                stored_updated = True
            if port and port != self._stored.guacd_port:
                self._stored.guacd_port = port
                stored_updated = True
            if stored_updated:
                self.charm.on.guacd_changed.emit()


class GuacdProvides(Object):
    """Provides-side of the guacd interface."""

    def __init__(self, charm, relation_name="guacd"):
        super().__init__(charm, relation_name)
        self.relation_name = relation_name
        self.charm = charm
        self.framework.observe(charm.on.start, self._on_start)
        self.framework.observe(
            charm.on[self.relation_name].relation_changed, self._on_relation_changed
        )

    def _on_start(self, _):
        for relation in self.model.relations[self.relation_name]:
            self.charm.on[self.relation_name].relation_changed.emit(
                relation, unit=self.model.unit, app=self.model.app
            )

    def _on_relation_changed(self, event: RelationEvent):
        relation_data = {"hostname": str(pod_ip()), "port": str(4822)}
        if self.model.unit.is_leader():
            event.relation.data[self.model.app].update(relation_data)
        event.relation.data[self.model.unit].update(relation_data)
