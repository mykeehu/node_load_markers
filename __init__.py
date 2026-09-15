"""
Empty __init__.py - only needed so ComfyUI does not try to load this
folder as a "real" custom node package (which would fail without it).
The actual logic lives in prestartup_script.py, which has already run
by the time this file would be imported.
"""

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
