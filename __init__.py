bl_info = {
    "name": "BikeRig",
    "author": "Antigravity",
    "version": (1, 2),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > BikeRig",
    "description": "Auto-rigging tools for bikes (Launch Control Style)",
    "category": "Rigging",
}

import bpy
from . import ui
from . import core

modules = [ui, core]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()

if __name__ == "__main__":
    register()
