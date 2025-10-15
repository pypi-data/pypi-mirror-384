"""Observer pattern implementation for GUI synchronization.

This module provides the observer pattern to allow GUIs and other
components to be notified of state changes without tight coupling.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Observer(ABC):
    """Abstract base class for observers.

    Observers register with Observable objects to receive notifications
    when the observable's state changes.
    """

    @abstractmethod
    def update(self, observable: Observable, **kwargs: Any) -> None:
        """Called when the observed object changes.

        Args:
            observable: The object that changed
            **kwargs: Additional context about the change
        """
        pass


class Observable:
    """Base class for objects that can be observed.

    Observable objects maintain a list of observers and notify them
    when their state changes. This is useful for keeping GUIs in sync
    with game state.
    """

    def __init__(self) -> None:
        """Initialize the observable object."""
        self._observers: List[Observer] = []
        self._notification_enabled = True

    def attach(self, observer: Observer) -> None:
        """Attach an observer to this observable.

        Args:
            observer: The observer to attach
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """Detach an observer from this observable.

        Args:
            observer: The observer to detach
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, **kwargs: Any) -> None:
        """Notify all observers of a state change.

        Args:
            **kwargs: Additional context to pass to observers
        """
        if not self._notification_enabled:
            return

        for observer in self._observers:
            observer.update(self, **kwargs)

    def enable_notifications(self) -> None:
        """Enable observer notifications."""
        self._notification_enabled = True

    def disable_notifications(self) -> None:
        """Disable observer notifications temporarily."""
        self._notification_enabled = False

    def has_observers(self) -> bool:
        """Check if this observable has any observers."""
        return len(self._observers) > 0

    def observer_count(self) -> int:
        """Get the number of attached observers."""
        return len(self._observers)


class PropertyObservable(Observable):
    """Observable that tracks changes to specific properties.

    This class extends Observable to provide fine-grained observation
    of individual properties.
    """

    def __init__(self) -> None:
        """Initialize the property observable."""
        super().__init__()
        self._property_observers: Dict[str, List[Observer]] = {}

    def attach_to_property(self, property_name: str, observer: Observer) -> None:
        """Attach an observer to a specific property.

        Args:
            property_name: The name of the property to observe
            observer: The observer to attach
        """
        if property_name not in self._property_observers:
            self._property_observers[property_name] = []
        if observer not in self._property_observers[property_name]:
            self._property_observers[property_name].append(observer)

    def detach_from_property(self, property_name: str, observer: Observer) -> None:
        """Detach an observer from a specific property.

        Args:
            property_name: The name of the property
            observer: The observer to detach
        """
        if property_name in self._property_observers and observer in self._property_observers[property_name]:
            self._property_observers[property_name].remove(observer)

    def notify_property_changed(self, property_name: str, old_value: Any = None, new_value: Any = None) -> None:
        """Notify observers that a specific property changed.

        Args:
            property_name: The name of the property that changed
            old_value: The previous value
            new_value: The new value
        """
        if not self._notification_enabled:
            return

        # Notify property-specific observers
        if property_name in self._property_observers:
            for observer in self._property_observers[property_name]:
                observer.update(self, property=property_name, old_value=old_value, new_value=new_value)

        # Also notify general observers
        self.notify(property=property_name, old_value=old_value, new_value=new_value)
