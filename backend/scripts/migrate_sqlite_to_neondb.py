from __future__ import annotations

import os
from typing import Any

from sqlalchemy import MetaData, create_engine, delete, insert, select, text


def _engine(url: str):
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def _column_names(table) -> set[str]:
    return {col.name for col in table.columns}


def main() -> None:
    source_sqlite_url = os.getenv("SOURCE_SQLITE_URL", "sqlite:///./governance.db")
    target_neon_url = os.getenv("TARGET_NEON_URL", "")

    if not target_neon_url:
        raise RuntimeError(
            "TARGET_NEON_URL is required. Example: "
            "postgresql+psycopg://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require"
        )

    src_engine = _engine(source_sqlite_url)
    dst_engine = _engine(target_neon_url)

    src_meta = MetaData()
    src_meta.reflect(bind=src_engine)

    dst_meta = MetaData()
    dst_meta.reflect(bind=dst_engine)

    totals: dict[str, int] = {}
    skipped: dict[str, str] = {}

    with src_engine.connect() as src_conn, dst_engine.begin() as dst_conn:
        for src_table in src_meta.sorted_tables:
            table_name = src_table.name

            if table_name in dst_meta.tables:
                dst_table = dst_meta.tables[table_name]
                if _column_names(src_table) != _column_names(dst_table):
                    skipped[table_name] = "column mismatch"
                    continue
            else:
                src_table.to_metadata(dst_meta)
                dst_meta.tables[table_name].create(bind=dst_conn)

            dst_table = dst_meta.tables[table_name]

            rows: list[dict[str, Any]] = [dict(row) for row in src_conn.execute(select(src_table)).mappings().all()]

            # Replace target table contents to mirror source snapshot.
            dst_conn.execute(delete(dst_table))
            if rows:
                dst_conn.execute(insert(dst_table), rows)

            totals[table_name] = len(rows)

    print("Migration complete")
    for table_name, count in totals.items():
        print(f"- {table_name}: {count} rows")
    if skipped:
        print("Skipped tables")
        for table_name, reason in skipped.items():
            print(f"- {table_name}: {reason}")

    with dst_engine.connect() as conn:
        conn.execute(text("SELECT 1"))


if __name__ == "__main__":
    main()
