from fastapi.testclient import TestClient
from modbus_api import app, CoilRequest, RegisterRequest  # modbus_api.pyが同じディレクトリにある場合

client = TestClient(app)

def test_read_modbus():
    print("Testing /modbus/read endpoint...")
    response = client.get("/modbus/read")
    if response.status_code == 200:
        data = response.json()
        if "coils" in data and "registers" in data:
            print("SUCCESS: Read coils and registers.")
            print(f"Coils: {data['coils']}")
            print(f"Registers: {data['registers']}")
        else:
            print("FAILURE: Missing keys in response data.")
    else:
        print(f"FAILURE: Status code {response.status_code}.")
        print(response.text)

def test_write_coil():
    print("Testing /modbus/writeCoil endpoint...")
    request_data = CoilRequest(address=104, value=True)
    response = client.post("/modbus/writeCoil", json=request_data.dict())
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print("SUCCESS: Write coil.")
        else:
            print("FAILURE: Write coil not successful.")
        print(f"Response Data: {data}")
    else:
        print(f"FAILURE: Status code {response.status_code}.")
        print(response.text)

def test_write_register():
    print("Testing /modbus/writeRegister endpoint...")
    request_data = RegisterRequest(address=103, value=123)
    response = client.post("/modbus/writeRegister", json=request_data.dict())
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print("SUCCESS: Write register.")
        else:
            print("FAILURE: Write register not successful.")
        print(f"Response Data: {data}")
    else:
        print(f"FAILURE: Status code {response.status_code}.")
        print(response.text)

if __name__ == "__main__":
    test_write_coil()
    test_write_register()
    test_read_modbus()
