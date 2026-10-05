from __future__ import annotations

import sqlite3

from fastapi import FastAPI, HTTPException

app = FastAPI(title="inventory")

DB_PATH = "inventory.db"


def _init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "create table if not exists stock (sku text primary key, qty integer not null)"
        )
        conn.execute("insert or ignore into stock(sku, qty) values ('BOOK-1', 10)")
        conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def startup() -> None:
    _init_db()


@app.get("/stock/{sku}")
def get_stock(sku: str) -> dict[str, int | str]:
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute("select qty from stock where sku=?", (sku,)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="sku not found")
    return {"sku": sku, "qty": row[0]}


@app.post("/reserve/{sku}")
def reserve_stock(sku: str, amount: int = 1) -> dict[str, int | str]:
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute("select qty from stock where sku=?", (sku,)).fetchone()
        if not row or row[0] < amount:
            raise HTTPException(status_code=409, detail="insufficient stock")
        conn.execute("update stock set qty = qty - ? where sku=?", (amount, sku))
        conn.commit()
    finally:
        conn.close()
    return {"sku": sku, "reserved": amount}
