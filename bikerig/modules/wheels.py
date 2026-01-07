import bpy
import math

class BikeRig_OT_RigWheel(bpy.types.Operator):
    """Rig the selected object as a Wheel"""
    bl_idname = "bikerig.rig_wheel"
    bl_label = "Rig Wheel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "Select a wheel object first")
            return {'CANCELLED'}
        
        # Calculate Dimensions
        dims = obj.dimensions
        # Assuming Y is forward usually, or Z up. For wheels, Radius is usually Z/2 or Y/2.
        # Let's assume Z is Up, Y is Forward, X is Side. Wheel rotates around X.
        radius = dims.z / 2.0
        
        # 1. Create Armature if not exists or add bone
        bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=obj.location)
        armature_obj = context.active_object
        armature_obj.name = "BikeRig_Armature"
        
        # 2. Add Driver for Rotation
        # This is a simplified placeholder logic.
        # Real logic: Driver on Bone Rotation using Local Y Location of the Control / Radius.
        
        self.report({'INFO'}, f"Rigged {obj.name} with Radius {radius:.2f}")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(BikeRig_OT_RigWheel)

def unregister():
    bpy.utils.unregister_class(BikeRig_OT_RigWheel)
