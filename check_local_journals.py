import json
import os
from bs4 import BeautifulSoup

def extract_grades(tr_element):
    """
    Извлекает все оценки из строки таблицы (без итоговой оценки в общем списке)
    Обрабатывает ячейки с несколькими оценками и специальные значения
    """
    result = {
        'all_grades': [],  # простой массив с оценками и специальными значениями
        'grades_details': [],  # список словарей с детальной информацией
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
        for i, td in enumerate(all_td[1:-1]):
            # Ищем элемент с data-test-component содержащий "markCell"
            grade_div = td.find('div', attrs={'data-test-component': lambda x: x and 'markCell' in x})
            
            if grade_div:
                data_test = grade_div.get('data-test-component', '')
                
                # Пропускаем итоговую оценку для общего списка
                if 'finalResult' in data_test:
                    grade_span = grade_div.find('span', class_='R4p7ZXgwQ59R96TEeVm3')
                    if grade_span and grade_span.get_text(strip=True):
                        result['final_grade'] = grade_span.get_text(strip=True)
                    continue
                
                # Проверяем, есть ли иконка стопки (несколько оценок)
                stack_icon = grade_div.find('div', class_='reW5yKeh505HpxGYfGSw')
                has_multiple_grades = stack_icon is not None
                
                # Ищем значение оценки
                grade_span = grade_div.find('span', class_='R4p7ZXgwQ59R96TEeVm3')
                
                if grade_span and grade_span.get_text(strip=True):
                    grade_value = grade_span.get_text(strip=True)
                    
                    # Добавляем в простой массив
                    result['all_grades'].append(grade_value)
                    
                    # Добавляем детальную информацию
                    grade_detail = {
                        'value': grade_value,
                        'multiple_grades': has_multiple_grades
                    }
                    result['grades_details'].append(grade_detail)
                    
                else:
                    # Если оценки нет (пустая ячейка)
                    result['all_grades'].append(None)
                    result['grades_details'].append({
                        'value': None,
                        'multiple_grades': False
                    })
        
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

def analyze_sequence(grades_details, start_index):
    """
    Анализирует последовательность из 3 двоек и определяет тип нарушения
    """
    violation_types = []
    
    # Проверяем три элемента последовательности
    for i in range(start_index, start_index + 3):
        if i < len(grades_details):
            grade_info = grades_details[i]
            
            # Проверяем множественные оценки
            if grade_info['multiple_grades']:
                violation_types.append('multiple_grades')
            
            # Проверяем специальные значения
            if grade_info['value'] in ['См', 'НВ']:
                violation_types.append('special_values')
    
    # Определяем тип нарушения
    if not violation_types:
        return 'simple_sequence'  # Просто 3 двойки подряд
    elif 'multiple_grades' in violation_types and 'special_values' in violation_types:
        return 'combined'  # Комбинированный вариант
    elif 'multiple_grades' in violation_types:
        return 'multiple_grades'  # Множественные оценки
    elif 'special_values' in violation_types:
        return 'special_values'  # Есть См или НВ
    
    return 'simple_sequence'

def has_three_consecutive_twos_with_types(grades_details):
    """
    Проверяет наличие последовательностей из 3 двоек и возвращает типы нарушений
    """
    violation_types = set()
    count = 0
    sequence_start = -1
    
    for i, grade_info in enumerate(grades_details):
        value = grade_info['value']
        
        if value == "2":
            if count == 0:
                sequence_start = i
            count += 1
            
            if count >= 3:
                # Нашли последовательность из 3+ двоек
                violation_type = analyze_sequence(grades_details, sequence_start)
                violation_types.add(violation_type)
                # Сбрасываем для поиска следующей последовательности
                count = 0
                sequence_start = -1
                
        elif value is None:
            # Пропускаем None, продолжаем текущую последовательность
            continue
        else:
            # Любое другое значение сбрасывает счетчик
            count = 0
            sequence_start = -1
    
    return list(violation_types)

def process_journals(json_file_path):
    """
    Читает JSON файл с информацией о журналах и проверяет на нарушения
    """
    results = {
        'baseURL': '',
        'violations_found': 0,
        'journals': []
    }
    
    try:
        # Читаем JSON файл
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        base_url = data.get('baseURL', '')
        results['baseURL'] = base_url
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
                
                # Формируем полное название журнала: класс + предмет
                full_journal_name = f"{class_name} - {journal_name}"
                
                journal_violations = set()
                violation_count = 0
                
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
                        
                        # Парсим HTML и ищем элемент table
                        soup = BeautifulSoup(html_content, 'html.parser')
                        table_element = soup.find('table')
                        
                        if table_element:
                            tabBodyRows = table_element.find('tbody').find_all(recursive=False)
                            
                            for row in tabBodyRows[1:]:  # пропускаем первого ребенка
                                student_data = extract_grades(row)
                                grades_details = student_data["grades_details"]
                                
                                # Ищем нарушения для этого студента
                                violations = has_three_consecutive_twos_with_types(grades_details)
                                
                                if violations:
                                    for violation_type in violations:
                                        journal_violations.add(violation_type)
                                        violation_count += 1
                                        results['violations_found'] += 1
                        
                    except Exception as e:
                        print(f"    Ошибка при чтении файла {file_path}: {e}")
                
                # Если в журнале найдены нарушения, добавляем в результаты
                if journal_violations:
                    results['journals'].append({
                        'journal_id': journal_id,
                        'journal_name': full_journal_name,
                        'violations_count': violation_count,
                        'sequence_twos': list(journal_violations)
                    })
                    print(f"    ✓ Нарушения в журнале {journal_name}: {list(journal_violations)} (количество: {violation_count})")
            
            print(f"\n{'='*50}")
        
        # Сохраняем результаты в JSON файл
        output_file = "violations_report.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\nРезультаты проверки сохранены в файл: {output_file}")
        print(f"Всего найдено журналов с нарушениями: {len(results['journals'])}")
        print(f"Всего найдено нарушений: {results['violations_found']}")
        
    except FileNotFoundError:
        print(f"Файл {json_file_path} не найден")
    except json.JSONDecodeError as e:
        print(f"Ошибка при чтении JSON: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    
    return results

# Основная часть программы
if __name__ == "__main__":
    json_file_path = "data.json"
    results = process_journals(json_file_path)