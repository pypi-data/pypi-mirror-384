import logging
from importlib import import_module

# from flask_login import current_user
try:
    flask_login = import_module("flask_login")
except ImportError as e:
    raise Exception(f"flask_login is not exist,run:pip install Flask-Login==0.6.3")
from lesscode_flask.db import db
from lesscode_flask.model.base_model import BaseModel
from lesscode_flask.utils.helpers import result_to_dict, parameter_validation, format_page_index

logger = logging.getLogger(__name__)


class BaseService:

    def __init__(self, model):
        self.model = model

    @staticmethod
    def add_item(item: BaseModel):
        """
        添加数据
        :param item: 待添加数据对象
        :return:
        """

        # try:
        #
        # except AttributeError:
        #     current_user = None
        try:
            if hasattr(item, "create_user_id") and not getattr(item, "create_user_id"):
                item.create_user_id = flask_login.current_user.id
            if hasattr(item, "create_user_name") and not getattr(item, "create_user_name"):
                item.create_user_name = flask_login.current_user.display_name
        except Exception as e:
            if hasattr(item, "create_user_id"):
                item.create_user_id = "AnonymousUserId"
            if hasattr(item, "create_user_name"):
                item.create_user_name = "匿名用户"
        db.session.add(item)
        db.session.commit()
        return item.id

    def add_items(self, items: list):
        """
        添加数据
        :param items: 待添加数据对象集合
        :return:
        """
        for item in items:
            try:
                if hasattr(item, "create_user_id") and not getattr(item, "create_user_id"):
                    item.create_user_id = flask_login.current_user.id
                if hasattr(item, "create_user_name") and not getattr(item, "create_user_name"):
                    item.create_user_name = flask_login.current_user.display_name
            except Exception as e:
                if hasattr(item, "create_user_id"):
                    item.create_user_id = "AnonymousUserId"
                if hasattr(item, "create_user_name"):
                    item.create_user_name = "匿名用户"
        if items:
            # db.session.execute(
            #     self.model.__table__.insert(),
            #     items
            # )
            db.session.bulk_save_objects(items)
            db.session.commit()
        return result_to_dict(items)

    def update_item(self, id: str, item: dict):

        try:
            if hasattr(self.model, "modify_user_id") and not getattr(item, "modify_user_id"):
                item["modify_user_id"] = flask_login.current_user.id
            if hasattr(self.model, "modify_user_name") and not getattr(item, "modify_user_name"):
                item["modify_user_name"] = flask_login.current_user.display_name
        except Exception as e:
            if hasattr(item, "modify_user_id"):
                item.create_user_id = "AnonymousUserId"
            if hasattr(item, "modify_user_name"):
                item.create_user_name = "匿名用户"
        self.model.query.filter_by(id=id).update(parameter_validation(item))
        db.session.commit()
        return id

    def update_items(self, filters: list, item: dict):

        try:
            if hasattr(self.model, "modify_user_id") and not getattr(item, "modify_user_id"):
                item["modify_user_id"] = flask_login.current_user.id
            if hasattr(self.model, "modify_user_name") and not getattr(item, "modify_user_name"):
                item["modify_user_name"] = flask_login.current_user.display_name
        except Exception as e:
            if hasattr(item, "modify_user_id"):
                item.create_user_id = "AnonymousUserId"
            if hasattr(item, "modify_user_name"):
                item.create_user_name = "匿名用户"
        data = self.model.query.filter(*filters).update(parameter_validation(item))
        db.session.commit()
        return data

    def get_item(self, id: str):
        """
        获取单条信息
        :param id:
        :param select_columns:
        :return:
        """
        query = self.model.query
        return result_to_dict(query.get(id))

    # def get_one(self, filters: list, select_columns: list = None, ):
    def get_one(self, select_columns: list = None, order_columns: list = None, filters: list = None):
        """
        获取单条信息
        :param filters:
        :return:
        """
        data = self.get_items(select_columns, order_columns, filters, offset=0, size=1)
        if data:
            return data[0]
        return None

    def get_items(self, select_columns: list = None, order_columns: list = None, filters: list = None, offset: int = 0,
                  size: int = 10):
        """
        获取列表信息
        :param select_columns:
        :param order_columns:
        :param filters:
        :param offset:
        :param size:
        :return:
        """
        query = self.model.query
        if filters:
            query = query.filter(*filters)
        if order_columns:
            query = query.order_by(*order_columns)
        if offset > 0:
            query = query.offset(offset).limit(size)
        if select_columns:
            query = query.with_entities(*select_columns)
        return result_to_dict(query.all())

    def delete_item(self, id: str):
        data = self.model.query.filter_by(id=id).delete()
        db.session.commit()
        return data

    def delete_items(self, filters: list):
        if filters and len(filters) > 0:
            data = self.model.query.filter(*filters).delete()
            db.session.commit()
            return data
        return 0

    def page(self, select_columns: list = None, order_columns: list = None, group_columns: list = None,
             filters: list = None,
             page_num: int = 1,
             page_size: int = 10):
        """
        分页查询
        :param select_columns:
        :param order_columns:
        :param filters:
        :param page_num:
        :param page_size:
        :return:
        """
        query = self.model.query
        if filters:
            query = query.filter(*filters)
        if order_columns:
            query = query.order_by(*order_columns)
        if select_columns:
            query = query.with_entities(*select_columns)
        if group_columns:
            query = query.group_by(*group_columns)
        pagination = query.paginate(page=page_num, per_page=page_size, error_out=False)
        # 获取当前页的数据
        items = pagination.items
        # 获取分页信息
        total = pagination.total
        has_prev = pagination.has_prev
        has_next = pagination.has_next
        data = result_to_dict(items)
        # if select_columns:
        #     data = alchemy_result_to_dict(items)
        # else:
        #     data = serialize_result_to_dict(items)
        format_page_index(data, page_num, page_size)
        result = {"dataSource": data, "total": total,
                  "has_prev": has_prev,
                  "has_next": has_next}
        return result
