from typing import Union
from uuid import UUID

import sqlalchemy as sa

from fastdup.vl.common import logging_init
from fastdup.vldbaccess.connection_manager import get_session, get_engine_dialect
from fastdup.vldbaccess.models import events

logger = logging_init.get_vl_logger(__name__)


class EventDAO:

    @staticmethod
    def store(event: Union[events.Event, events.TransactionalEvent]) -> None:
        if get_engine_dialect() == 'duckdb':
            return
        with get_session(autocommit=True) as session:
            sequence_name = f'event_seq_{event.dataset_id}'.replace('-', '_')
            session.execute(
                sa.text(f'CREATE SEQUENCE IF NOT EXISTS {sequence_name} MINVALUE 0 START WITH 0;')
            )
            try:
                session.execute(
                    sa.text(
                        '''
                        INSERT INTO events (serial_n, dataset_id, event_type, event, trans_id)
                        VALUES (nextval(:sequence_name), :dataset_id, :event_type, (:event)::jsonb, :trans_id);
                        '''
                    ),
                    {
                        'sequence_name': sequence_name,
                        'dataset_id': event.dataset_id,
                        'event_type': event.event_type,
                        'event': event.json(),
                        'trans_id': event.transaction_id if isinstance(event, events.TransactionalEvent) else None
                    }
                )
            except sa.exc.IntegrityError as e:
                logger.warning(f"Trying to store an event for non-existing dataset? {e}")

    @staticmethod
    def filter_last_tx_events(_events: list[events.Event], offset: int):
        assert _events
        assert offset <= len(_events)

        tx_ids: list[int] = list({e.transaction_id for e in _events if isinstance(e, events.TransactionalEvent)})
        if not tx_ids or len(tx_ids) == 1:
            return _events[offset:]

        tx_ids.sort()
        last_tx_id = tx_ids[-1]

        events_reverse_sorted_by_sn = sorted(_events, key=lambda e: e.serial, reverse=True)
        last_tx_events: list[events.Event] = []

        for e in events_reverse_sorted_by_sn:
            if isinstance(e, events.TransactionalEvent):
                if e.transaction_id < last_tx_id:
                    break
                else:
                    last_tx_events.insert(0, e)
            else:
                last_tx_events.insert(0, e)

        assert last_tx_events

        computed_offset = max(offset, last_tx_events[0].serial)
        return [e for e in last_tx_events if e.serial >= computed_offset]

    @staticmethod
    def load(dataset_id: UUID, offset: int = 0) -> list[events.Event]:
        if get_engine_dialect() == 'duckdb':
            return []
        with get_session() as session:
            res_events: list[events.Event] = []
            query_result = session.execute(
                sa.text(
                    '''
                    SELECT
                        *
                    FROM
                        events 
                    WHERE
                        dataset_id = :dataset_id 
                    ORDER BY
                        serial_n;
                    '''
                ),
                {'dataset_id': dataset_id, 'offset': offset}
            )
            for row in query_result.mappings().all():
                event_type = row['event_type']
                event_class = getattr(events, event_type)
                event_instance: events.Event = event_class(**row['event'])
                event_instance.serial = row['serial_n']
                res_events.append(event_instance)

        last_tx_events: list[events.Event] = EventDAO.filter_last_tx_events(res_events, offset)
        return last_tx_events

    @staticmethod
    def load_by_event_type(
            dataset_id: UUID,
            event_type: str,
    ) -> list:
        if get_engine_dialect() == 'duckdb':
            return []
        with get_session() as session:
            query = sa.text(
                '''
                SELECT
                    *
                FROM
                    events 
                WHERE
                    dataset_id = :dataset_id 
                    AND event_type = :event_type
                ORDER BY
                    serial_n
                '''
            )
            query_result = session.execute(
                query,
                {'dataset_id': dataset_id, 'event_type': event_type}
            )
            res_events: list = []
            event_class = getattr(events, event_type)
            for row in query_result.mappings().all():
                event_instance = event_class(**row['event'])
                event_instance.serial = row['serial_n']
                res_events.append(event_instance)

        return res_events

    @staticmethod
    def load_by_event_type_and_transaction(
            dataset_id: UUID,
            transaction_id: int,
            event_type: str,
    ) -> list:
        if get_engine_dialect() == 'duckdb':
            return []
        with get_session() as session:
            query = sa.text(
                '''
                SELECT
                    *
                FROM
                    events 
                WHERE
                    dataset_id = :dataset_id
                    AND trans_id = :trans_id
                    AND event_type = :event_type
                ORDER BY
                    serial_n
                '''
            )
            query_result = session.execute(
                query,
                {'dataset_id': dataset_id, 'event_type': event_type, 'trans_id': transaction_id}
            )
            res_events: list = []
            event_class = getattr(events, event_type)
            for row in query_result.mappings().all():
                event_instance = event_class(**row['event'])
                event_instance.serial = row['serial_n']
                res_events.append(event_instance)

        return res_events

    @staticmethod
    def generate_transaction_id() -> int:
        if get_engine_dialect() == 'duckdb':
            return -1
        with get_session() as session:
            return session.execute(sa.text(
                "SELECT nextval('ingestion_transaction_id_seq')"
            )).fetchone()[0]
