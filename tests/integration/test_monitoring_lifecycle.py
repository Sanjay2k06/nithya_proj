"""
Integration Tests for Camera Registration and Monitoring Lifecycle.
"""


def test_camera_crud_lifecycle(client):
    # 1. Register a new camera
    new_cam = {
        "name": "Integration Test Tower 9",
        "source_type": "ip_camera",
        "source_reference": "rtsp://10.0.0.1:554/live",
        "location_label": "High Ridge Sector",
        "latitude": 37.86,
        "longitude": -119.53,
        "enabled": True
    }
    res = client.post("/api/v1/monitoring/cameras", json=new_cam)
    assert res.status_code == 200
    cam_data = res.json()
    assert cam_data["name"] == new_cam["name"]
    cam_id = cam_data["id"]

    # 2. List cameras
    res_list = client.get("/api/v1/monitoring/cameras")
    assert res_list.status_code == 200
    assert any(c["id"] == cam_id for c in res_list.json())

    # 3. Check monitoring status
    res_status = client.get("/api/v1/monitoring/status")
    assert res_status.status_code == 200
    assert "active_workers_count" in res_status.json()

    # 4. Clean up / delete camera
    res_del = client.delete(f"/api/v1/monitoring/cameras/{cam_id}")
    assert res_del.status_code == 200
