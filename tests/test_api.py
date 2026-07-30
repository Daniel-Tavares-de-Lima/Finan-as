def test_post_emprestimo_and_get(client):
    payload = {
        "salario": 5000.00,
        "perfil": "CLT",
        "valor_solicitado": 10000.00,
        "numero_parcelas": 24,
    }

    r = client.post("/api/v1/simulacoes/emprestimo", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["tipo"] == "EMPRESTIMO"
    sim_id = data["id"]

    r2 = client.get(f"/api/v1/simulacoes/{sim_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == sim_id


def test_post_cartao_and_get(client):
    payload = {"salario": 5000.00, "perfil": "INSS"}
    r = client.post("/api/v1/simulacoes/cartao", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["tipo"] == "CARTAO"
    sim_id = data["id"]

    r2 = client.get(f"/api/v1/simulacoes/{sim_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == sim_id
