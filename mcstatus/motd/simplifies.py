from __future__ import annotations

from collections.abc import Sequence

from mcstatus.motd.components import Formatting, MinecraftColor, ParsedMotdComponent, WebColor


def get_unused_elements(parsed: Sequence[ParsedMotdComponent]) -> set[int]:
    """Get indices of all items which are unused and can be safely removed from the MOTD.

    This is a wrapper method around several unused item collection methods.
    """
    to_remove: set[int] = set()

    for simplifier in [get_double_items, get_double_colors, get_formatting_before_color, get_empty_text, get_end_non_text]:
        to_remove.update(simplifier(parsed))

    return to_remove


def get_double_items(parsed: Sequence[ParsedMotdComponent]) -> set[int]:
    """Get indices of all doubled items that can be removed.

    Removes any items that are followed by an item of the same kind (compared using ``__eq__``).
    """
    to_remove: set[int] = set()

    for index, item in enumerate(parsed):
        try:
            next_item = parsed[index + 1]
        except IndexError:  # Last item (without any next item)
            break

        if isinstance(item, (Formatting, MinecraftColor, WebColor)) and item == next_item:
            to_remove.add(index)

    return to_remove


def get_double_colors(parsed: Sequence[ParsedMotdComponent]) -> set[int]:
    """Get indices of all doubled color items.

    As colors (obviously) override each other, we only ever care about the last one, ignore
    the previous ones. (for example: specifying red color, then orange, then yellow, then some text
    will just result in yellow text)
    """
    to_remove: set[int] = set()

    prev_color: int | None = None
    for index, item in enumerate(parsed):
        if isinstance(item, (MinecraftColor, WebColor)):
            # If we found a color after another, remove the previous color
            if prev_color is not None:
                to_remove.add(prev_color)
            prev_color = index

        # If we find a string, that's what our color we found previously applies to,
        # set prev_color to None, marking this color as used
        if isinstance(item, str):
            prev_color = None

    return to_remove


def get_formatting_before_color(parsed: Sequence[ParsedMotdComponent]) -> set[int]:
    """Obtain indices of all unused formatting items before colors.

    Colors override any formatting before them, meaning we only ever care about the color, and can
    ignore all formatting before it. (For example: specifying bold formatting, then italic, then yellow,
    will just result in yellow text.)
    """
    to_remove: set[int] = set()

    collected_formattings = []
    for index, item in enumerate(parsed):
        # Collect the indices of formatting items
        if isinstance(item, Formatting):
            collected_formattings.append(index)

        # Only run checks if we have some collected formatting items
        if len(collected_formattings) == 0:
            continue

        # If there's a string after some formattings, the formattings apply to it.
        # This means they're not unused, remove them.
        if isinstance(item, str):
            collected_formattings = []
            continue

        # If there's a color after some formattings, these formattings will be overridden
        # as colors reset everything. This makes these formattings pointless, mark them
        # for removal.
        if isinstance(item, (MinecraftColor, WebColor)):
            to_remove.update(collected_formattings)
            collected_formattings = []
    return to_remove


def get_empty_text(parsed: Sequence[ParsedMotdComponent]) -> set[int]:
    """Get indices of all empty text items.

    Empty strings in motd serve no purpose and can be marked for removal.
    """
    to_remove: set[int] = set()

    for index, item in enumerate(parsed):
        if isinstance(item, str) and len(item) == 0:
            to_remove.add(index)

    return to_remove


def get_end_non_text(parsed: Sequence[ParsedMotdComponent]) -> set[int]:
    """Get indices of all trailing items, found after the last text component.

    Any color/formatting items only make sense when they apply to some text.
    If there are some at the end, after the last text, they're pointless and
    can be removed.
    """
    to_remove: set[int] = set()

    for rev_index, item in enumerate(reversed(parsed)):
        # The moment we find our last string, stop the loop
        if isinstance(item, str):
            break

        # Remove any color/formatting that doesn't apply to text
        if isinstance(item, (MinecraftColor, WebColor, Formatting)):
            index = len(parsed) - 1 - rev_index
            to_remove.add(index)

    return to_remove
