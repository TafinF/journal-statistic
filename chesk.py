import json
import os
from bs4 import BeautifulSoup
import re

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
        'student_name': None,  # имя студента
        'last_grade_before_final': None  # последняя оценка перед итоговой
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
        valid_grades_before_final = []
        
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
                    
                    # Сохраняем валидные оценки (2,3,4,5) для определения последней перед итоговой
                    if grade_value in ['2', '3', '4', '5']:
                        valid_grades_before_final.append(grade_value)
                    
                else:
                    # Если оценки нет (пустая ячейка)
                    result['all_grades'].append(None)
                    result['grades_details'].append({
                        'value': None,
                        'multiple_grades': False
                    })
        
        # Определяем последнюю оценку перед итоговой
        if valid_grades_before_final:
            result['last_grade_before_final'] = valid_grades_before_final[-1]
        
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

def has_many_lessons(html_table_header):
    """
    Проверяет, много ли уроков в журнале
    Если уроков больше 15 - True, иначе False
    """
    soup = BeautifulSoup(html_table_header, 'html.parser')
    
    # Ищем все элементы с data-test-component начинающиеся с "scheduleLessonCell"
    lesson_elements = soup.find_all(attrs={'data-test-component': lambda x: x and x.startswith('scheduleLessonCell')})
    
    # Извлекаем уникальные ID уроков (вторая часть после дефиса)
    lesson_ids = set()
    
    for element in lesson_elements:
        data_test = element.get('data-test-component', '')
        parts = data_test.split('-')
        if len(parts) >= 2:
            lesson_id = parts[1]
            lesson_ids.add(lesson_id)
    
    # Считаем количество уникальных уроков
    total_lessons = len(lesson_ids)
    
    # print(f"    Найдено уникальных уроков: {total_lessons}")  # Для отладки
    
    return total_lessons > 15

def check_student_grades_count(student_data, min_grades_required, has_az_final_grade=False):
    """
    Проверяет количество оценок у студента
    См и НВ не считаются за оценки
    
    Args:
        student_data: данные студента
        min_grades_required: минимальное требуемое количество оценок
        has_az_final_grade: True если итоговая оценка "а/з"
    """
    valid_grades = []
    has_multiple_in_cell = False
    
    for grade_detail in student_data['grades_details']:
        value = grade_detail['value']
        
        # Считаем только валидные оценки (2, 3, 4, 5)
        if value and value in ['2', '3', '4', '5']:
            valid_grades.append(value)
            
            # Проверяем, есть ли ячейки с несколькими оценками
            if grade_detail['multiple_grades']:
                has_multiple_in_cell = True
    
    # Для "а/з" - оценок должно быть недостаточно, иначе нарушение
    if has_az_final_grade:
        if len(valid_grades) >= min_grades_required:
            return 'az_with_sufficient_grades'  # Нарушение: достаточно оценок, но стоит а/з
        else:
            return None  # Корректно: оценок недостаточно и стоит а/з
    
    # Стандартная проверка для остальных случаев
    if len(valid_grades) >= min_grades_required:
        return None  # Нарушений нет
    
    # Определяем тип нарушения
    if has_multiple_in_cell:
        return 'possibly_insufficient_grades'  # Возможно недостаточно (есть множественные оценки)
    else:
        return 'insufficient_grades'  # Недостаточно оценок

def calculate_expected_final_grade(average_grade, subject_name):
    """
    Вычисляет ожидаемую итоговую оценку по среднему баллу
    с учетом специальных правил для определенных предметов
    """
    if average_grade is None or not isinstance(average_grade, (int, float)):
        return None
    
    # Предметы с особыми правилами округления
    special_subjects = [
        'изобразительное искусство',
        'музыка', 
        'технология',
        'физическая культура'
    ]
    
    # Приводим название предмета к нижнему регистру для проверки
    subject_lower = subject_name.lower()
    
    is_special_subject = any(special_subject in subject_lower for special_subject in special_subjects)
    
    if is_special_subject:
        # Правила для специальных предметов
        if average_grade >= 4.5:
            return '5'
        elif average_grade >= 3.5:
            return '4'
        elif average_grade >= 2.5:
            return '3'
        else:
            return '2'
    else:
        # Стандартные правила округления
        if average_grade >= 4.65:
            return '5'
        elif average_grade >= 3.6:
            return '4'
        elif average_grade >= 2.6:
            return '3'
        else:
            return '2'

