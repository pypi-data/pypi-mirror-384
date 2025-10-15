# afl-ai-utils
    rm -rf build dist 
    python3 setup.py sdist bdist_wheel
    twine upload --repository pypi dist/* 


# Installation 
        pip install afl-ai-utils

# Usage

### Slack Alerting
    from afl_ai_utils.slack_alerts import send_slack_alert 
    send_slack_alert(info_alert_slack_webhook_url=None, red_alert_slack_webhook_url=None, slack_red_alert_userids=None, payload=None, is_red_alert=False)

        """Send a Slack message to a channel via a webhook.

    Args:
        info_alert_slack_webhook_url(str): Infor slack channel url
        red_alert_slack_webhook_url(str): red alert channel url
        slack_red_alert_userids (list): userid's to mention in slack for red alert notification
        payload (dict): Dictionary containing Slack message, i.e. {"text": "This is a test"}
        is_red_alert (bool): Full Slack webhook URL for your chosen channel.

    Returns:
        HTTP response code, i.e. <Response [503]>
    """


### BigQuery Dataframe to BigQuery  and get result in Datafeame
        
        def dump_dataframe_to_bq_table(self, dataframe: pd.DataFrame, schema_cols_type: dict, table_id: str, mode: str):

        >>> from afl_ai_utils.bigquery_utils import BigQuery
        >>> bq = BigQuery("keys.json")
        >>> bq.write_insights_to_bq_table(dataframe=None, schema=None, table_id=None, mode=None)
        
        
        """Insert a dataframe to bigquery

        Args:
            dataframe(pandas dataframe): for dataframe to be dumped to bigquery
            schema(BigQuery.Schema ): ex:
            schema_cols_type: {"date_start":"date", "id": "integer", "name": "string"}
            table_id (list): table_id in which dataframe need to be inserted e.g project_id.dataset.table_name = table_id
            mode(str): To append or replace the table - e.g mode = "append"  or mode="replace"
        Returns:
            returns as success message with number of inserted rows and table name
        """




### Execute any query to BigQuery    
        
        def execute_query(self, query):

        >>> from afl_ai_utils.bigquery_utils import BigQuery
        >>> bq = BigQuery("keys.json")
        >>> df = bq.execute_query(query = "SELECT * FROM TABLE")
        
        
        """
        Args:
            query (query of any type SELECT/INSERT/DELETE ) 
        Returns:
            returns dataframe of execute query result
        """
