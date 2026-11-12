import json
from pathlib import Path


class ConfigManager:
    def __init__(self, app_dir: Path):
        self.app_dir = Path(app_dir)
        self.path = self.app_dir / 'launcher-settings.json'
        self.manifest_url = ''
        self.show_console = False
        self.ram = 4
        self.load()

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            self.manifest_url = str(data.get('manifestUrl', '') or '')
            self.show_console = bool(data.get('showConsole', False))
        except (OSError, ValueError, TypeError):
            pass
        try:
            self.ram = int((self.app_dir / '.launcher-ram').read_text().strip())
            if not 2 <= self.ram <= 16:
                self.ram = 4
        except (OSError, ValueError):
            self.ram = 4

    def save(self):
        self.path.write_text(json.dumps({
            'manifestUrl': self.manifest_url,
            'showConsole': self.show_console,
        }, ensure_ascii=False, indent=2), encoding='utf-8')

    def save_ram(self, value: int):
        self.ram = max(2, min(16, int(value)))
        props = self.app_dir / 'gradle.properties'
        if not props.exists():
            raise FileNotFoundError('Не найден gradle.properties рядом с лаунчером.')
        content = props.read_text(encoding='utf-8')
        import re
        if re.search(r'(?m)^org\.gradle\.jvmargs=.*$', content):
            content = re.sub(r'(?m)^org\.gradle\.jvmargs=.*$', f'org.gradle.jvmargs=-Xmx{self.ram}G', content, count=1)
        else:
            content += f'\norg.gradle.jvmargs=-Xmx{self.ram}G\n'
        props.write_text(content, encoding='utf-8')
        (self.app_dir / '.launcher-ram').write_text(str(self.ram), encoding='ascii')
