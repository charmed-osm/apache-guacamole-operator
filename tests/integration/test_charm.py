#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.


import logging
import socket
import subprocess
from pathlib import Path

import pytest
import yaml
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest):
    """Build the charm-under-test and deploy it together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    await ops_test.model.set_config({"update-status-hook-interval": "10s"})
    await ops_test.model.deploy("charmed-osm-mariadb-k8s", application_name="mariadb-k8s")
    await ops_test.model.deploy("apache-guacd", application_name="guacd")
    await ops_test.model.deploy("nginx-ingress-integrator", application_name="ingress", trust=True)
    # build and deploy charm from local source folder
    subprocess.run(["/usr/bin/sg", "microk8s", "-c", "microk8s.enable ingress"])
    name = socket.getfqdn()
    ip = socket.gethostbyname(name)
    external_hostname = f"guacamole.{ip}.nip.io"
    charm_config = {"external-hostname": external_hostname}
    charm = await ops_test.build_charm(".")
    resources = {"guacamole-image": METADATA["resources"]["guacamole-image"]["upstream-source"]}
    await ops_test.model.deploy(
        charm, resources=resources, application_name="guacamole", config=charm_config, trust=True
    )
    await ops_test.model.add_relation("guacamole:guacd", "guacd:guacd")
    await ops_test.model.add_relation("guacamole:mysql", "mariadb-k8s:mysql")
    await ops_test.model.add_relation("guacamole:ingress", "ingress:ingress")
    await ops_test.model.wait_for_idle(
        apps=["guacamole", "ingress", "guacd"], status="active", timeout=2000
    )
    assert ops_test.model.applications["guacamole"].units[0].workload_status == "active"
    assert (
        ops_test.model.applications["guacamole"].units[0].workload_status_message
        == f"Go to http://{external_hostname}/guacamole"
    )

    await ops_test.model.set_config({"update-status-hook-interval": "60m"})
