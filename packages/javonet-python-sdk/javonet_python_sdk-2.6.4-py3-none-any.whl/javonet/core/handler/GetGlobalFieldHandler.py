import importlib
import inspect
import logging
import os
import sys
from importlib import import_module

from javonet.core.handler.AbstractCommandHandler import AbstractCommandHandler
from javonet.core.handler.LoadLibraryHandler import LoadLibraryHandler
from javonet.core.namespaceCache.NamespaceCache import NamespaceCache
from javonet.core.typeCache.TypeCache import TypeCache


class GetGlobalFieldHandler(AbstractCommandHandler):
    def __init__(self):
        self._required_parameters_count = 1

    def process(self, command):
        try:
            if len(command.payload) < self._required_parameters_count:
                raise Exception("GetGlobalField parameters mismatch! Expected a fully qualified field name.")

            full_field_name = command.payload[0]
            if not isinstance(full_field_name, str) or "." not in full_field_name:
                raise Exception("Invalid field name format. Expected 'module_name.field_name'.")

            module_name, field_name = full_field_name.rsplit(".", 1)

            try:
                module = importlib.import_module(module_name)
            except ImportError as e:
                raise ImportError(f"Could not import module '{module_name}'.") from e

            try:
                value = getattr(module, field_name)
            except AttributeError as e:
                try:
                    available = [
                        attr for attr in dir(module)
                        if not callable(getattr(module, attr, None)) and not attr.startswith("__")
                    ]
                except Exception:
                    available = []
                message = (
                    f"Field '{field_name}' not found in module '{module_name}'. "
                    "Available non-callable attributes:\n" + "\n".join(available)
                )
                raise AttributeError(message) from e

            return value

        except Exception as e:
            exc_type, exc_value = type(e), e
            new_exc = exc_type(exc_value).with_traceback(e.__traceback__)
            raise new_exc from None