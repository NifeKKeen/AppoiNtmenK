# 🧑‍💻 Что мы сделали — объяснение для начинающего

## Обзор: 3 больших изменения

Мы сделали **три крупных задачи**:

1. **Объединили User и Specialist** — убрали старое поле `role` (текст "USER"/"SPECIALIST"), заменили на простой `is_specialist = True/False`
2. **Переименовали модель** `Specialist` → `SpecialistDetails` (таблица в базе данных тоже переименовалась)
3. **Переделали фронтенд** — убрали хардкод ролей специалистов, добавили страницу "Чаты", обновили навбар

---

## 1️⃣ Замена `role` на `is_specialist`

### Зачем?

Раньше у пользователя было поле `role` с двумя вариантами: `"USER"` или `"SPECIALIST"`. Это лишнее — достаточно простого булеана `True`/`False`.

### Что изменили (бэкенд)

| Файл | Что сделали |
|------|------------|
| `backend/core/models.py` | Убрали `class Role`, `role = CharField(...)`, `@property is_specialist`. Добавили `is_specialist = BooleanField(default=False)` |
| `backend/core/serializers.py` | Везде заменили `user.role == User.Role.SPECIALIST` на `user.is_specialist`. Убрали `'role'` из полей сериализаторов |
| `backend/core/views.py` | В `IsSpecialistPermission` заменили `user.role == User.Role.SPECIALIST` на `user.is_specialist` |
| `backend/core/admin.py` | В `list_display` и `list_filter` заменили `'role'` на `'is_specialist'` |
| `backend/core/tests.py` | Все `User.Role.SPECIALIST` → `is_specialist=True`, все `User.Role.USER` → `assertFalse(user.is_specialist)` |

### Что изменили (фронтенд)

| Файл | Что сделали |
|------|------------|
| `auth.service.ts` | Убрали `role: 'USER' \| 'SPECIALIST'` из интерфейса `UserProfile` |
| `chat.service.ts` | Заменили `sender_role: 'USER' \| 'SPECIALIST'` на `sender_is_specialist: boolean` |
| `chat.component.html` | `msg.sender_role === 'SPECIALIST'` → `msg.sender_is_specialist` |

### Команда для миграции

```bash
python manage.py makemigrations core
python manage.py migrate
```

Django создал файл миграции:
```
backend/core/migrations/0005_remove_user_role_user_is_specialist.py
```

> ⚠️ Мы вручную отредактировали эту миграцию, чтобы она:
> 1. Сначала добавила новое поле `is_specialist`
> 2. Скопировала данные (`role='SPECIALIST'` → `is_specialist=True`)
> 3. Потом удалила старое поле `role`

Это важно, потому что без этого шага все существующие специалисты потеряли бы свой статус!

---

## 2️⃣ Переименование `Specialist` → `SpecialistDetails`

### Зачем?

Раньше модель называлась `Specialist` — это звучит как отдельная сущность. Но на самом деле это **детали профиля** пользователя, который является специалистом. Поэтому переименовали в `SpecialistDetails`.

### Какие файлы затронули

Пришлось обновить **каждый файл**, который импортирует или использует `Specialist`:

| Файл | Было | Стало |
|------|------|-------|
| `models.py` | `class Specialist(models.Model)` | `class SpecialistDetails(models.Model)` |
| `serializers.py` | `from .models import Specialist` | `from .models import SpecialistDetails` |
| `views.py` | `Specialist.objects.filter(...)` | `SpecialistDetails.objects.filter(...)` |
| `admin.py` | `@admin.register(Specialist)` | `@admin.register(SpecialistDetails)` |
| `tests.py` | `Specialist.objects.create(...)` | `SpecialistDetails.objects.create(...)` |
| `google_calendar.py` | `specialist: Specialist` | `specialist: SpecialistDetails` |
| `seed_specialists.py` | `Specialist.objects.update_or_create(...)` | `SpecialistDetails.objects.update_or_create(...)` |

### Команда для миграции

```bash
python manage.py makemigrations core
```

Django спросил: `Was the model core.Specialist renamed to SpecialistDetails? [y/N]` — мы ответили `y`.

```bash
python manage.py migrate
```

Результат — файл:
```
backend/core/migrations/0006_rename_specialist_specialistdetails_and_more.py
```

