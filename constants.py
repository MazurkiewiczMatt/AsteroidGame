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




FONT_FAMILY = "Arial"