def check_final_grade_correctness(student_data, subject_name):
    """
    Проверяет правильность итоговой оценки
    """
    final_grade = student_data.get('final_grade')
    average_grade = student_data.get('average_grade')
    
    # Если нет итоговой оценки или среднего балла - пропускаем
    if not final_grade or average_grade is None:
        return None
    
    # Если средний балл равен 0.00 или не число - пропускаем
    if not isinstance(average_grade, (int, float)) or average_grade == 0.0:
        return None
    
    # Если итоговая оценка "б/о" - пропускаем проверку
    if final_grade.lower() in ['б/о', 'бо']:
        return None
    
    # Если итоговая оценка "а/з" - не проверяем соответствие средней
    if final_grade.lower() in ['а/з', 'аз']:
        return None  # Проверка на а/з будет в check_student_grades_count
    
    # Вычисляем ожидаемую итоговую оценку
    expected_grade = calculate_expected_final_grade(average_grade, subject_name)
    
    if expected_grade is None:
        return None
    
    # Сравниваем фактическую и ожидаемую оценки
    if final_grade != expected_grade:
        return f'incorrect_final_grade_{final_grade}_expected_{expected_grade}'
    
    return None

def check_last_grade_before_final(student_data):
    """
    Проверяет, что последняя оценка перед итоговой не является двойкой
    при положительной итоговой оценке
    """
    final_grade = student_data.get('final_grade')
    last_grade = student_data.get('last_grade_before_final')
    
    # Если нет итоговой оценки или последней оценки - пропускаем
    if not final_grade or not last_grade:
        return None
    
    # Пропускаем специальные итоговые оценки
    if final_grade.lower() in ['б/о', 'бо', 'а/з', 'аз']:
        return None
    
    # Проверяем нарушение: последняя оценка "2", а итоговая "3", "4" или "5"
    if last_grade == '2' and final_grade in ['3', '4', '5']:
        return f'last_grade_2_final_{final_grade}'
    
    return None

def process_journals(json_file_path):
    """
    Читает JSON файл с информацией о журналах и проверяет на нарушения по количеству оценок и итоговым оценкам
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
                        
                        # Проверяем количество уроков в журнале
                        many_lessons = has_many_lessons(html_content)
                        min_grades_required = 5 if many_lessons else 3
                        
                        print(f"    Журнал {journal_name}: уроков много - {many_lessons}, требуется оценок - {min_grades_required}")
                        
                        # Парсим HTML и ищем элемент table
                        soup = BeautifulSoup(html_content, 'html.parser')
                        table_element = soup.find('table')
                        
                        if table_element:
                            tabBodyRows = table_element.find('tbody').find_all(recursive=False)
                            
                            for row in tabBodyRows[1:]:  # пропускаем первого ребенка
                                student_data = extract_grades(row)
                                final_grade = student_data.get('final_grade', '')
                                
                                # Если итоговая оценка "б/о" - пропускаем все проверки
                                if final_grade and final_grade.lower() in ['б/о', 'бо']:
                                    continue
                                
                                # Проверяем количество оценок у студента
                                has_az = final_grade and final_grade.lower() in ['а/з', 'аз']
                                count_violation = check_student_grades_count(
                                    student_data, min_grades_required, has_az_final_grade=has_az
                                )
                                if count_violation:
                                    journal_violations.add(count_violation)
                                    violation_count += 1
                                    results['violations_found'] += 1
                                
                                # Проверяем правильность итоговой оценки (только если не "а/з" и не "б/о")
                                if not has_az:
                                    final_grade_violation = check_final_grade_correctness(student_data, journal_name)
                                    if final_grade_violation:
                                        journal_violations.add(final_grade_violation)
                                        violation_count += 1
                                        results['violations_found'] += 1
                                
                                # Проверяем последнюю оценку перед итоговой
                                last_grade_violation = check_last_grade_before_final(student_data)
                                if last_grade_violation:
                                    journal_violations.add(last_grade_violation)
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
        output_file = "all_violations_report.json"
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