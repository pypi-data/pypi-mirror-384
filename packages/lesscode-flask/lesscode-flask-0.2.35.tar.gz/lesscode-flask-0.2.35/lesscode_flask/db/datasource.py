from redash.query_runner import get_query_runner


class DataSource():
    def __init__(self):
        self.options = None
        self.data_source_id = None

    @staticmethod
    def get_by_id(object_id):
        datasource = DataSource()
        datasource.data_source_id = object_id
        from lesscode_flask.utils.helpers import app_config
        datasource_list = app_config.get("DATA_SOURCE")
        datasource_list = [item for item in datasource_list if item.get("id") == object_id]
        if len(datasource_list) > 0:
            datasource.options = datasource_list[0]
        return datasource

    @property
    def query_runner(self):
        query_runner = get_query_runner(self.options.get("type"), self.options)
        # uses_ssh_tunnel = self.options.get("ssh_tunnel", False)
        # if uses_ssh_tunnel:
        #     query_runner = with_ssh_tunnel(query_runner, self.options.get("ssh_tunnel"))

        return query_runner
