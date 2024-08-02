import csv
import os
from itertools import islice


import pymssql
import time

from config.helpers import QueueItem
from config.orc import Orchestrator


import urllib3.exceptions
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



# BR03
BR03_USER_KEY = "ecpgu0Qjx-5-7R2eoHba0ajvZV8BrtFwQR9GDEB9Rjd78"
BR03_ORG_ID = "yusada"
BR03_TENANT = "DefaultTenant"
BR03_CLIENT_ID = "8DEv1AMNXczW3y4U15LL3jYf62jK93n5"
BR03_ORG_UNIT_ID = "3826561" # Id папки в орке


# BR06
BR06_USER_KEY = "wCcmiCc9eab6APdRVneCX8Yde85IFEXM9lUCLCY4gzx5S"
BR06_ORG_ID = "exfat"
BR06_TENANT = "DefaultTenant"
BR06_CLIENT_ID = "8DEv1AMNXczW3y4U15LL3jYf62jK93n5"
BR06_ORG_UNIT_ID = "3739129"


db_conn = pymssql.connect("MSK-DPRO-DBA438", "rpa_admin", "Zd25a37ec0f87ab1674d50156", "rpa_processing_data")
db_cursor = db_conn.cursor(as_dict=True)




def send_csv_data_to_db(csv_file_path, queue_id):
    db_conn = pymssql.connect("MSK-DPRO-DBA438", "rpa_admin", "Zd25a37ec0f87ab1674d50156", "rpa_processing_data")
    db_cursor = db_conn.cursor(as_dict=True)

    sql_request_base = "INSERT INTO QueueItems (Id, Priority, Status, QueueDefinitionId, [Key], ReviewStatus, " \
                       "SecondsInPreviousAttempts, RetryNumber, TenantId, CreationTime, OrganizationUnitId, " \
                       "HasDueDate, Reference, SpecificData, StartProcessing, EndProcessing, [ProcessingExceptionReason]) VALUES "
    sql_data = ""

    with open(csv_file_path, encoding="utf-8") as csv_file:
        row_count = 0
        for row in islice(csv.reader(csv_file), 2, None):
            item = QueueItem(row)
            sql_data += f"({row_count}, 1, {item.status_id}, {queue_id}, '{item.key}', 1, 1, {item.retry_count}, 1, '2/20/2022', 1, 1," \
                        f"'{item.reference}', '{item.specific_data}', '{item.started}', '{item.ended}', '{item.exception_reason or 'NULL'}'), "

            row_count += 1

            if row_count % 1000 == 0:
                db_cursor.execute(sql_request_base + sql_data[:-2])
                db_conn.commit()
                sql_data = ""

        if sql_data:
            db_cursor.execute(sql_request_base + sql_data[:-2])
            db_conn.commit()


def refresh_db(orc: Orchestrator, queue_cloud_id, queue_robot_id):
    report_path = os.path.join(".", "temp", "report.csv")
    orc.download_report_queue(queue_cloud_id, report_path)
    send_csv_data_to_db(report_path, queue_robot_id)



if __name__ == '__main__':
    br03_orchestrator = Orchestrator(BR03_USER_KEY, BR03_ORG_ID, BR03_TENANT, BR03_CLIENT_ID, BR03_ORG_UNIT_ID)
    br06_orchestrator = Orchestrator(BR06_USER_KEY, BR06_ORG_ID, BR06_TENANT, BR06_CLIENT_ID, BR06_ORG_UNIT_ID)

    while True:
        db_cursor.execute("truncate table dbo.QueueItems")
        db_conn.commit()

        br06_queue_id = 635191
        refresh_db(br06_orchestrator, br06_queue_id, 6)
        print("BR06 обновлен")


        br3_1_queue_id = 667843  # - BR03 SAP
        br3_2_queue_id = 667845  # - BR03 Support

        refresh_db(br03_orchestrator, br3_1_queue_id, 31)
        refresh_db(br03_orchestrator, br3_2_queue_id, 32)
        print("BR03 обновлен")
        time.sleep(300)



#
