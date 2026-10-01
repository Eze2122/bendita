import os
import uuid
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://bendita-coleccion.preview.emergentagent.com").rstrip("/")


def test_catalog_crud_and_categories():
    suffix = uuid.uuid4().hex[:8]
    category = {"name": f"TEST_{suffix}", "slug": f"test-{suffix}"}
    c = requests.post(f"{BASE_URL}/api/categories", json=category, timeout=20)
    assert c.status_code == 200, c.text
    created_category = c.json()
    assert created_category["name"] == category["name"]

    product = {"name": f"TEST_{suffix}", "description": "QA", "price": 12.5,
               "category": category["name"], "audience": "mujer", "stock": 3,
               "images": [], "variants": [], "is_new": True}
    p = requests.post(f"{BASE_URL}/api/products", json=product, timeout=20)
    assert p.status_code == 200, p.text
    created = p.json()
    assert created["name"] == product["name"] and created["price"] == 12.5
    pid = created["id"]
    listed = requests.get(f"{BASE_URL}/api/products", timeout=20)
    assert listed.status_code == 200
    assert any(item["id"] == pid for item in listed.json())

    product["name"] = f"TEST_EDITED_{suffix}"
    updated = requests.put(f"{BASE_URL}/api/products/{pid}", json={**product, "id": pid}, timeout=20)
    assert updated.status_code == 200 and updated.json()["name"] == product["name"]
    deleted = requests.delete(f"{BASE_URL}/api/products/{pid}", timeout=20)
    assert deleted.status_code == 200 and deleted.json()["ok"] is True
    assert not any(item["id"] == pid for item in requests.get(f"{BASE_URL}/api/products", timeout=20).json())
    requests.delete(f"{BASE_URL}/api/categories/{created_category['id']}", timeout=20)
