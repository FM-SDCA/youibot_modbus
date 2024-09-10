import asyncio
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.server.async_io import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG)

DATABASE = "modbus.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS coils (
            id INTEGER PRIMARY KEY,
            value BOOLEAN NOT NULL
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS registers (
            id INTEGER PRIMARY KEY,
            value INTEGER NOT NULL
        )
    """
    )
    for i in range(1000):
        conn.execute(
            "INSERT OR IGNORE INTO coils (id, value) VALUES (?, ?)", (i, False)
        )
    for i in range(1000):
        conn.execute(
            "INSERT OR IGNORE INTO registers (id, value) VALUES (?, ?)", (i, 0)
        )
    conn.commit()
    conn.close()


def read_coils(start, count):
    conn = get_db_connection()
    coils = conn.execute(
        "SELECT * FROM coils WHERE id >= ? AND id < ?", (start, start + count)
    ).fetchall()
    conn.close()
    return [bool(coil["value"]) for coil in coils]


def read_registers(start, count):
    conn = get_db_connection()
    registers = conn.execute(
        "SELECT * FROM registers WHERE id >= ? AND id < ?", (start, start + count)
    ).fetchall()
    conn.close()
    return [register["value"] for register in registers]


def update_coil(address, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE coils SET value = ? WHERE id = ?", (value, address))
    conn.commit()
    conn.close()


def update_register(address, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE registers SET value = ? WHERE id = ?", (value, address))
    conn.commit()
    conn.close()


async def updating_writer(context):
    while True:
        await asyncio.sleep(5)
        coils = context[0x00].getValues(1, 0, count=1000)
        registers = context[0x00].getValues(3, 0, count=1000)
        for address, value in enumerate(coils):
            update_coil(address, value)
        for address, value in enumerate(registers):
            update_register(address, value)


async def run_server():
    initialize_database()

    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * 1000),
        co=ModbusSequentialDataBlock(0, [False] * 1000),
        hr=ModbusSequentialDataBlock(0, [0] * 1000),
        ir=ModbusSequentialDataBlock(0, [0] * 1000),
    )
    context = ModbusServerContext(slaves=store, single=True)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "ModbusSim"
    identity.ProductCode = "MS"
    identity.VendorUrl = "http://example.com"
    identity.ProductName = "Modbus Simulator"
    identity.ModelName = "ModbusSim"
    identity.MajorMinorRevision = "1.0"

    asyncio.create_task(updating_writer(context))
    logging.debug("Starting Modbus server on localhost:5020")
    await StartAsyncTcpServer(context, identity=identity, address=("localhost", 5020))
    logging.debug("Modbus server started successfully")


if __name__ == "__main__":
    print("Starting Modbus server")
    asyncio.run(run_server())
