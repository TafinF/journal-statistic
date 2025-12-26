from flask import Flask, render_template, abort
import json
import os
from datetime import datetime

app = Flask(__name__)

# Директория с данными (можно задать через переменную окружения)
DATA_DIR = os.environ.get('DATA_DIR', '/data')

@app.route('/journal-report/chain/<date_str>')
def chain_report(date_str):
    """Страница отчета по цепочкам нарушений"""
    # Формируем путь к файлу
    filename = f"violations_chain_report_{date_str}.json"
    filepath = os.path.join(DATA_DIR, filename)
    
    # Проверяем существование файла
    if not os.path.exists(filepath):
        abort(404)
    
    # Читаем JSON отчет
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
    except:
        abort(404)
    
    # Форматируем дату для отображения
    try:
        report_date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = report_date_obj.strftime('%d.%m.%Y')
    except:
        formatted_date = date_str
    
    # Подсчитываем журналы
    journals_count = len(report_data.get('journals', []))
    violations_count = report_data.get('violations_found', 0)
    
    # Преобразуем JSON в строку для JavaScript
    json_str = json.dumps(report_data, ensure_ascii=False)
    
    return render_template(
        'chain_report.html',
        report_date=date_str,
        display_date=formatted_date,
        journals_count=journals_count,
        violations_count=violations_count,
        report_json=json_str
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)