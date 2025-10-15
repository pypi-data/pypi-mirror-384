from oracle_csv_creator import csv_writer

db_info = {
    "host": "10.0.0.1",
    "user": "SCOTT",
    "password": "tiger",
    "port": 1521,
    "service_name": "ORCL",
}

csv_writer(
    db_info=db_info,
    owner="HR",
    table_name="EMPLOYEES",
    path="./output",
    degree=4,
    consistent=True,
    delimiter=",",
    quotechar="",
    encoding="euc-kr",
)
