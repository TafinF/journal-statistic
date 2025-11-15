from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import os
import tempfile
from datetime import datetime


def setup_driver():
    """Настройка Chrome драйвера"""
    chrome_options = Options()
    
    # Основные опции для стабильной работы
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Используем временную директорию для профиля
    profile_dir = os.path.join(tempfile.gettempdir(), "chrome_profile")
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Ошибка при создании драйвера: {e}")
        raise


def load_json_data(filename):
    """Загрузка данных из JSON файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка при загрузке JSON файла: {e}")
        return None


def save_json_data(filename, data):
    """Сохранение данных в JSON файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка при сохранении JSON файла: {e}")
        return False


def ensure_save_directory():
    """Создает структуру папок для сохранения HTML файлов"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    save_dir = os.path.join("save", current_date)
    
    # Создаем папки если их нет
    os.makedirs(save_dir, exist_ok=True)
    
    return save_dir


def save_html_to_file(html_content, journal_id, save_dir):
    """Сохраняет HTML в файл и возвращает относительный путь"""
    filename = f"{journal_id}.html"
    filepath = os.path.join(save_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Возвращаем относительный путь для JSON
        relative_path = os.path.join("save", os.path.basename(save_dir), filename)
        return relative_path
    except Exception as e:
        print(f"Ошибка при сохранении HTML файла: {e}")
        return None


def wait_for_page_load(driver, timeout=15):
    """
    Ожидает загрузки страницы по появлению SVG элементов
    Возвращает True если страница загрузилась, False если таймаут
    """
    try:
        print("  Ожидаю загрузки страницы...")
        # Ждем появления элементов с указанными классами
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".MV57GCYYcPhOHkSQsK9F.EoyGTa_NIo_M5boZkXU0"))
        )
        print("  ✓ Страница загружена полностью")
        return True
    except TimeoutException:
        print(f"  ✗ Страница не загрузилась за {timeout} секунд")
        return False


def wait_for_manual_authorization(driver, url):
    """Ожидание ручной авторизации на главной странице"""
    print(f"Открываю страницу для авторизации: {url}")
    driver.get(url)
    
    print("Сайт загружен успешно!")
    print("Вы можете выполнить вход вручную...")
    print("После успешного входа нажмите Enter в консоли для продолжения...")
    
    # Ожидание ручного входа пользователя
    input("Выполните вход и нажмите Enter для продолжения...")
    
    print("Авторизация завершена, продолжаю работу...")


def wait_for_first_journal(driver, url):
    """Ожидание подтверждения для первого журнала"""
    print(f"Открываю первый журнал: {url}")
    driver.get(url)
    
    print("Первый журнал загружен!")
    print("Убедитесь, что страница загрузилась корректно...")
    print("Нажмите Enter для сохранения первого журнала и продолжения автоматической работы...")
    
    # Ожидание подтверждения пользователя
    input("Нажмите Enter для продолжения...")
    
    print("Первый журнал подтвержден, продолжаю автоматическую работу...")
    return driver.page_source


def find_next_journal_to_process(data):
    """Находит следующий журнал для обработки (без сохраненной страницы)"""
    for class_idx, class_item in enumerate(data.get("classes", [])):
        for journal_idx, journal in enumerate(class_item.get("journals", [])):
            # Если у журнала нет сохраненных данных или массив save пустой
            if "save" not in journal or not journal["save"]:
                return class_idx, journal_idx, class_item, journal
    return None, None, None, None


def process_journals(driver, data):
    """Обработка журналов с продолжением с места остановки"""
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_dir = ensure_save_directory()
    
    print(f"HTML файлы сохраняются в: {save_dir}")
    
    # Находим первый необработанный журнал
    class_idx, journal_idx, class_item, journal = find_next_journal_to_process(data)
    
    if class_idx is None:
        print("Все журналы уже обработаны!")
        return data
    
    print(f"Начинаю обработку с класса '{class_item['name']}', журнал '{journal['name']}'")
    
    first_journal = True
    processed_count = 0
    
    # Обрабатываем начиная с найденного журнала
    for current_class_idx in range(class_idx, len(data.get("classes", []))):
        current_class = data["classes"][current_class_idx]
        
        # Определяем с какого журнала начинать в текущем классе
        start_journal_idx = journal_idx if current_class_idx == class_idx else 0
        
        print(f"Обрабатываю класс: {current_class['name']}")
        
        for current_journal_idx in range(start_journal_idx, len(current_class.get("journals", []))):
            current_journal = current_class["journals"][current_journal_idx]
            
            # Пропускаем уже обработанные журналы (на всякий случай)
            if "save" in current_journal and current_journal["save"]:
                print(f"  Пропускаю уже обработанный журнал: {current_journal['name']}")
                continue
            
            # Формируем целевую ссылку
            target_url = data["baseURL"] + current_journal["ID"]
            print(f"  Журнал: {current_journal['name']}")
            print(f"  URL: {target_url}")
            print(f"  ID: {current_journal['ID']}")
            
            try:
                if first_journal:
                    # Для первого журнала ждем подтверждения
                    driver.get(target_url)
                    page_html = wait_for_first_journal(driver, target_url)
                    first_journal = False
                    
                    # После подтверждения проверяем загрузку
                    page_loaded = wait_for_page_load(driver)
                else:
                    # Для остальных журналов работаем автоматически
                    driver.get(target_url)
                    page_loaded = wait_for_page_load(driver)
                    page_html = driver.page_source
                    
                    if page_loaded:
                        print(f"  ✓ Страница загружена автоматически")
                    else:
                        print(f"  ⚠ Страница загружена не полностью")
                
                # Сохраняем HTML в файл
                file_path = save_html_to_file(page_html, current_journal["ID"], save_dir)
                
                if file_path:
                    # Создаем запись о сохранении с путем к файлу
                    save_entry = {
                        "date": current_date,
                        "file": file_path  # Сохраняем путь к файлу вместо HTML
                    }
                    
                    # Добавляем ошибку если страница не загрузилась
                    if not page_loaded:
                        save_entry["error"] = "не загрузилась страница"
                        print(f"  ⚠ Добавлена ошибка: страница не загрузилась полностью")
                    
                    # Добавляем в журнал
                    if "save" not in current_journal:
                        current_journal["save"] = []
                    
                    current_journal["save"].append(save_entry)
                    print(f"  ✓ HTML сохранен в файл: {file_path}")
                    
                    # НЕМЕДЛЕННО СОХРАНЯЕМ В ИСХОДНЫЙ ФАЙЛ
                    if save_json_data("data.json", data):
                        print(f"  ✓ Данные сохранены в исходный файл")
                        processed_count += 1
                    else:
                        print("  ✗ Ошибка сохранения данных")
                else:
                    print("  ✗ Не удалось сохранить HTML файл")
                
            except Exception as e:
                print(f"  ✗ Ошибка при обработке журнала: {e}")
                # При ошибке все равно сохраняем прогресс
                try:
                    save_json_data("data.json", data)
                    print(f"  ✓ Прогресс сохранен несмотря на ошибку")
                except:
                    print("  ✗ Не удалось сохранить прогресс")
            
            # Небольшая пауза между запросами
            time.sleep(2)
    
    print(f"Обработка завершена. Обработано журналов: {processed_count}")
    return data


def main():
    # Загружаем данные из исходного JSON файла
    json_filename = "data.json"
    data = load_json_data(json_filename)
    
    if not data:
        print("Не удалось загрузить JSON файл")
        return
    
    print("Настраиваю драйвер...")
    
    try:
        driver = setup_driver()
    except Exception as e:
        print(f"Не удалось запустить драйвер: {e}")
        return
    
    try:
        # Проверяем, нужна ли авторизация (если есть необработанные журналы)
        if find_next_journal_to_process(data)[0] is not None:
            # Шаг 1: Авторизация на главной странице
            main_url = "https://authedu.mosreg.ru/teacher/study-process/journal/grade/"
            wait_for_manual_authorization(driver, main_url)
        
        # Шаг 2: Обработка журналов с продолжением
        print("Начинаю обработку журналов...")
        updated_data = process_journals(driver, data)
        
        print("✓ Все журналы обработаны и сохранены в исходный файл!")
            
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        # Сохраняем прогресс даже при ошибке
        try:
            save_json_data("data.json", data)
            print(f"✓ Прогресс сохранен в исходный файл")
        except:
            print("✗ Не удалось сохранить прогресс")
    
    finally:
        if driver:
            driver.quit()
            print("Драйвер закрыт")


if __name__ == "__main__":
    main()