<!-- Copyright 2021 Canonical Ltd.
See LICENSE file for licensing details. -->

# Apache Guacamole Operator

[![code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black/tree/main)
[![Run-Tests](https://github.com/davigar15/charm-apache-guacd/actions/workflows/ci.yaml/badge.svg)](https://github.com/davigar15/charm-apache-guacd/actions/workflows/ci.yaml)

## Description

Apache Guacamole is a clientless remote desktop gateway. It supports standard protocols like VNC, RDP, and SSH.
We call it clientless because no plugins or client software are required.
Thanks to HTML5, once Guacamole is installed on a server, all you need to access your desktops is a web browser.

## Usage

The Apache Guacamole Operator may be deployed using the Juju command line as in

```shell
juju add-model apache-guacamole2
juju deploy charmed-osm-mariadb-k8s db
juju deploy davigar15-apache-guacd --channel edge guacd
juju deploy davigar15-apache-guacamole --channel edge guacamole
juju relate guacamole db
juju relate guacamole guacd
```
## OCI Images

- [guacamole](https://hub.docker.com/layers/guacamole/guacamole/1.3.0/images/sha256-739cb6820ae884827ceaaa87b45b8802769649c848d737584aea79d999177dc3?context=explore)

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines
on enhancements to this charm following best practice guidelines, and
`CONTRIBUTING.md` for developer guidance.
