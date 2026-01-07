import bpy

class BikeRig_OT_RigChain(bpy.types.Operator):
    """Rig the selected object as Chain"""
    bl_idname = "bikerig.rig_chain"
    bl_label = "Rig Chain"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Rigged Chain (Placeholder)")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(BikeRig_OT_RigChain)

def unregister():
    bpy.utils.unregister_class(BikeRig_OT_RigChain)
