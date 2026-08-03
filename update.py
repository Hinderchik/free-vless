#!/usr/bin/env python3
"""
VLESS Links Aggregator for GitHub Pages
Создаёт единый файл со всеми ссылками для автообновления в Happ/Hiddify
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
import os

# ======================== КОНФИГУРАЦИЯ ========================
SOURCE_URL = "https://raw.githubusercontent.com/tiagorrg/vless-checker/refs/heads/main/docs/keys.json"
OUTPUT_DIR = "docs"  # Папка для GitHub Pages
OUTPUT_FILE = "index.txt"  # Основной файл со ссылками
BACKUP_FILE = "backup.json"  # Резервная копия
README_FILE = "README.md"  # Автоматический README
# =============================================================

def fetch_json(url: str) -> Optional[Dict]:
    """Загружает JSON с URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return None

def extract_links(data: Dict) -> Dict[str, List[str]]:
    """Извлекает ссылки и группирует по странам."""
    grouped = {}
    all_links = set()
    
    def process_links(links_list: List, group_name: str):
        """Обрабатывает список ссылок."""
        group_links = []
        for item in links_list:
            if isinstance(item, dict) and "key" in item:
                link = item["key"]
                if link.startswith("vless://"):
                    group_links.append(link)
                    all_links.add(link)
            elif isinstance(item, str) and item.startswith("vless://"):
                group_links.append(item)
                all_links.add(item)
        
        if group_links:
            # Убираем дубликаты, сохраняя порядок
            unique_links = []
            for link in group_links:
                if link not in unique_links:
                    unique_links.append(link)
            grouped[group_name] = unique_links
    
    # Основные регионы
    for key, value in data.items():
        if key == "updated_at":
            continue
        if key.startswith("w_") or key == "russia":
            continue
            
        if isinstance(value, dict):
            # Добавляем best
            if "best" in value and value["best"]:
                all_links.add(value["best"])
            
            # Добавляем top10
            if "top10" in value and isinstance(value["top10"], list):
                for item in value["top10"]:
                    if isinstance(item, dict) and "key" in item:
                        all_links.add(item["key"])
            
            # Сохраняем лучшие ссылки как отдельную группу
            if "best" in value and value["best"]:
                group_name = key
                if group_name not in grouped:
                    grouped[group_name] = []
                grouped[group_name].append(value["best"])
            
            # Обрабатываем top10 отдельно
            if "top10" in value and isinstance(value["top10"], list):
                group_name = key
                if group_name not in grouped:
                    grouped[group_name] = []
                process_links(value["top10"], group_name)
    
    # Добавляем w_ группы
    for key, value in data.items():
        if key.startswith("w_") and isinstance(value, dict):
            clean_name = key.replace("w_", "w_")
            if "best" in value and value["best"]:
                if clean_name not in grouped:
                    grouped[clean_name] = []
                grouped[clean_name].append(value["best"])
            
            if "top10" in value and isinstance(value["top10"], list):
                if clean_name not in grouped:
                    grouped[clean_name] = []
                process_links(value["top10"], clean_name)
    
    return grouped, list(all_links)

def create_subscription_file(grouped: Dict[str, List[str]], all_links: List[str], updated_at: str):
    """Создаёт файл подписки для Happ/Hiddify."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    
    with open(filepath, "w", encoding="utf-8") as f:
        # Заголовок
        f.write("# ==========================================\n")
        f.write(f"# VLESS Subscription for Happ/Hiddify\n")
        f.write(f"# Updated: {updated_at}\n")
        f.write(f"# Total: {len(all_links)} links, {len(grouped)} groups\n")
        f.write("# ==========================================\n\n")
        
        # Группы по странам
        f.write("# ===== GROUPS BY COUNTRY =====\n\n")
        for group_name, links in sorted(grouped.items(), key=lambda x: -len(x[1])):
            if links:
                f.write(f"# ----- {group_name} ({len(links)} links) -----\n")
                for link in links:
                    f.write(f"{link}\n")
                f.write("\n")
        
        # Все ссылки для массового импорта
        f.write("\n# ===== ALL LINKS =====\n")
        for link in all_links:
            f.write(f"{link}\n")
    
    print(f"✅ Файл подписки создан: {filepath}")
    return filepath

def create_backup(data: Dict):
    """Создаёт резервную копию."""
    filepath = os.path.join(OUTPUT_DIR, BACKUP_FILE)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Резервная копия: {filepath}")

def create_readme(grouped: Dict[str, List[str]], total_links: int, updated_at: str):
    """Создаёт README для GitHub Pages."""
    filepath = os.path.join(OUTPUT_DIR, README_FILE)
    
    # Сортируем страны по количеству ссылок
    sorted_groups = sorted(grouped.items(), key=lambda x: -len(x[1]))
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"""# 🌐 VLESS Subscription for Happ/Hiddify

## 📦 Автообновляемая подписка

**Ссылка для импорта:**
https://{os.environ.get('GITHUB_REPOSITORY', 'username.github.io/repo')}/docs/{OUTPUT_FILE}

**Статистика:**
- 📅 Обновлено: {updated_at}
- 🔗 Всего ссылок: {total_links}
- 🌍 Стран: {len(grouped)}

## 📊 Распределение по странам

| Страна | Количество ссылок |
|--------|------------------|
""")
        for name, links in sorted_groups[:10]:  # Топ-10 стран
            f.write(f"| {name} | {len(links)} |\n")
        
        f.write(f"""
## 🚀 Как использовать

### Для Happ:
1. Откройте Happ
2. Нажмите **"Подписки"** → **"Добавить подписку"**
3. Вставьте ссылку выше
4. Нажмите **"Обновить"**

### Для Hiddify:
1. Откройте Hiddify
2. Нажмите **"+"** → **"Импорт из URL"**
3. Вставьте ссылку выше
4. Нажмите **"Добавить"**

## ⚙️ Автообновление

Подписка обновляется автоматически каждый день через GitHub Actions.

Последнее обновление: {updated_at}

---
*Сгенерировано автоматически • Источник: [vless-checker](https://github.com/tiagorrg/vless-checker)*
""")
    
    print(f"📄 README создан: {filepath}")

def main():
    print("🚀 Загрузка данных с GitHub...")
    
    # Загружаем данные
    data = fetch_json(SOURCE_URL)
    if not data:
        print("❌ Не удалось загрузить данные")
        return
    
    updated_at = data.get('updated_at', datetime.now().strftime('%Y-%m-%d %H:%M UTC'))
    print(f"✅ Данные загружены (обновлено: {updated_at})")
    
    # Извлекаем ссылки
    grouped, all_links = extract_links(data)
    print(f"🔗 Найдено: {len(all_links)} уникальных ссылок в {len(grouped)} группах")
    
    # Создаём файлы
    create_subscription_file(grouped, all_links, updated_at)
    create_backup(data)
    create_readme(grouped, len(all_links), updated_at)
    
    print("\n✨ Готово! Ваша подписка доступна по ссылке:")
    print(f"📎 https://{os.environ.get('GITHUB_REPOSITORY', 'ваш-username.github.io/репозиторий')}/docs/{OUTPUT_FILE}")
    print("\n💡 Импортируйте эту ссылку в Happ/Hiddify для автообновления!")

if __name__ == "__main__":
    main()
