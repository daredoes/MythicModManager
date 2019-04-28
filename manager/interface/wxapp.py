import wx

from wxasync import WxAsyncApp
from asyncio.events import get_event_loop

from ..system.manager import ModManager, ModManagerConfiguration
from ..utils.log import log_exception

from .generated import MainFrame


class ObjectList:
    def __init__(self, element, columns, column_labels=None):
        self.element = element
        self.columns = columns
        if column_labels:
            self.column_labels = column_labels
        else:
            self.column_labels = [x.capitalize().replace("_", " ") for x in columns]
        self.objects = []

        self.element.ClearAll()
        for index, label in enumerate(self.column_labels):
            self.element.InsertColumn(index, label)
        self.resize_columns()
        self.element.Bind(wx.EVT_SIZE, lambda event: self.resize_columns())

    def update(self, new_objects):
        self.element.DeleteAllItems()
        for row, entry in enumerate(new_objects):
            label = str(getattr(entry, self.columns[0], None) or "")
            self.element.InsertItem(row, label)
            for i in range(1, len(self.columns)):
                item = wx.ListItem()
                item.SetId(row)
                item.SetColumn(i)
                label = str(getattr(entry, self.columns[i], None) or "")
                item.SetText(label)
                self.element.SetItem(item)
        self.objects = new_objects

    def get_selected_objects(self):
        selection = self.element.GetFirstSelected()
        if selection == -1:
            return None

        selections = [self.objects[selection]]
        while selection != -1:
            selection = self.element.GetNextSelected(selection)
            if selection != -1:
                selections.append(self.objects[selection])

        return selections

    def resize_columns(self):
        width, height = self.element.GetClientSize()
        column_width = int(float(width) / len(self.column_labels))
        for index in range(len(self.column_labels)):
            self.element.SetColumnWidth(index, column_width)


class TestMod:
    def __init__(self, name, author, description, version, downloads):
        self.name = name
        self.author = author
        self.description = description
        self.version = version
        self.downloads = downloads


class Application:
    def __init__(self):
        self.app = WxAsyncApp()
        self.main_frame = MainFrame(None)
        self.remote_mod_list = ObjectList(
            element=self.main_frame.mod_list_list,
            columns=("name", "owner", "description", "latest_version", "downloads"),
        )
        self.installed_mod_list = ObjectList(
            element=self.main_frame.installed_mods_list,
            columns=("name", "namespace", "version"),
            column_labels=("Name", "Author", "Version"),
        )
        self.downloaded_mod_list = ObjectList(
            element=self.main_frame.downloaded_mods_list,
            columns=("name", "namespace", "version"),
            column_labels=("Name", "Author", "Version"),
        )
        self.job_queue_list = ObjectList(
            element=self.main_frame.job_queue_list, columns=("task", "parameters")
        )
        self.configuration = ModManagerConfiguration(
            thunderstore_url="https://thunderstore.io/",
            mod_cache_path="mod-cache/",
            mod_install_path="risk-of-rain-2/mods/",
            risk_of_rain_path="risk-of-rain-2/",
            log_path="logs/",
        )
        self.manager = ModManager(self.configuration)
        self.bind_events()

    def handle_remote_mod_list_select(self, event=None):
        selections = self.remote_mod_list.get_selected_objects()
        if not selections:
            return
        selection = self.manager.resolve_package_metadata(selections[0])
        self.main_frame.selection_title.SetLabel(selection.name)
        self.main_frame.selection_title.Wrap(160)

        self.main_frame.selection_description.SetLabel(selection.description)
        self.main_frame.selection_description.Wrap(240)

        version_text = f"Selected Version: v{selection.version}"
        self.main_frame.selection_version.SetLabel(version_text)
        self.main_frame.selection_version.Wrap(240)

        downloads_text = f"Downloads: {selection.downloads}"
        self.main_frame.selection_download_count.SetLabel(downloads_text)
        self.main_frame.selection_download_count.Wrap(240)

    def bind_events(self):
        self.main_frame.mod_list_refresh_button.Bind(
            wx.EVT_BUTTON, self.refresh_remote_mod_list
        )
        self.main_frame.downloaded_mods_group_version_checkbox.Bind(
            wx.EVT_CHECKBOX, self.refresh_downloaded_mod_list
        )
        self.main_frame.mod_list_list.Bind(
            wx.EVT_LIST_ITEM_SELECTED, self.handle_remote_mod_list_select
        )

    def refresh_remote_mod_list(self, event=None):
        try:
            self.manager.api.update_packages()
            packages = sorted(
                self.manager.api.packages.values(), key=lambda entry: entry.name
            )
            self.remote_mod_list.update(packages)
        except Exception as e:
            log_exception(self.configuration.log_path, e)
            wx.MessageBox(
                "Failed to pull remote package data. Server could be offline.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )

    def refresh_installed_mod_list(self, event=None):
        packages = sorted(self.manager.installed_packages, key=lambda entry: entry.name)
        self.installed_mod_list.update(packages)

    def refresh_downloaded_mod_list(self, event=None):
        packages = self.manager.cached_packages
        if self.main_frame.downloaded_mods_group_version_checkbox.GetValue():
            packages = set([package.without_version for package in packages])
        packages = sorted(packages, key=lambda entry: entry.name)
        self.downloaded_mod_list.update(packages)

    def launch(self):
        self.main_frame.Show()
        self.refresh_installed_mod_list()
        self.refresh_downloaded_mod_list()
        loop = get_event_loop()
        loop.run_until_complete(self.app.MainLoop())
