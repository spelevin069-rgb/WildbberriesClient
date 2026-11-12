import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox
from qfluentwidgets import FluentWindow, FluentIcon as FIF, InfoBar, InfoBarPosition, Theme, setTheme, setThemeColor

from src.config.settings import ConfigManager
from src.core.backend import LauncherBackend
from src.ui.views.pages import HomeInterface, InstancesInterface, ModsInterface, DiscoverInterface, SettingsInterface


class WildbberriesApp(FluentWindow):
    def __init__(self):
        super().__init__()
        self.root_dir = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[2]
        self.backend = LauncherBackend(self.root_dir)
        self.config = ConfigManager(self.root_dir)
        setTheme(Theme.DARK)
        setThemeColor('#f2f2f2')
        icon = self.root_dir / 'assets' / 'wildbberries.ico'
        if icon.exists(): self.setWindowIcon(QIcon(str(icon)))
        self.setWindowTitle('WildbberriesClient')
        self.resize(1050, 720)
        self.setMinimumSize(900, 640)
        self.setStyleSheet('FluentWindow { background: #0a0a0a; }')

        self.home = HomeInterface(self)
        self.instances = InstancesInterface(self)
        self.mods = ModsInterface(self)
        self.discover = DiscoverInterface(self)
        self.settings = SettingsInterface(self)
        self.addSubInterface(self.home, FIF.HOME, 'Главная')
        self.addSubInterface(self.instances, FIF.APPLICATION, 'Сборка')
        self.addSubInterface(self.mods, FIF.APPLICATION, 'Моды')
        self.addSubInterface(self.discover, FIF.INFO, 'Обзор')
        self.addSubInterface(self.settings, FIF.SETTING, 'Настройки')

        self.home.play.clicked.connect(self.launch_game)
        self.home.open_folder.clicked.connect(self.open_game_folder)
        self.home.check_updates.clicked.connect(self.check_updates)
        self.instances.open.clicked.connect(self.open_game_folder)
        self.mods.open.clicked.connect(self.open_mods_folder)
        self.mods.refresh.clicked.connect(self.mods.reload_items)
        self.settings.save.clicked.connect(self.save_settings)

    def notify(self, title, content, error=False):
        fn = InfoBar.error if error else InfoBar.success
        fn(title=title, content=content, orient=Qt.Orientation.Horizontal,
           isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=5000, parent=self)

    def launch_game(self):
        try:
            name = self.backend.launch(self.home.nickname.text(), self.home.ram.value(), self.config.show_console)
            self.config.ram = self.home.ram.value()
            self.home.status.setText(f'Запуск Minecraft для {name} • {self.config.ram} GB RAM')
            self.home.status.setStyleSheet('color: #ffffff;')
            self.notify('Запуск начат', f'WildbberriesClient запускает игру под ником {name}.')
        except Exception as exc:
            self.home.status.setText(str(exc))
            self.home.status.setStyleSheet('color: #ff7777;')
            self.notify('Ошибка запуска', str(exc), True)

    def open_game_folder(self):
        try: self.backend.open_game_folder()
        except Exception as exc: self.notify('Не удалось открыть папку', str(exc), True)

    def open_mods_folder(self):
        try: self.backend.open_mods_folder()
        except Exception as exc: self.notify('Не удалось открыть папку модов', str(exc), True)

    def save_settings(self):
        try:
            self.config.manifest_url = self.settings.manifest.text().strip()
            self.config.show_console = self.settings.console.isChecked()
            self.config.save()
            self.notify('Сохранено', 'Настройки лаунчера сохранены.')
        except Exception as exc: self.notify('Ошибка сохранения', str(exc), True)

    def check_updates(self):
        try:
            info = self.backend.check_client_update(self.config.manifest_url)
            if not info['updated']:
                self.notify('Обновления', f"Установлена последняя версия {info['version']}.")
                return
            answer = QMessageBox.question(self, 'Обновление клиента', f"Доступна версия {info['version']}. Установить обновление?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer == QMessageBox.StandardButton.Yes:
                version = self.backend.install_client_update(info)
                self.home.version_label.setText(f'Версия лаунчера {version}')
                self.notify('Готово', f'Клиент обновлён до {version}. Папка run сохранена.')
        except Exception as exc:
            self.notify('Ошибка обновления', str(exc), True)
