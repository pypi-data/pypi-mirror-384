import copy
import os
from tkinter import *

import cv2
import pandas as pd
import PIL.Image
from PIL import ImageTk

from simba.mixins.config_reader import ConfigReader
from simba.mixins.plotting_mixin import PlottingMixin
from simba.mixins.pop_up_mixin import PopUpMixin
from simba.roi_tools.ROI_image import ROI_image_class
from simba.roi_tools.ROI_move_shape import move_edge, update_all_tags
from simba.roi_tools.ROI_multiply import create_emty_df
from simba.roi_tools.ROI_size_calculations import (circle_size_calc,
                                                   polygon_size_calc,
                                                   rectangle_size_calc)
from simba.ui.pop_ups.roi_fixed_size_pop_up import DrawFixedROIPopUp
from simba.ui.tkinter_functions import SimbaButton, hxtScrollbar
from simba.utils.checks import check_file_exist_and_readable
from simba.utils.enums import Formats, TagNames
from simba.utils.errors import NoROIDataError
from simba.utils.lookups import get_color_dict, get_icons_paths
from simba.utils.printing import log_event, stdout_success
from simba.utils.read_write import find_all_videos_in_directory, get_fn_ext
from simba.utils.warnings import NoDataFoundWarning

WINDOW_SIZE = (825, 825) #800

