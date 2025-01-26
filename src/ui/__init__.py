from .animations import Animation
from .progress import Progress
from .graphs import ASCIIGraph
from .colors import ColorScheme
from .menu import Menu, MenuItem
from .colors import NexusColors
__all__ = [
    'Animation',
    'Progress',
    'ASCIIGraph',
    'ColorScheme',
    'Menu',
    'MenuItem',

    'NexusColors'
]

# UI Configuration
DEFAULT_THEME = 'default'
ANIMATION_SPEED = 0.1
REFRESH_RATE = 60
ENABLE_COLORS = True

# UI Components Registry
UI_COMPONENTS = {
    'animations': Animation,
    'progress': Progress,
    'graphs': ASCIIGraph,
    'colors': ColorScheme,
    'menu': Menu
}
