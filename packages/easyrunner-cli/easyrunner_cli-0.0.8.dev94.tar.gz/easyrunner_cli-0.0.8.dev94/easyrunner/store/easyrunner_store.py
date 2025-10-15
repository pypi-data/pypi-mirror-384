import json
from typing import List, Optional

from ... import logger
from .data_models import Server
from .db_config import DbConfig
from .db_ctx import DbCtx
from .object_id import ObjectId


class EasyRunnerStore:

    def __init__(self, db_config: Optional[DbConfig] = None):
        self.db_config: DbConfig = db_config or DbConfig()  # default config
        self.database_name: str = "easyrunner"
        self._init_db()

    def _init_db(self):
        with DbCtx(db_config=self.db_config, database_name=self.database_name) as db:
            db.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS servers (
                    id CHAR(36) PRIMARY KEY, -- UUIDv7
                    json_data JSON NOT NULL
                )
                """
            )
            db.conn.commit()

    # Server CRUD
    def add_server(self, server: Server) -> Server:

        with DbCtx(db_config=self.db_config, database_name=self.database_name) as db:
            db.conn.execute(
                "INSERT INTO servers (id, json_data) VALUES (?, ?)",
                (str(server.id), server.to_json_str()),
            )
            db.conn.commit()
            logger.debug(
                f"Server '{server.name}' with Hostname/IP: {server.hostname_or_ip} and ID: '{server.id}' added to the database."
            )
            return server

    def get_server_by_id(self, server_id: ObjectId) -> Optional[Server]:
        with DbCtx(db_config=self.db_config, database_name=self.database_name) as db:
            cur = db.conn.execute(
                "SELECT id, json_data FROM servers WHERE id = ?", (str(server_id),)
            )
            row = cur.fetchone()
            return Server.from_json_str(row["json_data"]) if row else None

    def get_server_by_hostname_or_ip(self, hostname_or_ip: str) -> Optional[Server]:
        with DbCtx(db_config=self.db_config, database_name=self.database_name) as db:
            cur = db.conn.execute(
                "SELECT id, json_data FROM servers WHERE json_extract(json_data, '$.hostname_or_ip') = ?",
                (hostname_or_ip,),
            )
            row = cur.fetchone()
            return Server.from_json_str(row["json_data"]) if row else None

    def get_server_by_name(self, name: str) -> Optional[Server]:
        with DbCtx(db_config=self.db_config, database_name=self.database_name) as db:
            cur = db.conn.execute(
                "SELECT id, json_data FROM servers WHERE json_extract(json_data, '$.name') = ?",
                (name,),
            )
            row = cur.fetchone()
            return Server.from_json_str(row["json_data"]) if row else None

    def list_servers(self) -> List[Server]:
        with DbCtx(db_config=self.db_config, database_name=self.database_name) as db:
            cur = db.conn.execute("SELECT id, json_data FROM servers")
            return [
                Server.from_json_str(row["json_data"])
                for row in cur.fetchall()
                if row["json_data"]
            ]

    def remove_server(self, server_id: ObjectId) -> None:
        with DbCtx(db_config=self.db_config, database_name=self.database_name) as db:
            db.conn.execute("DELETE FROM servers WHERE id = ?", (str(server_id),))
            db.conn.commit()

    def update_server(self, server: Server) -> None:
        with DbCtx(db_config=self.db_config, database_name=self.database_name) as db:
            db.conn.execute(
                "UPDATE servers SET json_data = ? WHERE id = ?",
                (json.dumps(server.to_json()), str(server.id)),
            )
            db.conn.commit()
