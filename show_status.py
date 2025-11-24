"""Показать текущий статус системы"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

try:
    # Проверка здоровья
    health = requests.get("http://localhost:8000/health", timeout=2)
    if health.status_code != 200:
        print("❌ Сервер не отвечает")
        exit(1)
    
    print("\n" + "="*70)
    print("  ✅ СИСТЕМА РАБОТАЕТ")
    print("="*70 + "\n")
    
    # Статистика
    stats = requests.get(f"{BASE_URL}/stats/operators-load", timeout=2).json()
    dist = requests.get(f"{BASE_URL}/stats/requests-distribution", timeout=2).json()
    
    print(f"📊 Операторов: {len(stats)}")
    print(f"📨 Обращений: {dist['total_requests']}")
    print(f"⏳ Не назначено: {dist['unassigned_requests']}")
    
    print("\n🔝 Топ-3 загруженных оператора:\n")
    sorted_ops = sorted(stats, key=lambda x: x['load_percentage'], reverse=True)[:3]
    for i, op in enumerate(sorted_ops, 1):
        bar = "█" * int(op['load_percentage'] / 10) + "░" * (10 - int(op['load_percentage'] / 10))
        print(f"  {i}. {op['operator_name']:20} [{bar}] {op['load_percentage']:5.1f}%")
    
    print("\n" + "="*70)
    print("  🌐 http://localhost:8000/docs")
    print("="*70 + "\n")
    
except requests.exceptions.ConnectionError:
    print("\n❌ Сервер не запущен!")
    print("   Запустите: python main.py\n")
except Exception as e:
    print(f"\n❌ Ошибка: {e}\n")
