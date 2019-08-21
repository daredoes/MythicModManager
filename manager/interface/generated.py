# -*- coding: UTF-8 -*-
#
# generated by wxGlade 0.9.3 on Sun Apr 28 17:10:15 2019
#

import wx
import wx.adv

from collections import defaultdict
from enum import Enum, auto

from aenum import NamedConstant

class Tabs(Enum):
    """
        To add a new Tab, just add a new enum. The value will be the name of the tab.
    """
    def _generate_next_value_(name, start, count, last_values):
        return name.title().replace("_", " ") 

    MANAGER = auto()
    MOD_LIST = auto()
    JOB_QUEUE = auto()
    SETTINGS = auto()
    ABOUT = auto()

class Buttons(Enum):
    # These are the strings used inside of buttons used Globally, put in one place for easy updating
    UNINSTALL = "uninstall"
    UPDATE = "update installed mods"
    EXPORT = "export"
    IMPORT = "import"
    INSTALL = "install"
    DELETE = "delete"
    REFRESH = "refresh"
    INSTALL_SELECTED = "install selected"
    DETAILS = "more metails"
    LAUNCH = "launch game"

def make_list_ctrl_enum_value(title, width=None, format_enum=wx.LIST_FORMAT_LEFT):
    return {
        'heading': title.title(),
        'width': width,
        'format': format_enum,
    }

class ColumnEnums(Enum):
    # These column enums exist to be put inside of enums that represent each ListCtrl and the column names that correlate to them.
    def _generate_next_value_(name, start, count, last_values):
        return name.title().replace("_", " ") 

    NAME = auto()
    OWNER = auto()
    DESCRIPTION = auto()
    LATEST_VERSION = auto()
    DOWNLOADS = auto()
    NAMESPACE = "Author"
    VERSION = auto()
    PARAMETERS_STR = "Parameters"

# The NamedConstant class must be used to allow unique lists with the same column names
class ListCtrlEnums(NamedConstant):
    MODS = [
        ColumnEnums.NAME,
        ColumnEnums.OWNER,
        ColumnEnums.DESCRIPTION,
        ColumnEnums.LATEST_VERSION,
        ColumnEnums.DOWNLOADS,
    ]
    DOWNLOADED = [
        ColumnEnums.NAME,
        ColumnEnums.NAMESPACE,
        ColumnEnums.VERSION,
    ]
    INSTALLED = [
        ColumnEnums.NAME,
        ColumnEnums.NAMESPACE,
        ColumnEnums.VERSION,
    ]
    JOBS = [
        ColumnEnums.NAME,
        ColumnEnums.PARAMETERS_STR,
    ]


# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
# end wxGlade


