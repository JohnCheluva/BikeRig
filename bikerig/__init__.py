bl_info = {
    "name": "BikeRig",
    "author": "Antigravity",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > BikeRig",
    "description": "Auto-rigging tools for bikes (Wheels, Steering, Suspension, Chain)",
    "category": "Rigging",
}

import bpy
from . import ui
from .modules import wheels, steering, suspension, chain

modules = [ui, wheels, steering, suspension, chain]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()

if __name__ == "__main__":
    register()
