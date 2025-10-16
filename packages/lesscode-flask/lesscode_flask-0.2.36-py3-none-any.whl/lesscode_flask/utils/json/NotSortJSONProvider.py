from flask.json.provider import DefaultJSONProvider


class NotSortJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, *args, **kwargs):
        kwargs.setdefault("default", self.default)
        kwargs.setdefault("ensure_ascii", self.ensure_ascii)
        kwargs['sort_keys'] = False  # 禁用键排序
        return super().dumps(obj, *args, **kwargs)
