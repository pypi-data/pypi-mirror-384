# 🧩 tp-shared

Общий репозиторий схем для использования в нескольких проектах.

---

## Установка:
`poetry add tp-shared`

## Очистка при обновлении
```
poetry cache clear pypi --all --no-interaction; poetry add tp-shared@latest
```

```
poetry cache clear pypi --all --no-interaction && poetry add tp-shared@latest
```

## Публикация:
Собирает и загружает собранный пакет в PyPI.

`poetry publish --build`

## Структура проекта

**messages** 
-------------------------
Схемы сообщений от сервисов

Пример импорта  

from tp_shared_schemas.messages import GibddDcResultMessage

В каждой папке лежат соответствующие Pydantic-схемы, сгруппированные по функционалу.
--------------------------
---

## Как подключить репозиторий к существующему проекту

Если у вас есть локальный проект и вы хотите добавить репозиторий с общими схемами, выполните команды:
в файле pyproject.toml прописать зависимость:
1) 

```Python
[tool.poetry.dependencies]
tp-shared = { git = "https://gitlab.8525.ru/modules/tp-shared.git", rev = "main" }
```

poetry add git

```python
poetry add git+https://gitlab.8525.ru/modules/tp-shared.git
```

2) Выполнить команду poetry install или poetry update


## Репозиторий
```
cd existing_repo
git remote add origin https://gitlab.8525.ru/modules/tp-shared.git
git branch -M main
git push -uf origin main
```

