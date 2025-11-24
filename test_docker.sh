#!/bin/bash

echo "🐳 Testing Docker setup..."
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    exit 1
fi
echo "✅ Docker установлен"

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi
echo "✅ Docker Compose установлен"

# Сборка образа
echo ""
echo "📦 Сборка Docker образа..."
docker-compose build

# Запуск контейнера
echo ""
echo "🚀 Запуск контейнера..."
docker-compose up -d

# Ожидание запуска
echo ""
echo "⏳ Ожидание запуска сервера..."
sleep 10

# Проверка health
echo ""
echo "🏥 Проверка health check..."
curl -f http://localhost:8000/health || echo "❌ Health check failed"

# Проверка API
echo ""
echo "🔍 Проверка API..."
curl -f http://localhost:8000/api/v1/operators || echo "❌ API check failed"

# Логи
echo ""
echo "📋 Последние логи:"
docker-compose logs --tail=20

echo ""
echo "✅ Тестирование завершено!"
echo ""
echo "Команды:"
echo "  docker-compose logs -f    # Смотреть логи"
echo "  docker-compose down       # Остановить"
echo "  docker-compose ps         # Статус"
