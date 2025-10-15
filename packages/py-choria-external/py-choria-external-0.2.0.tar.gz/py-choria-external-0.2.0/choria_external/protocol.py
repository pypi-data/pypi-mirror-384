import inspect
import json
import os

from jsonschema import validate, ValidationError

from choria_external.exceptions import InvalidRPCData, ImproperlyConfigured


class ProtocolMessage:

    # Maps protocols to the correct ProtocolMessage subclass
    # Filled in by calls to register_protocol
    _protocols = {}

    _protocol = None
    _schema = None

    def __init__(
            self,
            **kwargs
    ):
        if self._schema is None:
            raise ImproperlyConfigured("Must call {0}.load_schema before constructing an object".format(
                self.__class__.__name__))

        self._properties = {}
        for prop in self._schema["properties"]:
            self._properties[prop] = kwargs.get(prop, None)

    def __getattr__(self, item):
        if item not in self._properties:
            raise AttributeError(item)

        return self._properties[item]

    @classmethod
    def load_schema(cls):
        if cls._schema is not None:
            return

        schema_dir = os.path.join(os.path.dirname(inspect.getfile(cls)), 'schemas')
        print(schema_dir)

        with open(os.path.join(schema_dir, '{0}.json'.format(cls._protocol)), 'r') as fp:
            cls._schema = json.load(fp)

    @classmethod
    def get_protocol(cls, protocol_name):
        if protocol_name not in cls._protocols:
            raise InvalidRPCData("Unsupported message protocol {0}".format(protocol_name))

        protocol = cls._protocols[protocol_name]
        return protocol

    @classmethod
    def from_json(cls, request):
        message = json.loads(request)
        return cls.from_dict(message)

    @classmethod
    def from_dict(cls, message):
        """ Constructs a ProtocolMessage object from a dictionary of fields

        :param message: dict Message fields received
        """
        cls.load_schema()

        try:
            validate(message, cls._schema)
        except ValidationError as e:
            # Use of jsonschema is an implementation detail, so convert this error
            # into our own exception type
            raise InvalidRPCData(str(e))

        # Clone the message so as not to modify the original
        fields = message.copy()

        # Allow subclasses to override the fields as required
        cls.parse_message_hook(fields)

        obj = cls(**fields)
        return obj

    @classmethod
    def parse_message_hook(cls, fields):
        """ Hook to override how the message is converted into a protocol object

        Subclasses may override this method in order to customise the arguments to the constructor,
        for example converting a nested object into another ProtocolMessage object

        :param fields: dict Populated list of fields to pass to the ProtocolMessage constructor
        :return: None
        """
        pass

    @staticmethod
    def create_reply():
        """ Returns a reply object appropriate for this protocol

        :return: Reply
        """
        raise InvalidRPCData('Method should only be called for a ProtocolMessage subclass')

    @classmethod
    def register_protocol(cls):
        """ Registers the decorated class with the given protocol name so the correct
            ProtocolMessage object can be constructed when a message is received

        :return:
        """

        # noinspection PyProtectedMember
        def decorator(protocol_cls):
            if protocol_cls._protocol is None:
                raise ImproperlyConfigured('ProtocolMessage classes must define _protocol name')

            cls._protocols[protocol_cls._protocol] = protocol_cls
            return protocol_cls

        return decorator


class Reply:

    def __init__(self, *args, **kwargs):
        pass

    def successful(self):
        return True


