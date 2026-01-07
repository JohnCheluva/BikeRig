import bpy
import addon_utils
import numpy as np

from ..operators.physics import * 
from ..operators.rig import *
from ..operators.append import *
from ..operators.extra import *
from ..operators.animation import *
from ..operators.jump import *
from ..operators.physics import *
from ..operators.path import *
from ..operators.exports import *
from ..operators.camera import *
from ..operators.speed_segment import *
from ..operators.append import appendable_cars
from ..operators import addon_updater_ops 

from ..utils.functions import get_speed_rotate_keyframes


from .utils import label_multiline

SMALL = 0.2
MEDIUM = 0.4
LARGE = 0.8

class PANEL_PT_interface(bpy.types.Panel):
    bl_label = "Launch Control"
    bl_idname = "PANEL_PT_interface"
    bl_category = "Launch Control"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def cubic_bezier(self, t, p0, p1, p2, p3):
        return (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3
    

    def get_slope(self, p1, p2):
            
            try: slope = (p2[1]-p1[1]) / (p2[0]-p1[0])
            except: slope = 0
            
            return slope
        
    def get_speed(self, slope):
        
        fps = bpy.context.scene.render.fps
        
        m_per_frame = slope
        m_per_sec = (m_per_frame*fps)
        kmh = m_per_sec*3.6
        
        return kmh

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        multi_edit = scene.settings.edit_all_mode
        speed_segments_running = scene.settings.speed_segments_running
        garage_mode = False
        if scene.settings.mode == "garage_mode":
            garage_mode = True

        addon_preferences = context.preferences.addons[__name__.split(".")[0]].preferences

        selected_collection = scene.car_collection
        vehicle_source = scene.settings.vehicle_source

        # Title 1: VEHICLE SELECTION & RIG
        layout = self.layout
        split = layout.split(factor=0.75)
        col_1 = split.column()
        col_2 = split.column()

        col_1.label(text="Select Vehicle", icon="AUTO")

        if not selected_collection and addon_preferences.show_vehicle_gallery:

            if scene.car_collection_previous is not None:
                col_2.operator(OBJECT_OT_revert_vehicle_edit.bl_idname, text="", icon="LOOP_BACK")

            row = layout.row()
            row.prop(scene.settings, "vehicle_source", expand=True)

            
            if vehicle_source == 'gallery':

                row = layout.row()
                row.template_icon_view(
                    context.window_manager,
                    "vehicle_presets",
                    show_labels=True,
                    scale=8,
                )

                vehicle_preset_name = os.path.splitext(bpy.data.window_managers["WinMan"].vehicle_presets)[0]
                
                if "Add More" in vehicle_preset_name:
                    row = layout.row()
                    op = row.operator(OBJECT_OT_install_lib.bl_idname, text='Install .lcl', icon='IMPORT')
                    op.asset_type = "VEHICLE"

                    row = layout.row()
                    op = row.operator('wm.url_open', text='Get Packs', icon='URL')
                    op.url = 'launch-control-documentation.readthedocs.io/en/1.7.0/asset-packs.html#download-vehicle-packs'

                    

                else:
                    #row = layout.row(align=True)
                    #row.prop(scene, "car_collection", text="User Vehicle")

                    if "TMF" in vehicle_preset_name:
                        row = layout.row(align=True)
                        layout = self.layout
                        split = layout.split(factor=0.5)
                        sponsor_col_1 = split.column()
                        sponsor_col_2 = split.column()
                        sponsor_col_1.label(text="Sponsored by TMF:", icon="FUND")
                        op = sponsor_col_2.operator('wm.url_open', text='Learn More')
                        op.url = 'https://blendermarket.com/products/the-mega-fleet'

                    row = layout.row(align=True)
                    row.operator(OBJECT_OT_rig_car.bl_idname, text='Add Model', icon="PLUS")
                    op = row.operator('wm.url_open', text='', icon='HELP')
                    op.url = 'https://launch-control-documentation.readthedocs.io/en/latest/launch-control-core.html#gallery-vehicle'
            

            elif vehicle_source == 'append':

                row = layout.row()
                row.prop(scene.settings, "append_path", text="")

                row = layout.row()
                row.operator(OBJECT_OT_append_search_select_file.bl_idname, text='Search in Blend File', icon="ZOOM_ALL")
                op = row.operator('wm.url_open', text='', icon='HELP')
                op.url = 'https://launch-control-documentation.readthedocs.io/en/latest/launch-control-core.html#append-vehicle'


                if len(appendable_cars) > 0:
                    box = layout.box()
                    box.use_property_split = True
                    col = box.column()
                    row = col.row()

                    file_name = os.path.splitext(os.path.basename(scene.settings.append_file_path))[0]
                    text = ("File: " + file_name)
                    box.label(text = text)

                    row = box.row()
                    row = box.row()

                    box.prop(scene.settings, "append_lc_car_names", text='LC Vehicles in file:')

                    if scene.settings.append_version_control:
                        ico = 'FAKE_USER_ON'
                    else:
                        ico = 'FAKE_USER_OFF'
                    box.prop(scene.settings, "append_version_control", icon=ico)

                    row = box.row()
                    row = box.row()

                    box.use_property_split = False

                    name_collision = False
                    for coll in bpy.data.collections:
                        if coll.name == scene.settings.append_lc_car_names:
                            name_collision = True
                    
                    row.operator(OBJECT_OT_append_from_file.bl_idname, text="Append Vehicle", icon="APPEND_BLEND")
                    row.enabled = not name_collision

                    if name_collision:
                        box.label(text = "Vehicle Name exists in current file already", icon="INFO")
                        box.label(text = "Please select another vehicle to append")



            elif vehicle_source == 'local':

                row = layout.row(align=True)
                row.prop(scene, "car_collection")
                op = row.operator('wm.url_open', text='', icon='HELP')
                op.url = 'https://launch-control-documentation.readthedocs.io/en/latest/launch-control-core.html#local-vehicle'
                row.enabled = (not multi_edit) and (not garage_mode) and (not speed_segments_running)



        else:
            if selected_collection:
                active_car = scene.lc.find_selected()

                if addon_preferences.show_vehicle_gallery and (active_car and active_car.is_rigged):
                    col_2.operator(OBJECT_OT_revert_vehicle_add.bl_idname, text="", icon="PLUS")
                    col_2.enabled = (not multi_edit) and (not garage_mode) and (not speed_segments_running)

            row = layout.row(align=True)
            row.prop(scene, "car_collection")
            row.enabled = (not multi_edit) and (not garage_mode) and (not speed_segments_running)

            if len(scene.lc.cars) > 1:
                row.operator(OBJECT_OT_find_selected_car.bl_idname, text="", icon="RESTRICT_SELECT_OFF")

            if len(scene.lc.cars) > 0:
                row.prop(scene.settings, "show_rigged_coll_only", text="", icon="FILTER")

        if not multi_edit:
            if addon_preferences.enable_multi_rigging and len(scene.lc.cars) == 0:
                row.prop(scene.settings, "edit_all_mode", text="", icon="OUTLINER_OB_POINTCLOUD")
        else:
            row = layout.row(align=True)
            row.prop(scene.settings, "edit_all_mode", text="Disable Multi-Edit", icon="OUTLINER_OB_POINTCLOUD")

        if selected_collection:
            
            active_car = scene.lc.find_selected()

            if (active_car and active_car.is_rigged) and not (addon_preferences.enable_multi_rigging and len(scene.lc.cars) == 0 and multi_edit):
                props = active_car.properties
                settings = active_car.settings

                if len(scene.lc.cars) > 1 and not multi_edit:
                    row.prop(scene.settings, "edit_all_mode", text="", icon="OUTLINER_OB_POINTCLOUD")

                row = layout.row()
                row.operator(OBJECT_OT_delete_rig.bl_idname, icon="X")
                row.enabled = (not multi_edit) and (not garage_mode) and (not speed_segments_running)

                layout.separator(factor=LARGE)
                layout.separator(factor=LARGE)

                # Title 2: ANIMATIONS
                layout.label(text="Select Animations", icon="IPO_BEZIER")

                if addon_preferences.show_animation_gallery:
                    row = layout.row()
                    row.template_icon_view(
                        context.window_manager,
                        "animation_presets",
                        show_labels=True,
                        scale=8,
                    )
                    row.enabled = not props.custom_path and (not garage_mode)
                
                row = layout.row(align=True)
                row.prop(props, "custom_path", text="User Path")
                row.operator(OBJECT_OT_pick_selected_path.bl_idname, text="", icon="RESTRICT_SELECT_OFF")
                row.enabled = (not garage_mode)

                if active_car.properties.custom_path is not None    and    addon_preferences.override_anim_on_path_change and (not garage_mode):
                    box = layout.box()
                    col = box.column(align=True)

                    row = col.row(align=True)
                    row.prop(scene, "frame_preview_start", text="Start")
                    row.prop(scene, "frame_preview_end", text="End")
                    row.prop(active_car.properties, "path_anim_intpl", text="")

                    row = col.row(align=True)
                    duration = (scene.frame_preview_end-scene.frame_preview_start)/scene.render.fps
                    row.label(text=f"Length: {round(duration, 1)} Sec")

                    unit = "mph" if addon_preferences.use_imperial else "km/h"

                    if active_car.properties.custom_path.data.use_path == True:
                        path_len = active_car.properties.custom_path.data.path_duration  # in m
                        if path_len > 1 and duration > 0:

                            if active_car.properties.path_anim_intpl == 'VECTOR':
                                max_speed = (path_len/duration)*3.6
                                label = "Speed:"

                            else:
                                start = scene.frame_preview_start
                                end = scene.frame_preview_end

                                offset = (scene.frame_preview_end - scene.frame_preview_start)/3

                                t = 0.49
                                p0 = np.array([start, 0])
                                p1 = np.array([start + offset, 0])
                                p2 = np.array([end, path_len])
                                p3 = np.array([end - offset, path_len])

                                mid_p0 = self.cubic_bezier(t, p0, p1, p2, p3,)
                                t = 0.51
                                mid_p1 = self.cubic_bezier(t, p0, p1, p2, p3,)

                                max_speed = self.get_speed(  self.get_slope(mid_p0, mid_p1)  )

                                label = "Max Speed:"

                            if unit == 'mph':
                                max_speed = max_speed*0.6213
                            row.label(text=f"{label} {round(max_speed, 0)} {unit}")
                        else:
                            row.label(text=f"Max Speed: -- {unit}")
                    else:
                        row.label(text=f"Max Speed: -- {unit}")
                        

                row = layout.row(align=True)
                row.operator(OBJECT_OT_prepare_animation.bl_idname)
                op = row.operator(OBJECT_OT_select_driving_path.bl_idname, text='', icon='CURVE_DATA')
                op = row.operator('wm.url_open', text='', icon='HELP')
                op.url = 'https://launch-control-documentation.readthedocs.io/en/latest/launch-control-core.html#animation'

                row.enabled = (not garage_mode)

                try:
                    layer_visible_state = active_car.rig_armature.collections["internal_warning_path"].is_visible
                except:
                    #Fallback for LC 1.5
                    layer_visible_state = active_car.rig_armature.collections["Layer 8"].is_visible

                if layer_visible_state:
                    layout.operator(OBJECT_OT_refresh_path_len.bl_idname)
                

                # If no Ground Detection is found
                ground_detect_collection = get_collection_by_name(COLLECTIONNAME_GROUNDDETECT, scene.collection)

                if ground_detect_collection is not None:  # Avoid breaking pre LC 1.6
                    if len(ground_detect_collection.objects) < 1:

                        layout.separator(factor=LARGE)
                        layout.separator(factor=LARGE)

                        b = layout.box()
                        lisr = b.row()
                        lisr.label(text="No Objects in Ground Detection", icon="ERROR")

                        lisr = b.row(align=True)
                        lisr.operator(OBJECT_OT_add_ground_colliders.bl_idname, text="Add Selected", icon="ADD")

                        layout.separator(factor=LARGE)

                else:
                    pass
                    #log_info(f"Could not find 'ground_detection_collection' reference inside the LC data. Will not draw UI element. Remove all LC vehicles and rig them again to fix this.", "LC - missing data")


                layout.separator(factor=SMALL)
                
                row = layout.row()

                if speed_segments_running:

                    flow = layout.column_flow(columns=2)
                    flow.prop(scene.settings, "speed_segments_kill", icon="QUIT")

                    flow.prop(props, "settings_speed_segments")

                    if props.settings_speed_segments:
                        box = layout.box()
                        box.use_property_split = True
                        col = box.column()
                        row = col.row()

                        row.label(text="Controls:", icon="MODIFIER")

                        row = col.row()
                        row.prop(props, "max_acc", text="Max G-Force")
                        row.enabled = props.auto_interpolation
                        
                        row = col.row()
                        row.prop(props, "auto_fit_frame_range", text="Auto-fit Range", icon='ACTION')

                        col = box.column()
                        row = col.row()
                        col = box.column()
                        row = col.row()
                        col = box.column()
                        row = col.row()
                        col = box.column()
                        row = col.row()

                        row.label(text="Graph:", icon="RNDCURVE")
                        row = col.row()

                        if props.graph_enable:
                            row.prop(props, "graph_enable", icon="HIDE_OFF")
                            row = col.row()
                            row.prop(props, "speed_graph_resolution", text="Resolution")
                            row = col.row()
                            row.prop(props, "graph_scale", text="Scale")
                            row = col.row()
                            row.prop(props, "graph_color")
                            row = col.row()
                        else:
                            row.prop(props, "graph_enable", icon="HIDE_ON")

                        col = box.column()
                        row = col.row()
                        col = box.column()
                        row = col.row()
                        col = box.column()
                        row = col.row()
                        col = box.column()
                        row = col.row()

                        row.label(text="Units:", icon="DRIVER_DISTANCE")
                        row = col.row()
                        row.prop(props, "timecode_type")
                        row = col.row()
                        row.prop(props, "units_type")
                        row.enabled = False
                        
                        col = box.column()
                        row = col.row()
                        col = box.column()
                        row = col.row()
                        col = box.column()
                        row = col.row()
                        col = box.column()
                        row = col.row()

                        row.label(text="Expert Settings:", icon="COMMUNITY")

                        row = col.row()
                        if props.auto_interpolation:
                            row.prop(props, "auto_interpolation", icon="HANDLE_AUTOCLAMPED")
                        else:
                            row.prop(props, "auto_interpolation", icon="HANDLE_FREE")
                        
                        col = box.column()
                        row = col.row()
                        col = box.column()
                        row = col.row()
                        col = box.column()
                        row = col.row()

                        row.label(text="Auto-save blocked while tool is active", icon="INFO")


                else:
                    flow = layout.column_flow(columns=2)
                    flow.operator(OBJECT_OT_speed_segment_tool.bl_idname, text="Speed Segments", icon="PARTICLE_POINT")

                flow.enabled = (not garage_mode) and (not bpy.context.screen.is_animation_playing) and (not multi_edit)

                flow = layout.column_flow(columns=2)
                flow.prop(settings, "speedometer", text="Speedometer", icon="MOD_TIME")

                if settings.speedometer:
                    flow.operator(OBJECT_OT_refresh_speedometer.bl_idname, text="Refresh Speed", icon="FILE_REFRESH")

                flow.enabled = (not garage_mode)

                if settings.speedometer and not multi_edit:
                    dgraph_Evaluated = context.evaluated_depsgraph_get()
                    object_eval = active_car.speed_calculator.evaluated_get(dgraph_Evaluated)

                    try: current_kmh = object_eval.data.attributes["vel_attribute"].data[0].value
                    except: current_kmh = 0

                    current_speed = current_kmh*0.6214 if addon_preferences.use_imperial else current_kmh
                    
                    unit = "mph" if addon_preferences.use_imperial else "km/h"

                    label = (f"{(round(current_speed, 2))} {unit}")

                    layout.label(text=label, icon="PREVIEW_RANGE")
                    
                
                if settings.speedometer and multi_edit:
                    flow.label(text="Unavailable", icon="PREVIEW_RANGE")

                    
                layout.separator(factor=LARGE)
                layout.separator(factor=LARGE)

                # TITLE 3: PHYSICS
                layout.label(text="Select Physics", icon="PHYSICS")

                # Warnings and Settings
                switch = active_car.rig_object.pose.bones[B_SWITCH_USE_SIMULATION].location[1]
                switch_setup_mode = active_car.rig_object.pose.bones["bone_Switch_Setup"].location[1]
                outdated_physics = physics_outdated(scene, active_car)
                changed_physics = physics_changed(scene, active_car)
                bake_invalid = active_car.rig_armature.collections["internal_warning_physics"].is_visible
                bugged_simulation_nodes = simulation_nodes_bugged(scene, active_car)

                
                if scene.settings.confirm_bake_state:

                    if scene.settings.bake_running:
                        #row = layout.row()
                        #row.label(text="Baking Physics...")
                        
                        row = layout.row()
                        row.operator(OBJECT_OT_physics_revert_to_main.bl_idname, icon="LOOP_BACK")

                    else:
                        row = layout.row()
                        row.label(text="Physics are ready to be Baked!")

                        layout.separator(factor=MEDIUM)

                        box = layout.box()
                        col = box.column(align=True)

                        row = col.row(align=True)

                        row.prop(scene.settings, "physics_use_warm_up", text="Warm Up",)
                        if scene.settings.physics_use_warm_up:
                            row.prop(scene.settings, "physics_warm_up_frames", text="Frames",)

                            if (scene.frame_preview_start - scene.settings.physics_warm_up_frames) < 0:
                                box.label(text="Frame Count cannot go below 0", icon="INFO")
                            

                        box.separator(factor=LARGE)
                                                
                        box.operator(OBJECT_OT_execute_physics_bake.bl_idname, icon="CHECKMARK")

                        box.operator(OBJECT_OT_free_physics.bl_idname, icon="CANCEL")
                
                else:

                    if (switch > 0.5) or props.mute_physics:
                        
                        row = layout.row()
                        row.prop(active_car.properties, "physics_presets", text="")
                        row.enabled = not multi_edit

                        label, icon = physics_status(active_car, changed_physics, outdated_physics, props.baked_physics, bake_invalid, bugged_simulation_nodes, switch, switch_setup_mode)

                        flow = layout.column_flow(columns=2)
                        flow.label(text=label, icon=icon)
                        flow.prop(active_car.settings, "show_custom_physics", text="Customize", expand=True)

                        layout.separator(factor=SMALL)

                        if label == "Physics are LIVE" and scene.sync_mode != 'NONE':
                            layout.label(text="Frame Dropping is Active.", icon="ERROR")
                            layout.label(text="Physics will be inaccurate!")

                        # Advance Physics
                        if active_car.settings.show_custom_physics:                            
                            row = layout.row()
                            row.prop(active_car.properties, "physics_tightness", text="Spring Hardness",)
                            row.enabled = not multi_edit
                            row = layout.row()
                            row.prop(active_car.properties, "physics_dampening", text="Spring Damping")
                            row.enabled = not multi_edit
                            row = layout.row()
                            row.prop(active_car.properties, "physics_softness", text="Smoothing")
                            row.enabled = not multi_edit
                            #row = layout.row()
                            #row.prop(active_car.properties, "physics_multiplier", text="Physics Multiplier")
                            #row.enabled = not multi_edit

                            layout.separator(factor=MEDIUM)

                            row = layout.row(align=True)
                            row.prop(active_car.properties, "use_gravity", text="Simulate Gravity")
                            row.enabled = not multi_edit
                            if active_car.properties.use_gravity:
                                row.prop(active_car.properties, "auto_level", text="Auto Level")
                                row.enabled = not multi_edit
                                
                                row = layout.row(align=True)
                                row.label(text="   ")
                                row.prop(active_car.properties, "mass", text="Vehicle Mass (Tons)")
                                row.enabled = not multi_edit
                                row = layout.row(align=True)
                                row.label(text="   ")
                                row.prop(active_car.properties, "spring_offset", text="Spring Offset")
                                row.enabled = not multi_edit

                        layout.separator(factor=SMALL)

                        if props.baked_physics:
                            row = layout.row(align=True)
                            row.operator(OBJECT_OT_free_physics.bl_idname, icon="PLAY")
                            if props.mute_physics:
                                row.operator(OBJECT_OT_unmute_physics.bl_idname, icon="RESTRICT_VIEW_OFF")
                            else:
                                row.operator(OBJECT_OT_mute_physics.bl_idname, icon="RESTRICT_VIEW_ON")
                            row.operator(OBJECT_OT_bake_physics.bl_idname, text="", icon="FILE_REFRESH")
                            row.enabled = (not garage_mode)

                        else:
                            row = layout.row(align=True)
                            row.operator(OBJECT_OT_bake_physics.bl_idname, icon="FREEZE")
                            row.operator(OBJECT_OT_disable_physics.bl_idname, icon="X")
                            row.operator(OBJECT_OT_refresh_physics.bl_idname, text="", icon="FILE_REFRESH")
                            row.enabled = (not garage_mode)

                    else:
                        row = layout.row(align=True)
                        row.operator(OBJECT_OT_free_physics.bl_idname, icon="QUIT", text="Enable Physics!")
                        op = row.operator('wm.url_open', text='', icon='HELP')
                        op.url = 'https://launch-control-documentation.readthedocs.io/en/latest/launch-control-core.html#real-time-physics'
                        row.enabled = (not garage_mode)
        
            else:
                if not scene.settings.cad_setup:
                    #layout.prop(scene.settings, "rig_help", text="Rig Help")
                    #show_help(context, scene, layout)

                    layout.prop(scene.settings, "quick_tag", text="Quick Tag Tool")
                    show_quick_tag(context, scene, layout)

                if addon_preferences.show_pro_options:
                    layout.prop(scene.settings, "cad_setup", text="CAD Data Setup")
                    show_cad_setup(context, scene, layout)
                
                for coll in scene.collection.children_recursive:
                    if coll.name == "CarRigAddon":
                        layout.separator(factor=LARGE)
                        layout.label(text="Legacy Rig detected", icon="INFO")
                        layout.label(text="Head to 'Manual Gearbox' -> 'Rig Info' to update it")

                row = layout.row(align=True)
                row.operator(OBJECT_OT_rig_car.bl_idname, text='Rig Vehicle')
                op = row.operator('wm.url_open', text='', icon='HELP')
                op.url = 'https://launch-control-documentation.readthedocs.io/en/latest/launch-control-core.html#rigging'
                    
                

def show_help(context, scene, layout):
    if scene.settings.rig_help:
        layout.separator(factor=SMALL)

        layout.label(text="Tags are needed to detect Car Parts", icon="INFO")

        layout.separator(factor=SMALL)

        box = layout.box()
        box.label(text="Required Car Parts:")
        box.label(text="     Car Body Tag:  'Body'")
        box.label(text="     Front Right Wheel Tag:  'wheel.FR'")
        box.label(text="     Front Left Wheel Tag:  'wheel.FL'")
        box.label(text="     Rear Right Wheel Tag:  'wheel.RR'")
        box.label(text="     Rear Left Wheel Tag:  'wheel.RL'")

        layout.separator(factor=SMALL)

        text = "Make sure above mentioned Car Parts exists in the scene, and that each one has the corresponding tag in its object name."
        label_multiline(context, text, layout, icon="DOT")

        layout.separator(factor=SMALL)

        box = layout.box()
        box.label(text="Optional Car Parts:")
        box.label(text="     Front Right Brake Tag:  'brake.FR'")
        box.label(text="     Front Left Brake Tag:  'brake.FL'")
        box.label(text="     Rear Right Brake Tag:  'brake.RR'")
        box.label(text="     Rear Left Brake Tag:  'brake.RL'")
        box.label(text="     Right Headlight Tag:  'headlight.R'")
        box.label(text="     Left Headlight Tag:  'headlight.L'")
        box.label(text="     Front Right Wheel Cover Tag:  'wheelcover.FR'")
        box.label(text="     Front Left Wheel Cover Tag:  'wheelcover.FL'")

        layout.separator(factor=SMALL)

        text = "Optional Car Parts will be rigged if found, but ignored if not found."
        label_multiline(context, text, layout, icon="DOT")
        
        layout.separator(factor=LARGE)

        text = "A wide variety of Tags can be detected by the add-on. Above, only the primary Tags are shown. See the full list of 'detectable' Tags in the documentation."
        label_multiline(context, text, layout, icon="INFO")
        
        layout.separator(factor=LARGE)


def show_quick_tag(context, scene, layout):
    if scene.settings.quick_tag:
        
        layout.separator(factor=SMALL)

        layout.label(text="Quick Renamer!", icon="GREASEPENCIL")

        layout.separator(factor=LARGE)

        text = "Select an object and click a button below, to rename it to the desired Tag."
        label_multiline(context, text, layout)

        layout.separator(factor=LARGE)

        layout.label(text="Required Tags:")

        box = layout.box()
        try: 
            box.prop(context.object, "name", text="Object Tag") 
        except: 
            pass
        box.operator("object.rename_to_option", text="body").option_name = "body"
        box.operator("object.rename_to_option", text="wheel.FL").option_name = "wheel.FL"
        box.operator("object.rename_to_option", text="wheel.FR").option_name = "wheel.FR"
        box.operator("object.rename_to_option", text="wheel.RL").option_name = "wheel.RL"
        box.operator("object.rename_to_option", text="wheel.RR").option_name = "wheel.RR"

        layout.separator(factor=LARGE)

        layout.label(text="Optional Tags:")

        box = layout.box()
        box.operator("object.rename_to_option", text="brake.FL").option_name = "brake.FL"
        box.operator("object.rename_to_option", text="brake.FR").option_name = "brake.FR"
        box.operator("object.rename_to_option", text="brake.RL").option_name = "brake.RL"
        box.operator("object.rename_to_option", text="brake.RR").option_name = "brake.RR"
        box.operator("object.rename_to_option", text="headlight.L").option_name = "headlight.L"
        box.operator("object.rename_to_option", text="headlight.R").option_name = "headlight.R"
        box.operator("object.rename_to_option", text="wheelcover.FL").option_name = "wheelcover.FL"
        box.operator("object.rename_to_option", text="wheelcover.FR").option_name = "wheelcover.FR"

        layout.separator(factor=LARGE)


def show_cad_setup(context, scene, layout):
    if scene.settings.cad_setup:
        
        layout.separator(factor=SMALL)

        layout.label(text="CAD Setup", icon="SYSTEM")

        layout.separator(factor=LARGE)

        text = "Drop Empties corrosponding to the assembly type in the fields below."
        label_multiline(context, text, layout)

        layout.separator(factor=LARGE)

        layout.label(text="Required Assemblies:")

        box = layout.box()
        box.prop(scene, "body_assembly", text="Body")
        box.prop(scene, "anim_rot_fr_assembly", text="Anim Rot FR")
        box.prop(scene, "anim_rot_fl_assembly", text="Anim Rot FL")
        box.prop(scene, "anim_rot_rr_assembly", text="Anim Rot RR")
        box.prop(scene, "anim_rot_rl_assembly", text="Anim Rot RL")

        layout.separator(factor=LARGE)

        layout.label(text="Optional Assemblies:")

        box = layout.box()
        box.prop(scene, "no_rot_fr_assembly", text="No Rot FR")
        box.prop(scene, "no_rot_fl_assembly", text="No Rot FL")
        box.prop(scene, "no_rot_rr_assembly", text="No Rot RR")
        box.prop(scene, "no_rot_rl_assembly", text="No Rot RL")

        layout.separator(factor=LARGE)

        layout.label(text="Vehicle Data:")
        
        box = layout.box()
        box.use_property_split = True
        box.prop(scene.settings, "tire_width")
        box.prop(scene.settings, "tire_ratio")
        box.prop(scene.settings, "rim_diameter")

        col = box.column()
        row = col.row()
        row.use_property_split = False

        row.operator("object.calculate_wheel_diameter", text="Calculate Tire Diameter")
        row.prop(scene.settings, "wheel_size_rear", text="")
        
        box = layout.box()
        box.use_property_split = True
        box.prop(scene.settings, "wheel_camber", text="Wheel Camber")
        box.prop(scene.settings, "emulated_body_weight", text="Emulated Weight")


# PHYSICS AUXILIAR FUNCTIONS
def physics_changed(scene, active_car):
    #True if physics have changed
    return not (
        active_car.properties.physics_tightness == active_car.properties.physics_baked_tightness
        and active_car.properties.physics_dampening == active_car.properties.physics_baked_dampening
        and active_car.properties.physics_softness == active_car.properties.physics_baked_softness
        and active_car.properties.physics_multiplier == active_car.properties.physics_baked_multiplier
        and active_car.properties.use_gravity == active_car.properties.baked_use_gravity
        and active_car.properties.auto_level == active_car.properties.baked_auto_level
        and active_car.properties.spring_offset == active_car.properties.baked_spring_offset
        and active_car.properties.mass == active_car.properties.baked_mass
    )

def physics_outdated(scene, active_car):
    
    outside_frame_range = False
    if scene.frame_start < active_car.properties.baked_frame_start - scene.settings.physics_warm_up_frames    or    scene.frame_end > active_car.properties.baked_frame_end:
        outside_frame_range = True

    is_outdated = False
    if active_car.path_changed or outside_frame_range:
        is_outdated = True

    return is_outdated

def simulation_nodes_bugged(scene, active_car):
    # Todo
    return False  

def physics_status(active_car, changed_physics, outdated_physics, baked_physics, bake_invalid, bugged_simulation_nodes, switch, switch_setup_mode):
    '''Returns label, icon symbolizing status of the physics'''
    if switch > 0.5:
        text = "Physics are LIVE"
        icon = "MOD_WAVE"

        if bugged_simulation_nodes:
            text = "Restart Blender Please"
            icon = "ERROR"

        if baked_physics:
            text = "Physics are BAKED"
            icon = "FREEZE"

            if outdated_physics or changed_physics:
                text = "Bake Outdated!"
                icon = "ERROR"

            if bake_invalid:
                text = "Bake Invalid - Please Reset"
                icon = "ERROR"

            

    elif active_car.properties.mute_physics:
        text = "Physics are MUTED"
        icon = "RESTRICT_VIEW_ON"
    
    else:
        text = "Physics are OFF"
        icon = "ONIONSKIN_OFF"

    return text, icon


class PANEL_PT_PostFX(bpy.types.Panel):
    bl_parent_id = "PANEL_PT_interface"
    bl_category = "Launch Control"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Physics PostFX"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        multi_edit = scene.settings.edit_all_mode
        
        selected_collection = scene.car_collection
        if selected_collection:
            active_car = scene.lc.find_selected()
            if active_car and active_car.is_rigged:
                car_properties = active_car.properties

                switch = active_car.rig_object.pose.bones[B_SWITCH_USE_SIMULATION].location[1]
                switch_setup_mode = active_car.rig_object.pose.bones["bone_Switch_Setup"].location[1]
                
                if switch > 0.5:              
                    text = "Art direct the simulated data to fit your needs."
                    label_multiline(context, text, layout)

                    layout.separator(factor=MEDIUM)

                    layout.label(text="Body Forces: ")
                    
                    layout.use_property_split = True
                    col = layout.column()
                    col.prop(car_properties, "overdrive_pitch", text="Pitch")
                    col.enabled = not multi_edit
                    col.prop(car_properties, "overdrive_yaw", text="Yaw")
                    col.enabled = not multi_edit
                    col.prop(car_properties, "overdrive_roll", text="Roll")
                    col.enabled = not multi_edit

                    col = layout.column()
                    col.prop(car_properties, "overdrive_location", text="Up/Down")
                    col.enabled = not multi_edit

                    layout.separator(factor=MEDIUM)

                    layout.label(text=("Wheel Forces:"))
                    col = layout.column()
                    col.prop(car_properties, "overdrive_wheel_location", text="Up/Down")
                    col.enabled = not multi_edit
                    col.prop(car_properties, "overdrive_wheel_pressure", text="Tire Pressure")
                    col.enabled = not multi_edit

                else:
                    text = "Please 'Enable Physics' before adjusting the Physics PostFX"
                    label_multiline(context, text, layout)

            else:
                row = layout.row()
                row.label(text="Please rig the Vehicle")

        else:
            row = layout.row()
            row.label(text="Please select or add an LC Vehicle")
                

# MANUAL GEARBOX -------------------------------------------------------------------------------------
class PANEL_AdvancedOverall:
    bl_category = "Launch Control"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        speed_segments_running = bpy.context.scene.settings.speed_segments_running
        return not speed_segments_running


class PANEL_PT_Advanced(PANEL_AdvancedOverall, bpy.types.Panel):
    bl_idname = "PANEL_PT_Advanced"
    bl_label = "Manual Gearbox"

    def draw_header(self, context):
        self.layout.label(text="", icon="TOOL_SETTINGS")

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        selected_collection = scene.car_collection
        multi_edit = scene.settings.edit_all_mode

        """if selected_collection == None: # In case vehicle collection is deleted while in Garage Mode
            row = layout.row()
            row.prop(scene.settings, "mode", expand=True)
            op = row.operator('wm.url_open', text='', icon='HELP')
            op.url = 'https://launch-control-documentation.readthedocs.io/en/latest/manual-gearbox.html#garage-mode'
            row.enabled = not multi_edit"""
            

        if selected_collection:
            active_car = scene.lc.find_selected()

            if active_car and active_car.is_rigged:
                row = layout.row()
                row.prop(scene.settings, "mode", expand=True)
                op = row.operator('wm.url_open', text='', icon='HELP')
                op.url = 'https://launch-control-documentation.readthedocs.io/en/latest/manual-gearbox.html#garage-mode'
                row.enabled = not multi_edit

                row = layout.row()
                row.operator(OBJECT_OT_reset_props.bl_idname, icon="LOOP_BACK")
                row.enabled = not multi_edit
                    


class PANEL_PT_QuickFBX(PANEL_AdvancedOverall, bpy.types.Panel):
    bl_parent_id = "PANEL_PT_Advanced"
    bl_label = "Quick Export"

    def draw_header(self, context):
        self.layout.label(text="", icon="EXPORT")

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        selected_collection = scene.car_collection
        multi_edit = scene.settings.edit_all_mode

        if selected_collection:
            active_car = scene.lc.find_selected()
            if active_car and active_car.is_rigged:
                car_settings = active_car.settings

                layout.prop(car_settings, "export_path", text="Export Path")
                row = layout.row()

                # Show only if multiple cars are rigged 
                if len(scene.lc.cars) > 1:
                    row.prop(scene.settings, "export_all_cars", text="Export All Cars")
                    row.enabled = not multi_edit
                    
                    
                    #if scene.settings.export_all_cars or multi_edit:
                    layout.prop(scene.settings, "include_ground_for_all", text="Include Ground Colliders")
                    
                    #if not scene.settings.include_ground_for_all:
                        #layout.prop(car_settings, "include_ground", text="Include Ground Colliders for Selected Car")
                
                else:
                    layout.prop(car_settings, "include_ground", text="Include Ground Colliders")


                layout.operator(OBJECT_OT_quick_export_datasmith.bl_idname)
                layout.operator(OBJECT_OT_quick_export_blend.bl_idname)

                layout.separator(factor=LARGE)

                layout.label(text="FBX exclusive settings", icon="OPTIONS")

                row = layout.row()
                row.prop(scene.settings, "include_anim", text="Include Animations")
                if scene.settings.include_anim:
                    row.prop(scene.settings, "export_anim_only", text="Only Animations")
                    row = layout.row()
                    row.prop(scene.settings, "subframes", text="Animation Subframes")

                layout.operator(OBJECT_OT_quick_export.bl_idname)
                layout.operator(OBJECT_OT_quick_exportUE.bl_idname)

            else:
                row = layout.row()
                row.label(text="Please rig the Vehicle")
                
        else:
            row = layout.row()
            row.label(text="Please select or add an LC Vehicle")


class PANEL_PT_AdvancedHeadlights(PANEL_AdvancedOverall, bpy.types.Panel):
    bl_parent_id = "PANEL_PT_Advanced"
    bl_label = "Headlights (Cycles only)"

    def draw_header(self, context):
        self.layout.label(text="", icon="LIGHT")

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        selected_collection = scene.car_collection
        multi_edit = scene.settings.edit_all_mode

        if selected_collection:
            active_car = scene.lc.find_selected()
            if active_car and active_car.is_rigged:
                car_settings = active_car.settings
                car_properties = active_car.properties

                layout.separator(factor = MEDIUM)

                layout.prop(car_properties, "headlights_presets", text="Type")

                layout.label(text="Beams Visibility:")
                flow = layout.column_flow(columns=2)
                flow.prop(car_settings, "low_beam_visibility", text="Low Beam")
                flow.prop(car_settings, "high_beam_visibility", text="High Beam")

                layout.separator(factor=MEDIUM)

                if car_settings.low_beam_visibility or car_settings.high_beam_visibility:
                    layout.prop(car_settings, "link_beams", text="Link Beam Settings")

                    text = "Headlights" if car_settings.link_beams else "Low Beam"
                    layout.label(text=text + " Settings", icon="PROP_OFF")
                    layout.prop(car_properties, "low_beam_temperature", text="Temperature")
                    layout.prop(car_properties, "low_beam_intensity", text="Intensity")
                    row = layout.row()
                    row.prop(car_properties, "low_beam_spread", text="Spread")
                    row.enabled = not multi_edit
                    layout.prop(car_properties, "low_beam_sharpness", text="Sharpness")

                    if not car_settings.link_beams:
                        layout.label(text="High Beam Settings", icon="PROP_ON")
                        layout.prop(car_properties, "high_beam_temperature", text="Temperature")
                        layout.prop(car_properties, "high_beam_intensity", text="Intensity")
                        row = layout.row()
                        row.prop(car_properties, "high_beam_spread", text="Spread")
                        row.enabled = not multi_edit
                        layout.prop(car_properties, "high_beam_sharpness", text="Sharpness")

                layout.separator(factor = MEDIUM)
            
            else:
                row = layout.row()
                row.label(text="Please rig the Vehicle")
                
        else:
            row = layout.row()
            row.label(text="Please select or add an LC Vehicle")


class PANEL_PT_Skidmarks(PANEL_AdvancedOverall, bpy.types.Panel):
    bl_parent_id = "PANEL_PT_Advanced"
    bl_label = "Skidmarks"

    def draw_header(self, context):
        self.layout.label(text="", icon="PARTICLE_TIP")

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        selected_collection = scene.car_collection

        if selected_collection:
            active_car = scene.lc.find_selected()

            if active_car and active_car.is_rigged:
                car_settings = active_car.settings
                car_properties = active_car.properties

                layout.label(text="Epic Skidmarks:")
                
                layout.separator(factor=MEDIUM)

                layout.prop(car_settings, "enable_skidmarks", text="Enable Skidmark Generator")
                if car_settings.enable_skidmarks:
                    layout.label(text="Is calculated based on G-force. Wheel spin and Wheel locking is not yet considered")

                    layout.separator(factor=SMALL)

                    flow = layout.column_flow(columns=2)
                    flow.operator(OBJECT_OT_bake_skidmarks.bl_idname, icon="FREEZE")
                    flow.operator(OBJECT_OT_free_skidmarks.bl_idname, icon="PLAY")
                    
                    layout.separator(factor=MEDIUM)

                    layout.prop(car_properties, "skidmarks_mul", text="Skidmark Intensity")

                    layout.separator(factor=SMALL)

                    layout.prop(car_properties, "skidmarks_var", text="Skidmark Variance")

            else:
                row = layout.row()
                row.label(text="Please rig the Vehicle")
                
        else:
            row = layout.row()
            row.label(text="Please select or add an LC Vehicle")


class PANEL_PT_View(PANEL_AdvancedOverall, bpy.types.Panel):
    bl_parent_id = "PANEL_PT_Advanced"
    bl_label = "View"

    def draw_header(self, context):
        self.layout.label(text="", icon="HIDE_OFF")

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        selected_collection = scene.car_collection

        if selected_collection:
            active_car = scene.lc.find_selected()

            if active_car and active_car.is_rigged:
                car_settings = active_car.settings

                layout.label(text="Show in Viewport: ")
                box = layout.box()
                box.prop(car_settings, "ui_view_elements", text="")
                #box.prop(car_settings, "show_extra_animation_controls", text="Extra Animation Controls")
                box.prop(car_settings, "show_camera_hooks", text="Camera Hooks")
                box.prop(car_settings, "show_ground_grid", text="Detection Grid")
                
                layout.separator(factor=LARGE)

                layout.label(text="Debug Physics: ", icon="PHYSICS")
                box = layout.box()
                box.prop(car_settings, "show_acc_viz", text="G-Force Visualizer")
                box.prop(car_settings, "show_vel_viz", text="Velocity Visualizer")
            
            else:
                row = layout.row()
                row.label(text="Please rig the Vehicle")
                
        else:
            row = layout.row()
            row.label(text="Please select or add an LC Vehicle")


class PANEL_PT_RigSettings(PANEL_AdvancedOverall, bpy.types.Panel):
    bl_parent_id = "PANEL_PT_Advanced"
    bl_label = "Settings"

    def draw_header(self, context):
        self.layout.label(text="", icon="SETTINGS")

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        multi_edit = scene.settings.edit_all_mode

        selected_collection = scene.car_collection

        if selected_collection:
            active_car = scene.lc.find_selected()

            if active_car and active_car.is_rigged:
                car_settings = active_car.settings
                car_properties = active_car.properties

                layout.label(text="Path: ") 
                box = layout.box()
                box.operator(OBJECT_OT_refresh_path_len.bl_idname, icon="FILE_REFRESH")
                box.prop(car_settings, "snap_path", text="Snap Control Points")

                layout.separator(factor=LARGE)
                layout.separator(factor=LARGE)

                layout.label(text="Ground Colliders: ") 

                ground_detect_collection = get_collection_by_name(COLLECTIONNAME_GROUNDDETECT, scene.collection)

                if ground_detect_collection is not None:  # Avoid breaking pre LC 1.6

                    c = layout.column()
                    row = c.row()
                    split = row.split(factor=0.10)
                    c = split.column()

                    split = split.box()
                    c = split.column()
                    for o in ground_detect_collection.objects: 
                        if (o.name!=""):
                            lisr = c.row()
                            lisr.label(text= ("•  " + o.name))
                    
                    if ("lisr" not in locals()):
                        lisr = c.row()
                        lisr.label(text="No Objects in Ground Detection", icon="ERROR")

                    lisr = c.row(align=True)
                    lisr.operator(OBJECT_OT_add_ground_colliders.bl_idname, text="Add Selected", icon="ADD")
                    lisr.operator(OBJECT_OT_remove_ground_colliders.bl_idname, text="Remove Selected", icon="REMOVE")
                    lisr.operator(OBJECT_OT_remove_all_ground_colliders.bl_idname, text="", icon="CANCEL")

                else:
                    pass
                    #log_info(f"Could not find 'ground_detection_collection' reference inside the LC data. Will not draw UI element. Remove all LC vehicles and rig them again to fix this.", "LC - missing data")

                layout.separator(factor=MEDIUM)


                layout.label(text="Ground Detection: ") 

                box = layout.box()

                if not car_settings.use_true_ground:
                    box.prop(car_settings, "show_ground_grid", text="Detection Grid")

                    if car_settings.show_ground_grid:
                        box.prop(car_settings, "grid_resolution", text="Resolution")

                box.prop(car_settings, "use_true_ground", text="Use True Ground (Smooth shading only)")

                layout.separator(factor=LARGE)
                layout.separator(factor=LARGE)

                layout.label(text="Animation: ") 
                box = layout.box()
                box.prop(car_settings, "limit_sliders", text="Limit animation sliders")
                box.prop(car_properties, "shake_frequency", text="Wheel Shake Rate")

                layout.separator(factor=LARGE)
                layout.separator(factor=LARGE)

                layout.label(text="Find more settings inside 'Add-on Preferences'") 
                
            else:
                row = layout.row()
                row.label(text="Please rig the Vehicle")
                
        else:
            row = layout.row()
            row.label(text="Please select or add an LC Vehicle")


class PANEL_PT_AdvancedPath(PANEL_AdvancedOverall, bpy.types.Panel):
    bl_parent_id = "PANEL_PT_Advanced"
    bl_label = "Jump Trajectory"

    def draw_header(self, context):
        self.layout.label(text="", icon="DRIVER_ROTATIONAL_DIFFERENCE")

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        multi_edit = scene.settings.edit_all_mode

        selected_collection = scene.car_collection
        addon_preferences = context.preferences.addons[__name__.split(".")[0]].preferences

        if selected_collection:
            active_car = scene.lc.find_selected()

            if active_car and active_car.is_rigged:
                car_settings = active_car.settings

                layout.separator(factor = MEDIUM)

                # info text
                text1 = "Generate points on the driving path that emulates a realistic car jump."
                label_multiline(context, text1, layout)

                # help
                layout.prop(car_settings, "show_jump_help", text="Show Help")
                if car_settings.show_jump_help:
                    step1 = "1. Select the last point before the car leaves the ground."
                    step2 = "2. Click 'Jump!'"
                    step3 = "3. Make sure the point handle is pointing in the direction the car will fly."
                    label_multiline(context, step1, layout)
                    label_multiline(context, step2, layout)
                    label_multiline(context, step3, layout)

                layout.separator(factor=LARGE)

                # Commands
                unit = "mph" if addon_preferences.use_imperial else "km/h"
                flow = layout.column_flow(columns=2)
                flow.prop(car_settings, "jump_speed", text=f"Speed ({unit})")
                flow.operator(OBJECT_OT_prepare_jump.bl_idname)
                flow.enabled = not multi_edit

                layout.separator(factor = MEDIUM)
            
            else:
                row = layout.row()
                row.label(text="Please rig the Vehicle")
                
        else:
            row = layout.row()
            row.label(text="Please select or add an LC Vehicle")


class PANEL_PT_AdvancedCamera(PANEL_AdvancedOverall, bpy.types.Panel):
    bl_parent_id = "PANEL_PT_Advanced"
    bl_label = "Cinematographer "

    def draw_header(self, context):
        self.layout.label(text="", icon="CAMERA_DATA")

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        multi_edit = scene.settings.edit_all_mode

        selected_collection = scene.car_collection

        if selected_collection:
            active_car = scene.lc.find_selected()

            if active_car and active_car.is_rigged:
                car_settings = active_car.settings

                layout.separator(factor = MEDIUM)

                row = layout.row()
                row.operator(CAMERAS_OT_create_cams.bl_idname)
                row.enabled = not multi_edit

                layout.separator(factor = MEDIUM)

                text = "More fun stuff is gonna appear here soon :)"
                label_multiline(context, text, layout)
                
                layout.separator(factor = MEDIUM)
            
            else:
                row = layout.row()
                row.label(text="Please rig the Vehicle")
                
        else:
            row = layout.row()
            row.label(text="Please select or add an LC Vehicle")


class PANEL_PT_RigInfo(PANEL_AdvancedOverall, bpy.types.Panel):
    bl_parent_id = "PANEL_PT_Advanced"
    bl_label = "Rig Info"

    def draw_header(self, context):
        self.layout.label(text="", icon="INFO")

    def draw(self, context):
        
        # Call to check for update in background
        addon_updater_ops.check_for_update_background()

        scene = context.scene
        layout = self.layout
        multi_edit = scene.settings.edit_all_mode

        selected_collection = scene.car_collection

        if selected_collection:
            active_car = scene.lc.find_selected()

            if active_car and active_car.is_rigged:

                if not multi_edit:
                    car_props = active_car.properties
                    has_attr = hasattr(car_props, 'lc_version')
                    
                    if has_attr:
                        if car_props.lc_version != "0.0.0":
                            
                            lc_version = str(car_props.lc_version).replace(", ", ".")
                            lc_version = lc_version.replace("(", "")
                            lc_version = lc_version.replace(")", "")

                        else:
                            lc_version = "-.-.-"
                    else:
                        lc_version = "-.-.-"
                    
                    addon_version = get_addon_version()
                    addon_version = addon_version.replace(", ", ".")
                    addon_version = addon_version.replace("(", "")
                    addon_version = addon_version.replace(")", "")

                    if addon_version == lc_version:
                        version_icon = "CHECKMARK"
                    else:
                        version_icon = "ERROR"

                    row = layout.row()
                    row.label(text=("Version Check:"))

                    row = layout.row(align=True)
                    row.label(text=("Vehicle: " + lc_version),icon=version_icon)
                    row.label(text=("Add-on: " + addon_version))

                    row = layout.row()
                    row.operator(OBJECT_OT_update_vehicle_rig.bl_idname)


                else:
                    row = layout.row()
                    row.label(text="Please disable 'Multi-Edit'")

            else:
                legacy_detection = False

                for coll in scene.collection.children_recursive:
                    if coll.name == "CarRigAddon":
                        legacy_detection = True

                if legacy_detection:
                    row = layout.row()
                    row.label(text=("Version Check:"))
                    row = layout.row()
                    row.label(text="Legacy Rig Detected (1.0.0 - 1.3.5)")
                    row = layout.row()
                    row.operator(OBJECT_OT_update_vehicle_rig.bl_idname)
                
                else:
                    row = layout.row()
                    row.label(text="Please rig the Vehicle")        
                
        else:
            row = layout.row()
            row.label(text="Please select or add an LC Vehicle")

        addon_updater_ops.update_notice_box_ui(self, context)


class ADDONPREFERENCES_UserPref(bpy.types.AddonPreferences):
    bl_idname = __name__.split(".")[0]

    show_vehicle_gallery: bpy.props.BoolProperty(
        name="Show Vehicle Gallery and Append options",
        default=True,
    )

    show_animation_gallery: bpy.props.BoolProperty(
        name="Show Animation Gallery",
        default=True,
    )
    
    animation_sliders_location: bpy.props.EnumProperty(
        items=[
            ('3d_interface', 'Floating in Viewport', '', '', 1),
            ('python_interface', 'Static in N-Panel', '', '', 0)   
        ],
        default='3d_interface'
    )

    show_slider_labels: bpy.props.BoolProperty(
        name="Show Animation Handle Labels",
        default=True,
        update=commands.update_labels
    )

    use_imperial: bpy.props.BoolProperty(
        name="Use Imperial Units",
        default=False,
        update=commands.reveal_imperial
    )

    override_anim_on_path_change: bpy.props.BoolProperty(
        name = "Override Animation Data",
        description="Remove current animation data when a new 'User Path' is picked in the interface and 'Animate Vehicle!' is pressed. Animation will be replaced by an automatically calculated offset animation", 
        default=True
    )

    open_graph_editor_segments: bpy.props.BoolProperty(
        name = "Open Graph Editor with Speed Segments",
        description="Allow LC to automatically turn your timeline into a graph editor when the Speed Segment Tool is activated. This makes sure that you can preview and debug the animation curve while using the Speed Segments in the viewport", 
        default=True
    )

    auto_pivot: bpy.props.BoolProperty(
        name="Calculate Tire Pivot",
        description="Let LC automatically create new pivots for the tire meshes used for rigging. The new pivots will override any user set pivots. Uncheck to keep user pivots. Auto Pivot will make each wheel a 'single user data'",
        default=True,
    )

    use_custom_tags: bpy.props.BoolProperty(
        name="Use Custom Tags",
        description="Allow the user to define custom search tags that LC will search for when rigging the car",
        default=0,
    )

    custom_tire: bpy.props.StringProperty(
        name="Custom Tire Tag",
        description="Custom rigging search tag for LC to detect tire meshes",
        default="tire",
    )

    custom_RL: bpy.props.StringProperty(
        name="Custom Rear Left Tag",
        description="Custom rigging search tag for LC to detect rear left (wheel) meshes. E.g. '_RL'",
        default="_RL",
    )

    custom_RR: bpy.props.StringProperty(
        name="Custom Rear Right Tag",
        description="Custom rigging search tag for LC to detect rear right (wheel) meshes. E.g. '_RR'",
        default="_RR",
    )

    custom_FR: bpy.props.StringProperty(
        name="Custom Front Right Tag",
        description="Custom rigging search tag for LC to detect front right (wheel) meshes. E.g. '_FR'",
        default="_FR",
    )

    custom_FL: bpy.props.StringProperty(
        name="Custom Front Left Tag",
        description="Custom rigging search tag for LC to detect front left (wheel) meshes. E.g. '_FL'",
        default="_FL",
    )

    custom_brake: bpy.props.StringProperty(
        name="Custom Brake Caliper Tag",
        description="Custom rigging search tag for LC to detect brake caliper meshes",
        default="brake",
    )

    custom_covers: bpy.props.StringProperty(
        name="Custom Wheelcovers Tag",
        description="Custom rigging search tag for LC to detect wheelcover meshes",
        default="wheelcover",
    )

    custom_body: bpy.props.StringProperty(
        name="Custom Body Tag",
        description="Custom rigging search tag for LC to detect body meshes",
        default="body",
    )

    force_rig_brakes: bpy.props.EnumProperty(
        name="Rigging brakes",
        description="Options for rigging brakes when clicking 'Rig Vehicle'",
        items=[
            (
                "OP1",
                "If possible",
                "Only rig the brakes if they can be found. If they cannot be found ignore them and move on",
            ),
            (
                "OP2",
                "Force it",
                "Force the brakes to be rigged. If brakes cannot be found give an error message",
            ),
            ("OP3", "Never", "Just ignore brakes. Don't even try..."),
        ],
    )

    force_rig_headlights: bpy.props.EnumProperty(
        name="Rigging Headlights",
        description="Options for rigging headlights when clicking 'Rig Vehicle'",
        items=[
            (
                "OP1",
                "If possible",
                "Only rig the headlights if they can be found. If they cannot be found, leave them at the location and let the user move them",
            ),
            ("OP2", "Never", "Just ignore headlights. Don't even try..."),
        ],
    )

    force_rig_wheelcovers: bpy.props.EnumProperty(
        name="Rigging Wheel Covers",
        description="Options for rigging Wheel Covers when clicking 'Rig Vehicle'",
        items=[
            (
                "OP1",
                "If possible",
                "Only rig the Wheel Covers if they can be found. If they cannot be found ignore them and move on",
            ),
            (
                "OP2",
                "Force it",
                "Force the Wheel Covers to be rigged. If Wheel Covers cannot be found give an error message",
            ),
            ("OP3", "Never", "Just ignore Wheel Covers. Don't even try..."),
        ],
    )

    apply_path_color: bpy.props.BoolProperty(
        name="Colorize Driving Paths",
        description="Automatically color the Driving Paths the color of the collection which the corrosponding vehicle exists in when clicking 'Animate Vehicle!'",
        default=True,
    )

    enable_multi_rigging: bpy.props.BoolProperty(
        name="Multi-Rigging",
        description="Show the 'Multi-Edit' button when NO VEHICLES are rigged. This specifically allows you to rig all vehicles in your file at the same time. Please do not have any other collections, but collections containing cars inside the file to use this feature.",
        default=False,
    )

    show_pro_options: bpy.props.BoolProperty(
        name="Show CAD Workflow in UI",
        description="Enable elements in the UI that are built for rigging manufaturers data-sets",
        default=False,
    )

    
    # addon updater preferences from `__init__`, be sure to copy all of them
    auto_check_update: bpy.props.BoolProperty(
        name = "Auto-check for Update",
        description = "If enabled, auto-check for updates using an interval",
        default = False,
    )

    web_loc: bpy.props.EnumProperty(
        name = "Platform",
        description = "Pick the platform that you Bought Launch Control from",
        items=[
            (
                "OP1",
                "BlenderMarket",
                "If you ordered Launch Control on BlenderMarket",
            ),
            ("OP2", "GumRoad", "If you ordered Launch Control on GumRoad"),
        ],
    )

    updater_interval_months: bpy.props.IntProperty(
        name='Months',
        description = "Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_interval_days: bpy.props.IntProperty(
        name='Days',
        description = "Number of days between checking for updates",
        default=7,
        min=0,
    )
    updater_interval_hours: bpy.props.IntProperty(
        name='Hours',
        description = "Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    updater_interval_minutes: bpy.props.IntProperty(
        name='Minutes',
        description = "Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
    )


    def draw(self, context):
        layout = self.layout
        addon_preferences = context.preferences.addons[__name__.split(".")[0]].preferences

        layout.separator(factor=SMALL)

        blender_min_version = get_blender_min_version()

        blender_min_version_string = str(blender_min_version)
        blender_min_version_string = blender_min_version_string.replace(", ", ".")
        blender_min_version_string = blender_min_version_string.replace("(", "")
        blender_min_version_string = blender_min_version_string.replace(")", "")

        if bpy.app.version < blender_min_version:  # Validate installation version!
            box = layout.box()
            box.label(text="Warning!", icon="ERROR")
            box.label(text=f"This version of Launch Control requires Blender {blender_min_version_string} or higher!")
            box.label(text=f"Your version: {bpy.app.version_string}")
            box.label(text=f"Please upgrade Blender or install a compatible version of Launch Control")

            layout.separator(factor=SMALL)


        row = layout.row(align=True)
        op = row.operator('wm.url_open', text='Launch Control Documentation', icon='URL')
        op.url = 'https://launch-control-documentation.readthedocs.io/en/latest/launch-control-core.html'

        layout.separator(factor=SMALL)

        box = layout.box()
        box.label(text="Interface:", icon="VIEW3D")
        box.prop(self, "show_vehicle_gallery")
        box.prop(self, "show_animation_gallery")
        #box.prop(self, "animation_sliders_location", text="Show Animation Sliders")

        if addon_preferences.animation_sliders_location == '3d_interface':
            box.prop(self, "show_slider_labels", text="Show Slider Labels")
        

        box = layout.box()
        box.label(text="Animation:", icon="GRAPH")
        box.prop(self, "use_imperial", text="Use Imperial Units")
        box.prop(self, "override_anim_on_path_change", text="Override Animation Data")
        box.prop(self, "apply_path_color", text="Colorize Driving Paths")
        box.prop(self, "open_graph_editor_segments", text="Auto-convert Timeline into Graph Editor")
        


        box = layout.box()
        
        box.label(text="Rigging:", icon="ARMATURE_DATA")
        box.prop(self, "auto_pivot", text="Automatic Tire Pivot")
        box.prop(self, "use_custom_tags", text="Use Custom Tags")

        if addon_preferences.use_custom_tags:
            box.prop(self, "custom_body", text="Body")
            box.prop(self, "custom_tire", text="Tire")
            box.prop(self, "custom_RL", text="Rear Left")
            box.prop(self, "custom_RR", text="Rear Right")
            box.prop(self, "custom_FR", text="Front Right")
            box.prop(self, "custom_FL", text="Front Left")
            box.prop(self, "custom_brake", text="Brake Caliper [Optional]")
            box.prop(self, "custom_covers", text="Wheel Covers [Optional]")
        

        box.prop(self, "force_rig_brakes", text="Rig Brakes")
        box.prop(self, "force_rig_headlights", text="Rig Headlights")
        box.prop(self, "force_rig_wheelcovers", text="Rig Wheel Covers")
        box.prop(self, "show_pro_options", text="Show CAD Workflow in UI")
        #box.prop(self, "enable_multi_rigging", text="Multi-Rigging [Experimental]")

        addon_updater_ops.update_settings_ui(self,context) 
        