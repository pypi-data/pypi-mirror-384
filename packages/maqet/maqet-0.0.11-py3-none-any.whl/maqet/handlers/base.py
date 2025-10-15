import inspect
from abc import ABC
from typing import Callable

from benedict import benedict

from maqet.logger import LOG


class HandlerError(Exception):
    """
    Handler error
    """


class Handler(ABC):
    """
    Interface for Maqet state processors
    """
    __METHODS = {}

    @classmethod
    def method(self, function: Callable, **kwargs):
        """
        Decorator to add method to handler methods
        """
        name = kwargs.get('name', function.__name__)
        handler_name = self.__name__
        if handler_name not in self.__METHODS:
            self.__METHODS[handler_name] = {}

        self.__METHODS[handler_name][name] = function

        # TODO: add signature check:
        # method(state: dict, *args, **kwargs)

        def stub(*args, **kwargs):
            raise HandlerError("Handler method called outside of handler")

        return stub

    def __init__(self, state: dict,
                 argument: list | dict | str,
                 *args, **kwargs):

        self.state = benedict(state)
        self.error_fatal = kwargs.get('error_fatal', False)

        self.__execute(argument)

    def __execute(self, argument: list | dict | str):
        if isinstance(argument, list):
            LOG.debug(f"Argument {argument} - splitting into subarguments")
            for subargument in argument:
                self.__execute(subargument)
        elif isinstance(argument, dict):
            LOG.debug(f"Argument {argument} - running by key-value")
            for method_name, subargument in argument.items():
                self.__call_method(method_name, subargument)
        elif isinstance(argument, str):
            LOG.debug(f"Argument {argument} - running without argument")
            self.__call_method(argument, None)
        else:
            self.__fail("Type check error"
                        f" {argument} is not list | dict | str")

    @classmethod
    def method_exists(self, method_name: str) -> bool:
        if method_name not in self.__METHODS[self.__name__]:
            LOG.debug(f"{self.__name__}::{method_name} not exists")
            return False
        LOG.debug(f"{self.__name__}::{method_name} exists")
        return True

    @classmethod
    def get_methods(self) -> list:
        return self.__METHODS[self.__name__].keys()

    def __call_method(self,
                      method_name: str,
                      argument: list | dict | str = None):

        if not self.method_exists(method_name):
            self.__fail(f"Method '{method_name}' not available"
                        f" in {self.__class__.__name__}")
        method = self.__METHODS[self.__class__.__name__].get(method_name)

        LOG.debug(f"Inspecting signature for {method_name}: {inspect.signature(method)}")
        LOG.debug(f"{self.__class__.__name__}::"
                  f"{method.__name__}({str(argument)})")
        try:
            if isinstance(argument, list):
                method(self.state, *argument)
            elif isinstance(argument, dict):
                method(self.state, **argument)
            elif argument is None:
                method(self.state)
            else:
                method(self.state, argument)
        except Exception as exc:
            msg = f"{method_name}({argument}) execution error\n{exc}\n"
            self.__fail(msg)

    def __fail(self, msg: str):
        if self.error_fatal:
            raise HandlerError(msg)
        else:
            LOG.error(msg)
