from javonet.core.handler.AbstractCommandHandler import AbstractCommandHandler

class CreateNullHandler(AbstractCommandHandler):
    def process(self, command):
        raise NotImplementedError("%s is not implemented in Python" % self.__class__.__name__)
