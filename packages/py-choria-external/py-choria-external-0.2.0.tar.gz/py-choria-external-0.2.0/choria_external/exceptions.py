class ChoriaExternalException(Exception):
    """ Base exception"""
    description = 'Unknown error'
    statuscode = 5

    def __str__(self):
        return '{0}: {1}'.format(self.description, ' '.join(self.args))


class RPCAborted(ChoriaExternalException):
    description = "RPC Aborted"
    statuscode = 1


class UnknownRPCAction(ChoriaExternalException):
    description = "Unknown RPC Action"
    statuscode = 2


class InvalidRPCData(ChoriaExternalException):
    description = "Invalid Data"
    statuscode = 4


class ImproperlyConfigured(ChoriaExternalException):
    description = "RPC Aborted"
