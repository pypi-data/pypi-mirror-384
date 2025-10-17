"""
VLOEX SDK - Video generation as a computing primitive

Usage:
    from vloex import Vloex

    vloex = Vloex('vs_live_...')
    video = vloex.videos.create(script='Hello world')
"""

__version__ = '0.1.0'

from .client import Vloex
from .exceptions import VloexError

__all__ = ['Vloex', 'VloexError']
