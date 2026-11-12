import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path


class LauncherBackend:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.run_dir = self.root / 'run'
        self.profile_file = self.run_dir / 'config' / 'blade' / 'menu.json'
        self.mods_dir = self.run_dir / 'mods'
        self.version_file = self.root / '.launcher-version'

    def version(self):
        try:
            return self.version_file.read_text(encoding='utf-8').strip()
        except OSError:
            return '1.0.0'

    def nickname(self):
        try:
            data = json.loads(self.profile_file.read_text(encoding='utf-8'))
            name = str(data.get('selectedAccount', ''))
            if name.isascii() and name.replace('_', 'a').isalnum() and 3 <= len(name) <= 16:
                return name
        except (OSError, ValueError, TypeError):
            pass
        return 'Wildbberries'

    def save_nickname(self, nickname: str):
        name = nickname.strip()
        if not (3 <= len(name) <= 16) or not name.isascii() or not all(c.isalnum() or c == '_' for c in name):
            raise ValueError('Ник должен содержать 3–16 символов: латинские буквы, цифры и _.')
        self.profile_file.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if self.profile_file.exists():
            try:
                data = json.loads(self.profile_file.read_text(encoding='utf-8'))
            except ValueError as exc:
                raise ValueError('Не удалось прочитать run/config/blade/menu.json.') from exc
        data['selectedAccount'] = name
        accounts = list(data.get('accounts') or [])
        if not any(str(a.get('name', '')) == name for a in accounts if isinstance(a, dict)):
            accounts.append({'name': name, 'activity': 'Never played', 'avatar': len(accounts), 'pinned': False})
        data['accounts'] = accounts
        self.profile_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        return name

    def launch(self, nickname: str, ram: int, show_console: bool):
        name = self.save_nickname(nickname)
        self.save_ram(ram)
        bat = self.root / 'run-client.bat'
        if not bat.is_file():
            raise FileNotFoundError('Не найден run-client.bat. Проверь установку клиента.')
        flags = 0
        if os.name == 'nt':
            flags = subprocess.CREATE_NEW_CONSOLE if show_console else subprocess.CREATE_NO_WINDOW
            subprocess.Popen(['cmd.exe', '/c', str(bat)], cwd=self.root, creationflags=flags)
        else:
            subprocess.Popen(['/bin/sh', str(bat)], cwd=self.root)
        return name

    def save_ram(self, ram: int):
        props = self.root / 'gradle.properties'
        if not props.exists():
            raise FileNotFoundError('Не найден gradle.properties рядом с лаунчером.')
        import re
        content = props.read_text(encoding='utf-8')
        if re.search(r'(?m)^org\.gradle\.jvmargs=.*$', content):
            content = re.sub(r'(?m)^org\.gradle\.jvmargs=.*$', f'org.gradle.jvmargs=-Xmx{int(ram)}G', content, count=1)
        else:
            content += f'\norg.gradle.jvmargs=-Xmx{int(ram)}G\n'
        props.write_text(content, encoding='utf-8')
        (self.root / '.launcher-ram').write_text(str(int(ram)), encoding='ascii')

    def installed_mods(self):
        if not self.mods_dir.exists():
            return []
        return sorted(p for p in self.mods_dir.glob('*.jar') if p.is_file())

    def open_mods_folder(self):
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            os.startfile(str(self.mods_dir))
        else:
            subprocess.Popen(['xdg-open', str(self.mods_dir)])

    def open_game_folder(self):
        if os.name == 'nt':
            os.startfile(str(self.root))
        else:
            subprocess.Popen(['xdg-open', str(self.root)])

    def check_client_update(self, manifest_url: str):
        if not manifest_url.startswith('https://'):
            raise ValueError('Укажи HTTPS-ссылку на latest.json в настройках.')
        req = urllib.request.Request(manifest_url, headers={'User-Agent': 'WildbberriesClient/2.0'})
        with urllib.request.urlopen(req, timeout=20) as response:
            manifest = json.loads(response.read().decode('utf-8'))
        latest = str(manifest.get('version', '')).strip()
        download_url = str(manifest.get('downloadUrl', '')).strip()
        if not latest or not download_url.startswith('https://'):
            raise ValueError('В latest.json нужны version и HTTPS downloadUrl.')
        try:
            newer = tuple(map(int, latest.split('.'))) > tuple(map(int, self.version().split('.')))
        except ValueError:
            newer = latest != self.version()
        if not newer:
            return {'updated': False, 'version': self.version()}
        return {'updated': True, 'version': latest, 'downloadUrl': download_url, 'sha256': str(manifest.get('sha256', '')).lower()}

    def install_client_update(self, info):
        with tempfile.TemporaryDirectory(prefix='wb-client-update-') as tmp:
            archive = Path(tmp) / 'client-update.zip'
            req = urllib.request.Request(info['downloadUrl'], headers={'User-Agent': 'WildbberriesClient/2.0'})
            with urllib.request.urlopen(req, timeout=180) as response, archive.open('wb') as out:
                shutil.copyfileobj(response, out)
            expected = info.get('sha256', '')
            if expected:
                digest = hashlib.sha256(archive.read_bytes()).hexdigest()
                if digest.lower() != expected.lower():
                    raise ValueError('SHA-256 не совпал. Обновление отменено.')
            unpack = Path(tmp) / 'unpacked'
            unpack.mkdir()
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(unpack)
            candidates = list(unpack.rglob('run-client.bat'))
            if not candidates:
                raise ValueError('В архиве обновления не найден run-client.bat.')
            source = candidates[0].parent
            preserve = {'run', '.gradle', 'build', 'launcher-settings.json', '.launcher-version', 'assets', 'src', 'ClientPayload.zip', 'WildbberriesClient.exe', '_internal'}
            for item in source.iterdir():
                if item.name in preserve:
                    continue
                target = self.root / item.name
                if target.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)
            self.version_file.write_text(info['version'], encoding='ascii')
        return info['version']
