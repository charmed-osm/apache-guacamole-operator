#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

"""Guacamole charm module."""

import logging

from charms.davigar15_apache_guacd.v0.guacd import GuacdEvents, GuacdRequires
from ops.charm import CharmBase, ConfigChangedEvent, WorkloadEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus
from opslib.osm.interfaces.mysql import MysqlClient

from mysql import Mysql

logger = logging.getLogger(__name__)


class ApacheGuacamoleCharm(CharmBase):
    """Apache Guacamole Charm operator."""

    on = GuacdEvents()
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.guacd = GuacdRequires(self, self._stored)
        event_observe_mapping = {
            self.on.guacamole_pebble_ready: self._on_guacamole_pebble_ready,
            self.on.config_changed: self._on_config_changed,
            self.on.guacd_changed: self._on_config_changed,
            self.on.mysql_relation_changed: self._on_config_changed,
        }
        for event, observer in event_observe_mapping.items():
            self.framework.observe(event, observer)
        self._stored.set_default(db_initialized=False)
        self.mysql = MysqlClient(self, "mysql")

    @property
    def container(self):
        """Property to get guacamole container."""
        return self.unit.get_container("guacamole")

    @property
    def services(self):
        """Property to get the services in the container plan."""
        return self.container.get_plan().services

    def _on_guacamole_pebble_ready(self, _: WorkloadEvent):
        self._restart()

    def _on_config_changed(self, event: ConfigChangedEvent):
        if self.container.can_connect():
            self._restart()
        else:
            logger.info("pebble socket not available, deferring config-changed")
            event.defer()
            self.unit.status = MaintenanceStatus("waiting for pebble to start")

    def _restart(self):
        missing_relations = []
        if not self.guacd.hostname or not self.guacd.port:
            missing_relations.append("guacd")
        if self.mysql.is_missing_data_in_unit():
            missing_relations.append("mysql")
        if missing_relations:
            self.unit.status = BlockedStatus(f'missing relations: {", ".join(missing_relations)}')
            return
        if not self._stored.db_initialized:
            sql_script = self._get_initdb_sql()
            mysql = Mysql(
                self.mysql.host,
                int(self.mysql.port),
                self.mysql.user,
                self.mysql.password,
                self.mysql.database,
            )
            mysql.execute(sql_script)
            self._stored.db_initialized = True
        layer = self._get_pebble_layer()
        self._set_pebble_layer(layer)
        self._restart_service()
        self.unit.status = ActiveStatus()

    def _restart_service(self):
        container = self.container
        if "guacamole" in self.services:
            container.restart("guacamole")
            logger.info("guacamole service has been restarted")

    def _get_pebble_layer(self):
        return {
            "summary": "guacamole layer",
            "description": "pebble config layer for httpbin",
            "services": {
                "guacamole": {
                    "override": "replace",
                    "summary": "guacamole service",
                    "command": "/opt/guacamole/bin/start.sh",
                    "startup": "enabled",
                    "environment": {
                        "PATH": "/usr/local/tomcat/bin:/usr/local/openjdk-8/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                        "LANG": "C.UTF-8",
                        "JAVA_HOME": "/usr/local/openjdk-8",
                        "CATALINA_HOME": "/usr/local/tomcat",
                        "TOMCAT_NATIVE_LIBDIR": "/usr/local/tomcat/native-jni-lib",
                        "LD_LIBRARY_PATH": "/usr/local/tomcat/native-jni-lib",
                        "MYSQL_HOSTNAME": self.mysql.host,
                        "MYSQL_PORT": self.mysql.port,
                        "MYSQL_DATABASE": self.mysql.database,
                        "MYSQL_USER": self.mysql.user,
                        "MYSQL_PASSWORD": self.mysql.password,
                        "GUACD_HOSTNAME": self.guacd.hostname,
                        "GUACD_PORT": self.guacd.port,
                    },
                }
            },
        }

    def _set_pebble_layer(self, layer):
        self.container.add_layer("guacamole", layer, combine=True)

    def _get_initdb_sql(self):
        process = self.container.exec(
            ["/opt/guacamole/bin/initdb.sh", "--mysql"], encoding="utf-8"
        )
        sql, _ = process.wait_output()
        return sql


if __name__ == "__main__":  # pragma: no cover
    main(ApacheGuacamoleCharm, use_juju_for_storage=True)
