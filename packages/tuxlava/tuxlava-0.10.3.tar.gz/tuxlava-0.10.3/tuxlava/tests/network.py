# -*- coding: utf-8 -*-
#
# vim: set ts=4
#
# Copyright 2024-present Linaro Limited
# Copyright (c) 2025-present Qualcomm Technologies, Inc. and/or its subsidiaries.
#
# SPDX-License-Identifier: MIT

from tuxlava.tests import Test


class NetworkTest(Test):
    devices = [
        "qemu-*",
        "fvp-aemva",
        "avh-imx93",
        "avh-rpi4b",
        "nfs-*",
        "fastboot-*",
        "flasher-*",
    ]
    need_test_definition = True

    def render(self, **kwargs):
        kwargs["name"] = self.name
        kwargs["timeout"] = self.timeout
        return self._render("network.yaml.jinja2", **kwargs)


class NetworkBasic(NetworkTest):
    name = "network-basic"
    timeout = 25
