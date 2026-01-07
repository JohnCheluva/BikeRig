import bpy
import math

class BikeRig_OT_BuildRig(bpy.types.Operator):
    """Generate a complete rig from selected objects"""
    bl_idname = "bikerig.build_rig"
    bl_label = "Build Bike Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.bikerig_props
        
        # 1. Validation
        if not (props.frame and props.front_wheel and props.back_wheel):
            self.report({'ERROR'}, "Frame, Front Wheel, and Back Wheel are required!")
            return {'CANCELLED'}

        # 2. Renaming (LC Style Tagging)
        mapping = {
            props.frame: "BikeRig_Frame",
            props.front_wheel: "BikeRig_FWheel",
            props.back_wheel: "BikeRig_BWheel",
            props.fork: "BikeRig_Fork",
            props.handlebar: "BikeRig_Handlebar"
        }
        
        for obj, name in mapping.items():
            if obj:
                obj.name = name

        # 3. Create Armature
        bpy.ops.object.armature_add(enter_editmode=False, location=(0,0,0))
        arm_obj = context.active_object
        arm_obj.name = "BikeRig_Armature"
        arm_data = arm_obj.data
        arm_data.name = "BikeRig_Armature_Data"
        arm_data.display_type = 'STICK'
        
        # 4. Bone Placement & Hierarchy
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = arm_data.edit_bones
        
        # Clear default bone
        for b in edit_bones:
            edit_bones.remove(b)

        # Helper to create bone
        def create_bone(name, target_obj, parent_bone=None):
            if not target_obj:
                return None
            
            bone = edit_bones.new(name)
            bone.head = target_obj.matrix_world.translation
            # Default tail: Up 0.2m or along local Y? 
            # For wheels: Tail should be along local X (axle). 
            # For Frame: Up.
            
            # Simple approach: Tail is Head + (0,0,0.2)
            bone.tail = bone.head + bpy.mathutils.Vector((0, 0, 0.2))
            
            # Align bone orientation to object (Advanced: copy matrix)
            # For now, let's keep them upright Z-up for simplicity, 
            # or try to match object rotation if possible.
            
            if parent_bone:
                bone.parent = parent_bone
            
            return bone

        # Root Bone (The "God" bone)
        root = edit_bones.new("root")
        root.head = (0,0,0)
        root.tail = (0,0,1)

        # Structure
        bn_frame = create_bone("frame", props.frame, root)
        bn_fork = create_bone("fork", props.fork, bn_frame) if props.fork else None
        bn_handle = create_bone("handlebar", props.handlebar, bn_fork if bn_fork else bn_frame)
        
        bn_fwheel = create_bone("f_wheel", props.front_wheel, bn_fork if bn_fork else bn_frame)
        bn_bwheel = create_bone("b_wheel", props.back_wheel, bn_frame)

        bpy.ops.object.mode_set(mode='OBJECT')

        # 5. Skinning (Parenting Objects to Bones)
        def parent_to_bone(obj, bone_name):
            if not obj: return
            obj.parent = arm_obj
            obj.parent_type = 'BONE'
            obj.parent_bone = bone_name
            # Keep transform
            obj.matrix_parent_inverse = arm_obj.matrix_world.inverted()

        parent_to_bone(props.frame, "frame")
        parent_to_bone(props.fork, "fork")
        parent_to_bone(props.handlebar, "handlebar")
        parent_to_bone(props.front_wheel, "f_wheel")
        parent_to_bone(props.back_wheel, "b_wheel")

        self.report({'INFO'}, "Bike Rig Created Successfully!")
        return {'FINISHED'}

classes = [BikeRig_OT_BuildRig]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
