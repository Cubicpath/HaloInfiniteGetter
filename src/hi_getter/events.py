###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module used for Event subscription."""

__all__ = (
    'DeferredCallable',
    'Event',
    'EventBus',
)

from collections.abc import Callable
from collections.abc import Generator
from typing import Any
from typing import Type

from .utils import get_parent_doc


class DeferredCallable:
    """A :py:class:`Callable` with args and kwargs stored for further execution.

    Supports deferred argument evaluation when using :py:class:`Callable`'s as arguments.
    This allows the value of the stored arguments to dynamically change depending on
    when the :py:class:`DeferredCallable` is executed.
    """
    __slots__ = ('__no_event_arg__', 'callable', 'args', 'kwargs')

    def __init__(self, __callable: Callable, /, *args: Any | Callable, _event: bool = False, **kwargs: Any | Callable) -> None:
        """Creates a new :py:class:`DeferredCallable`.

        :param __callable: Callable to store for later execution.
        :param args: positional arguments to store
        :param _event: Whether to accept an additional positional argument
        :param kwargs: keyword arguments to store
        """
        self.__no_event_arg__ = not _event
        self.callable: Callable = __callable
        self.args:     tuple[Any | Callable, ...] = args
        self.kwargs:   dict[str, Any | Callable] = kwargs

    def __call__(self, *args, **kwargs) -> Any:
        """Syntax sugar for self.run()"""
        return self.run(*args, **kwargs)

    def run(self, *args, call_args: bool = True, **kwargs) -> Any:
        """Run the stored :py:class:`Callable`.

        Takes any additional arguments and temporarily adds to the stored arguments before execution.

        :param args: positional arguments to pass to callable.
        :param call_args: Whether to call callable arguments.
        :param kwargs: keyword arguments to pass callable.
        """
        # Add additional arguments from local args
        args: tuple[Any | Callable, ...] = self.args + args
        kwargs |= self.kwargs  # PEP 0584

        # Evaluate all callable arguments
        if call_args:
            args:   Generator[Any] = (arg() if callable(arg) else arg for arg in args)
            kwargs: dict[Any] = {key: val() if callable(val) else val for key, val in kwargs.items()}

        return self.callable(*args, **kwargs)


class Event:
    """Normal event with no special abilities."""
    __slots__ = ()

    @property
    def name(self) -> str:
        """Name of event.

        Defaults to class name.
        """
        return type(self).__name__

    @property
    def description(self) -> str:
        """Short description of the event.

        Defaults to the first line of the nearest type doc in the mro.
        """
        doc = self.__doc__
        if doc is None and isinstance(self, Event) and type(self) is not Event:
            doc = get_parent_doc(type(self))
        return doc.splitlines()[0]


# pylint: disable=deprecated-typing-alias
class EventBus:
    """Object that keeps track of all :py:class:`Callable` subscriptions to :py:class:`Event`'s.

    All eventbuses are stored in the class with a unique id.
    """

    def __init__(self) -> None:
        self._event_subscribers: dict[Type[Event], list[tuple[
            Callable[[Event], None] | Callable,  # Callable to run
            Callable[[Event], bool] | None       # Optional predicate to run callable
        ]]] = {}

    def clear(self, event: Type[Event] | None = None) -> None:
        """Clear event subscribers of a given type.

        None is treated as a wildcard and deletes ALL event subscribers.

        :param event: Event type to clear.
        """
        if event is None:
            self._event_subscribers.clear()
        else:
            self._event_subscribers.pop(event)

    def fire(self, event: Event | Type[Event]) -> None:
        """Fire all :py:class:`Callables` subscribed to the :py:class:`Event`'s :py:class:`type`.

        :py:class:`Event` subclasses call their parent's callables as well.
        Ex: ChildEvent will fire ParentEvent, but ParentEvent will not fire ChildEvent.

        If event is a :py:class:`type`, it is instantiated with no arguments.

        :param event: Event object passed to callables as an argument.
        """
        # Transform Event types to their default instances
        if isinstance(event, type) and issubclass(event, Event):
            event = event()

        # Run all current and parent event callables
        for event_type in self._event_subscribers.keys():
            if isinstance(event, event_type):
                for e_callable_pair in self._event_subscribers[event_type]:
                    # Check predicate if one is given
                    if e_callable_pair[1] is None or e_callable_pair[1](event):

                        # Add event to args if dunder __no_event_arg__ does not evaluate to True
                        event_args = (event,)
                        if hasattr(e_callable_pair[0], '__no_event_arg__') and getattr(e_callable_pair[0], '__no_event_arg__') is True:
                            event_args = ()

                        # Finally, call
                        e_callable_pair[0](*event_args)

    def subscribe(self, __callable: Callable, /, event: Type[Event], event_predicate: Callable[[Event], bool] | None = None) -> None:
        """Subscribe a :py:class:`Callable` to an :py:class:`Event` type.

        By default, every time an :py:class:`Event` is fired, it will call the callable with the event as an argument.

        If the :py:class:`Callable` as the attribute "__no_event_arg__" set to True,
        no arguments are passed to the callable during execution. :py:class:`DeferredCallable` has
        this set to True during default initialization.

        :param __callable: Callable to run.
        :param event: Event to subscribe to.
        :param event_predicate: Predicate to validate before running callable.
        """
        callable_pair = (__callable, event_predicate)
        if self._event_subscribers.get(event) is None:
            # Create event key if not yet defined
            self._event_subscribers[event] = [callable_pair]
        else:
            self._event_subscribers.get(event, []).append(callable_pair)
