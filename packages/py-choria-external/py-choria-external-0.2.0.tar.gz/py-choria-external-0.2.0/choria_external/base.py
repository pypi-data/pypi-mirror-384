import logging

from choria_external.config import Config
from choria_external.exceptions import RPCAborted, ChoriaExternalException


class ChoriaExternal:

    def __init__(self, request, reply):
        self.plugin_name = self.__class__.__name__.lower()
        self.request = request
        self.reply = reply
        self.config = None
        self.logger = logging.getLogger('choria.{0}'.format(self.plugin_name))

    def load_config(self):
        self.config = Config(self.plugin_name)
        self.config.read_config()

    # noinspection PyMethodMayBeStatic
    def execute(self):
        """ The method which executes the request and populates the reply with the data to return

            This method should be overridden by subclasses to do something useful
        """
        pass

    @classmethod
    def dispatch(cls, request, reply):
        """ Executes a request and returns the reply

        :param request: RPC request object
        :param reply: RPC reply object
        :return:
        """
        try:
            plugin = cls(
                request=request,
                reply=reply
            )
            plugin.load_config()

            try:
                plugin.execute()
            except Exception as e:
                raise RPCAborted(str(e))

        except ChoriaExternalException as e:
            reply.fail(str(e))
