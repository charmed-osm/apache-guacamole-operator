# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from ipaddress import IPv4Address

import pytest
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus
from ops.testing import Harness
from pytest_mock import MockerFixture

from charm import ApacheGuacamoleCharm, pod_ip

pebble_exec_mock = None
mysql_rel_id = None


def test_pod_ip(mocker: MockerFixture):
    socket_mock = mocker.patch("charm.socket")
    socket_mock.getfqdn.return_value = "host"
    socket_mock.gethostbyname.return_value = "1.1.1.1"
    assert pod_ip() == IPv4Address("1.1.1.1")
    assert socket_mock.getfqdn.call_count == 1
    socket_mock.gethostbyname.assert_called_once_with("host")


@pytest.fixture
def harness_no_relations(mocker: MockerFixture):
    mocker.patch("charm.KubernetesServicePatch")
    process_mock = mocker.Mock()
    process_mock.wait_output.return_value = ("sql", None)
    global pebble_exec_mock
    pebble_exec_mock = mocker.patch("ops.testing._TestingPebbleClient.exec")
    pebble_exec_mock.return_value = process_mock
    mocker.patch("charm.Mysql")
    guacamole_harness = Harness(ApacheGuacamoleCharm)
    guacamole_harness.begin()
    yield guacamole_harness
    guacamole_harness.cleanup()


@pytest.fixture
def harness(mocker: MockerFixture, harness_no_relations: Harness):
    guacd_rel_id = harness_no_relations.add_relation("guacd", "guacd")
    harness_no_relations.add_relation_unit(guacd_rel_id, "guacd/0")
    harness_no_relations.update_relation_data(
        guacd_rel_id, "guacd", {"hostname": "hostname", "port": "4822"}
    )
    global mysql_rel_id
    mysql_rel_id = harness_no_relations.add_relation("mysql", "mysql")
    harness_no_relations.add_relation_unit(mysql_rel_id, "mysql/0")
    harness_no_relations.update_relation_data(
        mysql_rel_id,
        "mysql/0",
        {
            "host": "host",
            "port": "3306",
            "user": "user",
            "root_password": "root_pass",
            "password": "password",
            "database": "db",
        },
    )

    return harness_no_relations


def test_missing_relations(harness_no_relations: Harness):
    harness_no_relations.charm.on.guacamole_pebble_ready.emit("guacamole")
    assert harness_no_relations.charm.unit.status == BlockedStatus(
        "missing relations: guacd, mysql"
    )


def test_missing_units_in_relation(harness: Harness):
    # Test missing relation data
    harness.update_relation_data(mysql_rel_id, "mysql/0", {"host": None})
    assert harness.charm.unit.status == BlockedStatus("missing relations: mysql")
    # Test missing relation unit
    harness.remove_relation_unit(mysql_rel_id, "mysql/0")
    harness.charm.on.guacamole_pebble_ready.emit("guacamole")
    assert harness.charm.unit.status == BlockedStatus("missing relations: mysql")


def test_guacamole_pebble_ready_leader(mocker: MockerFixture, harness: Harness):
    harness.set_leader(True)
    pod_ip_mock = mocker.patch("charm.pod_ip")
    pod_ip_mock.return_value = "IP"
    spy = mocker.spy(harness.charm, "_restart")
    harness.charm.on.guacamole_pebble_ready.emit("guacamole")
    assert harness.charm.unit.status == ActiveStatus("Go to http://IP:8080/guacamole")
    assert spy.call_count == 1


def test_guacamole_pebble_ready(mocker: MockerFixture, harness: Harness):
    spy = mocker.spy(harness.charm, "_restart")
    harness.charm.on.guacamole_pebble_ready.emit("guacamole")
    assert harness.charm.unit.status == ActiveStatus()
    assert spy.call_count == 1


def test_config_changed_can_connect(mocker: MockerFixture, harness: Harness):
    spy = mocker.spy(harness.charm, "_restart")
    harness.charm.on.config_changed.emit()
    assert harness.charm.unit.status == ActiveStatus()
    assert spy.call_count == 1


def test_config_changed_cannot_connect(mocker: MockerFixture, harness: Harness):
    spy = mocker.spy(harness.charm, "_restart")
    container_mock = mocker.Mock()
    container_mock.can_connect.return_value = False
    mocker.patch(
        "charm.ApacheGuacamoleCharm.container",
        return_value=container_mock,
        new_callable=mocker.PropertyMock,
    )
    harness.charm.on.config_changed.emit()
    assert harness.charm.unit.status == MaintenanceStatus("waiting for pebble to start")
    assert spy.call_count == 0


def test_restart_service_service_not_exists(mocker: MockerFixture, harness: Harness):
    container_mock = mocker.Mock()
    mocker.patch(
        "charm.ApacheGuacamoleCharm.container",
        return_value=container_mock,
        new_callable=mocker.PropertyMock,
    )
    mocker.patch(
        "charm.ApacheGuacamoleCharm.services", return_value={}, new_callable=mocker.PropertyMock
    )
    harness.charm._restart_service()
    container_mock.restart.assert_not_called()
