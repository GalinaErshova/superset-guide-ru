# Состояние

## Решения

- ЦА: аналитики, создающие дашборды; начало с работающей установки Superset.
- Пользователь выбрала GitHub Pages, как codex.galaershova.ru. Целевой домен superset.galaershova.ru.
- Пользователь заменила A-запись на CNAME GalinaErshova.github.io; DNS подтверждён. Развёртывание на Alex отменено.
- Короткие статусы: Стабильно / Превью / Эксперимент. Тематические подборки: темы, CSS, AI/MCP/Codex.
- Стенд Superset не подключался. Материал Codex объясняет возможное подключение, не выдаёт его за готовое.
- Новости редактируются и публикуются через Git; расписание не настраивалось.
- Пустой приватный проект Sites был зарегистрирован до выбора хостинга; не публиковался, конфигурация исключена из Git.

## Выполнено

- 23 материала: 8 уроков, 5 экспериментов, справочные рецепты и релизы; 30 HTML-страниц.
- Учебный CSV, поиск по полному тексту, фильтры, тематические подборки, журнал, Atom, sitemap.
- PR #1, отдельная ветка codex/superset-guide. В main изменений не вносили.
- Источники сверены 06.11.2026; AI_ASSISTANT — открытый PR, MCP зависит от сборки и отдельной настройки.

## Проверки

- Сборка, все внутренние ссылки/якоря, структура страниц, CSV (итоги, месяцы, регионы), JSON и XML: PASS.
- JavaScript syntax: PASS. В браузере проверены каталог, фильтры/пустое состояние, поиск MCP и мобильное меню.
- Прямой SSH на Alex недоступен с ноутбука; теперь не нужен, поскольку выбран GitHub Pages.
- Полное прохождение уроков на живом Superset не выполнено.
- Широкий экран 1440 px и мобильный 390 px: горизонтального переполнения нет; меню, поиск и фильтры работают.
- Независимое ревью: два P2 исправлены в a5dd5cf (даты Atom/sitemap и единый источник релизов); повторное ревью исправлений — принято. test_updates.py — PASS.
- Дополнительное ревью nordik-claude запрошено для a5dd5cf; ответа пока нет.

## Публикация

- Репозиторий: https://github.com/GalinaErshova/superset-guide-ru, PR https://github.com/GalinaErshova/superset-guide-ru/pull/1.
- GitHub Pages настроен на gh-pages и superset.galaershova.ru. После замены DNS сайт по HTTP возвращает 200 с сервера GitHub.
- По прямому поручению пользователя добавлена Метрика 114109969 с предоставленными настройками, включая Вебвизор. Исходники a52466e, сборка в gh-pages 1cbfba1. Проверены единственная инициализация и noscript внутри body на всех 30 страницах; build/validate/test_updates — PASS.
- Дополнительное ревью счётчика отправлено nordik-claude; ответ ожидается.
- Публикация сборки с Метрикой завершилась; наличие инициализации 114109969 подтверждено в HTML публичной страницы. Получение визитов в кабинете Метрики не проверялось.
- Сертификата HTTPS ещё нет: API GitHub отклонил включение https_enforced с ответом «The certificate does not exist yet». Проверка TLS не отключалась.

## SEO

- Уникальные title/description и canonical дополнены robots, автором, Open Graph, Twitter Card и JSON-LD WebSite/WebPage/Article/BreadcrumbList. Статьи используют редакционные даты.
- Поиск и 404: noindex, follow; sitemap содержит только 28 индексируемых адресов. Страниц по-прежнему 30.
- Сборка, проверки метаданных всех страниц, JSON-LD, sitemap, ссылок и регрессионные проверки дат — PASS. Проверки Google Rich Results и Search Console не выполнялись.
- SEO-исходники: 18f9d2d, публикация gh-pages: 1c1391f. GitHub Pages run 42237450334 завершился успешно. На публичной статье /guide/performance/ подтверждены JSON-LD и Метрика 114109969. CNAME корректен. Сертификат по повторной проверке ещё отсутствует; GitHub вновь отклонил https_enforced с «The certificate does not exist yet». Ревью nordik-claude запрошено отдельно.

## Восстановление выпуска HTTPS — 06.11.2026

- GitHub Pages health подтвердил is_valid=true, is_https_eligible=true, caa_error=null. CNAME и конечные A/AAAA ведут на GitHub Pages; CAA разрешает letsencrypt.org. Блокирующих ошибок DNS не обнаружено.
- После первоначальной настройки Pages до смены A на CNAME заявка на сертификат отсутствовала. Причина зависания предположительно связана с первой DNS-проверкой; внутреннего журнала GitHub нет.
- В 17:11 по Берлину выполнено рекомендованное GitHub снятие и немедленное восстановление того же custom domain через API. DNS не менялся. CNAME восстановлен, локальная gh-pages синхронизирована с автоматическими коммитами GitHub до 807be64.
- Новый Pages run 42250032560 завершился успешно. Появился https_certificate.state=authorization_created; раньше объекта https_certificate не было. Выпуск перезапущен, но сертификат ещё не установлен и https_enforced=false.
- Инструкция: https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https#troubleshooting-certificate-provisioning-certificate-not-yet-created-error

## Следующий шаг

Проверить сертификат и включить HTTPS после выпуска. Проверить ответ nordik-claude. Стенд Superset подключать отдельной задачей после получения адреса и версии.
