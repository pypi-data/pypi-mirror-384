import sqlalchemy as sa

from fastdup.vl.utils.useful_decorators import timed
from fastdup.vldbaccess.base import BaseDB
from fastdup.vldbaccess.connection_manager import get_session


class TagsDB(BaseDB):

    @staticmethod
    @timed
    def new_tag(tag_name: str):
        statement = """
            insert into tags (name) values (:tag_name) RETURNING id;
        """
        with get_session(autocommit=True) as session:
            tag_id = session.execute(sa.text(statement), {"tag_name": tag_name}).one()[0]
        return tag_id

    @staticmethod
    @timed
    def get_tags(tag_ids: list):
        statement = """
            select id, name from tags where id = ANY(:tag_ids);
        """
        with get_session() as session:
            res = session.execute(sa.text(statement), {"tag_ids": tag_ids}).all()
        return res
