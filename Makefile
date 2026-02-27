# 🐺 CYBERHOUND MAKEFILE
# Common commands for development and deployment

.PHONY: help install install-dev test test-coverage lint format clean run quick dashboard cron-status docker-build docker-run

# Default target
help:
	@echo "🐺 Cyberhound Commands:"
	@echo ""
	@echo "SETUP:"
	@echo "  make install         Install production dependencies"
	@echo "  make install-dev     Install development dependencies"
	@echo "  make setup           Full setup (install + config)"
	@echo ""
	@echo "DEVELOPMENT:"
	@echo "  make run             Run sovereign loop (continuous)"
	@echo "  make quick           Quick hunt (example.com)"
	@echo "  make dashboard       Start web dashboard on port 8080"
	@echo "  make cli             Show CLI dashboard with stats"
	@echo ""
	@echo "TESTING:"
	@echo "  make test            Run all tests"
	@echo "  make test-coverage   Run tests with coverage report"
	@echo "  make lint            Run linting (flake8)"
	@echo "  make format          Format code (black)"
	@echo ""
	@echo "PRODUCTION:"
	@echo "  make cron-run        Run cron hunt once"
	@echo "  make cron-status     Check cron status"
	@echo "  make cron-setup      Interactive cron setup (Linux/Mac)"
	@echo "  make health          Check system health"
	@echo ""
	@echo "DOCKER:"
	@echo "  make docker-build    Build Docker image"
	@echo "  make docker-run      Run in Docker container"
	@echo ""
	@echo "MAINTENANCE:"
	@echo "  make backup          Backup data files"
	@echo "  make clean           Clean up cache and temp files"
	@echo "  make logs            Show recent logs"

# Setup
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install black flake8 mypy pytest pytest-cov

setup: install-dev
	@echo "🐺 Setting up Cyberhound..."
	@mkdir -p hound_core/data/logs
	@mkdir -p hound_core/data/backups
	@if [ ! -f .env ]; then cp .env.example .env; echo "✅ Created .env file"; fi
	@if [ ! -f hound_core/data/targets.txt ]; then \
		echo "# Add your targets here (one per line)" > hound_core/data/targets.txt; \
		echo "✅ Created targets.txt"; \
	fi
	@echo "✅ Setup complete! Edit .env and targets.txt to configure."

# Development
run:
	cd hound_core && python sovereign_loop.py

quick:
	cd hound_core && python sovereign_loop.py --quick example.com

dashboard:
	@echo "🌐 Starting dashboard on http://localhost:8080"
	cd web_dashboard && python -m http.server 8080

cli:
	@python -c "
import sys
sys.path.insert(0, 'hound_core')
from cli_dashboard import show_dashboard
show_dashboard()
"

# Testing
test:
	python run_tests.py -v

test-coverage:
	python run_tests.py --coverage

lint:
	flake8 hound_core/ --max-line-length=120 --ignore=E501,W503

format:
	black hound_core/ --line-length=120

# Production
cron-run:
	cd hound_core && python cron_hunt.py

cron-status:
	@cd hound_core && python cron_hunt.py --status

cron-setup:
	./scripts/setup_cron.sh

health:
	@python -c "
import sys
sys.path.insert(0, 'hound_core')
from health_check import check_health
result = check_health()
sys.exit(0 if result['healthy'] else 1)
"

# Docker
docker-build:
	docker build -t cyberhound:latest .

docker-run:
	docker run -it --rm -v $(PWD)/hound_core/data:/app/hound_core/data cyberhound:latest

# Maintenance
backup:
	@echo "💾 Backing up data..."
	@mkdir -p hound_core/data/backups
	@tar -czf hound_core/data/backups/backup_$$(date +%Y%m%d_%H%M%S).tar.gz -C hound_core/data \
		LE_BUTIN.json pending_strikes.json settled_strikes.json targets.txt 2>/dev/null || true
	@echo "✅ Backup complete"

clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@rm -rf .pytest_cache .mypy_cache htmlcov 2>/dev/null || true
	@echo "✅ Clean complete"

logs:
	@tail -n 50 hound_core/data/logs/cron.log 2>/dev/null || \
		echo "No cron logs found. Run 'make cron-run' first."

# Install cron job (Linux/Mac)
install-cron:
	@echo "0,30 * * * * cd $$(pwd) && $$(which python3) hound_core/cron_hunt.py >> hound_core/data/logs/cron.log 2>&1" | crontab -
	@echo "✅ Cron job installed (runs every 30 minutes)"

# Show stats
stats:
	@python -c "
import sys
import json
from pathlib import Path
sys.path.insert(0, 'hound_core')

butin = Path('hound_core/data/LE_BUTIN.json')
pending = Path('hound_core/data/pending_strikes.json')

print('📊 CYBERHOUND STATS')
print('=' * 50)

if butin.exists():
    data = json.loads(butin.read_text())
    print(f\"Latest Hunt: {data.get('timestamp', 'N/A')}\")
    print(f\"Cycle: #{data.get('cycle', 0)}\")
    print(f\"Strikes Forged: {data.get('strikes_forged', 0)}\")
    print(f\"Pipeline Value: ${data.get('pipeline_value', 0):,}\")
else:
    print('No hunts yet. Run: make quick')

if pending.exists():
    data = json.loads(pending.read_text())
    print(f\"Pending Strikes: {len(data)}\")
print('=' * 50)
"
