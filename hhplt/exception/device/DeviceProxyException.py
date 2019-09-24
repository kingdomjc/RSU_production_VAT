class DeviceProxyException(Exception):

    def __init__(self, msg):
        self.msg = str(msg)

    def __str__(self):
        if self.msg:
            return self.msg