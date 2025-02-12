# ---------- Dark Theme Colors ----------
DARK_BG = "#2b2b2b"  # Base background for empty/discovered tiles
UNDISCOVERED_BG = "#1a1a1a"  # Background for undiscovered tiles
BUTTON_BG = "#444444"  # Button background
BUTTON_FG = "white"  # Button text
ENTRY_BG = "#333333"  # Entry background
ENTRY_FG = "white"  # Entry text
DARK_FG = "white"  # Default text color

# ---------- Highlight Colors ----------
ALLOWED_MOVE_COLOR = "#666666"  # Allowed move tiles
REMOTE_ALLOWED_COLOR = "#1E90FF"  # Allowed remote planting (blue)
SELECTED_TILE_COLOR = "#955595"  # Selected grid element (purple)
ACTIVE_PLAYER_TILE_COLOR = "#005000"  # Active player's cell
FIELD_OF_VIEW_COLOR = "#3a3a3a"  # Tiles within discovery range, not used afaik
DEBRIS_ALLOWED_COLOR = "#FF4500"  # Allowed debris deployment targets (orange-red)

# ---------- Tile Backgrounds for discovered tiles ----------
EMPTY_TILE_BG = DARK_BG
ASTEROID_BG = "#444444"  # Background for a tile that contains an asteroid
DEBRIS_BG = "#111111"  # Background for debris (impassable)

# ---------- Object Colors ----------
PLAYER_COLORS = ["#E87BFF", "#99FF8A", "#91DCFF", "#FFC899", "#9367DE", "#C2C3FF"]
DEFAULT_ASTEROID_COLOR = "white"

# =================== Helper Functions ===================

def manhattan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)



# ----------------------------------------------------------------------
# UI Constants and Standardized Fonts
# ----------------------------------------------------------------------
UI_PADDING_SMALL = 5
UI_PADDING_MEDIUM = 10
UI_PADDING_GRID_CELL = 1

FONT_FAMILY = "Arial"
FONT_TIMER = (FONT_FAMILY, 30, "bold")
FONT_MONEY = (FONT_FAMILY, 24, "bold")
FONT_PLAYER_INFO = (FONT_FAMILY, 10, "bold")
FONT_TILE_INFO = (FONT_FAMILY, 10)
FONT_HEADER = (FONT_FAMILY, 14, "bold")
FONT_NORMAL = (FONT_FAMILY, 10)

GRID_CELL_WIDTH = 4
GRID_CELL_HEIGHT = 2
TEXT_WIDGET_WIDTH = 40
TEXT_WIDGET_HEIGHT = 15
INFO_LABEL_WIDTH = 40
INFO_LABEL_HEIGHT = 6

TIMER_DELAY_MS = 1000



FONT_FAMILY = "Arial"

# Standardized fonts for PANELS
FONT_SMALL = (FONT_FAMILY, 10)
FONT_MEDIUM = (FONT_FAMILY, 12, "bold")
FONT_HEADER = (FONT_FAMILY, 14, "bold")



# for lenses

def short_num(n):
    """
    Return a shortened string representation of n using k/M such that
    the resulting string is at most 3 characters long.

    Examples:
      999    -> "999"
      1000   -> "1k"
      15000  -> "15k"
      123456 -> "12k"   # note: resolution is sacrificed to keep it short
      1000000-> "1M"
    """
    if n < 1000:
        return str(int(n))
    # For numbers in the thousands we want either 1- or 2-digit number before the suffix.
    elif n < 1000000:
        return f"{int(n // 1000)}k"
    else:
        return f"{int(n // 1000000)}M"


import colorsys


def value_to_bg(val, min_val, max_val, base_color, dark=0, bright=100):
    """
    Returns a hex color string with the same hue and saturation as `base_color`
    but with brightness (lightness) varying between the provided `dark` and `bright`
    bounds (which are in the 0-255 range).

    Parameters:
      val        : The current numeric value.
      min_val    : The minimum value in the range.
      max_val    : The maximum value in the range.
      base_color : A hex color string (e.g. "#RRGGBB") that provides the base hue and saturation.
      dark       : The lower bound for brightness (default 50, corresponding to dark).
      bright     : The upper bound for brightness (default 255, corresponding to fully bright).

    Returns:
      A hex color string representing the base color with adjusted brightness.
    """
    # Remove '#' if present and validate input length
    base_color = base_color.lstrip('#')
    if len(base_color) != 6:
        raise ValueError("base_color must be a 6-digit hex string (e.g. '#RRGGBB').")

    # Convert hex to RGB integers
    r = int(base_color[0:2], 16)
    g = int(base_color[2:4], 16)
    b = int(base_color[4:6], 16)

    # Normalize the RGB components to the [0,1] range for colorsys
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0

    # Convert RGB to HLS (Hue, Lightness, Saturation)
    h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)

    # Map the value to a new lightness level.
    # First, normalize the dark and bright bounds to [0,1]
    dark_norm = dark / 255.0
    bright_norm = bright / 255.0

    # Compute the interpolation fraction (avoid division by zero)
    if max_val == min_val:
        new_l = dark_norm
    else:
        fraction = (val - min_val) / (max_val - min_val)
        new_l = dark_norm + (bright_norm - dark_norm) * fraction

    # Convert back to RGB using the new lightness while preserving hue and saturation.
    new_r_norm, new_g_norm, new_b_norm = colorsys.hls_to_rgb(h, new_l, s)
    new_r = int(round(new_r_norm * 255))
    new_g = int(round(new_g_norm * 255))
    new_b = int(round(new_b_norm * 255))

    return f"#{new_r:02x}{new_g:02x}{new_b:02x}"
