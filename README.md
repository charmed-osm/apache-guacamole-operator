<!-- Copyright 2021 Canonical Ltd.
See LICENSE file for licensing details. -->

# Apache Guacamole Operator

[![codecov](https://codecov.io/gh/davigar15/charm-apache-guacamole/branch/main/graph/badge.svg?token=D8PJOLUQHM)](https://codecov.io/gh/davigar15/charm-apache-guacamole)
[![code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black/tree/main)
[![Run-Tests](https://github.com/davigar15/charm-apache-guacd/actions/workflows/ci.yaml/badge.svg)](https://github.com/davigar15/charm-apache-guacd/actions/workflows/ci.yaml)

## Description

Apache Guacamole is a clientless remote desktop gateway. It supports standard protocols like VNC, RDP, and SSH.
We call it clientless because no plugins or client software are required.
Thanks to HTML5, once Guacamole is installed on a server, all you need to access your desktops is a web browser.

## Usage

The Apache Guacamole Operator needs relations [`mysql`](https://charmhub.io/charmed-osm-mariadb-k8s) and [`guacd`](https://charmhub.io/davigar15-apache-guacd). All the charms may be deployed using the Juju command line as in

```shell
# Create a Juju Model
juju add-model apache-guacamole
# Deploy database and guacd
juju deploy charmed-osm-mariadb-k8s db
juju deploy davigar15-apache-guacd --channel edge guacd
# Deploy Apache Guacamole Operator
juju deploy davigar15-apache-guacamole --channel edge guacamole
# Add relations
juju relate guacamole db
juju relate guacamole guacd
```

# Accessing the UI

Execute the command `watch -c juju status --color` to check the status of the deployment. When the deployment is done, the `guacamole` charm will show a status log to the URL you need to go to access guacamole.

Default credentials are `guacadmin`/`guacadmin`.


## OCI Images

- [guacamole](https://hub.docker.com/layers/guacamole/guacamole/1.3.0/images/sha256-739cb6820ae884827ceaaa87b45b8802769649c848d737584aea79d999177dc3?context=explore)

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines
on enhancements to this charm following best practice guidelines, and
`CONTRIBUTING.md` for developer guidance.
