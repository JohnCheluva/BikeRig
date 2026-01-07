import bpy

class BikeRig_Properties(bpy.types.PropertyGroup):
    """Properties for selecting bike parts"""
    frame: bpy.props.PointerProperty(type=bpy.types.Object, name="Frame", description="Main Body/Frame")
    front_wheel: bpy.props.PointerProperty(type=bpy.types.Object, name="Front Wheel")
    back_wheel: bpy.props.PointerProperty(type=bpy.types.Object, name="Back Wheel")
    fork: bpy.props.PointerProperty(type=bpy.types.Object, name="Fork", description="Front Fork (holds front wheel)")
    handlebar: bpy.props.PointerProperty(type=bpy.types.Object, name="Handlebar", description="Steering Handlebar")
    
    # Suspension (Optional for now)
    # suspension_f: bpy.props.PointerProperty(type=bpy.types.Object, name="Front Suspension")
    # suspension_b: bpy.props.PointerProperty(type=bpy.types.Object, name="Back Suspension")

class BikeRig_PT_MainPanel(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport Sidebar"""
    bl_label = "BikeRig Builder"
    bl_idname = "BIKERIG_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BikeRig"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.bikerig_props

        layout.label(text="Select Components:", icon='OBJECT_DATA')
        
        box = layout.box()
        box.prop(props, "frame")
        box.prop(props, "front_wheel")
        box.prop(props, "back_wheel")
        
        layout.separator()
        layout.label(text="Steering Assembly:")
        box = layout.box()
        box.prop(props, "fork")
        box.prop(props, "handlebar")

        layout.separator()
        layout.operator("bikerig.build_rig", text="Generate Rig", icon='ARMATURE_DATA')

classes = [BikeRig_Properties, BikeRig_PT_MainPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.bikerig_props = bpy.props.PointerProperty(type=BikeRig_Properties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.bikerig_props
