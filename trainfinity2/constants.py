from arcade import color

GRID_WIDTH_CELLS = 20
GRID_HEIGHT_CELLS = 20
GRID_WIDTH_PIXELS = 600
GRID_HEIGHT_PIXELS = 600
GRID_BOX_SIZE_PIXELS = 30
GRID_LINE_WIDTH = 1
GRID_COLOR = color.BLACK
FINISHED_RAIL_COLOR = [128, 128, 128]  # Gray
BUILDING_RAIL_COLOR = [128, 128, 128, 128]  # Gray translucent
BUILDING_ILLEGAL_RAIL_COLOR = [255, 0, 0, 128]  # Red translucent
RAIL_TO_BE_DESTROYED_COLOR = [255, 0, 0, 128]  # Red
HIGHLIGHT_COLOR = [255, 128, 128, 128]  # Light red translucent
RAIL_LINE_WIDTH = 2
WATER_TILES = 20

PIXEL_OFFSET_PER_CARGO = 4
CARGO_SIZE = GRID_BOX_SIZE_PIXELS / 3
SECONDS_BETWEEN_CARGO_CREATION = 2
