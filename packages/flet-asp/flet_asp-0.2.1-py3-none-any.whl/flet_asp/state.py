from flet import Page, Control
from typing import Any, Callable, Dict, Optional
from flet.core.ref import Ref

from flet_asp.atom import Atom
from flet_asp.selector import Selector


class StateManager:
    """
    A reactive global state manager following the Atom/Selector pattern (Flet-ASP).

    Each key represents an isolated Atom or derived Selector. Useful for building
    modular and predictable UI state.

    Features:
        - Automatic flush of pending updates after page.update()
        - Hybrid update strategy for reliable bindings
        - Python 3.14+ optimizations (free-threading, incremental GC)

    Attributes:
        _atoms (Dict[str, Atom]): All registered atom states.
        _selectors (Dict[str, Selector]): All registered computed selectors.
        _page (Optional[Page]): Reference to the Flet page (if provided).
    """

    def __init__(self, page: Optional[Page] = None):
        self._atoms: Dict[str, Atom] = {}
        self._selectors: Dict[str, Selector] = {}
        self._page: Optional[Page] = page

        # Hook page.update() to flush pending updates automatically
        if page:
            self._hook_page_update(page)

    def _hook_page_update(self, page: Page) -> None:
        """
        Hooks into page.update() to automatically flush pending atom updates.

        This ensures that any controls that were bound before being added to the page
        will be updated as soon as page.update() is called.

        Args:
            page (Page): The Flet page to hook.
        """
        # Only hook if page has update method (defensive programming for tests/mocks)
        if not hasattr(page, "update") or not callable(getattr(page, "update", None)):
            return

        original_update = page.update

        def wrapped_update(*args, **kwargs):
            # Call original page.update()
            result = original_update(*args, **kwargs)

            # Flush all pending updates from all atoms
            for atom in self._atoms.values():
                atom._flush_pending_updates()

            # Selectors inherit from Atom, so flush them too
            for selector in self._selectors.values():
                selector._flush_pending_updates()

            return result

        # Replace page.update with wrapped version
        page.update = wrapped_update

    def atom(self, key: str, default: Optional[Any] = None) -> Atom:
        """
        Returns the Atom for a given key, or creates it with an optional default value.

        Args:
            key (str): Unique key for the atom.
            default (Any, optional): Initial value.

        Returns:
            Atom: The corresponding atom instance.
        """

        if key in self._selectors:
            raise ValueError(f"Key '{key}' is already registered as a Selector.")

        if key not in self._atoms:
            self._atoms[key] = Atom(default, key=key)

        return self._atoms[key]

    def _resolve_atom_or_selector(self, key: str) -> Atom:
        """
        Internal method to resolve both atoms and selectors.

        This allows selectors to depend on other selectors, not just atoms.

        Args:
            key (str): The key to resolve.

        Returns:
            Atom: The atom or selector (which inherits from Atom).
        """
        if key in self._selectors:
            return self._selectors[key]
        return self.atom(key)

    def add_selector(
        self, key: str, select_fn: Callable[[Callable[[str], Any]], Any]
    ) -> Selector:
        """
        Registers a derived reactive value (Selector) from existing atoms or other selectors.

        Args:
            key (str): Unique key for the selector.
            select_fn (Callable): Function that derives the value.

        Returns:
            Selector: The registered selector.
        """

        if key in self._atoms:
            raise ValueError(f"Key '{key}' is already registered as an Atom.")

        if key not in self._selectors:
            self._selectors[key] = Selector(select_fn, self._resolve_atom_or_selector)

        return self._selectors[key]

    def get(self, key: str) -> Any:
        """
        Retrieves the current value of an Atom or Selector.

        Args:
            key (str): The key of the state.

        Returns:
            Any: Current value.
        """

        if key in self._selectors:
            return self._selectors[key].value
        return self.atom(key).value

    def set(self, key: str, value: Any) -> None:
        """
        Updates the value of an Atom.

        Args:
            key (str): Atom key.
            value (Any): New value.
        """

        self._set_atom_value(key, value)

    def _set_atom_value(self, key: str, value: Any) -> None:
        """
        Internal method for updating atom values.

        Args:
            key (str): Atom key.
            value (Any): New value.
        """

        self.atom(key)._set_value(value)

    def bind(
        self, key: str, control: Ref, prop: str = "value", update: bool = True
    ) -> None:
        """
        Binds an Atom or Selector to a Ref (Flet UI element).

        Args:
            key (str): State key.
            control (Ref): Flet control Ref.
            prop (str): Property to bind (default: "value").
            update (bool): Call `update()` after assignment.
        """

        if key in self._selectors:
            self._selectors[key].bind(control, prop, update)
        else:
            self.atom(key).bind(control, prop, update)

    def bind_dynamic(
        self, key: str, control: Control | Ref, prop: str = "value", update: bool = True
    ):
        """
        Dynamically binds state to a Control or Ref (for flexible layouts).

        Args:
            key (str): State key.
            control (Control | Ref): Flet UI component or Ref.
            prop (str): Property to bind.
            update (bool): Call `update()` after change.
        """

        if key in self._selectors:
            self._selectors[key].bind_dynamic(control, prop, update)
        else:
            self.atom(key).bind_dynamic(control, prop, update)

    def bind_two_way(
        self,
        key: str,
        control: Ref,
        prop: str = "value",
        update: bool = True,
        on_input_change: Callable = None,
    ):
        """
        Creates a two-way binding between Atom and a Ref input (e.g. TextField).

        Args:
            key (str): Atom key.
            control (Ref): Input control.
            prop (str): Property to sync (default: "value").
            update: (bool): Call `update()` after change.
            on_input_change (Callable, optional): Custom change handler.
        """

        if key in self._selectors:
            raise ValueError("bind_two_way is not supported for selectors")

        self.atom(key).bind_two_way(control, prop, update, on_input_change)

    def unbind(self, key: str, target: Control | Ref):
        """
        Unbinds a Ref or Control from a state key.

        Args:
            key (str): State key.
            target (Control | Ref): Control or reference to unbind.
        """

        atom = self._selectors.get(key) or self._atoms.get(key)
        if not atom:
            return

        if isinstance(target, Ref):
            atom.unbind(target)
        elif isinstance(target, Control) and hasattr(target, "ref"):
            atom.unbind(target.ref)

    def listen(
        self, key: str, callback: Callable[[Any], None], immediate: bool = True
    ) -> None:
        """
        Registers a listener function for a given key.

        Args:
            key (str): State key.
            callback (Callable): Function to call when value changes.
            immediate (bool): Call immediately with current value.
        """

        atom = self._selectors[key] if key in self._selectors else self.atom(key)

        if any(cb == callback for cb in atom._listeners):
            return

        atom.listen(callback, immediate)

    def listen_multiple(self, keys_callbacks: dict[str, Callable[[Any], None]]):
        """
        Registers multiple listeners at once.

        Args:
            keys_callbacks (dict): Map of key → callback.
        """

        for key, callback in keys_callbacks.items():
            self.listen(key, callback)

    def unlisten(self, key: str, callback: Callable[[Any], None]):
        """
        Removes a previously registered listener.

        Args:
            key (str): State key.
            callback (Callable): Listener to remove.
        """

        atom = self._selectors.get(key) or self._atoms.get(key)
        if atom:
            atom.unlisten(callback)

    def has(self, key: str) -> bool:
        """
        Checks if a key is registered in the state.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if exists.
        """

        return key in self._atoms or key in self._selectors

    def reset(self, key: str, value: Any = None) -> None:
        """
        Resets an Atom value to default.

        Args:
            key (str): Atom key.
            value (Any): New default value.

        Raises:
            ValueError: If key is a selector.
        """

        if key in self._atoms:
            self._set_atom_value(key, value)
        elif key in self._selectors:
            raise ValueError(f"Selector '{key}' cannot be reset directly.")

    def delete(self, key: str):
        """
        Removes a state key from memory.

        Args:
            key (str): Key to delete.
        """

        self._atoms.pop(key, None)
        self._selectors.pop(key, None)

    def clear(self) -> None:
        """
        Clears all atoms and listeners from memory.

        Ideal for logout or session reset.
        """

        for atom in self._atoms.values():
            atom.clear_listeners()

        for s in self._selectors.values():
            s.clear_listeners()

        self._atoms.clear()
        self._selectors.clear()

    def invalidate(self, key: str):
        """
        Forces recomputation of a selector.

        Args:
            key (str): Selector key.
        """

        if key in self._selectors:
            self._selectors[key].recompute()

    def selector(self, key: str):
        """
        Decorator for creating a named selector.

        Example:
            @selector("full_name")
            def full_name(get):
                return f"{get('first_name')} {get('last_name')}"

        Args:
            key (str): Selector key.

        Returns:
            Callable: Decorator wrapper.
        """

        def decorator(func):
            self.add_selector(key, func)
            return func

        return decorator


def get_state_manager(page: Page) -> StateManager:
    """
    Returns a page-scoped singleton instance of StateManager with automatic flush support.

    This function creates a StateManager bound to the page and hooks into page.update()
    to automatically process pending control updates from the hybrid binding strategy.

    Args:
        page (Page): Flet page context.

    Returns:
        StateManager: Unique manager instance for the page with automatic flush enabled.

    Example:
        >>> import flet as ft
        >>> import flet_asp as fa
        >>>
        >>> def main(page: ft.Page):
        >>>     state = fa.get_state_manager(page)
        >>>     state.atom("count", 0)
        >>>     # Now bindings will work even if controls aren't added yet!
    """
    if not hasattr(page, "_state_manager"):
        manager = StateManager(page)  # Pass page for automatic flush
        setattr(page, "_state_manager", manager)
        setattr(page, "state", manager)

    return getattr(page, "_state_manager")
