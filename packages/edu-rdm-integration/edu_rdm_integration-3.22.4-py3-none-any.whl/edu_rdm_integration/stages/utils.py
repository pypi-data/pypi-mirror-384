from django.db import (
    connection,
)


def update_foreign_key_constraint(
    table_name: str,
    field_name: str,
    target_table: str,
    on_delete: str,
):
    """
    Обновляет внешний ключ (FOREIGN KEY) в PostgreSQL.

    Выполняет:
      1. Поиск существующего constraint'а по таблице и целевой модели.
      2. Удаление найденного constraint'а.
      3. Создание нового constraint'а с заданным ON DELETE.

    Args:
        table_name (str): Имя таблицы, содержащей внешний ключ.
        field_name (str): Имя поля внешнего ключа.
        target_table (str): Таблица, на которую указывает внешний ключ.
        on_delete (str): Поведение при удалении связанной записи.
    """
    with connection.cursor() as cursor:
        # Найти имя constraint'а
        cursor.execute(f"""
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = '{table_name}'::regclass
              AND confrelid = '{target_table}'::regclass
              AND contype = 'f'
        """)
        row = cursor.fetchone()
        if not row:
            return

        constraint_name = row[0]

        # Удалить старый constraint, Добавить новый constraint с нужным ON DELETE
        cursor.execute(f'''
            ALTER TABLE "{table_name}"
            DROP CONSTRAINT IF EXISTS "{constraint_name}",
            ADD CONSTRAINT "{constraint_name}"
            FOREIGN KEY ("{field_name}")
            REFERENCES "{target_table}"(id)
            ON DELETE {on_delete};
        ''')
