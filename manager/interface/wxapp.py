import wx
import json
import webbrowser

from collections import defaultdict

from wxasync import WxAsyncApp, AsyncBind, StartCoroutine
from asyncio.events import get_event_loop
from pathlib import Path

from ..system.manager import ModManager, ModManagerConfiguration, PackageMetadata
from ..system.job_manager import JobManager
from ..system.jobs import (
    DownloadAndInstallPackage,
    InstallPackage,
    UninstallPackage,
    DeletePackage,
)
from ..utils.log import log_exception
from ..utils.install_finder import get_install_path
from ..api.types import PackageReference

from .generated import MainFrame, Tabs, Buttons, ListCtrlEnums, ModLists


def get_mod_and_tab_and_list_ctrl_from_mod(Mod):
    tab, list_ctrl, _ = Mod.value
    return Mod, tab, list_ctrl


class ObjectList:
    def __init__(self, element, columns, column_labels=None):
        self.current_sort = 1
        self.element = element
        self.columns = columns
        self.column_labels = (
            column_labels
            if column_labels
            else [x.capitalize().replace("_", " ") for x in columns]
        )
        self.objects = []

        self.element.ClearAll()
        for index, label in enumerate(self.column_labels):
            self.element.InsertColumn(index, label)

        self.resize_columns()
        self.bind_events()

    def bind_events(self):
        self.element.Bind(wx.EVT_SIZE, self.resize_columns)
        self.element.Bind(wx.EVT_LIST_COL_CLICK, self.sort_list)

    def sort_list(self, event):
        col_index = event.GetColumn() + 1
        self.current_sort = -col_index if self.current_sort == col_index else col_index
        self.update(self.objects)

    def update(self, new_objects):
        def get_sort_key(entry):
            key = getattr(entry, self.columns[abs(self.current_sort) - 1], None)
            return key or ""

        new_objects = sorted(
            new_objects, key=get_sort_key, reverse=self.current_sort < 0
        )

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
        while selection != -1:
            yield self.objects[selection]
            selection = self.element.GetNextSelected(selection)

    def get_first_selection(self):
        selection = self.element.GetFirstSelected()
        if selection != -1:
            return self.objects[selection]

    def resize_columns(self, *args, **kwargs):
        width, height = self.element.GetClientSize()
        column_width = int(float(width) / len(self.column_labels))
        for index, _ in enumerate(self.column_labels):
            self.element.SetColumnWidth(index, column_width)


class CopyableDialog(wx.Dialog):
    def __init__(self, parent, title, text):
        wx.Dialog.__init__(self, parent, title=title)
        text = wx.TextCtrl(
            parent=self,
            value=text,
            style=(wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_BESTWRAP),
        )
        text.SetSelection(-1, -1)
        self.ShowModal()
        self.Destroy()