class MainFrame(wx.Frame):
    tabs = {}
    tabs_data = {}

    def get_tab_and_tab_data(self, enum):
        return self.tabs[enum.value], self.tabs_data[enum.value]

    def make_button(self, tab, label):
        return wx.Button(tab, wx.ID_ANY, label)

    def setup_tabs(self):
        for tab in list(Tabs):
            self.tabs[tab.value] = wx.Panel(self.main_content_notebook, wx.ID_ANY)
            self.tabs_data[tab.value] = {"name": tab.name, "children": {}}

    def make_buttons_for_tab_and_tab_data_from_enum_list(self, enum_list, tab, tab_data):
        for button in enum_list:
            tab_data["children"][button.name] = self.make_button(
                tab, button.value.title()
            )

    def setup_manager_tab(self):
        tab, tab_data = self.get_tab_and_tab_data(Tabs.MANAGER)
        self.make_buttons_for_tab_and_tab_data_from_enum_list(
            [
                Buttons.UNINSTALL,
                Buttons.UPDATE,
                Buttons.EXPORT,
                Buttons.IMPORT,
                Buttons.INSTALL,
                Buttons.DELETE,
            ],
            tab,
            tab_data,
        )
        tab_data['children'][ListCtrlEnums.INSTALLED._name_] = wx.ListCtrl(
            tab, wx.ID_ANY, style=wx.LC_HRULES | wx.LC_REPORT | wx.LC_VRULES
        )
        self.downloaded_mods_group_version_checkbox = wx.CheckBox(
            tab, wx.ID_ANY, "Group by version"
        )
        tab_data['children'][ListCtrlEnums.DOWNLOADED._name_] = wx.ListCtrl(
            tab, wx.ID_ANY, style=wx.LC_HRULES | wx.LC_REPORT | wx.LC_VRULES
        )

    def setup_mod_list_tab(self):
        tab, tab_data = self.get_tab_and_tab_data(Tabs.MOD_LIST)
        self.make_buttons_for_tab_and_tab_data_from_enum_list(
            [
                Buttons.REFRESH,
                Buttons.INSTALL_SELECTED,
            ],
            tab,
            tab_data,
        )
        self.mod_list_search = wx.SearchCtrl(tab, wx.ID_ANY, "")
        tab_data['children'][ListCtrlEnums.MODS._name_] = wx.ListCtrl(
            tab, wx.ID_ANY, style=wx.LC_HRULES | wx.LC_REPORT | wx.LC_VRULES
        )

    def setup_job_queue_tab(self):
        tab, tab_data = self.get_tab_and_tab_data(Tabs.JOB_QUEUE)
        tab_data['children'][ListCtrlEnums.JOBS._name_] = wx.ListCtrl(
            tab,
            wx.ID_ANY,
            style=wx.LC_HRULES | wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_VRULES,
        )

    def setup_settings_tab(self):
        pass

    def setup_about_tab(self):
        tab, tab_data = self.get_tab_and_tab_data(Tabs.ABOUT)
        self.about_github_link = wx.adv.HyperlinkCtrl(
            tab,
            wx.ID_ANY,
            "MythicModManager on GitHub",
            "https://github.com/MythicManiac/MythicModManager/",
        )

    def setup_selection_panel(self):
        self.selection_icon_bitmap = wx.StaticBitmap(
            self,
            wx.ID_ANY,
            wx.Bitmap("resources\\icon-unknown.png", wx.BITMAP_TYPE_ANY),
        )
        self.selection_info_panel = wx.Panel(self, wx.ID_ANY)
        self.selection_title = wx.StaticText(
            self.selection_info_panel,
            wx.ID_ANY,
            "Placeholder Mod Name That Is Very Long And Could Break The UI",
        )
        self.selection_description = wx.StaticText(
            self.selection_info_panel,
            wx.ID_ANY,
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in",
        )
        self.selection_version = wx.StaticText(
            self.selection_info_panel, wx.ID_ANY, "Latest Version: v1.0.3"
        )
        self.selection_download_count = wx.StaticText(
            self.selection_info_panel, wx.ID_ANY, "Total downloads: 68309"
        )

    def __init__(self, *args, **kwds):
        # begin wxGlade: MainFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((937, 647))
        self.main_content_notebook = wx.Notebook(self, wx.ID_ANY)
        self.setup_tabs()
        self.setup_manager_tab()
        self.setup_mod_list_tab()
        self.setup_job_queue_tab()
        self.setup_settings_tab()
        self.setup_about_tab()
        self.setup_selection_panel()
        self.selection_thunderstore_button = self.make_button(self, "More Details")
        self.launch_game_button = self.make_button(self, "Launch Game")
        self.progress_bar_big = wx.Gauge(self, wx.ID_ANY, 1000)
        self.progress_bar_small = wx.Gauge(self, wx.ID_ANY, 1000)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MainFrame.__set_properties
        self.SetTitle("MythicModManager")
        self.downloaded_mods_group_version_checkbox.SetValue(1)
        self.mod_list_search.ShowCancelButton(True)
        self.selection_title.SetFont(
            wx.Font(
                14,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Segoe UI",
            )
        )
        self.selection_title.Wrap(160)
        self.selection_description.Wrap(240)
        self.selection_version.Wrap(240)
        self.selection_download_count.Wrap(240)
        # end wxGlade

    def get_title_sizer(self, tab, text):
        title = wx.StaticText(tab, wx.ID_ANY, text)
        title.SetFont(
            wx.Font(
                14,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                0,
                "Segoe UI",
            )
        )
        return title

    def __do_layout(self):
        # begin wxGlade: MainFrame.__do_layout
        root_sizer = wx.BoxSizer(wx.VERTICAL)
        progress_bars_sizer = wx.BoxSizer(wx.VERTICAL)
        main_content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        selection_info_sizer = wx.BoxSizer(wx.VERTICAL)
        selection_info_content_sizer = wx.BoxSizer(wx.VERTICAL)
        selection_info_buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        selection_info_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        about_sizer = wx.BoxSizer(wx.HORIZONTAL)
        job_queue_sizer = wx.BoxSizer(wx.VERTICAL)
        mod_list_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        manager_sizer = wx.BoxSizer(wx.VERTICAL)
        downloaded_mods_sizer = wx.BoxSizer(wx.VERTICAL)
        downloaded_mods_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        installed_mods_sizer = wx.BoxSizer(wx.VERTICAL)
        installed_mods_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        installed_mods_title = self.get_title_sizer(
            self.tabs[Tabs.MANAGER.value], "Installed Mods"
        )
        installed_mods_sizer.Add(installed_mods_title, 0, 0, 0)
        for button in [
            Buttons.UNINSTALL,
            Buttons.UPDATE,
            Buttons.EXPORT,
            Buttons.IMPORT,
        ]:
            installed_mods_buttons_sizer.Add(
                self.tabs_data[Tabs.MANAGER.value]["children"][button.name],
                1,
                wx.EXPAND,
                0,
            )
        installed_mods_sizer.Add(installed_mods_buttons_sizer, 0, wx.EXPAND, 0)
        installed_mods_sizer.Add(self.tabs_data[Tabs.MANAGER.value]['children'][ListCtrlEnums.INSTALLED._name_], 1, wx.EXPAND, 0)
        manager_sizer.Add(installed_mods_sizer, 1, wx.EXPAND, 0)
        downloaded_mods_title = self.get_title_sizer(
            self.tabs[Tabs.MANAGER.value], "Downloaded Mods"
        )
        downloaded_mods_sizer.Add(downloaded_mods_title, 0, 0, 0)
        for button in [Buttons.INSTALL, Buttons.DELETE]:
            downloaded_mods_buttons_sizer.Add(
                self.tabs_data[Tabs.MANAGER.value]["children"][button.name], 1, 0, 0
            )
        downloaded_mods_buttons_sizer.Add(
            self.downloaded_mods_group_version_checkbox, 0, wx.ALIGN_CENTER | wx.ALL, 4
        )
        downloaded_mods_sizer.Add(downloaded_mods_buttons_sizer, 0, wx.EXPAND, 0)
        downloaded_mods_sizer.Add(self.tabs_data[Tabs.MANAGER.value]['children'][ListCtrlEnums.DOWNLOADED._name_], 1, wx.EXPAND, 0)
        manager_sizer.Add(downloaded_mods_sizer, 1, wx.EXPAND, 0)
        self.tabs[Tabs.MANAGER.value].SetSizer(manager_sizer)
        for button in [
            Buttons.REFRESH,
            Buttons.INSTALL_SELECTED,
        ]:
            sizer_1.Add(
                self.tabs_data[Tabs.MOD_LIST.value]["children"][button.name],
                1,
                wx.EXPAND,
                0,
            )
        mod_list_sizer.Add(sizer_1, 0, wx.EXPAND, 0)
        mod_list_sizer.Add(self.mod_list_search, 0, wx.EXPAND, 0)
        mod_list_sizer.Add(self.tabs_data[Tabs.MOD_LIST.value]['children'][ListCtrlEnums.MODS._name_], 1, wx.EXPAND, 0)
        self.tabs[Tabs.MOD_LIST.value].SetSizer(mod_list_sizer)
        job_queue_sizer.Add(self.tabs_data[Tabs.JOB_QUEUE.value]['children'][ListCtrlEnums.JOBS._name_], 1, wx.EXPAND, 0)
        self.tabs[Tabs.JOB_QUEUE.value].SetSizer(job_queue_sizer)
        about_sizer.Add(self.about_github_link, 0, wx.ALIGN_CENTER, 0)
        self.tabs[Tabs.ABOUT.value].SetSizer(about_sizer)
        for tab in list(Tabs):
            self.main_content_notebook.AddPage(self.tabs[tab.value], tab.value)
        main_content_sizer.Add(self.main_content_notebook, 1, wx.EXPAND, 0)
        selection_info_sizer.Add(self.selection_icon_bitmap, 0, wx.EXPAND, 0)
        selection_info_panel_sizer.Add(self.selection_title, 50, 0, 0)
        selection_info_panel_sizer.Add(self.selection_description, 60, 0, 0)
        selection_info_panel_separator = wx.StaticLine(
            self.selection_info_panel, wx.ID_ANY
        )
        selection_info_panel_sizer.Add(selection_info_panel_separator, 1, wx.EXPAND, 0)
        selection_info_panel_sizer.Add(self.selection_version, 10, 0, 0)
        selection_info_panel_sizer.Add(self.selection_download_count, 10, wx.ALL, 0)
        self.selection_info_panel.SetSizer(selection_info_panel_sizer)
        selection_info_content_sizer.Add(self.selection_info_panel, 1, wx.EXPAND, 0)
        selection_info_buttons_sizer.Add(
            self.selection_thunderstore_button, 1, wx.EXPAND, 0
        )
        selection_info_buttons_sizer.Add(self.launch_game_button, 0, wx.EXPAND, 0)
        selection_info_content_sizer.Add(selection_info_buttons_sizer, 0, wx.EXPAND, 0)
        selection_info_sizer.Add(selection_info_content_sizer, 1, wx.EXPAND, 0)
        main_content_sizer.Add(selection_info_sizer, 0, wx.EXPAND, 0)
        root_sizer.Add(main_content_sizer, 95, wx.EXPAND, 0)
        progress_bars_sizer.Add(self.progress_bar_big, 1, wx.EXPAND, 0)
        progress_bars_sizer.Add(self.progress_bar_small, 0, wx.EXPAND, 0)
        root_sizer.Add(progress_bars_sizer, 8, wx.EXPAND, 0)
        self.SetSizer(root_sizer)
        self.Layout()
        # end wxGlade


# end of class MainFrame
