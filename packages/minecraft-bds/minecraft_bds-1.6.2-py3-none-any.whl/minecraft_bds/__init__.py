from pathlib import Path
from .core import MinecraftBDS

# Create a singleton instance of the server
BDS = MinecraftBDS()

# Expose main classes for advanced users
__all__ = [
    "BDS",
    "MinecraftBDS",
]
