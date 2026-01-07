import bpy

class BikeRig_OT_RigSteering(bpy.types.Operator):
    """Rig the selected object as Steering Handle"""
    bl_idname = "bikerig.rig_steering"
    bl_label = "Rig Steering"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Rigged Steering (Placeholder)")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(BikeRig_OT_RigSteering)

def unregister():
    bpy.utils.unregister_class(BikeRig_OT_RigSteering)
