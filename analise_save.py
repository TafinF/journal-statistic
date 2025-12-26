import json
import re

class JsonUrlFilter:
    def __init__(self, json_file_path):
        with open(json_file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.schedule_items = []
        self.homeworks = []
        self.groups = []
        
        self.groups_clean = []
        self.schedule_items_clean = []
        self.homeworks_clean = []
        
        self.schedule_homeworks = []

        self._filter_objects()
        self.prepare_groups_clean()
        self.prepare_schedule_items_clean()
        self.prepare_homeworks_clean()
        self.get_replaced_homeworks_to_verify()
        self.check_homeworks_verify_time()
    
    def _filter_objects(self):
        schedule_pattern = r'^https://authedu\.mosreg\.ru/api/ej/plan/teacher/v1/schedule_items'
        homework_pattern = r'^https://authedu\.mosreg\.ru/api/ej/core/teacher/v1/homeworks'
        groups_pattern = r'^https://authedu\.mosreg\.ru/api/ej/plan/teacher/v1/groups/\d+$'
        
        for obj in self.data:
            url = obj.get('url', '')
            
            if re.match(schedule_pattern, url):
                self.schedule_items.append(obj)
            elif re.match(homework_pattern, url):
                self.homeworks.append(obj)
            elif re.match(groups_pattern, url):
                self.groups.append(obj)
    
    def prepare_groups_clean(self):
        for group in self.groups:
            response = group.get('response', {})
            group_name = response.get('name', '')
            teachers = response.get('teachers', [])
            teacher_names = [teacher.get('full_name', '') for teacher in teachers]
            
            clean_data = {
                'name_jornal': group_name,
                'teacher': teacher_names
            }
            self.groups_clean.append(clean_data)
    
    def prepare_schedule_items_clean(self):
        for schedule_item in self.schedule_items:
            response_list = schedule_item.get('response', [])
            
            for item in response_list:
                clean_item = {
                    'iso_date_time': item.get('iso_date_time', ''),
                    'homeworks_to_give': item.get('homeworks_to_give', []),
                    'homeworks_to_verify': item.get('homeworks_to_verify', [])
                }
                self.schedule_items_clean.append(clean_item)
    
    def prepare_homeworks_clean(self):
        for homework in self.homeworks:
            response_list = homework.get('response', [])
            
            for item in response_list:
                h_es = []
                for homework_entrie in item.get('homework_entries', []):
                    h_e = {
                        'id': homework_entrie.get('id', ''),
                        'description': homework_entrie.get('description', ''),
                        'is_digital_homework': homework_entrie.get('is_digital_homework', ''),
                        'homework_id': homework_entrie.get('homework_id', ''),
                    }
                    h_es.append(h_e)
                clean_item = {
                    'id': item.get('id', ''),
                    'created_at': item.get('created_at', []),
                    'updated_at': item.get('updated_at', []),
                    'date_assigned_on': item.get('date_assigned_on', []),
                    'date_prepared_for': item.get('date_prepared_for', []),
                    'homework_entries': h_es
                }
                self.homeworks_clean.append(clean_item)

    def get_replaced_homeworks_to_verify(self):
        """
        Возвращает новый список schedule_items_clean с замененными объектами в homeworks_to_verify
        """
        # Создаем словарь для быстрого поиска домашних заданий по id
        homework_dict = {}
        for hw in self.homeworks_clean:
            homework_dict[str(hw['id'])] = hw

        # Создаем глубокую копию schedule_items_clean
        new_schedule_items = []
        for schedule_item in self.schedule_items_clean:
            # Создаем копию элемента
            new_item = schedule_item.copy()

            # Обрабатываем homeworks_to_verify если он не None и является списком
            if new_item.get('homeworks_to_verify') is not None and isinstance(new_item['homeworks_to_verify'], list):
                updated_verify = []
                for hw_ref in new_item['homeworks_to_verify']:
                    if isinstance(hw_ref, dict) and 'id' in hw_ref:
                        hw_id = str(hw_ref['id'])
                        # Ищем полное домашнее задание
                        full_hw = homework_dict.get(hw_id)
                        if full_hw:
                            updated_verify.append(full_hw)
                        else:
                            # Если не нашли, оставляем оригинальный объект
                            updated_verify.append(hw_ref)
                    else:
                        # Если структура неожиданная, оставляем как есть
                        updated_verify.append(hw_ref)
                new_item['homeworks_to_verify'] = updated_verify
            # Если homeworks_to_verify равен None или не список, оставляем как есть
            else:
                new_item['homeworks_to_verify'] = new_item.get('homeworks_to_verify')

            new_schedule_items.append(new_item)

            self.schedule_homeworks  =  new_schedule_items
    def check_homeworks_verify_time(self):
        """
        Проверяет домашние задания в homeworks_to_verify на соответствие дате и времени.
        Записывает результат проверки в self.schedule_homeworks_check
        """
        self.schedule_homeworks_check = []

        for schedule_item in self.schedule_homeworks:
            # Создаем копию элемента с добавленными полями проверки
            checked_item = schedule_item.copy()

            # Получаем дату и время урока
            lesson_datetime_str = schedule_item.get('iso_date_time', '')

            # Инициализируем список проверок
            check_results = []

            # Проверяем homeworks_to_verify, если он существует и является списком
            homeworks_to_verify = schedule_item.get('homeworks_to_verify')
            if homeworks_to_verify and isinstance(homeworks_to_verify, list):
                for hw in homeworks_to_verify:
                    check_info = {
                        'homework_id': hw.get('id'),
                        'checks': {}
                    }

                    # Проверка 1: Совпадение даты
                    hw_created_at = hw.get('created_at')

                    if lesson_datetime_str and hw_created_at:
                        # Извлекаем дату из ISO времени урока
                        try:
                            # Парсим дату урока (обрезаем до даты)
                            lesson_date_str = lesson_datetime_str.split('T')[0]

                            # Парсим дату создания задания (формат: "DD.MM.YYYY HH:MM")
                            # Получаем только дату из строки
                            hw_date_str = hw_created_at.split(' ')[0]

                            # Преобразуем оба формата дат для сравнения
                            from datetime import datetime

                            # Преобразуем дату урока (YYYY-MM-DD)
                            lesson_date = datetime.strptime(lesson_date_str, '%Y-%m-%d').date()

                            # Преобразуем дату задания (DD.MM.YYYY)
                            hw_date = datetime.strptime(hw_date_str, '%d.%m.%Y').date()

                            # Сравниваем даты
                            check_info['checks']['date_match'] = lesson_date == hw_date

                        except (ValueError, IndexError, AttributeError):
                            # Если не удалось распарсить, отмечаем как False
                            check_info['checks']['date_match'] = False
                    else:
                        # Если нет одной из дат, отмечаем как False
                        check_info['checks']['date_match'] = False

                    # Проверка 2: Время до 16:00
                    if hw_created_at:
                        try:
                            # Извлекаем время из строки создания задания
                            hw_time_str = hw_created_at.split(' ')[1]  # Получаем "HH:MM"
                            hw_hour = int(hw_time_str.split(':')[0])

                            # Проверяем, было ли задание создано до 16:00
                            check_info['checks']['time_before_16'] = hw_hour < 16

                        except (ValueError, IndexError, AttributeError):
                            # Если не удалось распарсить время, отмечаем как False
                            check_info['checks']['time_before_16'] = False
                    else:
                        # Если нет времени создания, отмечаем как False
                        check_info['checks']['time_before_16'] = False

                    check_results.append(check_info)

            # Добавляем проверки к элементу расписания
            checked_item['check'] = check_results
            self.schedule_homeworks_check.append(checked_item)

        # return self.schedule_homeworks_check

filter_obj = JsonUrlFilter("2314390_api.json")
print(filter_obj.schedule_homeworks)