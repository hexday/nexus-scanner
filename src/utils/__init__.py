from .config import Config
from .cache import CacheHandler
from .threading import ThreadManager
from .helpers import create_temp_dir, create_temp_file

__all__ = [
    'Config',
    'CacheHandler',
    'ThreadManager',
    'create_temp_dir',
    'create_temp_file'
]

# Utils Configuration
CACHE_DIR = '.cache'
CONFIG_PATH = 'config/default_config.yaml'
TEMP_DIR = 'temp'
MAX_THREADS = 10

# Utils Registry
UTILS = {
    'config': Config,
    'cache': CacheHandler,
    'threading': ThreadManager,
    'helpers': {
        'create_temp_dir': create_temp_dir,
        'create_temp_file': create_temp_file
    }
}
