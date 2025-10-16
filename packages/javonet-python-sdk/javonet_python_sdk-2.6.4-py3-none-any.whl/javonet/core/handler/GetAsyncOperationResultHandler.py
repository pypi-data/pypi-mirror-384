from javonet.core.handler.AbstractCommandHandler import AbstractCommandHandler

class GetAsyncOperationResultHandler(AbstractCommandHandler):
    def process(self, command):
        raise NotImplementedError(f"{self.__class__.__name__} is not implemented in Python")
