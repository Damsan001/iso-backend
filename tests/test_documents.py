# tests/test_documents.py
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.document import Classification

client = TestClient(app)

def test_create_and_get_document():
    # Crear un documento de prueba
    payload = {
        "name": "Política de seguridad",
        "type": "POLICY",
        "area_responsible": "TI",
        "author": "juan.perez",
        "reviewer": "ana.gomez",
        "approver": "luis.rodriguez",
        "classification": Classification.CONFIDENTIAL.value
    }
    resp = client.post("/documents", json=payload)
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["id"] == 1
    assert doc["name"] == payload["name"]

    # Obtenerlo por ID
    resp2 = client.get(f"/documents/{doc['id']}")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["code"] == payload["code"]

# def test_list_documents_empty_filters():
#     # Sin filtros válidos, pero dummy devuelve la lista entera
#     resp = client.get("/documents?role=any&classification=any")
#     assert resp.status_code == 200
#     assert isinstance(resp.json(), list)
