from contextlib import contextmanager
import dearpygui.dearpygui as dpg


_pages = {}
_active_pages = {}


def _try_get_window():
    dummy = dpg.add_spacer()
    parent = dpg.get_item_parent(dummy)
    dpg.delete_item(dummy)

    while parent and dpg.get_item_type(parent) != "mvAppItemType::mvWindowAppItem":
        parent = dpg.get_item_parent(parent)
    return parent

def _check_window(window):
    if window is None:
        window = _try_get_window()
        if window is None:
            raise ValueError("No window specified and could not infer from context.")
    if isinstance(window, str):
        window = dpg.get_alias_id(window)
    return window


@contextmanager
def page(label: str, window=None, show_callback=None, hide_callback=None):
    """
    Context manager for creating or reusing a page in a DearPyGui window.

    parameters:
    - label (str): Unique name for the page within the window.
    - window (int or str, optional): ID or alias of the parent window. If None, attempts to infer the current window from context.
    - show_callback (callable, optional): Function called when this page is shown.
    - hide_callback (callable, optional): Function called when this page is hidden.

    yields:
    - group_id (int): ID of the underlying DearPyGui group representing the page.
    """
    window = _check_window(window)
    
    existing_page = _pages.get(window, {}).get(label)
    if existing_page:
        group_id = existing_page["page"]
        dpg.push_container_stack(group_id, parent=window)
        try: 
            yield group_id
        finally:
            dpg.pop_container_stack()
    else:
        group_id = dpg.generate_uuid()
        dpg.push_container_stack(dpg.add_group(tag=group_id, show=False, parent=window))
        try: 
            yield group_id
        finally:
            _pages.setdefault(window, {})[label] = {
                "page": group_id,
                "show_callback": show_callback,
                "hide_callback": hide_callback
            }
            dpg.pop_container_stack()


def add_page(label: str, window=None, show_callback=None, hide_callback=None):
    """
    Adds a page to the specified window.

    parameters:
    - label (str): Unique name for the page within the window.
    - window (int or str, optional): ID or alias of the parent window. If None, attempts to infer the current window from context.
    - show_callback (callable, optional): Function called when this page is shown.
    - hide_callback (callable, optional): Function called when this page is hidden.
    
    returns:
    - group_id (int): ID of the underlying DearPyGui group representing the page.
    """
    window = _check_window(window)

    existing_page = _pages.get(window, {}).get(label)
    if existing_page:
        return existing_page["page"]

    group_id = dpg.add_group(tag=dpg.generate_uuid(), show=False, parent=window)
    _pages.setdefault(window, {})[label] = {
        "page": group_id,
        "show_callback": show_callback,
        "hide_callback": hide_callback
    }
    return group_id


def show_page(label: str, window):
    """
    Shows the specified page, hiding any currently active page in its window.
    
    parameters:
    - label (str): Name of the page to show.
    - window (int or str): ID or alias of the parent window.
    """
    if isinstance(window, str):
        window = dpg.get_alias_id(window)

    if _pages.get(window) is None or _pages[window].get(label) is None:
        raise KeyError(f"Page '{label}' in window '{window}' does not exist.")
     
    page = _pages[window][label]["page"]
    show_callback = _pages[window][label]["show_callback"]
    hide_callback = _pages[window][label]["hide_callback"]

    former_page = _active_pages.get(window)
    if former_page is not None:
        dpg.configure_item(former_page["page"], show=False)
        if former_page["hide_callback"] is not None:
            former_page["hide_callback"]()

    dpg.configure_item(page, show=True)
    _active_pages[window] = {"page": page, "hide_callback": hide_callback}
    if show_callback is not None:
        show_callback()
