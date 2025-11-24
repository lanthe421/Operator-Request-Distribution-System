"""Быстрая демонстрация работы системы"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("\n" + "="*70)
print("  🎯 БЫСТРАЯ ДЕМОНСТРАЦИЯ СИСТЕМЫ")
print("="*70 + "\n")

# Статистика загрузки
print("📊 ЗАГРУЗКА ОПЕРАТОРОВ:\n")
response = requests.get(f"{BASE_URL}/stats/operators-load")
stats = response.json()
operators_list = stats if isinstance(stats, list) else stats.get('operators', [])
for op in operators_list[:5]:  # Показать первых 5
    bar = "█" * int(op['load_percentage'] / 10) + "░" * (10 - int(op['load_percentage'] / 10))
    print(f"  {op['operator_name']:20} [{bar}] {op['load_percentage']:5.1f}% ({op['current_load']}/{op['max_load_limit']})")

# Распределение
print("\n📈 РАСПРЕДЕЛЕНИЕ ОБРАЩЕНИЙ:\n")
response = requests.get(f"{BASE_URL}/stats/requests-distribution")
dist = response.json()
print(f"  Всего обращений: {dist['total_requests']}")
print(f"  Не назначено: {dist['unassigned_requests']}")
print(f"\n  По операторам:")
for op in dist['by_operator'][:5]:
    print(f"    • {op['operator_name']}: {op['request_count']} обращений")

print("\n" + "="*70)
print("  ✅ СИСТЕМА РАБОТАЕТ!")
print("="*70)
print("\n📖 Документация: http://localhost:8000/docs")
print("📚 Руководство: USAGE_GUIDE_RU.md\n")
