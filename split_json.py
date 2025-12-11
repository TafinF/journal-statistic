import json
import os

def split_json_file(input_file, output_dir):
    """
    Разбивает JSON-файл с массивом объектов на отдельные файлы.
    
    Args:
        input_file (str): Путь к исходному JSON-файлу
        output_dir (str): Директория для сохранения отдельных файлов
        batch_size (int, optional): Размер батча для обработки больших файлов. 
                                    Если None, загружает весь файл в память.
    """
    # Создаем директорию для выходных файлов, если она не существует
    os.makedirs(output_dir, exist_ok=True)
    
    try:

            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON должен быть массивом объектов")
            
            # Сохраняем каждый объект в отдельный файл
            for i, item in enumerate(data, 1):
                output_file = os.path.join(output_dir, f"{i:03d}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(item, f, ensure_ascii=False, indent=2)
                
                print(f"Создан файл: {output_file}")
            
            print(f"\nВсего создано {len(data)} файлов в директории: {output_dir}")
            

                
    except FileNotFoundError:
        print(f"Файл {input_file} не найден")
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

split_json_file("save\\2025-12-11\\2314390_api.json","0")