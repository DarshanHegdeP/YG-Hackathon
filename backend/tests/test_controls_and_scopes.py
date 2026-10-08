from datetime import datetime, timezone, timedelta

def test_create_control_scope_assignment_and_review(client, reviewer_headers, reviewer_user):
    # 1. Create Control
    control_data = {
        "control_code": "C099",
        "name": "Cloud Security Benchmark",
        "description": "Evidence must demonstrate compliance with CIS benchmark.",
        "frequency": "MONTHLY",
        "status": "ACTIVE",
        "requirements": [
            {"name": "CIS Benchmark Report", "description": "Full scan report", "mandatory": True},
            {"name": "Remediation Ticket", "description": "Exceptions tracked", "mandatory": False}
        ]
    }
    res = client.post("/api/controls", json=control_data, headers=reviewer_headers)
    assert res.status_code == 200
    control_id = res.json()["id"]

    # 2. Create Scope
    scope_data = {
        "type": "TEAM",
        "name": "Cloud Engineering",
        "description": "Manages cloud assets",
        "email": "cloud-eng@example.com"
    }
    res = client.post("/api/scopes", json=scope_data, headers=reviewer_headers)
    assert res.status_code == 200
    scope_id = res.json()["id"]

    # 3. Create Assignment
    now_str = datetime.now(timezone.utc).isoformat()
    assign_data = {
        "control_id": control_id,
        "scope_id": scope_id,
        "reviewer_id": reviewer_user.id,
        "frequency": "MONTHLY",
        "effective_from": now_str,
        "status": "ACTIVE"
    }
    res = client.post("/api/control-assignments", json=assign_data, headers=reviewer_headers)
    assert res.status_code == 200
    assign_id = res.json()["id"]

    # 4. Create Review (which auto-creates EvidenceRequest)
    due_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    review_data = {
        "control_assignment_id": assign_id,
        "period_start": now_str,
        "period_end": due_date,
        "due_date": due_date,
        "status": "OPEN",
        "create_request": True
    }
    res = client.post("/api/reviews", json=review_data, headers=reviewer_headers)
    assert res.status_code == 200
    review_id = res.json()["id"]

    # Check request was created
    res = client.get("/api/evidence-requests", headers=reviewer_headers)
    assert res.status_code == 200
    requests = res.json()
    assert len(requests) >= 1
    req = requests[0]
    token = req["secure_token"]

    # Public endpoint token lookup
    res = client.get(f"/api/evidence-requests/token/{token}")
    assert res.status_code == 200
    pub_data = res.json()
    assert pub_data["control_code"] == "C099"
    assert pub_data["recipient_email"] == "cloud-eng@example.com"
