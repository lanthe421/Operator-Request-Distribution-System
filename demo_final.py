"""
Финальная демонстрация работы системы распределения обращений
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))

print_section("🚀 ДЕМОНСТРАЦИЯ СИСТЕМЫ РАСПРЕДЕЛЕНИЯ ОБРАЩЕНИЙ")

# 1. Показать текущих операторов
print_section("📋 ТЕКУЩИЕ ОПЕРАТОРЫ")
response = requests.get(f"{BASE_URL}/operators")
operators = response.json()
for op in operators:
    status = "🟢 Активен" if op['is_active'] else "🔴 Неактивен"
    print(f"  ID {op['id']}: {op['name']}")
    print(f"    {status} | Загрузка: {op['current_load']}/{op['max_load_limit']}")
    print()

# 2. Показать источники
print_section("📱 ИСТОЧНИКИ ОБРАЩЕНИЙ")
response = requests.get(f"{BASE_URL}/sources")
sources = response.json()
for src in sources:
    print(f"  ID {src['id']}: {src['name']} ({src['identifier']})")

# 3. Создать несколько новых обращений
print_section("📨 СОЗДАНИЕ НОВЫХ ОБРАЩЕНИЙ")

if len(sources) > 0:
    test_requests = [
        {
            "user_identifier": f"demo_user_{int(time.time())}@telegram",
            "source_id": sources[0]['id'],
            "message": "Здравствуйте! Как проверить статус заказа?"
        },
        {
            "user_identifier": f"demo_client_{int(time.time())}@email.com",
            "source_id": sources[0]['id'],
            "message": "Не приходит код подтверждения"
        },
        {
            "user_identifier": f"+7999{int(time.time()) % 10000000}",
            "source_id": sources[0]['id'],
            "message": "Хочу оформить возврат"
        },
    ]
    
    created_requests = []
    for i, req in enumerate(test_requests, 1):
        response = requests.post(f"{BASE_URL}/requests", json=req)
        if response.status_code == 201:
            data = response.json()
            created_requests.append(data)
            operator_name = "не назначен"
            if data.get('operator_id'):
                # Найти имя оператора
                for op in operators:
                    if op['id'] == data['operator_id']:
                        operator_name = op['name']
                        break
            print(f"  ✓ Обращение #{data['id']}: назначено → {operator_name}")
        else:
            print(f"  ✗ Ошибка создания обращения #{i}")
        time.sleep(0.5)

# 4. Показать детали одного обращения
if created_requests:
    print_section("🔍 ДЕТАЛИ ОБРАЩЕНИЯ")
    request_id = created_requests[0]['id']
    response = requests.get(f"{BASE_URL}/requests/{request_id}")
    if response.status_code == 200:
        request_detail = response.json()
        print(f"  ID: {request_detail['id']}")
        print(f"  Пользователь: {request_detail['user']['identifier']}")
        print(f"  Источник: {request_detail['source']['name']}")
        if request_detail.get('operator'):
            print(f"  Оператор: {request_detail['operator']['name']}")
        print(f"  Сообщение: {request_detail['message']}")
        print(f"  Статус: {request_detail['status']}")
        print(f"  Создано: {request_detail['created_at']}")

# 5. Показать статистику загрузки
print_section("📊 СТАТИСТИКА ЗАГРУЗКИ ОПЕРАТОРОВ")
response = requests.get(f"{BASE_URL}/stats/operators-load")
if response.status_code == 200:
    stats = response.json()
    for op_stat in stats['operators']:
        load_bar = "█" * int(op_stat['load_percentage'] / 10) + "░" * (10 - int(op_stat['load_percentage'] / 10))
        print(f"  {op_stat['operator_name']}")
        print(f"    [{load_bar}] {op_stat['load_percentage']:.1f}%")
        print(f"    {op_stat['current_load']}/{op_stat['max_load_limit']} обращений")
        print()

# 6. Показать распределение обращений
print_section("📈 РАСПРЕДЕЛЕНИЕ ОБРАЩЕНИЙ")
response = requests.get(f"{BASE_URL}/stats/requests-distribution")
if response.status_code == 200:
    dist = response.json()
    
    print("  По операторам:")
    for op_dist in dist['by_operator']:
        print(f"    • {op_dist['operator_name']}: {op_dist['request_count']} обращений")
    
    print("\n  По источникам:")
    for src_dist in dist['by_source']:
        print(f"    • {src_dist['source_name']}: {src_dist['request_count']} обращений")
    
    print(f"\n  Всего обращений: {dist['total_requests']}")
    print(f"  Не назначено: {dist['unassigned_requests']}")

# 7. Показать все обращения
print_section("📋 ВСЕ ОБРАЩЕНИЯ (последние 10)")
response = requests.get(f"{BASE_URL}/requests")
if response.status_code == 200:
    all_requests = response.json()
    for req in all_requests[-10:]:
        operator_info = f"→ Оператор #{req['operator_id']}" if req['operator_id'] else "⏳ Ожидает"
        print(f"  #{req['id']}: {req['message'][:40]}... {operator_info}")

print_section("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
print("\n💡 Что дальше:")
print("  • Откройте http://localhost:8000/docs для интерактивной документации")
print("  • Создавайте обращения через API")
print("  • Управляйте операторами (активация/деактивация, изменение лимитов)")
print("  • Настраивайте веса для разных источников")
print("\n📚 Документация: USAGE_GUIDE_RU.md")
print()
