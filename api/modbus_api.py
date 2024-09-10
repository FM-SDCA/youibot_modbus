from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging

app = FastAPI()
client = ModbusTcpClient('192.168.1.96', port=3001)

origins = [
    "http://localhost:3000",
    "http://192.168.1.53:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CoilRequest(BaseModel):
    address: int
    value: bool

class RegisterRequest(BaseModel):
    address: int
    value: int
    
import logging

logging.basicConfig(level=logging.DEBUG)
@app.get("/modbus/readAll")
async def read_all_modbus(
    discrete_start: int = Query(...), discrete_count: int = Query(...),
    input_start: int = Query(...), input_count: int = Query(...),
    coil_start: int = Query(...), coil_count: int = Query(...),
    holding_start: int = Query(...), holding_count: int = Query(...),
    indicator_start: int = Query(...), indicator_count: int = Query(...)
):
    try:
        client.connect()
        if not client.is_socket_open():
            logging.error("Could not connect to Modbus server")
            raise ModbusException("Could not connect to Modbus server")
        
        discrete_inputs = client.read_discrete_inputs(discrete_start, discrete_count) if discrete_count > 0 else None
        input_registers = client.read_input_registers(input_start, input_count) if input_count > 0 else None
        coils = client.read_coils(coil_start, coil_count) if coil_count > 0 else None
        holding_registers = client.read_holding_registers(holding_start, holding_count) if holding_count > 0 else None
        indicators = client.read_coils(indicator_start, indicator_count) if indicator_count > 0 else None
        
        client.close()
        
        # logging.debug(f"Discrete Inputs: {discrete_inputs.bits if discrete_inputs else []}")
        # logging.debug(f"Input Registers: {input_registers.registers if input_registers else []}")
        # logging.debug(f"Coils: {coils.bits if coils else []}")
        # logging.debug(f"Holding Registers: {holding_registers.registers if holding_registers else []}")
        # logging.debug(f"Indicators: {indicators.bits if indicators else []}")
        
        return {
            "discrete_inputs": discrete_inputs.bits if discrete_inputs else [],
            "input_registers": input_registers.registers if input_registers else [],
            "coils": coils.bits if coils else [],
            "holding_registers": holding_registers.registers if holding_registers else [],
            "indicators": indicators.bits if indicators else []
        }
    except ModbusException as e:
        logging.error(f"ModbusException: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/modbus/readDiscreteInputs")
async def read_discrete_inputs(start: int = Query(...), count: int = Query(...)):
    try:
        client.connect()
        if not client.is_socket_open():
            raise ModbusException("Could not connect to Modbus server")
        discrete_inputs = client.read_discrete_inputs(start, count)
        client.close()
        if discrete_inputs.isError():
            raise ModbusException("Error reading discrete inputs")
        return {"discrete_inputs": discrete_inputs.bits}
    except ModbusException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/modbus/readInputRegisters")
async def read_input_registers(start: int = Query(...), count: int = Query(...)):
    try:
        client.connect()
        if not client.is_socket_open():
            raise ModbusException("Could not connect to Modbus server")
        input_registers = client.read_input_registers(start, count)
        client.close()
        if input_registers.isError():
            raise ModbusException("Error reading input registers")
        return {"input_registers": input_registers.registers}
    except ModbusException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/modbus/readCoils")
async def read_coils(start: int = Query(...), count: int = Query(...)):
    try:
        client.connect()
        if not client.is_socket_open():
            raise ModbusException("Could not connect to Modbus server")
        coils = client.read_coils(start, count)
        client.close()
        if coils.isError():
            raise ModbusException("Error reading coils")
        return {"coils": coils.bits}
    except ModbusException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/modbus/readHoldingRegisters")
async def read_holding_registers(start: int = Query(...), count: int = Query(...)):
    try:
        client.connect()
        if not client.is_socket_open():
            raise ModbusException("Could not connect to Modbus server")
        holding_registers = client.read_holding_registers(start, count)
        client.close()
        if holding_registers.isError():
            raise ModbusException("Error reading holding registers")
        return {"holding_registers": holding_registers.registers}
    except ModbusException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/modbus/writeCoil")
async def write_coil(request: CoilRequest):
    try:
        client.connect()
        if not client.is_socket_open():
            raise ModbusException("Could not connect to Modbus server")
        result = client.write_coil(request.address, request.value)
        client.close()
        if result.isError():
            raise ModbusException("Error writing Modbus coil")
        return {"success": True}
    except ModbusException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/modbus/writeHoldingRegister")
async def write_holding_register(request: RegisterRequest):
    try:
        client.connect()
        if not client.is_socket_open():
            raise ModbusException("Could not connect to Modbus server")
        result = client.write_register(request.address, request.value)
        client.close()
        if result.isError():
            raise ModbusException("Error writing Modbus holding register")
        return {"success": True}
    except ModbusException as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/missionWorks/stopAll")
async def stop_all_mission_works():
    try:
        # COIL100～COIL110をOFFにする
        for i in range(100, 111):
            client.connect()
            if not client.is_socket_open():
                raise ModbusException("Could not connect to Modbus server")
            result = client.write_coil(i, False)
            client.close()
            if result.isError():
                raise ModbusException("Error writing Modbus coil")

        # 全てのミッションワークを取得
        response = requests.get("http://192.168.1.96:8080/api/v3/missionWorks")  # ホストとポートを修正
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch mission works, status code: {response.status_code}")
            raise HTTPException(status_code=500, detail="Failed to fetch mission works")
        
        mission_works = response.json()
        logging.debug(f"Mission works fetched: {mission_works}")  # デバッグメッセージ追加
        
        # 各ミッションワークを停止
        for mission_work in mission_works:
            if(mission_work['status'] != 'RUNNING' | mission_work['status'] != 'PAUSED'):
                continue

            stop_response = requests.post(f"http://192.168.1.96:8080/api/v3/missionWorks/{mission_work['id']}/controls/stop")
            
            if stop_response.status_code != 200:
                logging.error(f"Failed to stop mission work {mission_work['id']}, status code: {stop_response.status_code}")
        
        return {"success": True, "stopped_mission_works": [mw['id'] for mw in mission_works]}
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vehicles/emergencyStop")
async def emergency_stop():
    try:
        # 緊急停止のリクエストを送信
        response = requests.put("http://192.168.1.96:8080/api/v3/vehicles/devices/emergencyStop/open")
        
        if response.status_code != 200:
            logging.error(f"Failed to initiate emergency stop, status code: {response.status_code}")
            raise HTTPException(status_code=500, detail="Failed to initiate emergency stop")
        
        return {"success": True}
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