class Application:
    lists = {}

    def make_object_list(self, TabEnum, ListCtrlEnum, *args, **kwargs):
        return ObjectList(
            element=self.main_frame.tabs_data[TabEnum.value]["children"][
                ListCtrlEnum._name_
            ],
            columns=[v.name.lower() for v in ListCtrlEnum._value_],
            column_labels=[v.value for v in ListCtrlEnum._value_],
        )

    def get_risk_of_rain_path(self):
        risk_of_rain_path = get_install_path()

        if not risk_of_rain_path:
            wx.MessageBox(
                "Failed to detect Risk of Rain 2 path. Add it to config.toml",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            risk_of_rain_path = Path("risk-of-rain-2")
        return risk_of_rain_path

    def __init__(self):
        self.app = WxAsyncApp()
        self.main_frame = MainFrame(None)
        for list_data in list(ModLists):
            self.lists[list_data.name] = self.make_object_list(*list_data.value)

        risk_of_rain_path = self.get_risk_of_rain_path()

        self.configuration = ModManagerConfiguration(
            thunderstore_url="https://thunderstore.io/",
            mod_cache_path="mod-cache/",
            mod_install_path=risk_of_rain_path / "BepInEx" / "plugins",
            risk_of_rain_path=risk_of_rain_path,
        )
        self.job_manager = JobManager(
            big_progress_bar=self.main_frame.progress_bar_big,
            small_progress_bar=self.main_frame.progress_bar_small,
        )
        self.job_manager.bind_on_job_added(self.refresh_job_list)
        self.job_manager.bind_on_job_finished(self.refresh_job_list)

        self.manager = ModManager(self.configuration, self.job_manager)
        for attr, func in [
            ("install", self.refresh_installed_mod_list),
            ("uninstall", self.refresh_installed_mod_list),
            ("download", self.refresh_downloaded_mod_list),
            ("delete", self.refresh_downloaded_mod_list),
        ]:
            binding_func = getattr(self.manager, "bind_on_{}".format(attr))
            if binding_func:
                binding_func(func)

        self.current_selection = PackageMetadata.empty()
        self.main_frame.selection_description.SetLabel("")
        self.main_frame.selection_title.SetLabel("")
        self.main_frame.selection_version.SetLabel("")
        self.main_frame.selection_download_count.SetLabel("")
        self.main_frame.selection_thunderstore_button.Disable()
        self.bind_events()

    def refresh_job_list(self):
        self.lists[ModLists.JOB_QUEUE.name].update(self.job_manager.job_queue)

    def make_list_selection_update_function(self, ModList):
        async def handle_list_select(event=None):
            await self.handle_selection_update(
                self.lists[ModList.name].get_first_selection()
            )

        return handle_list_select

    async def handle_selection_update(self, selection):
        if not selection:
            return
        selection_meta = self.manager.resolve_package_metadata(selection)
        self.current_selection = selection_meta
        self.main_frame.selection_title.SetLabel(selection_meta.name)
        self.main_frame.selection_title.Wrap(160)

        self.main_frame.selection_description.SetLabel(selection_meta.description)
        self.main_frame.selection_description.Wrap(240)

        version_text = f"Selected Version: v{selection_meta.version}"
        self.main_frame.selection_version.SetLabel(version_text)
        self.main_frame.selection_version.Wrap(240)

        downloads_text = f"Downloads: {selection_meta.downloads}"
        self.main_frame.selection_download_count.SetLabel(downloads_text)
        self.main_frame.selection_download_count.Wrap(240)

        if selection_meta.thunderstore_url:
            self.main_frame.selection_thunderstore_button.Enable()
        else:
            self.main_frame.selection_thunderstore_button.Disable()

        bitmap = None

        icon_data = await selection_meta.get_icon_bytes()
        if icon_data:
            bitmap = wx.Image(icon_data).ConvertToBitmap()

        if bitmap is None:
            bitmap = wx.Bitmap("resources\\icon-unknown.png")

        if self.current_selection == selection_meta:
            self.main_frame.selection_icon_bitmap.SetBitmap(bitmap)

    def make_package_management_function(self, Mod, Package):
        async def handle_package_job(event=None):
            for selection in self.lists[Mod.name].get_selected_objects():
                meta = self.manager.resolve_package_metadata(selection)
                reference = meta.package_reference
                if not reference.version:
                    newest = self.manager.get_newest_cached(reference)
                    if newest:
                        reference = newest
                await self.add_job(Package, reference)

        return handle_package_job

    async def handle_downloaded_mod_list_delete(
        self, event=None, button=None, *args, **kwargs
    ):
        for selection in self.lists[
            ModLists.DOWNLOADED_MODS.name
        ].get_selected_objects():
            meta = self.manager.resolve_package_metadata(selection)
            reference = meta.package_reference
            if self.main_frame.tabs_data[Tabs.MANAGER.value]["children"][
                "{}{}".format(ListCtrlEnums.DOWNLOADED._name_, "checkbox")
            ].GetValue():
                reference = reference.without_version
            await self.add_job(DeletePackage, reference)

    async def handle_installed_mod_list_update_button(
        self, event=None, button=None, *args, **kwargs
    ):
        await self.handle_mod_list_refresh()
        installed_packages = self.manager.installed_packages
        for package in self.manager.installed_packages:
            package = package.without_version
            if package not in self.manager.api.packages:
                continue
            package = self.manager.api.packages[package]
            latest = package.versions.latest.package_reference
            if latest not in installed_packages:
                await self.add_job(DownloadAndInstallPackage, latest)

    def handle_selection_thunderstore_button(self, event=None):
        meta = self.manager.resolve_package_metadata(self.current_selection)
        if meta.thunderstore_url:
            webbrowser.open(meta.thunderstore_url)

    def bind_singular_selection_event(self, Mod):
        mod, tab, list_ctrl = get_mod_and_tab_and_list_ctrl_from_mod(Mod)
        AsyncBind(
            wx.EVT_LIST_ITEM_SELECTED,
            self.make_list_selection_update_function(mod),
            self.main_frame.tabs_data[tab.value]["children"][list_ctrl._name_],
        )

    def bind_singular_selection_events(self):
        for Mod in [
            ModLists.INSTALLED_MODS,
            ModLists.DOWNLOADED_MODS,
            ModLists.REMOTE_MODS,
        ]:
            self.bind_singular_selection_event(Mod)

    def bind_buttons_in_tabs_events(self):
        remote_mod, remote_tab, remote_list = get_mod_and_tab_and_list_ctrl_from_mod(
            ModLists.REMOTE_MODS
        )
        installed_mod, installed_tab, installed_list = get_mod_and_tab_and_list_ctrl_from_mod(
            ModLists.INSTALLED_MODS
        )
        downloaded_mod, downloaded_tab, downloaded_list = get_mod_and_tab_and_list_ctrl_from_mod(
            ModLists.DOWNLOADED_MODS
        )
        tabs = defaultdict(list)
        tabs[remote_tab].extend([
            [Buttons.REFRESH, self.handle_mod_list_refresh, "Refreshing..."],
            [Buttons.INSTALL_SELECTED, self.handle_mod_list_install, "Installing..."],
        ])
        tabs[installed_tab].extend([
            [
                Buttons.UNINSTALL,
                self.make_package_management_function(installed_mod, UninstallPackage),
                "Uninstalling...",
            ],
            [Buttons.EXPORT, self.handle_installed_mod_list_export, "Exporting..."],
            [Buttons.IMPORT, self.handle_installed_mod_list_import, "Importing..."],
            [
                Buttons.UPDATE,
                self.handle_installed_mod_list_update_button,
                "Updating...",
            ],
        ])
        tabs[downloaded_tab].extend([
            [
                Buttons.INSTALL,
                self.make_package_management_function(downloaded_mod, InstallPackage),
                "Installing...",
            ],
            [Buttons.DELETE, self.handle_downloaded_mod_list_delete, "Deleting..."],
        ])

        # Make Async Events For Buttons In Tabs Above
        for tab, button_list in tabs.items():
            for Button, func, label in button_list:
                self.make_async_bind_for_button(
                    self.main_frame.tabs_data[tab.value]["children"][Button.name],
                    func,
                    disabled_label=label,
                )

    def bind_events(self):
        self.bind_singular_selection_events()
        self.bind_buttons_in_tabs_events()

        _, remote_tab, remote_list = get_mod_and_tab_and_list_ctrl_from_mod(
            ModLists.REMOTE_MODS
        )
        downloaded_mod, downloaded_tab, downloaded_list = get_mod_and_tab_and_list_ctrl_from_mod(
            ModLists.DOWNLOADED_MODS
        )

        AsyncBind(
            wx.EVT_TEXT,
            self.handle_mod_list_search,
            self.main_frame.tabs_data[remote_tab.value]["children"][
                "{}{}".format(remote_list._name_, "search")
            ],
        )

        self.main_frame.tabs_data[downloaded_tab.value]["children"][
            "{}{}".format(downloaded_list._name_, "checkbox")
        ].Bind(wx.EVT_CHECKBOX, self.refresh_downloaded_mod_list)

        # A MakeAsyncBind function that takes the Button Element, An OnClick Func, and if the Button should be disabled during function call
        self.make_async_bind_for_button(
            self.main_frame.launch_game_button,
            self.handle_launch_game_button,
            disabled_label="Launching...",
        )
        self.main_frame.selection_thunderstore_button.Bind(
            wx.EVT_BUTTON, self.handle_selection_thunderstore_button
        )

    def make_async_bind_for_button(
        self, Button, func, is_disabled_during_func=True, disabled_label=None
    ):
        async def disable_during_click(event=None):
            label = Button.GetLabel()
            if is_disabled_during_func:
                Button.Disable()
                if disabled_label:
                    Button.SetLabel(disabled_label)

            await func(event=event, button=Button)
            if is_disabled_during_func:
                Button.Enable()
                if disabled_label:
                    Button.SetLabel(label)

        AsyncBind(wx.EVT_BUTTON, disable_during_click, Button)

    async def handle_launch_game_button(self, event=None, button=None, *args, **kwargs):
        webbrowser.open_new("steam://run/632360")

    async def handle_installed_mod_list_export(
        self, event=None, button=None, *args, **kwargs
    ):
        CopyableDialog(
            self.main_frame,
            "Installed mods export",
            json.dumps([str(x) for x in self.manager.installed_packages]),
        )

    async def attempt_import(self, raw_data):
        try:
            references = json.loads(raw_data)
        except Exception:
            wx.MessageBox(
                "Failed to import mod configuration. Is it proper JSON?",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        try:
            references = [PackageReference.parse(x) for x in references]
        except Exception:
            wx.MessageBox(
                "Failed to parse some of the mod names and could not import.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        for reference in references:
            await self.add_job(DownloadAndInstallPackage, reference)

    async def add_job(self, cls, *args):
        await self.job_manager.put(cls(self.manager, *args))

    async def handle_installed_mod_list_import(
        self, event=None, button=None, *args, **kwargs
    ):
        dialog = wx.TextEntryDialog(
            self.main_frame, "Enter mod configuration", "Installed mods import"
        )
        if dialog.ShowModal() == wx.ID_OK:
            await self.attempt_import(dialog.GetValue())
        dialog.Destroy()

    async def handle_mod_list_search(self, event=None, button=None, *args, **kwargs):
        query = event.GetString()
        if query is None:
            return
        await self.update_mod_list_content(query)

    async def handle_mod_list_install(self, event=None, button=None, *args, **kwargs):
        mod = ModLists.REMOTE_MODS
        for selection in self.lists[mod.name].get_selected_objects():
            meta = self.manager.resolve_package_metadata(selection)
            await self.add_job(DownloadAndInstallPackage, meta.package_reference)

    async def handle_mod_list_refresh(self, event=None, button=None, *args, **kwargs):
        if event:
            event.GetEventObject().Disable()
        try:
            await self.manager.api.async_update_packages()
            await self.update_mod_list_content()
        except Exception as e:
            log_exception(e)
            wx.MessageBox(
                "Failed to pull remote package data. Server could be offline.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
        if event:
            event.GetEventObject().Enable()

    async def update_mod_list_content(self, query=None):
        mod = ModLists.REMOTE_MODS
        tab, list_ctrl, _ = mod.value
        if query is None:
            query = self.main_frame.tabs_data[tab.value]["children"][
                "{}{}".format(list_ctrl._name_, "search")
            ].GetValue()

        def matches_query(package):
            matches_name = query.lower() in str(package.full_name).lower()
            matches_desc = query.lower() in package.description.lower()
            return matches_name or matches_desc

        packages = self.manager.api.packages.values()
        packages = filter(matches_query, packages)
        packages = sorted(packages, key=lambda entry: entry.name)
        self.lists[mod.name].update(packages)

    def refresh_installed_mod_list(self, event=None, button=None, *args, **kwargs):
        packages = sorted(self.manager.installed_packages, key=lambda entry: entry.name)
        self.lists[ModLists.INSTALLED_MODS.name].update(packages)

    def refresh_downloaded_mod_list(self, event=None, button=None, *args, **kwargs):
        packages = self.manager.cached_packages
        mod = ModLists.DOWNLOADED_MODS
        tab, list_ctrl, _ = mod.value
        if self.main_frame.tabs_data[tab.value]["children"][
            "{}{}".format(list_ctrl._name_, "checkbox")
        ].GetValue():
            packages = set([package.without_version for package in packages])
        packages = sorted(packages, key=lambda entry: entry.name)
        self.lists[mod.name].update(packages)

    def launch(self):
        self.main_frame.Show()
        self.refresh_installed_mod_list()
        self.refresh_downloaded_mod_list()
        wx.Log.SetActiveTarget(wx.LogStderr())
        StartCoroutine(self.job_manager.worker, self.main_frame)
        StartCoroutine(self.manager.validate_cache, self.main_frame)
        StartCoroutine(self.manager.migrate_mmm_prefixes, self.main_frame)
        loop = get_event_loop()
        loop.run_until_complete(self.app.MainLoop())
