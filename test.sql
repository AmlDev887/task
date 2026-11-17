-- ============================================================
-- Тестовые данные для Task Manager API (PostgreSQL), версия 2
-- В файле нет знака доллара и блоков DO: так он работает даже в тех
-- редакторах (VS Code, DBeaver), которые режут скрипт по точке с запятой.
--
-- Запуск:  psql -U <user> -d <база> -f seed.sql
-- Пароль у ВСЕХ пользователей: Test12345
-- Файл ничего не удаляет. Второй запуск упадёт на повторе email и откатится целиком.
-- Если в консоли красная ошибка "транзакция прервана", выполни ROLLBACK; и
-- ищи ПЕРВУЮ ошибку выше: остальные только её следствие.
-- ============================================================

BEGIN;

-- ---------- 1. Пользователи ----------
-- role: 'admin' или 'user' (маленькими буквами)
-- Хеш пароля хранится как E'...' строка: символ доллара записан кодом \044
INSERT INTO users (email, full_name, hashed_password, role, is_active, is_verified)
SELECT v.email, v.full_name, pw.h, v.role::user_role_enum, true, v.verified
FROM (SELECT E'\044argon2id\044v=19\044m=65536,t=3,p=4\0447SApbUOI83RBsQsZaYhFgA\0449HPHeqwp9I19mjXo72N4E1bNNryWeCUqnIift1ID2i8' AS h) AS pw
CROSS JOIN (VALUES
 ('admin@example.com',  'Админ Админов',           'admin', true),
 ('ali@example.com',    'Ali Karimov',             'user',  true),
 ('vali@example.com',   'Vali Rahimov',            'user',  true),
 ('sardor@example.com', 'Sardor Aliyev',           'user',  true),
 ('newbie@example.com', 'Новичок Неподтверждённый','user',  false)
) AS v(email, full_name, role, verified);

-- ---------- 2. Проекты ----------
INSERT INTO projects (name, description, owner_id) VALUES
 ('CRM tizimi', 'Внутренняя CRM для отдела продаж',
    (SELECT id FROM users WHERE email = 'ali@example.com')),
 ('Mobil ilova', 'Мобильное приложение для клиентов',
    (SELECT id FROM users WHERE email = 'vali@example.com'));

-- ---------- 3. Участники проектов ----------
-- role в project_members пишется ЗАГЛАВНЫМИ: 'OWNER', 'EDITOR', 'VIEWER'
INSERT INTO project_members (project_id, user_id, role)
SELECT p.id, u.id, m.role::project_role
FROM (VALUES
    ('CRM tizimi',  'ali@example.com',    'OWNER'),
    ('CRM tizimi',  'vali@example.com',   'EDITOR'),
    ('CRM tizimi',  'sardor@example.com', 'VIEWER'),
    ('Mobil ilova', 'vali@example.com',   'OWNER'),
    ('Mobil ilova', 'ali@example.com',    'EDITOR')
) AS m(project, email, role)
JOIN projects p ON p.name  = m.project
JOIN users    u ON u.email = m.email;

-- ---------- 4. Теги ----------
INSERT INTO tags (name, color) VALUES
 ('backend',  '#2563eb'),
 ('frontend', '#16a34a'),
 ('bug',      '#dc2626'),
 ('urgent',   '#f59e0b');

SELECT enumlabel
FROM pg_enum
WHERE enumtypid = 'task_status_enum'::regtype
ORDER BY enumsortorder;
-- ---------- 5. Задачи ----------
-- status: todo | in_progress | r   eview | done | cancelled
-- priority: low | medium | high | urgent
-- is_deleted и version заполняются вручную (в таблице нет значений по умолчанию)
INSERT INTO tasks (title, description, status, priority, due_date, project_id,
                   creator_id, assignee_id, completed_at, deleted_at, is_deleted, version)
SELECT t.title, t.descr, t.status::task_status_enum, t.priority::task_priority_enum,
       CURRENT_DATE + t.days, p.id, c.id, a.id, t.completed_at, t.deleted_at, t.is_deleted, 1
FROM (VALUES
 ('CRM tizimi',  'Настроить авторизацию',              'JWT access и refresh',                    'done',        'high',   -5, 'ali@example.com',  'vali@example.com', now() - interval '4 days', NULL::timestamptz, false),
 ('CRM tizimi',  'Список клиентов с фильтрами',        'Пагинация, поиск и сортировка',           'in_progress', 'medium',  2, 'ali@example.com',  'vali@example.com', NULL::timestamptz, NULL::timestamptz, false),
 ('CRM tizimi',  'Исправить ошибку экспорта в Excel',  'Просрочена: для проверки overdue=true',   'todo',        'urgent', -2, 'ali@example.com',  'vali@example.com', NULL::timestamptz, NULL::timestamptz, false),
 ('CRM tizimi',  'Дизайн дашборда',                    NULL,                                      'review',      'low',     5, 'vali@example.com', 'ali@example.com',  NULL::timestamptz, NULL::timestamptz, false),
 ('CRM tizimi',  'Письмо-напоминание клиентам',        'Срок сегодня: попадает в дайджест',       'todo',        'high',    0, 'ali@example.com',  'ali@example.com',  NULL::timestamptz, NULL::timestamptz, false),
 ('CRM tizimi',  'Старая идея (удалена)',              'Мягко удалённая: для проверки restore',   'cancelled',   'low',   -10, 'ali@example.com',  NULL,               NULL::timestamptz, now() - interval '1 day', true),
 ('Mobil ilova', 'Экран входа',                        NULL,                                      'in_progress', 'high',    3, 'vali@example.com', 'ali@example.com',  NULL::timestamptz, NULL::timestamptz, false),
 ('Mobil ilova', 'Push-уведомления',                   NULL,                                      'todo',        'medium', 10, 'vali@example.com', NULL,               NULL::timestamptz, NULL::timestamptz, false),
 ('Mobil ilova', 'Публикация в сторах',                'Срок завтра: для напоминания за 24 часа', 'todo',        'urgent',  1, 'vali@example.com', 'vali@example.com', NULL::timestamptz, NULL::timestamptz, false)
) AS t(project, title, descr, status, priority, days, creator, assignee, completed_at, deleted_at, is_deleted)
JOIN projects p ON p.name  = t.project
JOIN users    c ON c.email = t.creator
LEFT JOIN users a ON a.email = t.assignee;

