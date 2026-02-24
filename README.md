# LEGO Robot Builder

Веб-додаток для автоматизованої конфігурації LEGO-роботів із використанням генетичного та жадібного алгоритмів оптимізації.

## Опис

**LEGO Robot Builder** — це full-stack додаток, який дозволяє користувачу задати параметри бажаного робота (функції, бюджет, вагу, пріоритети) та автоматично підібрати оптимальний набір LEGO-компонентів.

### Алгоритми оптимізації

- **Жадібний алгоритм (Greedy)** — послідовно заповнює 8 слотів конфігурації (база, хаб, живлення, привід, модулі, сенсори, структура, аксесуари) з урахуванням обмежень. Працює миттєво (~5 мс).
- **Генетичний алгоритм (GA)** — еволюційний підхід з популяцією особин, кросовером, мутацією та ремонтом цілісності. Знаходить оптимальну конфігурацію за 1–3 секунди.

### Ключові можливості

- Мультикритерійна оціночна система (WSM) з 5 критеріями: швидкість, сила, економія, витривалість, еко
- 5 рівнів складності робота з відповідними профілями обмежень
- Система автентифікації (JWT)
- Порівняльний аналіз алгоритмів (бенчмарк)
- Історія конфігурацій з можливістю збереження та перегляду
- Підтримка доменів: наземний, водний, повітряний

## Технології

### Backend
- **Python 3.12** + **FastAPI**
- **SQLAlchemy** ORM + **SQLite** (з підтримкою PostgreSQL)
- **JWT** автентифікація з bcrypt хешуванням
- **Uvicorn** ASGI-сервер

### Frontend
- **React 19** + **TypeScript**
- **Vite** (збірка та dev-сервер)
- **TailwindCSS** (стилізація)
- **React Router** (навігація)

## Структура проєкту

```
lego-configurator/
├── backend/
│   ├── app/
│   │   ├── api/              # REST API ендпоінти
│   │   │   ├── auth/         # Автентифікація (login, register)
│   │   │   ├── history/      # Історія конфігурацій
│   │   │   ├── routes_config.py      # Конфігурація робота (greedy/genetic)
│   │   │   ├── routes_benchmark.py   # Бенчмарк алгоритмів
│   │   │   ├── routes_analytics.py   # Аналітика
│   │   │   └── routes_components.py  # CRUD компонентів
│   │   ├── services/         # Бізнес-логіка
│   │   │   ├── genetic.py    # Генетичний алгоритм
│   │   │   ├── greedy.py     # Жадібний алгоритм
│   │   │   ├── sequential.py # Послідовний конфігуратор (seed для GA)
│   │   │   ├── scoring.py    # Мультикритерійна оцінка (WSM)
│   │   │   ├── normalization.py  # Min-Max нормалізація
│   │   │   ├── constraints.py    # Профілі складності та обмеження
│   │   │   └── benchmark.py      # Бенчмарк-сервіс
│   │   ├── models/           # ORM-моделі та DTO
│   │   ├── db/               # Підключення до БД, репозиторій
│   │   ├── data/             # JSON-дані компонентів
│   │   └── static/           # Зображення компонентів
│   ├── tests/                # Юніт-тести алгоритмів
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # Сторінки додатку
│   │   ├── components/       # UI-компоненти
│   │   ├── api/              # HTTP-клієнт
│   │   └── types/            # TypeScript типи
│   └── package.json
```

## Запуск

### Передумови

- Python 3.12+
- Node.js 18+
- Git

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Сервер запуститься на `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Додаток буде доступний на `http://localhost:5173`

## API Ендпоінти

| Метод | Шлях | Опис |
|-------|------|------|
| `POST` | `/config/greedy` | Жадібна конфігурація |
| `POST` | `/config/genetic` | Генетична оптимізація |
| `POST` | `/config/genetic/stream` | GA з SSE-прогресом |
| `GET` | `/components/` | Список компонентів |
| `POST` | `/auth/register` | Реєстрація |
| `POST` | `/auth/login` | Автентифікація |
| `GET` | `/history/` | Історія конфігурацій |
| `POST` | `/benchmark/run` | Порівняння алгоритмів |

## Тестування

```bash
cd backend
python -m pytest tests/test_algorithms.py -v
```

Тести покривають: жадібний алгоритм, генетичний алгоритм, обмеження (symmetry, domain filtering, power balance, budget constraints).

## Автор

**Den4ik-art** — [GitHub](https://github.com/Den4ik-art)

## Ліцензія

MIT
