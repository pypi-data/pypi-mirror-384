from javonet.sdk.RuntimeContext import RuntimeContext
from javonet.sdk.internal.abstract.AbstractRuntimeFactory import AbstractRuntimeFactory
from javonet.utils.RuntimeName import RuntimeName
from javonet.utils.connectionData.IConnectionData import IConnectionData


class RuntimeFactory(AbstractRuntimeFactory):
    """
    The RuntimeFactory class implements the AbstractRuntimeFactory interface and provides methods for creating runtime contexts.
    Each method corresponds to a specific runtime (CLR, JVM, .NET Core, Perl, Ruby, Node.js, Python) and returns a RuntimeContext instance for that runtime.
    """

    def __init__(self, connection_data: IConnectionData):
        self.connection_data = connection_data

    def clr(self):
        """
        Creates RuntimeContext instance to interact with CLR runtime.

        Returns:
            RuntimeContext instance for the CLR runtime

        Refer to this `article on Javonet Guides <https://www.javonet.com/guides/v2/python/foundations/runtime-context>`_ for more information.
        """
        return RuntimeContext.get_instance(RuntimeName.clr, self.connection_data)

    def jvm(self):
        """
        Creates RuntimeContext instance to interact with JVM runtime.

        Returns:
            RuntimeContext instance for the JVM runtime

        Refer to this `article on Javonet Guides <https://www.javonet.com/guides/v2/python/foundations/runtime-context>`_ for more information.
        """
        return RuntimeContext.get_instance(RuntimeName.jvm, self.connection_data)

    def netcore(self):
        """
        Creates RuntimeContext instance to interact with .NET Core runtime.

        Returns:
            RuntimeContext instance for the .NET Core runtime

        Refer to this `article on Javonet Guides <https://www.javonet.com/guides/v2/python/foundations/runtime-context>`_ for more information.
        """
        return RuntimeContext.get_instance(RuntimeName.netcore, self.connection_data)

    def perl(self):
        """
        Creates RuntimeContext instance to interact with Perl runtime.

        Returns:
            RuntimeContext instance for the Perl runtime

        Refer to this `article on Javonet Guides <https://www.javonet.com/guides/v2/python/foundations/runtime-context>`_ for more information.
        """
        return RuntimeContext.get_instance(RuntimeName.perl, self.connection_data)

    def ruby(self):
        """
        Creates RuntimeContext instance to interact with Ruby runtime.

        Returns:
            RuntimeContext instance for the Ruby runtime

        Refer to this `article on Javonet Guides <https://www.javonet.com/guides/v2/python/foundations/runtime-context>`_ for more information.
        """
        return RuntimeContext.get_instance(RuntimeName.ruby, self.connection_data)

    def nodejs(self):
        """
        Creates RuntimeContext instance to interact with Node.js runtime.

        Returns:
            RuntimeContext instance for the Node.js runtime

        Refer to this `article on Javonet Guides <https://www.javonet.com/guides/v2/python/foundations/runtime-context>`_ for more information.
        """
        return RuntimeContext.get_instance(RuntimeName.nodejs, self.connection_data)

    def python(self):
        """
        Creates RuntimeContext instance to interact with Python runtime.
        
        Returns:
            a RuntimeContext instance for the Python runtime
        
        Refer to this `article on Javonet Guides <https://www.javonet.com/guides/v2/python/foundations/runtime-context>`_ for more information.
        """
        return RuntimeContext.get_instance(RuntimeName.python, self.connection_data)

    def php(self):
        """
        Creates RuntimeContext instance to interact with PHP runtime.

        Returns:
            a RuntimeContext instance for the PHP runtime

        Refer to this `article on Javonet Guides <https://www.javonet.com/guides/v2/python/foundations/runtime-context>`_ for more information.
        """
        return RuntimeContext.get_instance(RuntimeName.php, self.connection_data)


    def python27(self):
        """
        Creates RuntimeContext instance to interact with Python 2.7 runtime.
        
        Returns:
            a RuntimeContext instance for the Python 2.7 runtime
        
        Refer to this `article on Javonet Guides <https://www.javonet.com/guides/v2/python/foundations/runtime-context>`_ for more information.
        """
        return RuntimeContext.get_instance(RuntimeName.python27, self.connection_data)


def initialize_runtime_context(config):
    """
    Initializes RuntimeContext based on the Config object and loads modules.

    Args:
        config: Instance of Config.

    Returns:
        RuntimeContext with loaded modules.
    """
    # Create runtime context using config's runtime and connection data
    rtm_ctx = RuntimeContext.get_instance(config.runtime, config.connection_data)
    # Split modules by comma and remove empty entries
    modules = [m.strip() for m in config.modules.split(",") if m.strip()]

    for module in modules:
        # Load module from absolute path or from current working directory
        if os.path.isabs(module):
            rtm_ctx.load_library(module)
        else:
            rtm_ctx.load_library(os.path.join(os.getcwd(), module))
    return rtm_ctx
