"""
Скрипт для настройки демо-данных в системе распределения обращений
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

def print_response(title, response):
    """Красиво выводит ответ API"""
    print(f"\n{'='*60}")
    print(f"✓ {title}")
    print(f"{'='*60}")
    if response.status_code in [200, 201]:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"❌ Ошибка {response.status_code}: {response.text}")
    print()

def wait_for_server():
    """Ждем пока сервер запустится"""
    print("⏳ Ожидание запуска сервера...")
    for i in range(10):
        try:
            response = requests.get("http://localhost:8000/health", timeout=1)
            if response.status_code == 200:
                print("✓ Сервер готов!\n")
                return True
        except:
            time.sleep(1)
    print("❌ Сервер не запустился")
    return False

def main():
    print("\n" + "="*60)
    print("🚀 НАСТРОЙКА ДЕМО-ДАННЫХ")
    print("="*60)
    
    if not wait_for_server():
        return
    
    # 1. Создаем операторов
    print("\n📋 ШАГ 1: Создание операторов")
    print("-" * 60)
    
    operators = [
        {"name": "Иван Петров", "max_load_limit": 10},
        {"name": "Мария Сидорова", "max_load_limit": 15},
        {"name": "Алексей Иванов", "max_load_limit": 8},
    ]
    
    operator_ids = []
    for op in operators:
        response = requests.post(f"{BASE_URL}/operators", json=op)
        print_response(f"Создан оператор: {op['name']}", response)
        if response.status_code == 201:
            operator_ids.append(response.json()['id'])
    
    # 2. Создаем источники
    print("\n📱 ШАГ 2: Создание источников обращений")
    print("-" * 60)
    
    sources = [
        {"name": "Telegram Bot", "identifier": "telegram"},
        {"name": "Email Support", "identifier": "email"},
        {"name": "Phone Support", "identifier": "phone"},
    ]
    
    source_ids = []
    for src in sources:
        response = requests.post(f"{BASE_URL}/sources", json=src)
        print_response(f"Создан источник: {src['name']}", response)
        if response.status_code == 201:
            source_ids.append(response.json()['id'])
    
    # 3. Настраиваем веса
    print("\n⚖️  ШАГ 3: Настройка весов операторов")
    print("-" * 60)
    
    if len(operator_ids) >= 3 and len(source_ids) >= 3:
        # Веса для Telegram (все операторы)
        weights_telegram = {
            "weights": [
                {"operator_id": operator_ids[0], "weight": 50},
                {"operator_id": operator_ids[1], "weight": 30},
                {"operator_id": operator_ids[2], "weight": 20}
            ]
        }
        response = requests.post(f"{BASE_URL}/sources/{source_ids[0]}/operators", json=weights_telegram)
        print_response("Настроены веса для Telegram", response)
        
        # Веса для Email (первые два оператора)
        weights_email = {
            "weights": [
                {"operator_id": operator_ids[0], "weight": 40},
                {"operator_id": operator_ids[1], "weight": 60}
            ]
        }
        response = requests.post(f"{BASE_URL}/sources/{source_ids[1]}/operators", json=weights_email)
        print_response("Настроены веса для Email", response)
        
        # Веса для Phone (второй и третий операторы)
        weights_phone = {
            "weights": [
                {"operator_id": operator_ids[1], "weight": 70},
                {"operator_id": operator_ids[2], "weight": 30}
            ]
        }
        response = requests.post(f"{BASE_URL}/sources/{source_ids[2]}/operators", json=weights_phone)
        print_response("Настроены веса для Phone", response)
    
    # 4. Создаем тестовые обращения
    print("\n📨 ШАГ 4: Создание тестовых обращений")
    print("-" * 60)
    
    if len(source_ids) >= 3:
        test_requests = [
            {
                "user_identifier": "user1@telegram",
                "source_id": source_ids[0],
                "message": "Здравствуйте! У меня вопрос по заказу #12345"
            },
            {
                "user_identifier": "client@example.com",
                "source_id": source_ids[1],
                "message": "Не могу войти в личный кабинет"
            },
            {
                "user_identifier": "+79991234567",
                "source_id": source_ids[2],
                "message": "Хочу оформить возврат товара"
            },
            {
                "user_identifier": "user2@telegram",
                "source_id": source_ids[0],
                "message": "Когда будет доставка?"
            },
            {
                "user_identifier": "support@company.com",
                "source_id": source_ids[1],
                "message": "Нужна помощь с настройкой"
            },
        ]
        
        for i, req in enumerate(test_requests, 1):
            response = requests.post(f"{BASE_URL}/requests", json=req)
            if response.status_code == 201:
                data = response.json()
                print(f"✓ Обращение #{i}: назначено оператору #{data.get('operator_id', 'не назначен')}")
            else:
                print(f"❌ Ошибка создания обращения #{i}")
            time.sleep(0.3)
    
    # 5. Показываем статистику
    print("\n📊 ШАГ 5: Статистика системы")
    print("-" * 60)
    
    # Загрузка операторов
    response = requests.get(f"{BASE_URL}/stats/operators-load")
    print_response("Загрузка операторов", response)
    
    # Распределение обращений
    response = requests.get(f"{BASE_URL}/stats/requests-distribution")
    print_response("Распределение обращений", response)
    
    # Список всех обращений
    response = requests.get(f"{BASE_URL}/requests")
    if response.status_code == 200:
        requests_data = response.json()
        print(f"\n{'='*60}")
        print(f"📋 Всего создано обращений: {len(requests_data)}")
        print(f"{'='*60}\n")
    
    print("\n" + "="*60)
    print("✅ ДЕМО-ДАННЫЕ УСПЕШНО СОЗДАНЫ!")
    print("="*60)
    print("\n📖 Что дальше:")
    print("  • Откройте http://localhost:8000/docs для интерактивной документации")
    print("  • Создавайте новые обращения через API")
    print("  • Смотрите статистику в реальном времени")
    print("\n💡 Примеры команд:")
    print("  curl http://localhost:8000/api/v1/stats/operators-load")
    print("  curl http://localhost:8000/api/v1/requests")
    print()

if __name__ == "__main__":
    main()
