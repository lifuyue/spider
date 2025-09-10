import csv
import sqlite3

from crawler_core.pipelines.csv_sink import CSVSink
from crawler_core.pipelines.pg_sink import PgSink


def test_csv_sink(tmp_path):
    path = tmp_path / "out.csv"
    sink = CSVSink({"path": str(path)})
    sink.emit({"a": 1, "b": "x"})
    sink.emit({"a": 2, "b": "y"})
    rows = list(csv.DictReader(open(path)))
    assert rows[0]["a"] == "1"
    assert rows[1]["b"] == "y"


def test_pg_sink_upsert(tmp_path):
    db = tmp_path / "t.db"
    sink = PgSink({"dsn": f"sqlite:///{db}", "table": "t", "upsert_keys": ["id"]})
    sink.emit({"id": 1, "v": "a"})
    sink.emit({"id": 1, "v": "b"})
    conn = sqlite3.connect(db)
    cur = conn.execute("select count(*) from t")
    assert cur.fetchone()[0] == 1
    cur = conn.execute("select v from t where id=1")
    assert cur.fetchone()[0] == "b"

