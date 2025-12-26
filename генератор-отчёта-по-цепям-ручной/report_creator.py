import json
import os
from datetime import datetime

# Получаем текущую директорию
current_dir = os.path.dirname(os.path.abspath(__file__))

# Пути к файлам
json_file = os.path.join(current_dir, 'violations_report.json')
template_file = os.path.join(current_dir, 'template_chain_report.html')

# Читаем файлы
with open(json_file, 'r', encoding='utf-8') as f:
    report_data = json.load(f)

with open(template_file, 'r', encoding='utf-8') as f:
    html_template = f.read()

# Текущая дата
current_date = datetime.now().strftime('%Y-%m-%d')
current_date_display = datetime.now().strftime('%d.%m.%Y')

# Заменяем плейсхолдеры
html_output = html_template.replace('{{REPORT_DATE}}', current_date_display)
html_output = html_output.replace('{{REPORT_DATE_JS}}', f'{current_date}')
html_output = html_output.replace('{{JOURNALS_COUNT}}', str(len(report_data['journals'])))
html_output = html_output.replace('{{VIOLATIONS_COUNT}}', str(report_data['violations_found']))
html_output = html_output.replace('{{REPORT_JSON}}', json.dumps(report_data, ensure_ascii=False))

# Сохраняем результат
output_file = os.path.join(current_dir, f'violations_report_{current_date}.html')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_output)

print(f"Отчёт сохранён: {output_file}")
print(f"Журналов: {len(report_data['journals'])}")
print(f"Нарушений: {report_data['violations_found']}")