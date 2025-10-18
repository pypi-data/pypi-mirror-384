
def get_sessions_info_html(app_id, spark_ui_url, driver_log_url):
    table_root_style = "width: 75%; margin-top: var(--jp-content-heading-margin-top); margin-bottom:var(--jp-content-heading-margin-bottom); border: var(--jp-border-width) solid var(--jp-border-color2);"
    table_header_style = "text-align: left; border: var(--jp-border-width) solid var(--jp-border-color2);"
    table_row_style = "word-wrap: break-word; text-align: left; border: var(--jp-border-width) solid var(--jp-border-color2)"
    table = f"""
                <table class="session_info_table" style="{table_root_style}">
                    <tr>
                        <th style="{table_header_style}">Id</th>
                        <th style="{table_header_style}">Spark UI</th>
                        <th style="{table_header_style}">Driver logs</th>
                    </tr>
                    <tr>
                        <td class="application_id" style="{table_row_style}">{app_id}</td>
                        <td class="spark_ui_link" style="{table_row_style}"><a href="" target="_blank" log_location="{spark_ui_url}">link</a></td>
                        <td class="driver_log_link" style="{table_row_style}"><a href="" target="_blank" log_location="{driver_log_url}">link</a></td>
                    </tr>
                </table>
            """
    html = (
        table
    )

    return html
