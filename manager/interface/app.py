import json
import webbrowser
import PySimpleGUI as sg

from ..api.types import PackageReference
from ..system.manager import ModManager, ModManagerConfiguration


class Application:
    def __init__(self):
        configuration = ModManagerConfiguration(
            thunderstore_url="https://thunderstore.io/",
            mod_cache_path="mod-cache/",
            mod_install_path="risk-of-rain-2/mods/",
            risk_of_rain_path="risk-of-rain-2/",
        )
        self.manager = ModManager(configuration)
        self.build_window()
        if self.can_run:
            self.refresh_installed_mods()
        self.last_values = None
        self.last_event = None
        self.last_selection = None
        self.last_selection_latest_version = None

    def build_window(self):
        self.selection_title = sg.Text(f"", font=("Helvetica", 20), size=(30, 1))
        self.selection_description = sg.Multiline(
            f"", font=("Helvetica", 10), size=(60, 5)
        )
        self.selection_author = sg.Text(f"", font=("Helvetica", 12), size=(26, 1))
        self.selection_version = sg.Text(f"", font=("Helvetica", 12), size=(26, 1))
        self.selection_total_downloads = sg.Text(
            f"", font=("Helvetica", 12), size=(26, 1)
        )
        self.selection_url = None

        self.available_packages_list = sg.Listbox(
            values=self.manager.api.get_package_names(),
            size=(38, 16),
            select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED,
        )
        self.installed_packages_list = sg.Listbox(
            values=[], size=(38, 16), select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED
        )
        self.progress_bar = sg.ProgressBar(
            max_value=1000,
            orientation="h",
            size=(100, 40),
            auto_size_text=None,
            bar_color=(None, None),
            style=None,
            border_width=None,
            relief=None,
            key="progress",
            pad=None,
            visible=True,
        )

        self.layout = [
            [
                sg.Text(
                    (
                        "Find the source from https://github.com/MythicManiac/MythicModManager "
                        + "and please make a better tool than this abomination"
                    ),
                    font=("Helvetica", 14),
                )
            ],
            [sg.Button("Refresh list"), sg.Button("Export"), sg.Button("Import")],
            [
                sg.Column(
                    [
                        [sg.Text("Available mods", font=("Helvetica", 14))],
                        [self.available_packages_list],
                        [sg.Button("Install")],
                    ]
                ),
                sg.Column(
                    [
                        [sg.Text("Installed mods", font=("Helvetica", 14))],
                        [self.installed_packages_list],
                        [sg.Button("Uninstall")],
                    ]
                ),
                sg.Column(
                    [
                        [self.selection_title],
                        [self.selection_description],
                        [self.selection_author],
                        [self.selection_version],
                        [self.selection_total_downloads],
                        [sg.RealtimeButton("View on Thunderstore")],
                    ]
                ),
            ],
            [self.progress_bar],
        ]

        if not self.manager.risk_of_rain_path.exists():
            self.can_run = False
            sg.Popup(
                (
                    "Could not find your risk of rain installation path. "
                    + "Please add it in the config.json file"
                )
            )
        else:
            self.window = sg.Window("Mythic Mod Manager").Layout(self.layout).Finalize()
            self.can_run = True

    def refresh_installed_mods(self):
        installed_packages = self.manager.installed_packages
        available_package_list = [
            entry
            for entry in self.manager.api.get_package_names()
            if entry not in installed_packages
        ]
        self.installed_packages_list.Update(installed_packages)
        self.available_packages_list.Update(available_package_list)

    def navigate_to_thunderstore(self):
        if self.selection_url:
            webbrowser.open(self.selection_url)

    def update_selection(self, selection):
        if selection not in self.manager.api.packages:
            return
        if not isinstance(selection, PackageReference):
            selection = PackageReference.parse(selection)
        entry = self.manager.api.packages[selection.without_version]
        version = entry.versions.latest
        self.last_selection = entry
        self.last_selection_latest_version = version
        self.selection_title.Update(version.name.replace("_", " "))
        self.selection_description.Update(version.description)
        self.selection_author.Update(f"Author: {entry.owner}")
        self.selection_version.Update(f"Version: v{version.version_number}")
        self.selection_total_downloads.Update(f"Total downloads: {entry.downloads}")
        self.selection_url = entry.package_url

    def install_mod(self, package_reference):
        reference = PackageReference.parse(package_reference)
        if reference not in self.manager.api.packages:
            return
        package = self.manager.api.packages[reference]

        if reference.version:
            version = package
        else:
            version = package.versions.latest

        for dependency in version.dependencies:
            if not dependency.is_same_package("bbepis-BepInExPack"):
                self.install_mod(dependency)

        self.manager.download_and_install_package(version.package_reference)

    def full_refresh(self):
        self.manager.api.update_packages()
        self.refresh_installed_mods()

    def update(self, event, values):
        if not self.last_values:
            self.last_values = values
            return

        last_available_selections = self.last_values[0]
        new_available_selections = values[0]
        available_selection_change = None

        if last_available_selections != new_available_selections:
            for selection in new_available_selections:
                if selection not in last_available_selections:
                    available_selection_change = selection
                    break

        last_installed_selections = self.last_values[1]
        new_installed_selections = values[1]
        isntalled_selection_change = None

        if last_installed_selections != new_installed_selections:
            for selection in new_installed_selections:
                if selection not in last_installed_selections:
                    isntalled_selection_change = selection
                    break

        if available_selection_change:
            self.update_selection(available_selection_change)

        if isntalled_selection_change:
            if selection in self.manager.api.packages:
                self.update_selection(selection)

        thunderstore_event = "View on Thunderstore"
        if event == thunderstore_event and self.last_event != thunderstore_event:
            self.navigate_to_thunderstore()

        install_event = "Install"
        if event == install_event and self.last_event != install_event:
            self.progress_bar.UpdateBar(0, 1000)
            for index, reference in enumerate(values[0]):
                self.install_mod(reference)
                self.progress_bar.UpdateBar(float(index) / len(values[0]) * 1000, 1000)
            self.progress_bar.UpdateBar(1000, 1000)
            self.refresh_installed_mods()

        uninstall_event = "Uninstall"
        if event == uninstall_event and self.last_event != uninstall_event:
            self.progress_bar.UpdateBar(0, 1000)
            for index, reference in enumerate(values[1]):
                self.manager.uninstall_package(reference)
                self.progress_bar.UpdateBar(float(index) / len(values[1]) * 1000, 1000)
            self.progress_bar.UpdateBar(1000, 1000)
            self.refresh_installed_mods()

        refresh_event = "Refresh list"
        if event == refresh_event and self.last_event != refresh_event:
            self.progress_bar.UpdateBar(0, 1000)
            self.full_refresh()
            self.progress_bar.UpdateBar(1000, 1000)

        export_event = "Export"
        if event == export_event and self.last_event != export_event:
            installed = [str(x) for x in self.manager.installed_packages]
            sg.PopupScrolled(json.dumps(installed))

        import_event = "Import"
        if event == import_event and self.last_event != import_event:
            data = sg.PopupGetText("Import mod configuration")
            self.handle_import(data)
            self.refresh_installed_mods()

        self.last_event = event
        self.last_values = values

    def handle_import(self, data):
        if not data:
            return
        try:
            mods_to_install = json.loads(data)
        except Exception:
            sg.Popup("Invalid mod configuration supplied")
            return

        self.progress_bar.UpdateBar(0, 1000)
        for index, entry in enumerate(mods_to_install):
            try:
                reference = PackageReference.parse(entry)
            except Exception:
                sg.Popup("Invalid mod configuration supplied")
                return
            self.manager.download_and_install_package(reference)
            self.progress_bar.UpdateBar(
                float(index) / len(mods_to_install) * 1000, 1000
            )
        self.progress_bar.UpdateBar(1000, 1000)

    def launch(self):
        while self.can_run:
            event, values = self.window.Read(timeout=100)
            if values is None:
                break
            else:
                self.update(event, values)