-- ---------- 6. Теги задач ----------
-- в таблице task_tags колонка называется tags_id (а не tag_id)
INSERT INTO task_tags (task_id, tags_id)
SELECT t.id, g.id
FROM (VALUES
 ('Настроить авторизацию',             'backend'),
 ('Список клиентов с фильтрами',       'backend'),
 ('Список клиентов с фильтрами',       'frontend'),
 ('Исправить ошибку экспорта в Excel', 'bug'),
 ('Исправить ошибку экспорта в Excel', 'urgent'),
 ('Дизайн дашборда',                   'frontend'),
 ('Экран входа',                       'frontend')
) AS x(task, tag)
JOIN tasks t ON t.title = x.task
JOIN tags  g ON g.name  = x.tag;

-- ---------- 7. Комментарии ----------
INSERT INTO comments (task_id, author_id, body)
SELECT t.id, u.id, x.body
FROM (VALUES
 ('Список клиентов с фильтрами',       'ali@example.com',    'Начни с фильтра по статусу.'),
 ('Список клиентов с фильтрами',       'vali@example.com',   'Хорошо, сделаю. @ali@example.com посмотришь после?'),
 ('Исправить ошибку экспорта в Excel', 'sardor@example.com', 'Воспроизводится на больших таблицах.'),
 ('Экран входа',                       'vali@example.com',   'Макет утверждён.')
) AS x(task, email, body)
JOIN tasks t ON t.title = x.task
JOIN users u ON u.email = x.email;

-- ---------- 8. История изменений ----------
INSERT INTO task_history (user_id, task_id, field, old_value, new_value)
SELECT u.id, t.id, x.field, x.old_value, x.new_value
FROM (VALUES
 ('ali@example.com',  'Настроить авторизацию',             'status',      'todo',        'in_progress'),
 ('vali@example.com', 'Настроить авторизацию',             'status',      'in_progress', 'done'),
 ('ali@example.com',  'Список клиентов с фильтрами',       'priority',    'low',         'medium'),
 ('ali@example.com',  'Исправить ошибку экспорта в Excel', 'assignee_id', NULL,          'vali')
) AS x(email, task, field, old_value, new_value)
JOIN users u ON u.email = x.email
JOIN tasks t ON t.title = x.task;

-- ---------- 9. (необязательно) Твой существующий пользователь ----------
-- Раскомментируй и замени ВАШ_EMAIL на email, под которым ты уже зарегистрирован.
-- Он станет подтверждённым и получит доступ к обоим тестовым проектам.
--
-- UPDATE users SET is_verified = true WHERE email = 'ВАШ_EMAIL';
--
-- INSERT INTO project_members (project_id, user_id, role)
-- SELECT p.id, u.id, 'EDITOR'::project_role
-- FROM projects p, users u
-- WHERE p.name IN ('CRM tizimi', 'Mobil ilova') AND u.email = 'ВАШ_EMAIL'
-- ON CONFLICT (project_id, user_id) DO NOTHING;

COMMIT;

ROLLBACK;


-- 1. колонка с опечаткой
ALTER TABLE task_history RENAME COLUMN use_id TO user_id;

-- 2. значения статусов и приоритетов строчными
ALTER TYPE task_status_enum RENAME VALUE 'TODO'        TO 'todo';
ALTER TYPE task_status_enum RENAME VALUE 'IN_PROGRESS' TO 'in_progress';
ALTER TYPE task_status_enum RENAME VALUE 'REVIEW'      TO 'review';
ALTER TYPE task_status_enum RENAME VALUE 'DONE'        TO 'done';
ALTER TYPE task_status_enum RENAME VALUE 'CANCELLED'   TO 'cancelled';

ALTER TYPE task_priority_enum RENAME VALUE 'LOW'    TO 'low';
ALTER TYPE task_priority_enum RENAME VALUE 'MEDIUM' TO 'medium';
ALTER TYPE task_priority_enum RENAME VALUE 'HIGH'   TO 'high';
ALTER TYPE task_priority_enum RENAME VALUE 'URGENT' TO 'urgent';