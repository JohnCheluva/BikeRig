import bpy

class BikeRig_PT_MainPanel(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport Sidebar"""
    bl_label = "BikeRig Controls"
    bl_idname = "BIKERIG_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BikeRig"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Wheels")
        layout.operator("bikerig.rig_wheel", text="Rig Selected Wheel")

        layout.label(text="Steering")
        layout.operator("bikerig.rig_steering", text="Rig Steering (Handle+Fork)")

        layout.label(text="Suspension")
        layout.operator("bikerig.rig_suspension", text="Rig Suspension")

        layout.label(text="Chain")
        layout.operator("bikerig.rig_chain", text="Rig Chain")

def register():
    bpy.utils.register_class(BikeRig_PT_MainPanel)

def unregister():
    bpy.utils.unregister_class(BikeRig_PT_MainPanel)
