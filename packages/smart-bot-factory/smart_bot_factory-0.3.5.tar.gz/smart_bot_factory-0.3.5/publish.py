#!/usr/bin/env python3
"""
Скрипт автоматической публикации библиотеки в PyPI
- Увеличивает версию на 0.0.1
- Очищает dist/
- Собирает пакет через uv build
- Публикует через twine (использует API токен из .env)
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

def increment_version(version: str) -> str:
    """Увеличивает версию на 0.0.1"""
    parts = version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Неверный формат версии: {version}")
    
    major, minor, patch = map(int, parts)
    patch += 1
    
    return f"{major}.{minor}.{patch}"

def update_version_in_toml():
    """Обновляет версию в pyproject.toml"""
    toml_path = Path("pyproject.toml")
    
    if not toml_path.exists():
        raise FileNotFoundError("pyproject.toml не найден")
    
    content = toml_path.read_text(encoding='utf-8')
    
    # Находим текущую версию
    version_match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not version_match:
        raise ValueError("Версия не найдена в pyproject.toml")
    
    old_version = version_match.group(1)
    new_version = increment_version(old_version)
    
    # Обновляем версию
    new_content = re.sub(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    
    toml_path.write_text(new_content, encoding='utf-8')
    
    print(f"✅ Версия обновлена: {old_version} → {new_version}")
    return new_version

def clean_dist():
    """Очищает папку dist/"""
    dist_path = Path("dist")
    
    if dist_path.exists():
        shutil.rmtree(dist_path)
        print("✅ Папка dist/ очищена")
    
    dist_path.mkdir(exist_ok=True)
    print("✅ Папка dist/ создана")

def build_package():
    """Собирает пакет через uv build"""
    print("\n🔨 Сборка пакета...")
    result = subprocess.run(["uv", "build"], check=True)
    print("✅ Пакет собран")
    return result.returncode == 0

def upload_to_pypi():
    """Загружает пакет в PyPI через twine"""
    print("\n📤 Загрузка в PyPI...")
    
    # Проверяем наличие токена в .env
    pypi_token = os.getenv('PYPI_API_TOKEN')
    
    if not pypi_token:
        print("⚠️ PYPI_API_TOKEN не найден в .env")
        print("💡 Добавьте в .env файл:")
        print("   PYPI_API_TOKEN=pypi-...")
        print("\nИли введите вручную при запросе twine")
    else:
        print(f"✅ Используется API токен из .env (длина: {len(pypi_token)} символов)")
    
    # Twine автоматически использует переменные окружения:
    # TWINE_USERNAME (по умолчанию "__token__")
    # TWINE_PASSWORD (PYPI_API_TOKEN)
    env = os.environ.copy()
    if pypi_token:
        env['TWINE_USERNAME'] = '__token__'
        env['TWINE_PASSWORD'] = pypi_token
    
    # Используем twine через uv run
    result = subprocess.run(
        ["uv", "run", "twine", "upload", "dist/*"],
        env=env,
        check=True
    )
    
    print("✅ Пакет загружен в PyPI")
    return result.returncode == 0

def main():
    """Основная функция"""
    try:
        print("🚀 Начинаем публикацию в PyPI\n")
        
        # 1. Обновляем версию
        new_version = update_version_in_toml()
        
        # 2. Очищаем dist/
        clean_dist()
        
        # 3. Собираем пакет
        build_package()
        
        # 4. Загружаем в PyPI
        upload_to_pypi()
        
        print(f"\n🎉 Успешно! Версия {new_version} опубликована в PyPI")
        print(f"\n💡 Не забудьте закоммитить изменения:")
        print(f"   git add pyproject.toml")
        print(f"   git commit -m 'Bump version to {new_version}'")
        print(f"   git tag v{new_version}")
        print(f"   git push && git push --tags")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка выполнения команды: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

