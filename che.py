import json
import os
from bs4 import BeautifulSoup
import re

def extract_lesson_statuses(soup):
    """
    Извлекает статусы уроков (HOMEWORK, DIGITAL, WARNING, DEFAULT) из HTML журнала
    """
    statuses = []
    
    # Ищем все элементы с data-test-component, содержащие scheduleLessonCell
    lesson_cells = soup.find_all(attrs={"data-test-component": re.compile(r"scheduleLessonCell-.*")})
    
    for cell in lesson_cells:
        # Извлекаем значение из атрибута data-test-component
        test_component = cell.get('data-test-component', '')
        
        # Ищем паттерн scheduleLessonCell-XXXXX-STATUS
        match = re.search(r'scheduleLessonCell-\d+-(.+)', test_component)
        if match:
            status = match.group(1)
            statuses.append(status)
    
    return statuses

def process_journals(json_file_path):
    """
    Читает JSON файл с информацией о журналах
    """
    try:
        # Общий список для объектов журналов
        journals_data = []
        
        # Читаем JSON файл
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        base_url = data.get('baseURL', '')
        classes = data.get('classes', [])
        
        # Перебираем все классы
        for class_info in classes:
            class_name = class_info.get('name', 'Неизвестный класс')
            journals = class_info.get('journals', [])
            
            # Перебираем все журналы в классе
            for journal in journals:
                saves = journal.get('save', [])
                journal_name = journal.get('name', 'Неизвестный журнал')
                journal_id = journal.get('ID', 'Без ID')
                full_journal_name = f"{class_name} - {journal_name}"
                journal_url = f"{base_url}{journal_id}" if base_url and journal_id else ""
                
                # Обрабатываем все сохранения для этого журнала
                for save in saves:
                    file_path = save.get('file', '')
                    error = save.get('error', '')
                    
                    if error:
                        continue
                    
                    # Проверяем существование файла
                    if not os.path.exists(file_path):
                        continue
                    
                    try:
                        # Читаем HTML файл
                        with open(file_path, 'r', encoding='utf-8') as html_file:
                            html_content = html_file.read()
                            soup = BeautifulSoup(html_content, 'html.parser')
                            first_table = soup.find('table')
                            
                            if first_table:
                                thead = first_table.find('thead')
                                
                                # Извлекаем статусы уроков
                                journal_statuses = extract_lesson_statuses(thead)
                                
                                # Создаем объект журнала
                                journal_obj = {
                                    'full_journal_name': full_journal_name,
                                    'journal_url': journal_url,
                                    'journal_statuses': journal_statuses
                                }
                                
                                journals_data.append(journal_obj)
                                break  # Обрабатываем только первый валидный файл для журнала
                            
                    except Exception as e:
                        print(f"Ошибка при чтении файла {file_path}: {e}")
        
        # Сохраняем все объекты журналов в один файл
        output_file = "all_journals_statuses.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(journals_data, f, ensure_ascii=False, indent=2)
            print(f"Данные всех журналов сохранены в: {output_file}")
            print(f"Всего журналов обработано: {len(journals_data)}")
        except Exception as save_error:
            print(f"Ошибка при сохранении данных: {save_error}")
    
    except FileNotFoundError:
        print(f"Файл {json_file_path} не найден")
    except json.JSONDecodeError as e:
        print(f"Ошибка при чтении JSON: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

# Основная часть программы
if __name__ == "__main__":
    json_file_path = "data.json"
    process_journals(json_file_path)