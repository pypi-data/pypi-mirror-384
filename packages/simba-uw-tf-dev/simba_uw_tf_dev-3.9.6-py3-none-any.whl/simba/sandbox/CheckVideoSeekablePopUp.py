import os
from typing import Union, Optional
from simba.mixins.pop_up_mixin import PopUpMixin
from simba.ui.tkinter_functions import Entry_Box, CreateLabelFrameWithIcon, SimbaCheckbox, DropDownMenu, FileSelect, FolderSelect, SimbaButton
from simba.utils.enums import Keys, Links, Formats, Options
from tkinter import *
from simba.utils.checks import check_file_exist_and_readable, check_if_dir_exists, is_valid_video_file
from simba.utils.read_write import find_files_of_filetypes_in_directory
from simba.video_processors.video_processing import is_video_seekable


class CheckVideoSeekablePopUp(PopUpMixin):
    def __init__(self,
                 config_path: Optional[Union[str, os.PathLike]] = None):

        if config_path is not None:
            check_file_exist_and_readable(file_path=config_path)
        PopUpMixin.__init__(self, title="CHECK IF VIDEOS ARE SEEKABLE")
        settings_frm = LabelFrame(self.main_frm, text="SETTINGS", font=Formats.FONT_HEADER.value)
        batch_size_options = list(range(100, 5100, 100))
        batch_size_options.insert(0, 'NONE')
        self.use_gpu_cb, self.use_gpu_var = SimbaCheckbox(parent=settings_frm, txt="Use GPU (reduced runtime)", txt_img='gpu_2')
        self.batch_size_dropdown = DropDownMenu(settings_frm, "FRAME BATCH SIZE:", batch_size_options, "15")
        self.batch_size_dropdown.setChoices('NONE')

        single_video_frm = LabelFrame(self.main_frm, text="SINGLE VIDEO", font=Formats.FONT_HEADER.value)
        self.single_video_path = FileSelect(single_video_frm, "VIDEO PATH:", title="Select a video file", lblwidth=25, file_types=[("VIDEO", Options.ALL_VIDEO_FORMAT_STR_OPTIONS.value)])
        single_run_btn = SimbaButton(parent=single_video_frm, txt="RUN", img='rocket', font=Formats.FONT_REGULAR.value, cmd=self.run, cmd_kwargs={'directory': lambda: False})

        multiple_video_frm = LabelFrame(self.main_frm, text="VIDEO DIRECTORY", font=Formats.FONT_HEADER.value)
        self.directory_path = FolderSelect(multiple_video_frm, "VIDEO DIRECTORY PATH:", title="Select folder with videos: ", lblwidth="25")
        dir_run_btn = SimbaButton(parent=multiple_video_frm, txt="RUN", img='rocket', font=Formats.FONT_REGULAR.value, cmd=self.run, cmd_kwargs={'directory': lambda: True})


        settings_frm.grid(row=0, column=0, sticky=NW)
        self.use_gpu_cb.grid(row=0, column=0, sticky=NW)
        self.batch_size_dropdown.grid(row=1, column=0, sticky=NW)


        single_video_frm.grid(row=1, column=0, sticky=NW)
        self.single_video_path.grid(row=0, column=0, sticky=NW)
        single_run_btn.grid(row=1, column=0, sticky=NW)

        multiple_video_frm.grid(row=2, column=0, sticky=NW)
        self.directory_path.grid(row=0, column=0, sticky=NW)
        dir_run_btn.grid(row=1, column=0, sticky=NW)
        self.main_frm.mainloop()

    def run(self, directory: bool):
        if directory:
            data_path = self.directory_path.folder_path
            check_if_dir_exists(in_dir=dir, source=self.__class__.__name__)
            file_paths = find_files_of_filetypes_in_directory(directory=data_path, extensions=Options.ALL_VIDEO_FORMAT_OPTIONS.value, raise_error=True)
            for file_path in file_paths:
                _ = is_valid_video_file(file_path=file_path, raise_error=True)
        else:
            data_path = self.single_video_path.file_path
            is_valid_video_file(file_path=data_path, raise_error=True)
        gpu = self.use_gpu_var.get()
        batch_size = self.batch_size_dropdown.getChoices()
        if batch_size == 'NONE':
            batch_size = None
        else:
            batch_size = int(batch_size)
        _ = is_video_seekable(data_path=data_path, gpu=gpu, batch_size=batch_size, verbose=False)





        #settings_frm = CreateLabelFrameWithIcon(parent=self.main_frm, header="SETTINGS", icon_name=Keys.DOCUMENTATION.value, icon_link=Links.VIDEO_TOOLS.value)

        #self.time_delta_eb = Entry_Box(settings_frm, "TIME-DELTA", "10", validation="numeric")


#CheckVideoSeekablePopUp()