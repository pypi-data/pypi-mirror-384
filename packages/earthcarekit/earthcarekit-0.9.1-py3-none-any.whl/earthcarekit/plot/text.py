import matplotlib.patheffects as pe
from matplotlib.text import Text

from .color import Color, ColorLike


def add_shade_to_text(
    t: Text,
    alpha: float = 0.8,
    linewidth: float = 3,
    color: Color | ColorLike | None = None,
) -> Text:
    """Applies a shaded stroke effect around a Matplotlib text object.

    Args:
        t (Text): Matplotlib text object to apply the effect to.
        alpha (float, optional): Opacity of the stroke. Defaults to 0.8.
        linewidth (float, optional): Width of the stroke line. Defaults to 3.
        color (Color | ColorLike, optional): Color of the stroke. Defaults to "white".

    Returns:
        Text: The text object with the stroke effect applied.
    """

    if color is None:
        c = Color.from_optional(t.get_color())  # type: ignore
        color = c.get_best_bw_contrast_color()  # type: ignore
    else:
        color = Color.from_optional(color)

    t.set_path_effects(
        [pe.withStroke(linewidth=linewidth, foreground=color, alpha=alpha)]
    )
    return t
