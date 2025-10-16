# python
# -*- coding: utf-8 -*-
"""
The GetGlobalFieldHandler class handles retrieving global field values from a module.
"""

import sys
import traceback
try:
    from importlib import import_module
except Exception:
    import_module = None

from javonet.core.handler.AbstractCommandHandler import AbstractCommandHandler


class GetGlobalFieldHandler(AbstractCommandHandler):
    """
    Handler for retrieving global field values from a module.
    """

    def __init__(self):
        """
        Initializes a new global field retrieval handler.
        """
        self._required_parameters_count = 1

    def process(self, command):
        try:
            if len(command.payload) < self._required_parameters_count:
                raise Exception("GetGlobalField parameters mismatch! Expected a fully qualified field name.")

            full_field_name = command.payload[0]
            if not isinstance(full_field_name, basestring) or "." not in full_field_name:
                raise Exception("Invalid field name format. Expected 'module_name.field_name'.")

            module_name, field_name = full_field_name.rsplit(".", 1)

            # Import module with fallback for environments without importlib
            try:
                if import_module is not None:
                    module = import_module(module_name)
                else:
                    module = __import__(module_name, fromlist=['*'])
            except Exception:
                raise Exception("Could not import module '{0}'.".format(module_name))

            # Get attribute from module
            try:
                value = getattr(module, field_name)
            except Exception:
                # Prepare available non-callable attributes for better diagnostics
                available = []
                try:
                    for attr in dir(module):
                        if attr.startswith("__"):
                            continue
                        try:
                            attr_val = getattr(module, attr)
                            if not callable(attr_val):
                                available.append(attr)
                        except Exception:
                            pass
                except Exception:
                    pass

                message_lines = [
                    "Field '{0}' not found in module '{1}'.".format(field_name, module_name)
                ]
                if available:
                    message_lines.append("Available non-callable attributes:")
                    message_lines.extend(available)
                raise Exception("\n".join(message_lines))

            return value

        except Exception as e:
            # Python 2.7 style exception handling with full traceback
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            raise Exception("Error in GetGlobalFieldHandler: {0}\n{1}".format(str(e), tb_str))