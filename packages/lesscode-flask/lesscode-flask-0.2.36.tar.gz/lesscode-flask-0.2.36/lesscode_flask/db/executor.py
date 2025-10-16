import time


class QueryExecutionError(Exception):
    pass


class QueryExecutor:
    # , user_id, is_api_key, metadata, is_scheduled_query
    def __init__(self, query_text, query_runner):
        # self.job = get_current_job()
        self.query_text = query_text
        # self.data_source_id = data_source_id
        # self.metadata = metadata
        self.metadata = {}
        # self.data_source = self._load_data_source()
        self.query_runner = query_runner
        # self.query_id = metadata.get("query_id")
        # self.user = _resolve_user(user_id, is_api_key, metadata.get("query_id"))
        self.user = None
        # self.query_model = (
        #     models.Query.query.get(self.query_id)
        #     if self.query_id and self.query_id != "adhoc"
        #     else None
        # )  # fmt: skip

        # Close DB connection to prevent holding a connection for a long time while the query is executing.
        # models.db.session.close()
        # self.query_hash = gen_query_hash(self.query)
        # self.is_scheduled_query = is_scheduled_query
        # if self.is_scheduled_query:
        #     # Load existing tracker or create a new one if the job was created before code update:
        #     models.scheduled_queries_executions.update(self.query_model.id)

    def run(self):
        started_at = time.time()
        #
        # logger.debug("Executing query:\n%s", self.query)
        self._log_progress("executing_query")

        annotated_query = self._annotate_query(self.query_runner)

        data, error = self.query_runner.run_query(annotated_query, self.user)
        if error:
            raise QueryExecutionError(error)
        return data

    def exec(self):
        self._log_progress("executing_query")

        annotated_query = self._annotate_query(self.query_runner)

        data, error = self.query_runner.exec(annotated_query, self.user)
        if error:
            raise QueryExecutionError(error)
        return data

        #
        # logger.info(
        #     "job=execute_query query_hash=%s ds_id=%d data_length=%s error=[%s]",
        #     self.query_hash,
        #     self.data_source_id,
        #     data and len(data),
        #     error,
        # )
        #
        # _unlock(self.query_hash, self.data_source.id)

        # if error is not None and data is None:
        #     result = QueryExecutionError(error)
        #     # if self.is_scheduled_query:
        #     #     self.query_model = models.db.session.merge(self.query_model, load=False)
        #     #     track_failure(self.query_model, error)
        #     raise result
        # else:
        #     if self.query_model and self.query_model.schedule_failures > 0:
        #         self.query_model = models.db.session.merge(self.query_model, load=False)
        #         self.query_model.schedule_failures = 0
        #         self.query_model.skip_updated_at = True
        #         models.db.session.add(self.query_model)
        #
        #     query_result = models.QueryResult.store_result(
        #         self.data_source.org_id,
        #         self.data_source,
        #         self.query_hash,
        #         self.query,
        #         data,
        #         run_time,
        #         utcnow(),
        #     )
        #
        #     updated_query_ids = models.Query.update_latest_result(query_result)
        #
        #     models.db.session.commit()  # make sure that alert sees the latest query result
        #     self._log_progress("checking_alerts")
        #     for query_id in updated_query_ids:
        #         check_alerts_for_query.delay(query_id, self.metadata)
        #     self._log_progress("finished")
        #
        #     result = query_result.id
        #     models.db.session.commit()
        #     return result

    def _annotate_query(self, query_runner):
        pass
        # self.metadata["Job ID"] = self.job.id
        # self.metadata["Query Hash"] = self.query_hash
        # self.metadata["Scheduled"] = self.is_scheduled_query

        return query_runner.annotate_query(self.query_text, self.metadata)

    def _log_progress(self, state):
        pass
        # logger.info(
        #     "job=execute_query state=%s query_hash=%s type=%s ds_id=%d "
        #     "job_id=%s queue=%s query_id=%s username=%s",  # fmt: skip
        #     state,
        #     self.query_hash,
        #     self.data_source.type,
        #     self.data_source.id,
        #     self.job.id,
        #     self.metadata.get("Queue", "unknown"),
        #     self.metadata.get("query_id", "unknown"),
        #     self.metadata.get("Username", "unknown"),
        # )

    def _load_data_source(self):
        pass
        # logger.info("job=execute_query state=load_ds ds_id=%d", self.data_source_id)
        # return models.DataSource.query.get(self.data_source_id)
