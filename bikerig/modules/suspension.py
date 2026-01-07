import bpy

class BikeRig_OT_RigSuspension(bpy.types.Operator):
    """Rig the selected object as Suspension"""
    bl_idname = "bikerig.rig_suspension"
    bl_label = "Rig Suspension"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Rigged Suspension (Placeholder)")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(BikeRig_OT_RigSuspension)

def unregister():
    bpy.utils.unregister_class(BikeRig_OT_RigSuspension)
