#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.


import logging
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
    await ops_test.model.deploy("davigar15-apache-guacd", application_name="guacd", channel="edge")
    await ops_test.model.wait_for_idle(timeout=1000)
    # build and deploy charm from local source folder
    charm = await ops_test.build_charm(".")
    resources = {
        "guacamole-image": METADATA["resources"]["guacamole-image"]["upstream-source"],
    }
    await ops_test.model.deploy(charm, resources=resources, application_name="guacamole")
    await ops_test.model.add_relation("guacamole:guacd", "guacd:guacd")
    await ops_test.model.add_relation("guacamole:mysql", "mariadb-k8s:mysql")
    await ops_test.model.wait_for_idle(apps=["guacamole"], status="active", timeout=1000)
    assert ops_test.model.applications["guacamole"].units[0].workload_status == "active"

    await ops_test.model.set_config({"update-status-hook-interval": "60m"})
