from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QFormLayout,
    QCheckBox, QSpinBox, QScrollArea
)
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel, LineEdit,
    PrimaryPushButton, PushButton, ProgressBar, ElevatedCardWidget
)


def card(parent=None):
    w = ElevatedCardWidget(parent)
    w.setStyleSheet("ElevatedCardWidget { background: #191919; border: 1px solid #383838; border-radius: 16px; }")
    return w


class HomeInterface(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setObjectName('home_interface')
        root = QVBoxLayout(self)
        root.setContentsMargins(34, 26, 34, 28)
        root.setSpacing(18)

        root.addWidget(TitleLabel('Добро пожаловать в Wildbberries', self))
        root.addWidget(CaptionLabel('Твой Minecraft-клиент — всё необходимое в одном месте.', self))

        hero = card(self)
        hero_l = QVBoxLayout(hero)
        hero_l.setContentsMargins(26, 24, 26, 24)
        hero_l.setSpacing(14)
        brand = QLabel('WILDBBERRIES CLIENT')
        brand.setStyleSheet('font-size: 12px; font-weight: 800; letter-spacing: 3px; color: #ffffff;')
        hero_l.addWidget(brand)
        hero_l.addWidget(SubtitleLabel('Готов к игре?', hero))
        hero_l.addWidget(BodyLabel('Minecraft 26.2  •  Fabric  •  Java 25', hero))

        row = QHBoxLayout()
        self.nickname = LineEdit(hero)
        self.nickname.setPlaceholderText('Твой никнейм')
        self.nickname.setText(self.app.backend.nickname())
        self.nickname.setFixedWidth(245)
        row.addWidget(self.nickname)
        self.ram = QSpinBox(hero)
        self.ram.setRange(2, 16)
        self.ram.setSuffix(' GB RAM')
        self.ram.setValue(self.app.config.ram)
        self.ram.setFixedWidth(130)
        row.addWidget(self.ram)
        row.addStretch(1)
        hero_l.addLayout(row)

        actions = QHBoxLayout()
        self.play = PrimaryPushButton('▶   ИГРАТЬ', hero)
        self.play.setFixedSize(190, 48)
        self.open_folder = PushButton('Открыть папку клиента', hero)
        self.open_folder.setFixedHeight(48)
        actions.addWidget(self.play)
        actions.addWidget(self.open_folder)
        actions.addStretch(1)
        hero_l.addLayout(actions)
        self.progress = ProgressBar(hero)
        self.progress.setRange(0, 0)
        self.progress.hide()
        hero_l.addWidget(self.progress)
        self.status = CaptionLabel('Клиент установлен. Можно запускать.', hero)
        self.status.setStyleSheet('color: #bdbdbd;')
        hero_l.addWidget(self.status)
        root.addWidget(hero)

        bottom = QHBoxLayout()
        info = card(self)
        info_l = QVBoxLayout(info)
        info_l.setContentsMargins(20, 18, 20, 18)
        info_l.addWidget(SubtitleLabel('Текущая сборка', info))
        info_l.addWidget(BodyLabel('Wildbberries Client', info))
        info_l.addWidget(CaptionLabel('Minecraft 26.2 • Fabric • Java 25', info))
        bottom.addWidget(info, 2)
        update = card(self)
        update_l = QVBoxLayout(update)
        update_l.setContentsMargins(20, 18, 20, 18)
        update_l.addWidget(SubtitleLabel('Обновления', update))
        self.version_label = CaptionLabel(f"Версия лаунчера {self.app.backend.version()}", update)
        update_l.addWidget(self.version_label)
        self.check_updates = PushButton('Проверить обновления клиента', update)
        update_l.addWidget(self.check_updates)
        bottom.addWidget(update, 3)
        root.addLayout(bottom)
        root.addStretch(1)


class InstancesInterface(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setObjectName('instances_interface')
        l = QVBoxLayout(self); l.setContentsMargins(34, 28, 34, 28); l.setSpacing(16)
        l.addWidget(TitleLabel('Сборка', self))
        c = card(self); cl = QVBoxLayout(c); cl.setContentsMargins(24, 22, 24, 22)
        cl.addWidget(SubtitleLabel('Wildbberries Client', c))
        cl.addWidget(BodyLabel('Minecraft 26.2 • Fabric • Java 25', c))
        cl.addWidget(CaptionLabel('Это установленная сборка из твоего ClientPayload.zip. Переключение версий пока не подключено.', c))
        self.open = PushButton('Открыть папку сборки', c); cl.addWidget(self.open)
        l.addWidget(c); l.addStretch(1)


class ModsInterface(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setObjectName('mods_interface')
        l = QVBoxLayout(self); l.setContentsMargins(34, 28, 34, 28); l.setSpacing(14)
        head = QHBoxLayout(); head.addWidget(TitleLabel('Моды', self)); head.addStretch(1)
        self.refresh = PushButton('Обновить список', self); head.addWidget(self.refresh)
        self.open = PushButton('Открыть папку mods', self); head.addWidget(self.open)
        l.addLayout(head)
        l.addWidget(CaptionLabel('Список JAR-файлов из активной папки run/mods.', self))
        self.list = QScrollArea(self); self.list.setWidgetResizable(True); self.list.setFrameShape(QFrame.Shape.NoFrame)
        self.list_body = QWidget(); self.list_layout = QVBoxLayout(self.list_body); self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list.setWidget(self.list_body); l.addWidget(self.list)
        self.reload_items()

    def reload_items(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        mods = self.app.backend.installed_mods()
        if not mods:
            self.list_layout.addWidget(CaptionLabel('Пока нет установленных .jar-модов. Добавь файлы в папку run/mods.', self.list_body))
        for path in mods:
            c = card(self.list_body); row = QHBoxLayout(c); row.setContentsMargins(16, 12, 16, 12)
            row.addWidget(BodyLabel(path.name, c)); row.addStretch(1); row.addWidget(CaptionLabel(f'{path.stat().st_size // 1024} KB', c))
            self.list_layout.addWidget(c)
        self.list_layout.addStretch(1)


class DiscoverInterface(QWidget):
    def __init__(self, app):
        super().__init__()
        self.setObjectName('discover_interface')
        l = QVBoxLayout(self); l.setContentsMargins(34, 28, 34, 28); l.setSpacing(16)
        l.addWidget(TitleLabel('Обзор', self))
        c = card(self); cl = QVBoxLayout(c); cl.setContentsMargins(24, 22, 24, 22)
        cl.addWidget(SubtitleLabel('Wildbberries Client', c))
        cl.addWidget(BodyLabel('Локальный Minecraft-клиент с Fabric.', c))
        cl.addWidget(CaptionLabel('Миры, настройки и моды остаются в папке run. Не удаляй её при обновлении клиента.', c))
        l.addWidget(c); l.addStretch(1)


class SettingsInterface(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setObjectName('settings_interface')
        l = QVBoxLayout(self); l.setContentsMargins(34, 28, 34, 28); l.setSpacing(16)
        l.addWidget(TitleLabel('Настройки', self))
        c = card(self); cl = QVBoxLayout(c); cl.setContentsMargins(24, 22, 24, 22); cl.setSpacing(12)
        cl.addWidget(SubtitleLabel('Запуск и обновления', c))
        cl.addWidget(BodyLabel('Показывать консоль Minecraft при запуске', c))
        self.console = QCheckBox('Включить консоль')
        self.console.setChecked(app.config.show_console)
        cl.addWidget(self.console)
        cl.addWidget(BodyLabel('HTTPS-ссылка на latest.json для обновления клиента', c))
        self.manifest = LineEdit(c); self.manifest.setText(app.config.manifest_url); self.manifest.setPlaceholderText('https://.../latest.json')
        cl.addWidget(self.manifest)
        self.save = PrimaryPushButton('Сохранить настройки', c); cl.addWidget(self.save)
        l.addWidget(c); l.addStretch(1)