> 💡 Фронтенд НЕ менялся — в Angular `Specialist` это просто интерфейс TypeScript, он не связан с названием модели Django.

---

## 3️⃣ Фронтенд: свободные роли, страница чатов, навбар

### А) Убрали хардкод ролей специалистов

Раньше при регистрации специалист мог выбрать только 3 роли из списка:
- `Math Whisperer`
- `Tourist-Consultant`  
- `Code Debugger`

Мы заменили **dropdown (выпадающий список)** на **текстовое поле**, где можно написать что угодно.

| Файл | Что сделали |
|------|------------|
| `backend/core/serializers.py` | Убрали `SPECIALIST_ROLE_OPTIONS`. Заменили `ChoiceField` на `CharField(max_length=200)` |
| `register.component.ts` | Убрали массив `specialistRoles` |
| `register.component.html` | `<select>` → `<input type="text" placeholder="e.g. Code Debugger, Math Tutor">` |
| `dashboard.component.html` | То же самое для формы "стать специалистом" |

### Б) Создали страницу "Чаты"

Раньше кнопка "Chat" была прямо в карточке каждой записи на дашборде. Мы убрали её оттуда и создали отдельную страницу `/chats`, куда ведёт новая вкладка в навбаре.

#### Новые файлы (новая папка `chat-list/`):

```
frontend/src/app/features/chat-list/
├── chat-list.component.ts    ← логика: загружает записи и запросы
├── chat-list.component.html  ← шаблон: список карточек-разговоров
└── chat-list.component.css   ← стили: тёмная тема, анимации
```

**Что делает эта страница:**
- Загружает ваши записи (appointments) — показывает их как карточки с именем специалиста
- Если вы специалист — загружает ещё и входящие запросы (specialist inbox)
- Каждая карточка — это ссылка на `/chat/:id`

### В) Обновили навбар

| Было | Стало |
|------|-------|
| Отдельная вкладка для каждого специалиста (`🧠 Adilet`, `💻 Nuridin` и т.д.) | Одна вкладка `👥 Specialists` |
| Нет вкладки чатов | Новая вкладка `💬 Chats` |

**Файлы:**

| Файл | Что сделали |
|------|------------|
| `navbar.component.html` | Убрали `@for (spec of specialists)`, добавили ссылки на `/specialists` и `/chats` |
| `navbar.component.ts` | Убрали `SpecialistService`, массив `specialists[]` и весь код загрузки списка |
| `app.routes.ts` | Добавили маршрут `{ path: 'chats', component: ChatListComponent }` |

---

## 📋 Итого: все команды, которые мы использовали

```bash
# 1. Создать миграцию (убрать role, добавить is_specialist)
python manage.py makemigrations core

# 2. Применить миграцию к базе данных
python manage.py migrate

# 3. Создать миграцию (переименование Specialist → SpecialistDetails)
python manage.py makemigrations core
# Django спрашивает "Was the model renamed?" — отвечаем y

# 4. Применить эту миграцию тоже
python manage.py migrate

# 5. Запустить тесты (проверить что всё работает)
python manage.py test core -v2

# 6. Проверить сборку Angular
npx ng build
```

## 📂 Новые файлы и папки

```
📁 Новая папка:
  frontend/src/app/features/chat-list/

📄 Новые файлы:
  frontend/src/app/features/chat-list/chat-list.component.ts
  frontend/src/app/features/chat-list/chat-list.component.html
  frontend/src/app/features/chat-list/chat-list.component.css
  backend/core/migrations/0005_remove_user_role_user_is_specialist.py
  backend/core/migrations/0006_rename_specialist_specialistdetails_and_more.py
```

## 🔑 Главное на что обратить внимание

1. **Миграции** — это инструкции Django для изменения структуры базы данных. Каждый раз, когда мы меняем `models.py`, нужно запускать `makemigrations` и `migrate`
2. **При переименовании моделей** надо обновить ВСЕ файлы, которые их используют — это кропотливая работа
3. **Фронтенд и бэкенд** — независимы. TypeScript интерфейсы (`Specialist`) не обязаны совпадать с именами Django моделей (`SpecialistDetails`)
4. **При изменении API ответа** (например `sender_role` → `sender_is_specialist`) нужно обновить и бэкенд, и фронтенд одновременно
