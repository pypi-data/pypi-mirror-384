import sqlalchemy as sa
import json

from fastdup.vl.common.settings import Settings
from fastdup.vldbaccess.connection_manager import get_session


class FlowRunSettingsDB:

    @staticmethod
    def create_flow_run_id() -> int:
        with get_session(autocommit=True) as session:
            return session.execute(  # type: ignore
                sa.text('INSERT INTO flow_runs (settings) VALUES (null) RETURNING id;')
            ).one()[0]

    @staticmethod
    def store() -> None:
        if Settings.FLOW_RUN_ID is None:
            Settings.FLOW_RUN_ID = FlowRunSettingsDB.create_flow_run_id()  # type: ignore
        settings_dict: dict = Settings.dump()
        with get_session(autocommit=True) as session:
            session.execute(
                sa.text('UPDATE flow_runs SET settings = :settings WHERE id = :flow_run_id;'),
                {"settings": json.dumps(settings_dict), "flow_run_id": Settings.FLOW_RUN_ID}
            )

    @staticmethod
    def load() -> None:
        with get_session() as session:
            res = session.execute(
                sa.text('SELECT settings FROM flow_runs WHERE id=:flow_run_id'),
                {"flow_run_id": Settings.FLOW_RUN_ID}
            ).one_or_none()
            if res and res[0]:
                settings_dict, = res
                if isinstance(settings_dict, str):
                    settings_dict = json.loads(settings_dict)
                Settings.restore(settings_dict)