class ROI_definitions(ConfigReader, PopUpMixin):
    """
    Launch ROI user-interface for drawing user-defined shapes in a video.

    Parameters
    ----------
    config_path: str
        path to SimBA project config file in Configparser format
    video_path: str
        path to video file for which ROIs should be defined.

    Notes
    ----------
    `ROI tutorials <https://github.com/sgoldenlab/simba/blob/master/docs/ROI_tutorial_new.md>`__.

    Examples
    ----------
    >>> _ = ROI_definitions(config_path='MyProjectConfig', video_path='MyVideoPath')

    """

    def __init__(self, config_path: str, video_path: str):

        check_file_exist_and_readable(file_path=config_path)
        check_file_exist_and_readable(file_path=video_path)

        ConfigReader.__init__(self, config_path=config_path)
        log_event(logger_name=str(__class__.__name__),log_type=TagNames.CLASS_INIT.value,msg=self.create_log_msg_from_init_args(locals=locals()),)
        self.video_path = video_path
        _, self.file_name, self.file_ext = get_fn_ext(self.video_path)
        self.other_video_paths = list(find_all_videos_in_directory(directory=self.video_dir, as_dict=True).values())
        self.other_video_paths.remove(video_path)
        self.other_video_file_names = []
        for video in self.other_video_paths:
            self.other_video_file_names.append(os.path.basename(video))
        self.video_info, self.curr_px_mm, self.curr_fps = self.read_video_info(video_name=self.file_name)

        self.menu_icons = get_icons_paths()

        for k in self.menu_icons.keys():
            self.menu_icons[k]["img"] = ImageTk.PhotoImage(image=PIL.Image.open(os.path.join(os.path.dirname(__file__), self.menu_icons[k]["icon_path"])))

        self.roi_root = Toplevel()
        self.roi_root.minsize(WINDOW_SIZE[0], WINDOW_SIZE[1])
        self.screen_width = self.roi_root.winfo_screenwidth()
        self.screen_height = self.roi_root.winfo_screenheight()
        self.default_top_left_x = self.screen_width - WINDOW_SIZE[0]
        self.roi_root.geometry("%dx%d+%d+%d" % (WINDOW_SIZE[0], WINDOW_SIZE[1], self.default_top_left_x, 0))
        self.roi_root.wm_title("Region of Interest Settings")
        self.roi_root.protocol("WM_DELETE_WINDOW", self._terminate)

        self.shape_thickness_list = list(range(1, 26))
        self.ear_tag_size_list = list(range(1, 26))
        self.select_color = "red"
        self.non_select_color = "black"
        self.video_ROIs = ["None"]
        self.c_shape = None
        self.stored_interact = None
        self.stored_shape = None
        self.img_no = 1
        self.duplicate_jump_size = 20
        self.click_sens = 10
        self.text_size, _, _ = PlottingMixin().get_optimal_font_scales(text='TEN DIGITS', accepted_px_width=int(self.video_info['Resolution_width']/10), accepted_px_height=int(self.video_info['Resolution_height']/10), text_thickness=2, font=cv2.FONT_HERSHEY_SIMPLEX)
        self.text_thickness = 2
        self.line_type = -1
        self.named_shape_colors = get_color_dict()
        self.window_menus()
        self.roi_root.lift()
        self.master = Canvas(hxtScrollbar(self.roi_root))
        self.master.pack(fill="both", expand=True)
        self.show_video_info()
        self.select_img()
        self.apply_from_other_videos_menu()
        self.select_shape()
        self.select_shape_attr()
        self.select_shape_name()
        self.interact_menus()
        self.draw_menu()
        self.save_menu()
        self.image_data = ROI_image_class(config_path=self.config_path, video_path=self.video_path, ROI_define_instance=self)
        self.video_frame_count = int(self.image_data.video_frame_count)
        self.get_all_ROI_names()
        if len(self.video_ROIs) > 0:
            self.update_delete_ROI_menu()

        self.master.mainloop()

    def _terminate(self):
        self.Exit()

    def show_video_info(self):
        self.video_info_frame = LabelFrame(self.master, text="Video information", font=Formats.FONT_HEADER.value, padx=5, pady=5)
        self.video_info_frame.grid_configure(ipadx=55)
        self.video_name_lbl_1 = Label(self.video_info_frame, text="Video name: ", font=Formats.FONT_REGULAR.value).grid(row=0, column=0)
        self.video_name_lbl_2 = Label(self.video_info_frame, text=str(self.file_name), font=Formats.FONT_REGULAR.value)

        self.video_ext_lbl_1 = Label(self.video_info_frame, text="Video format: ", font=Formats.FONT_REGULAR.value).grid(row=0, column=2)
        self.video_ext_lbl_2 = Label(self.video_info_frame, text=str(self.file_ext), font=Formats.FONT_REGULAR.value)

        self.video_fps_lbl_1 = Label(self.video_info_frame, text="FPS: ", font=Formats.FONT_REGULAR.value).grid(row=0, column=4)
        self.video_fps_lbl_2 = Label(self.video_info_frame, text=str(self.curr_fps), font=Formats.FONT_REGULAR.value)

        self.video_frame_lbl_1 = Label(self.video_info_frame, text="Display frame #: ", font=Formats.FONT_REGULAR.value).grid(row=0, column=6)
        self.video_frame_lbl_2 = Label(self.video_info_frame, text=str(self.img_no), font=Formats.FONT_REGULAR.value)

        self.video_frame_time_1 = Label(self.video_info_frame, text="Display frame (s): ", font=Formats.FONT_REGULAR.value).grid(row=0, column=8)
        self.video_frame_time_2 = Label(self.video_info_frame,text=str(round((self.img_no / self.curr_fps), 2)),font=Formats.FONT_REGULAR.value)

        self.video_info_frame.grid(row=0, sticky=W)
        self.video_name_lbl_2.grid(row=0, column=1)
        self.video_ext_lbl_2.grid(row=0, column=3)
        self.video_fps_lbl_2.grid(row=0, column=5)
        self.video_frame_lbl_2.grid(row=0, column=7)
        self.video_frame_time_2.grid(row=0, column=9)

    def select_img(self):
        self.img_no_frame = LabelFrame(self.master, text="Change image", font=Formats.FONT_REGULAR.value, padx=5, pady=5)
        self.img_no_frame.grid_configure(ipadx=100)

        self.pos_1s = SimbaButton(parent=self.img_no_frame, txt="+1s", img='plus', font=Formats.FONT_REGULAR.value, txt_clr=self.non_select_color, cmd=self.set_current_image, cmd_kwargs={'stride': 'plus'})
        self.neg_1s = SimbaButton(parent=self.img_no_frame, txt="-1s", img='minus', font=Formats.FONT_REGULAR.value, txt_clr=self.non_select_color, cmd=self.set_current_image, cmd_kwargs={'stride': 'minus'})
        self.reset_btn = SimbaButton(parent=self.img_no_frame, txt="RESET FIRST FRAME", img='restart', font=Formats.FONT_REGULAR.value, txt_clr=self.non_select_color, cmd=self.set_current_image, cmd_kwargs={'stride': 'reset'})
        self.seconds_fw_label = Label(self.img_no_frame, font=Formats.FONT_REGULAR.value, text="Seconds forward: ")
        self.seconds_fw_entry = Entry(self.img_no_frame, width=4, font=Formats.FONT_REGULAR.value)
        self.custom_run_seconds = SimbaButton(parent=self.img_no_frame, txt="MOVE", img='fast_forward', font=Formats.FONT_REGULAR.value, txt_clr=self.non_select_color, cmd=self.set_current_image, cmd_kwargs={'stride': 'custom'})
        self.img_no_frame.grid(row=1, sticky=W)
        self.pos_1s.grid(row=1, column=0, sticky=W, pady=10, padx=10)
        self.neg_1s.grid(row=1, column=1, sticky=W, pady=10, padx=10)
        self.seconds_fw_label.grid(row=1, column=2, sticky=W, pady=10)
        self.seconds_fw_entry.grid(row=1, column=3, sticky=W, pady=10)
        self.custom_run_seconds.grid(row=1, column=4, sticky=W, pady=10)
        self.reset_btn.grid(row=1, column=5, sticky=W, pady=10, padx=10)

    def set_current_image(self, stride: str):
        if stride == "plus":
            img_no = self.img_no + self.curr_fps
            if (img_no > 0) and (img_no < self.video_frame_count):
                self.img_no = img_no
                self.pos_1s.configure(fg=self.select_color)
                self.neg_1s.configure(fg=self.non_select_color)
                self.custom_run_seconds.configure(fg=self.non_select_color)

        if stride == "minus":
            img_no = self.img_no - self.curr_fps
            if (img_no > 0) and (img_no < self.video_frame_count):
                self.img_no = img_no
                self.pos_1s.configure(fg=self.non_select_color)
                self.neg_1s.configure(fg=self.select_color)
                self.custom_run_seconds.configure(fg=self.non_select_color)

        if stride == "reset":
            self.img_no = 1

        if stride == "custom":
            img_no = self.img_no + int(self.curr_fps * int(self.seconds_fw_entry.get()))
            if (img_no > 0) and (img_no < self.video_frame_count):
                self.img_no = img_no
                self.pos_1s.configure(fg=self.non_select_color)
                self.neg_1s.configure(fg=self.non_select_color)
                self.custom_run_seconds.configure(fg=self.select_color)

        self.video_frame_lbl_2.config(text=str(self.img_no))
        self.video_frame_time_2.config(text=str(round((self.img_no / self.curr_fps), 2)))
        self.image_data.update_frame_no(self.img_no)

    def get_other_videos_w_data(self):
        self.other_videos_w_ROIs = []
        if os.path.isfile(self.roi_coordinates_path):
            for shape_type in ["rectangles", "circleDf", "polygons"]:
                try:
                    c_df = pd.read_hdf(self.roi_coordinates_path, key=shape_type)
                except ValueError as e:
                    raise NoROIDataError(
                        msg=f"Could not read prior ROI data for video {self.file_name}: The ROI data for the video was likely saved in a different python / pickle version. {e.args}",
                        source=self.__class__.__name__,
                    )
                if len(c_df) > 0:
                    self.other_videos_w_ROIs = list(
                        set(self.other_videos_w_ROIs + list(c_df["Video"].unique()))
                    )
        if len(self.other_videos_w_ROIs) == 0:
            self.other_videos_w_ROIs = ["None"]

    def get_all_ROI_names(self):
        self.video_ROIs = []
        for shape in [
            self.image_data.out_rectangles,
            self.image_data.out_circles,
            self.image_data.out_polygon,
        ]:
            for e in shape:
                shape_type = e["Shape_type"]
                shape_name = e["Name"]
                self.video_ROIs.append(shape_type + ": " + shape_name)

    def apply_rois_from_other_video(self):
        target_video = self.selected_other_video.get()
        if target_video != "None":
            if os.path.isfile(self.roi_coordinates_path):
                for shape_type in ["rectangles", "circleDf", "polygons"]:
                    c_df = pd.read_hdf(self.roi_coordinates_path, key=shape_type)
                    if len(c_df) > 0:
                        c_df = c_df[c_df["Video"] == target_video].reset_index(drop=True)
                        c_df["Video"] = self.file_name
                        c_df = c_df.to_dict("records")
                        if shape_type == "rectangles":
                            for r in c_df:
                                self.image_data.out_rectangles.append(r)
                        if shape_type == "circleDf":
                            for c in c_df:
                                self.image_data.out_circles.append(c)
                        if shape_type == "polygons":
                            for p in c_df:
                                self.image_data.out_polygon.append(p)
                self.get_all_ROI_names()
                self.update_delete_ROI_menu()
                self.image_data.insert_all_ROIs_into_image()

    def apply_from_other_videos_menu(self):
        self.get_other_videos_w_data()
        self.apply_from_other_video = LabelFrame( self.master, text="APPLY SHAPES FROM ANOTHER VIDEO", font=Formats.FONT_HEADER.value, padx=5, pady=5)
        self.select_video_label = Label(self.apply_from_other_video, text="SELECT VIDEO: ", font=Formats.FONT_REGULAR.value).grid(row=1, column=0)
        self.selected_other_video = StringVar()
        self.selected_other_video.set(self.other_videos_w_ROIs[0])
        self.video_dropdown = OptionMenu(self.apply_from_other_video, self.selected_other_video, *self.other_videos_w_ROIs)

        self.apply_button = SimbaButton(parent=self.apply_from_other_video, txt='APPLY', img='tick', txt_clr=self.non_select_color, cmd=self.apply_rois_from_other_video)
        self.apply_from_other_video.grid(row=7, sticky=W)
        self.video_dropdown.grid(row=1, column=1, sticky=W, pady=10)
        self.apply_button.grid(row=1, column=3, sticky=W, pady=10)

    def select_shape(self):
        self.new_shape_frame = LabelFrame(self.master, text="NEW SHAPE", font=Formats.FONT_HEADER.value, padx=5, pady=5, bd=5)
        self.shape_frame = LabelFrame(self.new_shape_frame, text="SHAPE TYPE", font=Formats.FONT_REGULAR.value, padx=5, pady=5)

        self.rectangle_button = SimbaButton(parent=self.shape_frame, txt='RECTANGLE', txt_clr=self.non_select_color, font=Formats.FONT_REGULAR.value, img='rectangle', cmd=self.set_current_shape, cmd_kwargs={'c_shape': lambda: "rectangle"})
        self.circle_button = SimbaButton(parent=self.shape_frame, txt='CIRCLE', txt_clr=self.non_select_color, font=Formats.FONT_REGULAR.value, img='circle_2', cmd=self.set_current_shape, cmd_kwargs={'c_shape': lambda: "circle"})
        self.polygon_button = SimbaButton(parent=self.shape_frame, txt='POLYGON', txt_clr=self.non_select_color, font=Formats.FONT_REGULAR.value, img='polygon_2', cmd=self.set_current_shape, cmd_kwargs={'c_shape': lambda: "polygon"})
        self.new_shape_frame.grid(row=3, sticky=W)
        self.shape_frame.grid(row=1, sticky=W)
        self.rectangle_button.grid(row=1, sticky=W, pady=10, padx=10)
        self.circle_button.grid(row=1, column=1, sticky=W, pady=10, padx=10)
        self.polygon_button.grid(row=1, column=2, sticky=W, pady=10, padx=10)

    def select_shape_attr(self):
        self.shape_attr_frame = LabelFrame(self.new_shape_frame, text="SHAPE ATTRIBUTES", font=Formats.FONT_HEADER.value, padx=5, pady=5)
        self.shape_attr_frame.grid_configure(ipadx=50)
        self.thickness_label = Label(self.shape_attr_frame, text="SHAPE THICKNESS: ", font=Formats.FONT_REGULAR.value)
        self.color_label = Label(self.shape_attr_frame, text="SHAPE COLOR: ", font=Formats.FONT_REGULAR.value)
        self.shape_thickness = IntVar()
        self.shape_thickness.set(5)
        self.shape_thickness_dropdown = OptionMenu(self.shape_attr_frame, self.shape_thickness, *self.shape_thickness_list, command=None)
        self.shape_thickness_dropdown.config(width=3)

        self.ear_tag_sizes_lbl = Label(self.shape_attr_frame, text="EAR TAG SIZE: ", font=Formats.FONT_REGULAR.value)
        self.ear_tag_size = IntVar()
        self.ear_tag_size.set(10)
        self.ear_tag_size_dropdown = OptionMenu(self.shape_attr_frame, self.ear_tag_size, *list(self.ear_tag_size_list))

        self.color_var = StringVar()
        self.color_var.set("Red")
        self.color_dropdown = OptionMenu(self.shape_attr_frame, self.color_var, *list(self.named_shape_colors.keys()))

        self.shape_attr_frame.grid(row=2, sticky=W, pady=10)
        self.thickness_label.grid(row=1, column=0)
        self.shape_thickness_dropdown.grid(row=1, column=1, sticky=W, pady=10, padx=(0, 10))
        self.ear_tag_sizes_lbl.grid(row=1, column=2)
        self.ear_tag_size_dropdown.grid(row=1, column=3, sticky=W, pady=10, padx=(0, 10))
        self.color_label.grid(row=1, column=4)
        self.color_dropdown.grid(row=1, column=5, sticky=W, pady=10)

    def select_shape_name(self):
        self.set_shape_name = LabelFrame(self.new_shape_frame, text="SHAPE NAME", font=Formats.FONT_HEADER.value, padx=5, pady=5)
        self.set_shape_name.grid_configure(ipadx=105)
        self.name_label = Label(self.set_shape_name, text="SHAPE NAME: ", font=Formats.FONT_REGULAR.value).grid(row=1, column=0)
        self.name_box = Entry(self.set_shape_name, width=55)
        self.set_shape_name.grid(row=3, sticky=W, pady=10)
        self.name_box.grid(row=1, column=2, sticky=W, pady=10)

    def interact_menus(self):
        self.interact_frame = LabelFrame(self.master, text="SHAPE INTERACTION", font=Formats.FONT_HEADER.value, padx=5, pady=5)
        self.interact_frame.grid_configure(ipadx=30)


        self.move_shape_button = SimbaButton(parent=self.interact_frame, txt="MOVE SHAPE", img='move', txt_clr=self.non_select_color, cmd=self.set_interact_state, cmd_kwargs={'c_interact': lambda: 'move_shape'})

        self.zoom_in_button = SimbaButton(parent=self.interact_frame, txt="Zoom IN", img='zoom_in', txt_clr=self.non_select_color, enabled=False, cmd=self.set_interact_state, cmd_kwargs={'c_interact': lambda: 'zoom_in'})
        self.zoom_out_button = SimbaButton(parent=self.interact_frame, txt="Zoom OUT", img='zoom_out', txt_clr=self.non_select_color, enabled=False, cmd=self.set_interact_state, cmd_kwargs={'c_interact': lambda: 'zoom_out'})
        self.zoom_home = SimbaButton(parent=self.interact_frame, txt="Zoom HOME", img='home', txt_clr=self.non_select_color, enabled=False, cmd=self.set_interact_state, cmd_kwargs={'c_interact': lambda: 'zoom_home'})

        self.zoom_pct_label = Label(self.interact_frame, text="Zoom %: ").grid(row=1, column=5, padx=(10, 0))
        self.zoom_pct = Entry(self.interact_frame, width=4, state=DISABLED)
        self.zoom_pct.insert(0, 10)

        self.pan = Button(self.interact_frame, text="Pan", fg=self.non_select_color, state=DISABLED, command=lambda: self.set_interact_state("pan"))
        self.shape_info_btn = SimbaButton(parent=self.interact_frame, txt="SHOW SHAPE INFO", img='info', txt_clr=self.non_select_color, enabled=True, cmd=self.show_shape_information)


        self.interact_frame.grid(row=6, sticky=W)
        self.move_shape_button.grid(row=1, column=0, sticky=W, pady=10, padx=10)
        self.pan.grid(row=1, column=1, sticky=W, pady=10, padx=10)
        self.zoom_in_button.grid(row=1, column=2, sticky=W, pady=10, padx=10)
        self.zoom_out_button.grid(row=1, column=3, sticky=W, pady=10, padx=10)
        self.zoom_home.grid(row=1, column=4, sticky=W, pady=10, padx=10)
        self.zoom_pct.grid(row=1, column=6, sticky=W, pady=10)
        self.shape_info_btn.grid(row=1, column=7, sticky=W, pady=10)

    def call_remove_ROI(self):
        self.shape_info_btn.configure(text="SHOW SHAPE INFO")
        self.apply_delete_button.configure(fg=self.select_color)
        self.image_data.remove_ROI(self.selected_video.get())
        self.video_ROIs.remove(self.selected_video.get())
        if len(self.video_ROIs) == 0:
            self.video_ROIs = ["None"]
        self.selected_video.set(self.video_ROIs[0])
        self.update_delete_ROI_menu()

    def draw_menu(self):
        self.draw_frame = LabelFrame(self.master, text="Draw", font=Formats.FONT_HEADER.value, padx=5, pady=5)
        self.draw_button = SimbaButton(parent=self.draw_frame, txt='DRAW', img='paint', txt_clr=self.non_select_color, cmd=self.create_draw)
        self.delete_all_rois_btn = SimbaButton(parent=self.draw_frame, txt='DELETE ALL', img='trash', txt_clr=self.non_select_color, cmd=self.call_delete_all_rois)

        self.select_roi_label = Label(self.draw_frame, text="SELECT ROI: ", font=Formats.FONT_REGULAR.value)
        self.selected_video = StringVar()
        self.selected_video.set(self.video_ROIs[0])
        self.roi_dropdown = OptionMenu(self.draw_frame, self.selected_video, *self.video_ROIs)

        self.apply_delete_button = SimbaButton(parent=self.draw_frame, txt='DELETE ROI', img='trash', txt_clr=self.non_select_color, cmd=self.call_remove_ROI)
        self.duplicate_ROI_btn = SimbaButton(parent=self.draw_frame, txt='DUPLICATE ROI', img='duplicate', txt_clr=self.non_select_color, cmd=self.call_duplicate_ROI)
        self.chg_attr_btn = SimbaButton(parent=self.draw_frame, txt='CHANGE ROI', img='edit', txt_clr=self.non_select_color, cmd=self.ChangeAttrMenu, cmd_kwargs={'shape_data': lambda: self, 'image_data': lambda: self.image_data})

        self.draw_frame.grid(row=5, sticky=W)
        self.draw_button.grid(row=1, column=1, sticky=W, pady=2, padx=10)
        self.delete_all_rois_btn.grid(row=1, column=2, sticky=W, pady=2, padx=10)
        self.select_roi_label.grid(row=1, column=3, sticky=W, pady=2, padx=(10, 0))
        self.roi_dropdown.grid(row=1, column=4, sticky=W, pady=2, padx=(0, 10))
        self.apply_delete_button.grid(row=1, column=5, sticky=W, pady=2, padx=10)
        self.duplicate_ROI_btn.grid(row=1, column=6, sticky=W, pady=2, padx=10)
        self.chg_attr_btn.grid(row=1, column=7, sticky=W, pady=2, padx=10)

    def show_shape_information(self):
        if (
            len(self.image_data.out_rectangles)
            + len(self.image_data.out_circles)
            + len(self.image_data.out_polygon)
            == 0
        ):
            print("No shapes to print info for.")

        elif self.shape_info_btn.cget("text") == "SHOW SHAPE INFO":
            if len(self.image_data.out_rectangles) > 0:
                self.rectangle_size_dict = {}
                self.rectangle_size_dict["Rectangles"] = {}
                for rectangle in self.image_data.out_rectangles:
                    self.rectangle_size_dict["Rectangles"][rectangle["Name"]] = (rectangle_size_calc(rectangle, self.curr_px_mm))
                self.image_data.rectangle_size_dict = self.rectangle_size_dict

            if len(self.image_data.out_circles) > 0:
                self.circle_size_dict = {}
                self.circle_size_dict["Circles"] = {}
                for circle in self.image_data.out_circles:
                    self.circle_size_dict["Circles"][circle["Name"]] = circle_size_calc(circle, self.curr_px_mm)
                self.image_data.circle_size_dict = self.circle_size_dict

            if len(self.image_data.out_polygon) > 0:
                self.polygon_size_dict = {}
                self.polygon_size_dict["Polygons"] = {}
                for polygon in self.image_data.out_polygon:
                    self.polygon_size_dict["Polygons"][polygon["Name"]] = (polygon_size_calc(polygon, self.curr_px_mm))
                self.image_data.polygon_size_dict = self.polygon_size_dict

            self.image_data.insert_all_ROIs_into_image(show_size_info=True)
            self.shape_info_btn.configure(text="HIDE SHAPE INFO")

        elif self.shape_info_btn.cget("text") == "HIDE SHAPE INFO":
            self.shape_info_btn.configure(text="SHOW SHAPE INFO")
            self.image_data.insert_all_ROIs_into_image()

    def save_menu(self):
        self.save_frame = LabelFrame(self.master, text="SAVE", font=Formats.FONT_HEADER.value, padx=5, pady=5)
        self.save_button = SimbaButton(parent=self.save_frame, txt="SAVE ROI DATA", img='save', txt_clr=self.non_select_color, cmd=self.save_data)
        self.save_frame.grid(row=8, sticky=W)
        self.save_button.grid(row=1, column=3, sticky=W, pady=10)

    def set_current_shape(self, c_shape: str):
        self.c_shape = c_shape
        self.shape_info_btn.configure(text="SHOW SHAPE INFO")
        if self.c_shape == self.stored_shape:
            self.rectangle_button.configure(fg=self.non_select_color)
            self.circle_button.configure(fg=self.non_select_color)
            self.polygon_button.configure(fg=self.non_select_color)
            self.stored_shape = None
        else:
            if c_shape == "rectangle":
                self.rectangle_button.configure(fg=self.select_color)
                self.circle_button.configure(fg=self.non_select_color)
                self.polygon_button.configure(fg=self.non_select_color)

            if c_shape == "circle":
                self.rectangle_button.configure(fg=self.non_select_color)
                self.circle_button.configure(fg=self.select_color)
                self.polygon_button.configure(fg=self.non_select_color)

            if c_shape == "polygon":
                self.rectangle_button.configure(fg=self.non_select_color)
                self.circle_button.configure(fg=self.non_select_color)
                self.polygon_button.configure(fg=self.select_color)
            self.stored_shape = c_shape

    def reset_selected_buttons(self, category):
        if category == "interact" or "all":
            self.move_shape_button.configure(fg=self.non_select_color)
            self.zoom_in_button.configure(fg=self.non_select_color)
            self.zoom_out_button.configure(fg=self.non_select_color)
            self.pan.configure(fg=self.non_select_color)
            self.zoom_home.configure(fg=self.non_select_color)
            self.stored_interact = None

    def set_interact_state(self, c_interact: str):
        self.shape_info_btn.configure(text="SHOW SHAPE INFO")
        if c_interact == self.stored_interact:
            self.move_shape_button.configure(fg=self.non_select_color)
            self.zoom_in_button.configure(fg=self.non_select_color)
            self.zoom_out_button.configure(fg=self.non_select_color)
            self.pan.configure(fg=self.non_select_color)
            self.zoom_home.configure(fg=self.non_select_color)
            self.stored_interact = None

        else:
            if c_interact == "move_shape":
                if self.image_data.no_shapes > 0:
                    self.move_shape_button.configure(fg=self.select_color)
                    self.zoom_in_button.configure(fg=self.non_select_color)
                    self.zoom_out_button.configure(fg=self.non_select_color)
                    self.zoom_home.configure(fg=self.non_select_color)
                    self.pan.configure(fg=self.non_select_color)
                else:
                    self.reset_selected_buttons("interact")
                    c_interact = None
                    NoDataFoundWarning(msg="You have no shapes that can be moved.", source=self.__class__.__name__)

            if c_interact == "zoom_in":
                self.move_shape_button.configure(fg=self.non_select_color)
                self.zoom_in_button.configure(fg=self.select_color)
                self.zoom_out_button.configure(fg=self.non_select_color)
                self.zoom_home.configure(fg=self.non_select_color)
                self.pan.configure(fg=self.non_select_color)

            if c_interact == "zoom_out":
                self.move_shape_button.configure(fg=self.non_select_color)
                self.zoom_in_button.configure(fg=self.non_select_color)
                self.zoom_out_button.configure(fg=self.select_color)
                self.zoom_home.configure(fg=self.non_select_color)
                self.pan.configure(fg=self.non_select_color)

            if c_interact == "zoom_home":
                self.move_shape_button.configure(fg=self.non_select_color)
                self.zoom_in_button.configure(fg=self.non_select_color)
                self.zoom_out_button.configure(fg=self.non_select_color)
                self.zoom_home.configure(fg=self.select_color)
                self.pan.configure(fg=self.non_select_color)

            if c_interact == "pan":
                self.move_shape_button.configure(fg=self.non_select_color)
                self.zoom_in_button.configure(fg=self.non_select_color)
                self.zoom_out_button.configure(fg=self.non_select_color)
                self.zoom_home.configure(fg=self.non_select_color)
                self.pan.configure(fg=self.select_color)
            self.stored_interact = c_interact

        self.image_data.interact_functions(self.stored_interact, zoom_val=0)
        self.reset_selected_buttons("interact")

    def call_delete_all_rois(self):
        self.shape_info_btn.configure(text="SHOW SHAPE INFO")
        if (
            len(self.image_data.out_rectangles)
            + len(self.image_data.out_circles)
            + len(self.image_data.out_polygon)
            == 0
        ):
            NoDataFoundWarning(
                msg="SimBA finds no ROIs to delete.", source=self.__class__.__name__
            )
        else:
            self.image_data.out_rectangles = []
            self.image_data.out_circles = []
            self.image_data.out_polygon = []
            self.video_ROIs = ["None"]
            self.selected_video.set(self.video_ROIs[0])
            self.update_delete_ROI_menu()
            self.image_data.insert_all_ROIs_into_image()

    def get_duplicate_shape_name(self):
        c_no = 1
        while True:
            self.new_name = self.current_shape_data["Name"] + "_copy_" + str(c_no)
            if str(self.shape_type) + ": " + self.new_name in self.video_ROIs:
                c_no += 1
            else:
                self.new_shape_data["Name"] = (
                    str(self.shape_type) + ": " + self.new_name
                )
                break

    def get_duplicate_coords(self):
        if self.shape_type == "Rectangle":
            self.new_shape_x = int(
                self.current_shape_data["topLeftX"] + self.duplicate_jump_size
            )
            self.new_shape_y = int(
                self.current_shape_data["topLeftY"] + self.duplicate_jump_size
            )
            for shape in self.image_data.out_rectangles:
                if (shape["topLeftX"] == self.new_shape_x) and (
                    shape["topLeftY"] == self.new_shape_y
                ):
                    self.new_shape_x += self.duplicate_jump_size
                    self.new_shape_y += self.duplicate_jump_size
        if self.shape_type == "Circle":
            self.new_shape_x = int(
                self.current_shape_data["centerX"] + self.duplicate_jump_size
            )
            self.new_shape_y = int(
                self.current_shape_data["centerY"] + self.duplicate_jump_size
            )
            for shape in self.image_data.out_circles:
                if (shape["centerY"] == self.new_shape_x) and (
                    shape["centerY"] == self.new_shape_y
                ):
                    self.new_shape_x += self.duplicate_jump_size
                    self.new_shape_y += self.duplicate_jump_size
        if self.shape_type == "Polygon":
            self.new_shape_x = int(
                self.current_shape_data["centerX"] + self.duplicate_jump_size
            )
            self.new_shape_y = int(
                self.current_shape_data["centerY"] + self.duplicate_jump_size
            )
            for shape in self.image_data.out_polygon:
                if (shape["Center_X"] == self.new_shape_x) and (
                    shape["centerY"] == self.new_shape_y
                ):
                    self.new_shape_x += self.duplicate_jump_size
                    self.new_shape_y += self.duplicate_jump_size

    def call_duplicate_ROI(self):
        shape_name = self.selected_video.get().split(": ")
        self.shape_info_btn.configure(text="SHOW SHAPE INFO")
        if shape_name[0] != "None":
            all_roi_list = (
                self.image_data.out_rectangles
                + self.image_data.out_circles
                + self.image_data.out_polygon
            )
            self.shape_type, shape_name = shape_name[0], shape_name[1]
            self.current_shape_data = [
                d for d in all_roi_list if d.get("Name") == shape_name
            ][0]
            self.new_shape_data = copy.deepcopy(self.current_shape_data)
            self.get_duplicate_shape_name()
            self.get_duplicate_coords()
            if self.shape_type == "Rectangle":
                self.new_shape_data["topLeftX"] = self.new_shape_x
                self.new_shape_data["topLeftY"] = self.new_shape_y
                self.new_shape_data["Name"] = self.new_shape_data["Name"].split(
                    "Rectangle: ", 1
                )[-1]
                update_all_tags(self.new_shape_data)
                self.image_data.out_rectangles.append(self.new_shape_data)

            if self.shape_type == "Circle":
                self.new_shape_data["centerX"] = self.new_shape_x
                self.new_shape_data["centerY"] = self.new_shape_y
                self.new_shape_data["Name"] = self.new_shape_data["Name"].split(
                    "Circle: ", 1
                )[-1]
                update_all_tags(self.new_shape_data)
                self.image_data.out_circles.append(self.new_shape_data)

            if self.shape_type == "Polygon":
                move_edge(
                    self.new_shape_data,
                    "Center_tag",
                    (self.new_shape_x, self.new_shape_y),
                )
                self.new_shape_data["Name"] = self.new_shape_data["Name"].split(
                    "Polygon: ", 1
                )[-1]
                self.image_data.out_polygon.append(self.new_shape_data)

            self.video_ROIs.append(self.shape_type + ": " + self.new_shape_data["Name"])
            self.image_data.insert_all_ROIs_into_image()

            self.update_delete_ROI_menu()
        else:
            print("No ROI selected.")

    def create_draw(self):
        self.shape_info_btn.configure(text="SHOW SHAPE INFO")
        if self.stored_shape is None:
            raise NoROIDataError(
                msg="No shape type selected.", source=self.__class__.__name__
            )
        if not self.name_box.get():
            raise NoROIDataError(
                msg="No shape name selected.", source=self.__class__.__name__
            )
        if not self.name_box.get().strip():
            raise NoROIDataError(
                msg="Shape name contains only spaces.", source=self.__class__.__name__
            )

        c_draw_settings = {
            "Video_name": self.file_name,
            "Shape_type": self.stored_shape,
            "Name": self.name_box.get(),
            "Shape_thickness": self.shape_thickness.get(),
            "Shape_ear_tag_size": self.ear_tag_size.get(),
            "Shape_color_name": self.color_var.get(),
            "Shape_color_BGR": self.named_shape_colors[self.color_var.get()],
        }

        self.video_ROIs = self.image_data.initiate_draw(c_draw_settings)
        # cv2.setWindowProperty('Define shape', cv2.WND_PROP_TOPMOST, 1)

        self.update_delete_ROI_menu()

    def update_delete_ROI_menu(self):
        self.selected_video.set(self.video_ROIs[0])
        self.roi_dropdown = OptionMenu(
            self.draw_frame, self.selected_video, *self.video_ROIs
        )
        self.roi_dropdown.grid(row=1, column=4, sticky=W, pady=10)

    def save_data(self):
        if os.path.isfile(self.roi_coordinates_path):
            rectangles_found = pd.read_hdf(self.roi_coordinates_path, key="rectangles")
            circles_found = pd.read_hdf(self.roi_coordinates_path, key="circleDf")
            polygons_found = pd.read_hdf(self.roi_coordinates_path, key="polygons")
            other_vid_rectangles = rectangles_found[
                rectangles_found["Video"] != self.file_name
            ]
            other_vid_circles = circles_found[circles_found["Video"] != self.file_name]
            other_vid_polygons = polygons_found[
                polygons_found["Video"] != self.file_name
            ]

            new_rectangles = pd.DataFrame.from_dict(self.image_data.out_rectangles)
            new_circles = pd.DataFrame.from_dict(self.image_data.out_circles)
            new_polygons = pd.DataFrame.from_dict(self.image_data.out_polygon)

            if len(new_rectangles) > 0:
                out_rectangles = (
                    pd.concat([other_vid_rectangles, new_rectangles], axis=0)
                    .sort_values(by=["Video"])
                    .reset_index(drop=True)
                )
            else:
                out_rectangles = other_vid_rectangles.sort_values(
                    by=["Video"]
                ).reset_index(drop=True)

            if len(new_circles) > 0:
                out_circles = (
                    pd.concat([other_vid_circles, new_circles], axis=0)
                    .sort_values(by=["Video"])
                    .reset_index(drop=True)
                )
            else:
                out_circles = other_vid_circles.sort_values(by=["Video"]).reset_index(
                    drop=True
                )

            if len(new_polygons) > 0:
                out_polygons = (
                    pd.concat([other_vid_polygons, new_polygons], axis=0)
                    .sort_values(by=["Video"])
                    .reset_index(drop=True)
                )
            else:
                out_polygons = other_vid_polygons.sort_values(by=["Video"]).reset_index(
                    drop=True
                )

        else:
            out_rectangles = pd.DataFrame.from_dict(self.image_data.out_rectangles)
            out_circles = pd.DataFrame.from_dict(self.image_data.out_circles)
            out_polygons = pd.DataFrame.from_dict(self.image_data.out_polygon)

            if len(out_rectangles) == 0:
                out_rectangles = create_emty_df("rectangles")
            if len(out_circles) == 0:
                out_circles = create_emty_df("circleDf")
            if len(out_polygons) == 0:
                out_polygons = create_emty_df("polygons")

        store = pd.HDFStore(self.roi_coordinates_path, mode="w")
        try:
            out_rectangles["width_cm"] = out_rectangles["width_cm"].fillna(0)
            out_rectangles["height_cm"] = out_rectangles["height_cm"].fillna(0)
            out_rectangles["area_cm"] = out_rectangles["area_cm"].fillna(0)
        except:
            pass

        store["rectangles"] = out_rectangles
        store["circleDf"] = out_circles
        store["polygons"] = out_polygons
        store.close()
        stdout_success(
            msg=f"ROI definitions saved for video: {self.file_name}",
            source=self.__class__.__name__,
        )

    class ChangeAttrMenu:
        def __init__(self, shape_data, image_data):
            shape_name = shape_data.selected_video.get().split(": ")
            if shape_name[0] != "None":
                self.all_roi_list = (
                    shape_data.image_data.out_rectangles
                    + shape_data.image_data.out_circles
                    + shape_data.image_data.out_polygon
                )
                self.shape_type, self.shape_name = shape_name[0], shape_name[1]
                current_shape_data = [
                    d for d in self.all_roi_list if d.get("Name") == self.shape_name
                ][0]
                self.attr_win = Toplevel()
                self.attr_win.minsize(400, 300)
                self.attr_win.wm_title("Selected Shape Attributes")
                attr_lbl_frame = LabelFrame(
                    self.attr_win,
                    text="Attributes",
                    font=("Arial", 16, "bold"),
                    pady=5,
                    padx=5,
                    fg="black",
                )
                selected_shape_name_lbl = Label(self.attr_win, text="Shape name: ")
                self.selected_shape_name_entry_txt = StringVar()
                self.selected_shape_name_entry_txt.set(current_shape_data["Name"])

                selected_shape_name_entry = Entry(
                    self.attr_win,
                    width=25,
                    textvariable=self.selected_shape_name_entry_txt,
                )
                selected_shape_thickness_lbl = Label(
                    self.attr_win, text="Shape thickness: "
                )
                self.selected_shape_thickness = IntVar()
                self.selected_shape_thickness.set(current_shape_data["Thickness"])
                selected_shape_thickness_dropdown = OptionMenu(
                    self.attr_win,
                    self.selected_shape_thickness,
                    *list(shape_data.shape_thickness_list),
                )

                selected_shape_eartag_size_lbl = Label(
                    self.attr_win, text="Ear tag size: "
                )
                self.selected_shape_eartag_size = IntVar()
                self.selected_shape_eartag_size.set(current_shape_data["Ear_tag_size"])
                selected_shape_eartag_size_dropdown = OptionMenu(
                    self.attr_win,
                    self.selected_shape_eartag_size,
                    *list(shape_data.ear_tag_size_list),
                )

                selected_shape_color_lbl = Label(self.attr_win, text="Shape color: ")
                self.selected_shape_color = StringVar()
                self.selected_shape_color.set(current_shape_data["Color name"])
                selected_shape_color_dropdown = OptionMenu(self.attr_win, self.selected_shape_color, *list(shape_data.named_shape_colors.keys()))

                save_button = SimbaButton(parent=self.attr_win, txt='SAVE', txt_clr=shape_data.non_select_color, img='save', cmd=self.save_attr_changes, cmd_kwargs={'shape_data': lambda: shape_data, 'image_data': lambda: image_data})

                attr_lbl_frame.grid(row=1, sticky=W)
                selected_shape_name_lbl.grid(row=1, column=0, sticky=W, pady=10)
                selected_shape_name_entry.grid(row=1, column=1, sticky=W, pady=10)
                selected_shape_thickness_lbl.grid(row=2, column=0, sticky=W, pady=10)
                selected_shape_thickness_dropdown.grid(row=2, column=1, sticky=W, pady=10)
                selected_shape_eartag_size_lbl.grid(row=3, column=0, sticky=W, pady=10)
                selected_shape_eartag_size_dropdown.grid(row=3, column=1, sticky=W, pady=10)
                selected_shape_color_lbl.grid(row=4, column=0, sticky=W, pady=10)
                selected_shape_color_dropdown.grid(row=4, column=1, sticky=W, pady=10)
                save_button.grid(row=5, column=0, sticky=W, pady=10)

            else:
                raise TypeError("No ROI selected.")

        def save_attr_changes(self, shape_data: str, image_data: str):
            new_shape_name = self.selected_shape_name_entry_txt.get()
            new_shape_thickness = self.selected_shape_thickness.get()
            new_shape_ear_tag_size = self.selected_shape_eartag_size.get()
            new_shape_color = self.selected_shape_color.get()
            for shape in [
                image_data.out_rectangles,
                image_data.out_circles,
                image_data.out_polygon,
            ]:
                for e in shape:
                    shape_type = e["Shape_type"]
                    if e["Name"] == self.shape_name:
                        e["Name"] = new_shape_name
                        e["Thickness"] = new_shape_thickness
                        e["Ear_tag_size"] = new_shape_ear_tag_size
                        e["Color name"] = new_shape_color
                        e["Color BGR"] = shape_data.named_shape_colors[new_shape_color]
                        shape_data.video_ROIs = [
                            w.replace(
                                str(shape_type) + ": " + self.shape_name,
                                str(shape_type) + ": " + new_shape_name,
                            )
                            for w in shape_data.video_ROIs
                        ]
            image_data.insert_all_ROIs_into_image()
            shape_data.update_delete_ROI_menu()
            self.attr_win.destroy()
            self.attr_win.update()

    def window_menus(self):
        menu = Menu(self.roi_root)
        file_menu = Menu(menu)
        menu.add_cascade(label="File (ROI)", menu=file_menu)

        file_menu.add_command(label="Preferences...", compound="left", image=self.menu_icons["settings"]["img"], command=lambda: PreferenceMenu(self.image_data))
        file_menu.add_command(label="Draw ROIs of pre-defined sizes...", compound="left", image=self.menu_icons["size_black"]["img"], command=lambda: DrawFixedROIPopUp(roi_image=self.image_data))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.Exit)
        self.roi_root.config(menu=menu)

    def Exit(self):
        cv2.destroyAllWindows()
        self.image_data.destroy_windows()
        self.master.destroy()
        self.roi_root.destroy()


