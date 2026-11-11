def test_environmental_readings_are_empty_until_real_input_is_posted(client):
    response = client.get("/api/v1/environment/readings")

    assert response.status_code == 200
    assert response.json() == []


def test_environmental_reading_is_validated_persisted_and_filterable(client):
    created = client.post(
        "/api/v1/environment/readings",
        json={
            "source_id": "cam02-fire",
            "temperature_c": 27.5,
            "humidity_percent": 48,
            "wind_speed_mps": 2.4,
            "wind_direction_degrees": 180,
            "smoke_sensor_value": 0.12,
        },
    )

    assert created.status_code == 201
    record = created.json()
    assert record["source_id"] == "cam02-fire"
    assert record["temperature_c"] == 27.5

    history = client.get("/api/v1/environment/readings?source_id=cam02-fire")
    assert history.status_code == 200
    assert [item["id"] for item in history.json()] == [record["id"]]


def test_environmental_reading_rejects_missing_or_out_of_range_values(client):
    missing = client.post(
        "/api/v1/environment/readings",
        json={"source_id": "sensor-1"},
    )
    invalid = client.post(
        "/api/v1/environment/readings",
        json={"source_id": "sensor-1", "humidity_percent": 160},
    )

    assert missing.status_code == 422
    assert invalid.status_code == 422
