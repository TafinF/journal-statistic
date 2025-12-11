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

    # def schedule_homeworks_create(self):
    #     for schedule_item in self.schedule_items_clean:
    #         homeworks_to_verify = schedule_item.get('homeworks_to_verify', {})
    #         for h_v in homeworks_to_verify:
    #             h_v.get('id', '')
    #         teacher_names = [teacher.get('full_name', '') for teacher in teachers]
            
    #         clean_data = {
    #             'name_jornal': group_name,
    #             'teacher': teacher_names
    #         }
    #         self.groups_clean.append(clean_data)
filter_obj = JsonUrlFilter("2314390_api.json")
print("")