class PreferenceMenu:
    def __init__(self, image_data):
        pref_win = Toplevel()
        pref_win.minsize(400, 300)
        pref_win.wm_title("Preference Settings")
        pref_lbl_frame = LabelFrame(
            pref_win,
            text="Preferences",
            font=("Arial", 16, "bold"),
            pady=5,
            padx=5,
            fg="black",
        )
        line_type_label = Label(pref_lbl_frame, text="SHAPE LINE TYPE: ", font=Formats.FONT_REGULAR.value)
        text_size_label = Label(pref_lbl_frame, text="TEXT SIZE: ",font=Formats.FONT_REGULAR.value)
        text_thickness_label = Label(pref_lbl_frame, text="TEXT THICKNESS: ", font=Formats.FONT_REGULAR.value)
        line_type_list = [4, 8, 16, -1]
        text_size_list = list(range(1, 20))
        text_thickness_list = list(range(1, 15))
        click_sensitivity_lbl = Label(pref_lbl_frame, text="MOUSE CLICK SENSITIVITY (PIXELS): ", font=Formats.FONT_REGULAR.value)
        click_sensitivity_list = list(range(1, 50, 5))
        self.click_sens = IntVar()
        self.line_type = IntVar()
        self.text_size = IntVar()
        self.text_thickness = IntVar()
        self.line_type.set(line_type_list[-1])
        self.text_size.set(text_size_list[0])
        self.click_sens.set(click_sensitivity_list[0])
        line_type_dropdown = OptionMenu(pref_lbl_frame, self.line_type, *line_type_list)
        text_thickness_dropdown = OptionMenu(pref_lbl_frame, self.text_thickness, *text_thickness_list)
        text_size_dropdown = OptionMenu(pref_lbl_frame, self.text_size, *text_size_list)
        click_sens_dropdown = OptionMenu(pref_lbl_frame, self.click_sens, *click_sensitivity_list)
        duplicate_jump_size_lbl = Label(pref_lbl_frame, text="DUPLICATE SHAPE JUMP: ", font=Formats.FONT_REGULAR.value)
        duplicate_jump_size_list = list(range(1, 100, 5))
        self.duplicate_jump_size = IntVar()
        self.duplicate_jump_size.set(20)
        duplicate_jump_size_dropdown = OptionMenu(pref_lbl_frame, self.duplicate_jump_size, *duplicate_jump_size_list)

        pref_save_btn = SimbaButton(parent=pref_lbl_frame, txt="SAVE", img='save', font=Formats.FONT_REGULAR.value, cmd=self.save_prefs, cmd_kwargs={'image_data': lambda: image_data})
        pref_lbl_frame.grid(row=1, sticky=W)
        line_type_label.grid(row=1, column=0, sticky=W, pady=10)
        line_type_dropdown.grid(row=1, column=1, sticky=W, pady=10)
        click_sensitivity_lbl.grid(row=2, column=0, sticky=W, pady=10)
        click_sens_dropdown.grid(row=2, column=1, sticky=W, pady=10)
        duplicate_jump_size_lbl.grid(row=3, column=0, sticky=W, pady=10)
        duplicate_jump_size_dropdown.grid(row=3, column=1, sticky=W, pady=10)
        text_size_label.grid(row=4, column=0, sticky=W, pady=10)
        text_size_dropdown.grid(row=4, column=1, sticky=W, pady=10)
        text_thickness_label.grid(row=5, column=0, sticky=W, pady=10)
        text_thickness_dropdown.grid(row=5, column=1, sticky=W, pady=10)
        pref_save_btn.grid(row=5, column=2, sticky=W, pady=10)

    def save_prefs(self, image_data):
        image_data.click_sens = self.click_sens.get()
        image_data.text_size = self.text_size.get()
        image_data.text_thickness = self.text_thickness.get()
        image_data.line_type = self.line_type.get()
        image_data.duplicate_jump_size = self.duplicate_jump_size.get()
        stdout_success(msg="Saved ROI preference settings.", source=self.__class__.__name__)


# test = ROI_definitions(config_path='/Users/simon/Desktop/envs/simba/troubleshooting/two_black_animals_14bp/project_folder/project_config.ini',
#                       video_path='/Users/simon/Desktop/envs/simba/troubleshooting/two_black_animals_14bp/project_folder/videos/Together_1.avi')


# test = ROI_definitions(config_path='/Users/simon/Desktop/envs/troubleshooting/two_black_animals_14bp/project_folder/project_config.ini', video_path='/Users/simon/Desktop/envs/troubleshooting/two_black_animals_14bp/project_folder/videos/Together_1.avi')
