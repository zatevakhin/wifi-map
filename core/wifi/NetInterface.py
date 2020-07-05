# -*- coding: utf-8 -*-

import os
import subprocess


class NetInterface:

    @staticmethod
    def all():
        return list(filter(lambda ifc: os.path.exists(f"/sys/class/net/{ifc}/wireless"), os.listdir("/sys/class/net")))

    @staticmethod
    def is_enabled(interface):
        try:
            output = subprocess.check_output(['/usr/bin/ip', 'link', 'show', interface])
        except subprocess.CalledProcessError as e:
            raise Exception(e.output.strip())
        else:
            output = output.decode('utf-8')

        return "state UP" in output
