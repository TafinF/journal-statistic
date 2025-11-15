import json
import os
from bs4 import BeautifulSoup

def extract_grades(tr_element):
    """
    Извлекает все оценки из строки таблицы (без итоговой оценки в общем списке)
    
    Args:
        tr_element: BeautifulSoup элемент <tr>
    
    Returns:
        dict: Словарь с оценками, финальной оценкой и средним баллом
    """
    result = {
        'all_grades': [],  # все обычные оценки (без итоговой)
        'final_grade': None,  # финальная оценка
        'average_grade': None,  # средний балл
        'student_name': None  # имя студента
    }
    
    try:
        # Получаем имя студента из первого td
        first_td = tr_element.find('td')
        if first_td:
            name_span = first_td.find('span', attrs={'title': True})
            if name_span:
                result['student_name'] = name_span.get('title', '').strip()
        
        # Находим все ячейки с оценками
        all_td = tr_element.find_all('td')
        
        # Обрабатываем все td кроме первого (имя) и последнего (средний балл)
        for td in all_td[1:-1]:
            # Ищем элемент с data-test-component содержащий "markCell"
            grade_div = td.find('div', attrs={'data-test-component': lambda x: x and 'markCell' in x})
            
            if grade_div:
                data_test = grade_div.get('data-test-component', '')
                
                # Пропускаем итоговую оценку для общего списка
                if 'finalResult' in data_test:
                    # Сохраняем только финальную оценку отдельно
                    grade_span = grade_div.find('span', class_='R4p7ZXgwQ59R96TEeVm3')
                    if grade_span and grade_span.get_text(strip=True):
                        result['final_grade'] = grade_span.get_text(strip=True)
                    continue
                
                # Обрабатываем обычные оценки
                grade_span = grade_div.find('span', class_='R4p7ZXgwQ59R96TEeVm3')
                
                if grade_span and grade_span.get_text(strip=True):
                    grade = grade_span.get_text(strip=True)
                    result['all_grades'].append(grade)
                else:
                    # Если оценки нет (пустая ячейка)
                    result['all_grades'].append(None)
        
        # Получаем средний балл из последнего td
        last_td = all_td[-1] if all_td else None
        if last_td:
            avg_span = last_td.find('span', class_='DSXOGdoSiFGKohRuaDDx')
            if avg_span:
                avg_text = avg_span.get_text(strip=True).replace(',', '.')
                try:
                    result['average_grade'] = float(avg_text)
                except ValueError:
                    result['average_grade'] = avg_text
    
    except Exception as e:
        print(f"Ошибка при извлечении оценок: {e}")
    
    return result

def has_three_consecutive_twos(arr):
    count = 0
    
    for item in arr:
        if item == "2":
            count += 1
            if count >= 3:
                return True
        elif item is None:
            # Пропускаем None, продолжаем текущую последовательность
            continue
        else:
            # Любое другое значение сбрасывает счетчик
            count = 0
    
    return False

def process_journals(json_file_path):
    """
    Читает JSON файл с информацией о журналах и находит элемент main в HTML файлах
    """
    try:
        # Читаем JSON файл
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        base_url = data.get('baseURL', '')
        classes = data.get('classes', [])
        
        print(f"Найдено классов: {len(classes)}")
        print(f"Base URL: {base_url}\n")
        
        # Перебираем все классы
        for class_info in classes:
            class_name = class_info.get('name', 'Неизвестный класс')
            journals = class_info.get('journals', [])
            
            print(f"Обрабатываем класс: {class_name}")
            print(f"Количество журналов: {len(journals)}")
            
            # Перебираем все журналы в классе
            for journal in journals:
                journal_name = journal.get('name', 'Неизвестный журнал')
                journal_id = journal.get('ID', 'Без ID')
                saves = journal.get('save', [])
                
                # print(f"\n  Журнал: {journal_name} (ID: {journal_id})")
                
                # Обрабатываем все сохранения для этого журнала
                for save in saves:
                    file_path = save.get('file', '')
                    date = save.get('date', 'Неизвестная дата')
                    error = save.get('error', '')
                    
                    # print(f"    Дата сохранения: {date}")
                    if error:
                        print(f"    Ошибка: {error}")
                        continue
                    
                    # Проверяем существование файла
                    if not os.path.exists(file_path):
                        print(f"    Файл не найден: {file_path}")
                        continue
                    
                    try:
                        # Читаем HTML файл
                        with open(file_path, 'r', encoding='utf-8') as html_file:
                            html_content = html_file.read()
                        
                        # Парсим HTML и ищем элемент table
                        soup = BeautifulSoup(html_content, 'html.parser')
                        table_element = soup.find('table')
                        
                        if table_element:
                            # print(f"    ✓ Элемент table найден")
                            tabBodyRows = table_element.find('tbody').find_all(recursive=False)  # только непосредственные дети
                            
                            for row in tabBodyRows[1:]:  # пропускаем первого ребенка
                                v = extract_grades(row)
                                i = v["all_grades"]
                                if(has_three_consecutive_twos(i)):
                                    print(f"Найдены 3 двойки подряд: {base_url}{journal_id}")

                        else:
                            print(f"    ✗ Элемент table не найден в файле {journal_id}")
                            
                    except Exception as e:
                        print(f"    Ошибка при чтении файла {file_path}: {e}")
            
            print(f"\n{'='*50}")
            
    except FileNotFoundError:
        print(f"Файл {json_file_path} не найден")
    except json.JSONDecodeError as e:
        print(f"Ошибка при чтении JSON: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

# Основная часть программы
if __name__ == "__main__":
    # Путь к JSON файлу (предполагается, что он в папке save)
    json_file_path = "save/data.json"  # укажите правильный путь к вашему JSON файлу
    
    # Если файл называется по-другому или лежит в другом месте, укажите правильный путь
    # Например: "save/journal_data.json" или просто "data.json"
    
    process_journals(json_file_path)