###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Module used for Event subscription."""

__all__ = (
    'Event',
    'EventBus',
)

from collections.abc import Callable
from typing import Optional

from .utils import get_parent_doc


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


class _EventBusMeta(type):
    """Metaclass for :py:class:`EventBus` type.

    Maps :py:class:`EventBus` objects to :py:class:`str` ids
    and allows accessing those ids using subscripts on :py:class:`EventBus`.
    """
    _id_bus_map: dict[str, 'EventBus'] = {}

    @classmethod
    def __getitem__(mcs, id: str) -> Optional['EventBus']:
        return mcs._id_bus_map.get(id.lower())

    @classmethod
    def __setitem__(mcs, id: str, bus: 'EventBus') -> None:
        """Set an :py:class:`EventBus` from the bus map."""
        if not isinstance(id, str):
            raise TypeError(f'parameter {id=} is not of type {str}.')
        if not isinstance(bus, EventBus):
            raise TypeError(f'parameter {bus=} is not of type {EventBus}.')
        mcs._id_bus_map[id.lower()] = bus

    @classmethod
    def __delitem__(mcs, id: str) -> None:
        """Delete an :py:class:`EventBus` from the bus map."""
        del mcs._id_bus_map[id.lower()]


# pylint: disable=deprecated-typing-alias
class EventBus(metaclass=_EventBusMeta):
    """Object that keeps track of all :py:class:`Callable` subscriptions to :py:class:`Event`'s.

    All :py:class:`EventBus`'s are stored in the class with a unique id.
    You can access created :py:class:`EventBus`'s with subscripts. ex::

        EventBus['foo'] -> None
        EventBus('foo') -> EventBus object at 0x000000001
        EventBus['foo'] -> EventBus object at 0x000000001
        del EventBus['foo']
        EventBus['foo'] -> None
    """

    def __init__(self, __id: str, /) -> None:
        """Create a new :py:class:`EventBus` object with a unique id.

        All ids are transformed to lowercase in the :py:class:`_EventBusMeta` id map.

        :param __id: id to register this instance as.
        :raises KeyError: When a bus with the given id already exists.
        """
        if type(self)[__id] is None:
            self._event_subscribers: dict[type[Event], list[tuple[
                Callable[[Event], None] | Callable,  # Callable to run
                Callable[[Event], bool] | None       # Optional predicate to run callable
            ]]] = {}
            type(self)[__id] = self
        else:
            raise KeyError(f'EventBus id "{__id}" is already defined in {type(type(self)).__name__}')

    def clear(self, event: type[Event] | None = None) -> None:
        """Clear event subscribers of a given type.

        None is treated as a wildcard and deletes ALL event subscribers.

        :param event: Event type to clear.
        """
        if event is None:
            self._event_subscribers.clear()
        else:
            self._event_subscribers.pop(event)

    def fire(self, event: Event | type[Event]) -> None:
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
        for event_type in self._event_subscribers:
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

    def subscribe(self, __callable: Callable, /, event: type[Event], event_predicate: Callable[[Event], bool] | None = None) -> None:
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
