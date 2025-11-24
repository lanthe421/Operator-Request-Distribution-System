# PowerShell скрипт для тестирования Docker

Write-Host "`n🐳 Testing Docker setup...`n" -ForegroundColor Cyan

# Проверка Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker установлен" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не установлен" -ForegroundColor Red
    exit 1
}

# Проверка Docker Compose
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose установлен" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose не установлен" -ForegroundColor Red
    exit 1
}

# Сборка образа
Write-Host "`n📦 Сборка Docker образа...`n" -ForegroundColor Yellow
docker-compose build

# Запуск контейнера
Write-Host "`n🚀 Запуск контейнера...`n" -ForegroundColor Yellow
docker-compose up -d

# Ожидание запуска
Write-Host "`n⏳ Ожидание запуска сервера...`n" -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Проверка health
Write-Host "🏥 Проверка health check..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    Write-Host "✅ Health check passed" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed" -ForegroundColor Red
}

# Проверка API
Write-Host "`n🔍 Проверка API..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/operators" -UseBasicParsing
    Write-Host "✅ API check passed" -ForegroundColor Green
} catch {
    Write-Host "❌ API check failed" -ForegroundColor Red
}

# Логи
Write-Host "`n📋 Последние логи:" -ForegroundColor Cyan
docker-compose logs --tail=20

Write-Host "`n✅ Тестирование завершено!`n" -ForegroundColor Green
Write-Host "Команды:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f    # Смотреть логи"
Write-Host "  docker-compose down       # Остановить"
Write-Host "  docker-compose ps         # Статус"
Write-Host ""
