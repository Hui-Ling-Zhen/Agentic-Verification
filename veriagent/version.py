# -*- coding: utf-8 -*-
"""Version information for VeriAgent."""

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.9.1.source-code"

__author__ = "XS-MLVP"
__email__ = "unitychip@bosc.ac.cn"
__description__ = "Agentic-Verification / VeriAgent - supervised Codex hardware verification runtime"

banner = f"""
\u001b[34m    _                    _   _        __     __         _  __ _           _   _             \u001b[0m
\u001b[34m   / \\    __ _  ___ _ __ | |_(_) ___   \\ \\   / /__ _ __ (_)/ _(_) ___ __ _| |_(_) ___  _ __  \u001b[0m
\u001b[34m  / _ \\  / _` |/ _ \\ '_ \\| __| |/ __|   \\ \\ / / _ \\ '__|| | |_| |/ __/ _` | __| |/ _ \\| '_ \\ \u001b[0m
\u001b[34m / ___ \\| (_| |  __/ | | | |_| | (__     \\ V /  __/ |   | |  _| | (_| (_| | |_| | (_) | | | |\u001b[0m
\u001b[34m/_/   \\_\\\\__, |\\___|_| |_|\\__|_|\\___|     \\_/ \\___|_|   |_|_| |_|\\___\\__,_|\\__|_|\\___/|_| |_|\u001b[0m
\u001b[34m         |___/                                                                          \u001b[0m \u001b[36mv{__version__}\u001b[0m
"""
