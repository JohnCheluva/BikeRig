import bpy
import math
import mathutils

class BikeRig_OT_BuildRig(bpy.types.Operator):
    """Generate a complete rig from selected objects (Launch Control Style)"""
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
        
        # Store original references before renaming might confusing things (though pointers track well)
        obj_frame = props.frame
        obj_fwheel = props.front_wheel
        obj_bwheel = props.back_wheel
        obj_fork = props.fork
        obj_handle = props.handlebar

        for obj, name in mapping.items():
            if obj:
                obj.name = name

        # 3. Organization (Collection)
        coll_name = "BikeRig_Collection"
        if coll_name in bpy.data.collections:
            main_coll = bpy.data.collections[coll_name]
        else:
            main_coll = bpy.data.collections.new(coll_name)
            context.scene.collection.children.link(main_coll)

        def move_to_coll(obj):
            if not obj: return
            # Unlink from all, link to main
            for c in obj.users_collection:
                c.objects.unlink(obj)
            main_coll.objects.link(obj)

        for o in [obj_frame, obj_fwheel, obj_bwheel, obj_fork, obj_handle]:
            move_to_coll(o)

        # 4. Create Armature
        bpy.ops.object.armature_add(enter_editmode=False, location=(0,0,0))
        arm_obj = context.active_object
        arm_obj.name = "BikeRig_Armature"
        move_to_coll(arm_obj)
        
        arm_data = arm_obj.data
        arm_data.name = "BikeRig_Armature_Data"
        arm_data.display_type = 'STICK'
        arm_data.show_axes = True
        
        # 5. Bone Placement & Hierarchy
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = arm_data.edit_bones
        
        for b in edit_bones:
            edit_bones.remove(b)

        def create_bone(name, head_loc, tail_loc=None, parent_bone=None):
            bone = edit_bones.new(name)
            bone.head = head_loc
            if tail_loc:
                bone.tail = tail_loc
            else:
                # Default tail up
                bone.tail = bone.head + mathutils.Vector((0, 0, 0.2))
            
            if parent_bone:
                bone.parent = parent_bone
            return bone

        # --- A. Root ---
        root = edit_bones.new("root")
        root.head = (0,0,0)
        root.tail = (0,0,1)

        # --- B. Body/Frame ---
        # Pivot at Frame Origin
        bn_frame = create_bone("frame", obj_frame.matrix_world.translation, parent_bone=root)
        # Tail should allow reasonable selection
        bn_frame.tail = bn_frame.head + mathutils.Vector((0, 0, 0.5))

        # --- C. Steering System ---
        # The Steering Axis is CRITICAL.
        # It should pivot at the Fork's origin.
        # IMPORTANT: User must set Fork Origin to the steerer tube/headset.
        
        steer_origin = obj_fork.matrix_world.translation if obj_fork else obj_frame.matrix_world.translation
        
        # Create a dedicated "Steer" bone for animation (User control)
        bn_steer = create_bone("steer", steer_origin, parent_bone=bn_frame)
        # Orient Steer bone for Z-axis rotation (Standard Blender Rigging)
        # We enforce verticality or align to fork? 
        # Vertical is safer for simple rigs. Aligned is better for realism (Rake angle).
        # Let's try to infer rake if possible, otherwise vertical.
        # Simple mode: Vertical Z axis.
        bn_steer.tail = bn_steer.head + mathutils.Vector((0, 0, 0.4))


        # --- D. Wheels ---
        # Front Wheel follows Steering
        bn_fwheel = create_bone("f_wheel", obj_fwheel.matrix_world.translation, parent_bone=bn_steer)
        # Align axle (Local X)
        bn_fwheel.tail = bn_fwheel.head + mathutils.Vector((0.2, 0, 0)) # X-axis tail

        # Back Wheel follows Frame
        bn_bwheel = create_bone("b_wheel", obj_bwheel.matrix_world.translation, parent_bone=bn_frame)
        bn_bwheel.tail = bn_bwheel.head + mathutils.Vector((0.2, 0, 0)) # X-axis tail

        # --- E. Components ---
        # Fork Mesh Bone (Constrained to Steer)
        if obj_fork:
            bn_fork_mesh = create_bone("def_fork", obj_fork.matrix_world.translation, parent_bone=bn_steer)

        # Handlebar Mesh Bone (Constrained to Steer)
        if obj_handle:
            bn_handle_mesh = create_bone("def_handle", obj_handle.matrix_world.translation, parent_bone=bn_steer)


        bpy.ops.object.mode_set(mode='OBJECT')

        # 6. Skinning (Parenting Objects to Bones)
        def parent_to_bone(obj, bone_name):
            if not obj: return
            obj.parent = arm_obj
            obj.parent_type = 'BONE'
            obj.parent_bone = bone_name
            obj.matrix_parent_inverse = arm_obj.matrix_world.inverted()

        parent_to_bone(obj_frame, "frame")
        parent_to_bone(obj_bwheel, "b_wheel")
        parent_to_bone(obj_fwheel, "f_wheel") # Spins
        
        if obj_fork:
            parent_to_bone(obj_fork, "def_fork") # Steers
        if obj_handle:
            parent_to_bone(obj_handle, "def_handle") # Steers

        # 7. Auto-Rotation Drivers
        def add_wheel_driver(bone_name, wheel_obj):
            if not wheel_obj: return
            radius = wheel_obj.dimensions.z / 2.0
            if radius <= 0.01: radius = 0.3
            
            pbone = arm_obj.pose.bones.get(bone_name)
            pbone.rotation_mode = 'XYZ'
            d = pbone.driver_add("rotation_euler", 0).driver # X axis
            d.type = 'SCRIPTED'
            
            var = d.variables.new()
            var.name = "dist"
            var.type = 'TRANSFORMS'
            var.targets[0].id = arm_obj
            var.targets[0].bone_target = "root"
            var.targets[0].transform_type = 'LOC_Y'
            var.targets[0].transform_space = 'LOCAL_SPACE'
            
            d.expression = f"-dist / {radius:.4f}"

        add_wheel_driver("f_wheel", obj_fwheel)
        add_wheel_driver("b_wheel", obj_bwheel)

        # 8. Optimization (Lock axes)
        # Lock Steer Loc/Scale/Rot(X,Y) -> Only Z allowed
        pb_steer = arm_obj.pose.bones.get("steer")
        if pb_steer:
            pb_steer.lock_location = (True, True, True)
            pb_steer.lock_rotation = (True, True, False) # Allow Z steer
            pb_steer.lock_scale = (True, True, True)

        self.report({'INFO'}, "Launch Control Style Rig Created!")
        return {'FINISHED'}

classes = [BikeRig_OT_BuildRig]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
