import oracledb
import time
import csv
from uuid import uuid1
from concurrent.futures import ProcessPoolExecutor
import os
import shutil
from typing import Dict, Optional

def table_info_call(db_info: Dict, owner: str, table_name: str, consistent: bool, 
                    date_format: str='YYYY-MM-DD HH24:MI:SS', 
                    timestamp_format: str='YYYY-MM-DD HH24:MI:SS.FF'):
    """테이블의 컬럼정보와 익스텐트 범위, SCN(옵션)을 조회합니다."""
    conn = oracledb.connect(**db_info)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {owner}.{table_name}")

    table_info = {}
    col_names, cols = [], []
    for col in cur.description:
        col_name = col[0]
        cols.append(col_name)
        if col[1].name == 'DB_TYPE_DATE':
            col_name = f"TO_CHAR({col_name}, '{date_format}') AS {col_name}"
        elif col[1].name == 'DB_TYPE_TIMESTAMP':
            col_name = f"TO_CHAR({col_name}, '{timestamp_format}') AS {col_name}"
        col_names.append(col_name)
    cur.close()
    table_info['col_names'] = col_names
    table_info['cols'] = cols

    # 익스텐트별 rowid 범위
    cur = conn.cursor()
    sql = """SELECT rownum as extent_id
                  , bytes
                  , dbms_rowid.rowid_create(1, t.data_object_id, e.file_id, e.block_id, 0) AS start_rid
                  , dbms_rowid.rowid_create(1, t.data_object_id, e.file_id, e.block_id + e.blocks - 1, 32767) AS end_rid
              FROM dba_extents e INNER JOIN dba_objects t ON ( e.segment_name = t.object_name 
                                                               AND e.owner = t.owner 
                                                               AND nvl(e.partition_name,'*') = nvl(t.subobject_name, '*')
                                                              )
             WHERE 1 = 1 
               AND e.owner = :owner
               AND e.segment_name = :table_name
               AND t.data_object_id is not null
               ORDER BY e.partition_name, e.extent_id"""
    cur.execute(sql, owner=owner, table_name=table_name)
    table_info['rowidset'] = cur.fetchall()

    # SCN (일관성 읽기)
    table_info['scn'] = None
    if consistent:
        cur.execute("SELECT CURRENT_SCN FROM V$DATABASE")
        scn, = cur.fetchone()
        table_info['scn'] = scn

    conn.close()
    return table_info

def session_execute(db_info: Dict, path: str, owner: str, table_name: str, trxn_id: str, table_info: Dict, 
                    rowidset: Dict, header: bool, delimiter: Optional[str], quotechar: Optional[str],
                    encoding: str = 'euc-kr', fetchsize: int = 10000):
    scn_sql = f" AS OF SCN {str(table_info['scn'])} " if table_info['scn'] is not None else ""
    sql = f"SELECT {','.join(table_info['col_names'])} FROM {owner}.{table_name} {scn_sql} where rowid between :start_rowid and :end_rowid"
    if delimiter is None:
        delimiter = ','
    if not quotechar:
        quoting = csv.QUOTE_NONE
        quotechar = None
    else:
        quoting = csv.QUOTE_ALL

    _conn = oracledb.connect(**db_info)
    try:
        for extentid, (start_rowid, end_rowid) in zip(rowidset['extentid'], rowidset['rowid']):
            filename = os.path.join(path, f"{trxn_id}_{str(extentid).rjust(7, '0')}.csv")
            cur = _conn.cursor()
            cur.execute(sql, start_rowid=start_rowid, end_rowid=end_rowid)

            with open(filename, 'w', newline="", encoding=encoding) as f:
                writer = csv.writer(f, delimiter=delimiter, quotechar=quotechar, quoting=quoting)
                if extentid == 1 and header:
                    writer.writerow(table_info['cols'])
                while True:
                    datas = cur.fetchmany(fetchsize)
                    if not datas:
                        break
                    writer.writerows(datas)
    finally:
        _conn.close()

def file_cleansing(path: str, owner: str, table_name: str, filename: Optional[str]):
    """시작 전 기존 CSV 파일 삭제"""
    file = os.path.join(path, f'{filename}.csv' if filename else f'{owner}.{table_name}.csv')
    if os.path.exists(file):
        os.remove(file)

def csv_file_merged(path: str, owner: str, table_name: str, trxn_id: str, filename: Optional[str]):
    """익스텐트 단위로 생성된 CSV 조각을 하나의 파일로 병합하고 조각을 삭제합니다."""
    files = sorted([f for f in os.listdir(path) if f.startswith(trxn_id)])
    output_file = os.path.join(path, f'{filename}.csv' if filename else f'{owner}.{table_name}.csv')

    BUF = 8 * 1024 * 1024
    with open(output_file, 'wb') as fo:
        for f in files:
            finame = os.path.join(path, f)
            with open(finame, 'rb') as fi:
                shutil.copyfileobj(fi, fo, length=BUF)
            os.remove(finame)

def rowid_set_split(table_info: Dict, degree: int):
    """익스텐트 크기(bytes)를 기준으로 병렬 세션에 균등 분배."""
    session_rowidset = {i: {'extentid': [], 'rowid': [], 'size': 0, 'count': 0} for i in range(degree)}
    for i, size, start_rowid, end_rowid in table_info['rowidset']:
        idx = min(session_rowidset, key=lambda k: session_rowidset[k]['size'])
        session_rowidset[idx]['extentid'].append(i)
        session_rowidset[idx]['rowid'].append([start_rowid, end_rowid])
        session_rowidset[idx]['size'] += size
        session_rowidset[idx]['count'] += 1
    return session_rowidset

def csv_writer(db_info: Dict, owner: str, table_name: str, path: str='.', filename: Optional[str]=None,
        degree: int=1, header: bool=True, consistent: bool=False,
        date_format: str='YYYY-MM-DD HH24:MI:SS', timestamp_format: str='YYYY-MM-DD HH24:MI:SS.FF',
        delimiter: Optional[str]=None, quotechar: Optional[str]=None,
        encoding: str='euc-kr', fetchsize: int=10000):
    """Oracle 테이블을 CSV로 추출합니다."""
    stime = time.time()
    owner, table_name = owner.upper(), table_name.upper()
    os.makedirs(path, exist_ok=True)

    table_info = table_info_call(db_info, owner, table_name, consistent, date_format, timestamp_format)
    session_rowidset = rowid_set_split(table_info, degree)
    file_cleansing(path, owner, table_name, filename)

    trxn_id = str(uuid1()).upper().replace('-', '')
    with ProcessPoolExecutor(max_workers=degree) as executor:
        futures = [
            executor.submit(
                session_execute, db_info, path, owner, table_name, trxn_id, table_info,
                rowidset, header, delimiter, quotechar, encoding, fetchsize
            )
            for rowidset in session_rowidset.values()
        ]
        for f in futures:
            f.result()

    csv_file_merged(path, owner, table_name, trxn_id, filename)
    print('process time', time.time() - stime)
