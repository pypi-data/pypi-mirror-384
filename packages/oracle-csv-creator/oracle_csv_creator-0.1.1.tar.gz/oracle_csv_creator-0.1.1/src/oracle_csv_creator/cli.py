import argparse
import getpass
from .core import csv_writer

def main():
    p = argparse.ArgumentParser(description="Parallel Oracle table to CSV writer (ROWID-based)")
    # DB
    p.add_argument("--db-host", required=True)
    p.add_argument("--db-port", type=int, required=True)
    p.add_argument("--service-name", required=True)
    p.add_argument("--db-user", required=True)
    p.add_argument("--db-password", required=False, help="미지정 시 프롬프트로 입력 요청")    
    # Target
    p.add_argument("--owner", required=True, help="스키마(OWNER)")
    p.add_argument("--table", required=True, help="테이블명")
    # Output
    p.add_argument("--path", default=".", help="출력 디렉토리")
    p.add_argument("--filename", default=None, help="출력 파일명(확장자 제외). 미지정 시 OWNER.TABLE.csv")
    # Options
    p.add_argument("--degree", type=int, default=1, help="병렬 프로세스 수")
    p.add_argument("--header", dest="header", action="store_true", help="헤더 기록 (기본)" )
    p.add_argument("--no-header", dest="header", action="store_false", help="헤더 기록 안 함" )
    p.set_defaults(header=True)
    p.add_argument("--consistent", action="store_true", help="AS OF SCN 일관성 읽기")
    p.add_argument("--date-format", default="YYYY-MM-DD HH24:MI:SS")
    p.add_argument("--timestamp-format", default="YYYY-MM-DD HH24:MI:SS.FF")
    p.add_argument("--delimiter", default=",", help="CSV 구분자 (기본 ,)")
    p.add_argument("--quotechar", default="", help="값 감싸기 문자. 빈 문자열이면 QUOTE_NONE")
    p.add_argument("--encoding", default="euc-kr", help="CSV 파일 인코딩")
    p.add_argument("--fetchsize", type=int, default=10000, help="배치 페치 크기")

    args = p.parse_args()
    if args.db_password is None:
        args.db_password = getpass.getpass("DB Password: ")

    db_info = {
        "host": args.db_host,
        "user": args.db_user,
        "password": args.db_password,
        "port": args.db_port,
        "service_name": args.service_name,
    }

    csv_writer(
        db_info=db_info,
        owner=args.owner,
        table_name=args.table,
        path=args.path,
        filename=args.filename,
        degree=args.degree,
        header=args.header,
        consistent=args.consistent,
        date_format=args.date_format,
        timestamp_format=args.timestamp_format,
        delimiter=args.delimiter,
        quotechar=args.quotechar,
        encoding=args.encoding,
        fetchsize=args.fetchsize,
    )

if __name__ == "__main__":
    main()
