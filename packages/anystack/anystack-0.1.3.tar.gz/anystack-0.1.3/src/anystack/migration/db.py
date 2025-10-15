from pathlib import Path
from typing import override

from .base import BaseMigration, MigrationData
from ..protocol.db import DB


class DBMigration(BaseMigration):
    db: DB
    migration: list[MigrationData]
    table_name: str

    def __init__(
        self,
        db: DB,
        migration: list[MigrationData] | str | Path,
        table_name: str = "migrations",
    ):
        self.db = db
        self.migration = self._load_migration(migration)
        self.table_name = table_name

    def _load_migration(
        self, dir_path: list[MigrationData] | str | Path
    ) -> list[MigrationData]:
        if isinstance(dir_path, list):
            return dir_path
        data: list[MigrationData] = []
        sql_files = sorted(Path(dir_path).glob("*.sql"))
        for file in sql_files:
            with open(file, "r") as f:
                data.append(
                    MigrationData(
                        version=file.stem,
                        sql=f.read(),
                        description=file.stem,
                    )
                )
        return data

    def _split_sql_statements(self, sql: str) -> list[str]:
        statements: list[str] = []
        current_statement: list[str] = []
        in_string = False
        in_dollar_quote = False
        string_char: str | None = None
        dollar_tag: str | None = None
        
        lines = sql.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped or stripped.startswith('--'):
                continue
            
            i = 0
            while i < len(line):
                char = line[i]
                
                if not in_dollar_quote:
                    if char in ("'", '"') and (i == 0 or line[i-1] != '\\'):
                        if not in_string:
                            in_string = True
                            string_char = char
                        elif char == string_char:
                            in_string = False
                            string_char = None
                
                if not in_string and char == '$':
                    tag_end = i + 1
                    while tag_end < len(line) and (line[tag_end].isalnum() or line[tag_end] == '_'):
                        tag_end += 1
                    if tag_end < len(line) and line[tag_end] == '$':
                        tag = line[i:tag_end+1]
                        if not in_dollar_quote:
                            in_dollar_quote = True
                            dollar_tag = tag
                            i = tag_end
                        elif tag == dollar_tag:
                            in_dollar_quote = False
                            dollar_tag = None
                            i = tag_end
                
                if not in_string and not in_dollar_quote and char == ';':
                    current_statement.append(line[:i+1])
                    statement = '\n'.join(current_statement).strip()
                    if statement:
                        statements.append(statement)
                    current_statement = []
                    if i + 1 < len(line):
                        line = line[i+1:]
                        i = -1
                    else:
                        break
                
                i += 1
            else:
                if current_statement or line.strip():
                    current_statement.append(line)
        
        if current_statement:
            statement = '\n'.join(current_statement).strip()
            if statement:
                statements.append(statement)
        
        return statements

    async def init_table_and_get_index(self) -> int:
        _ = await self.db.sql(
            f"CREATE TABLE IF NOT EXISTS {self.table_name} (id INTEGER PRIMARY KEY, version TEXT NOT NULL)"
        )
        migration_index = await self.db.sql(f"SELECT COUNT(*) as count FROM {self.table_name}")
        return (migration_index.rows[0]["count"] or 0) if migration_index.rows else 0

    @override
    async def up(self) -> None:
        index = await self.init_table_and_get_index()
        for migration in self.migration[index:]:
            async with self.db.transaction() as conn:
                statements = self._split_sql_statements(migration.sql)
                for statement in statements:
                    if statement.strip():
                        _ = await conn.sql(statement)
                _ = await conn.sql(
                    f"INSERT INTO {self.table_name} (version) VALUES (:version)",
                    {"version": migration.version},
                )
