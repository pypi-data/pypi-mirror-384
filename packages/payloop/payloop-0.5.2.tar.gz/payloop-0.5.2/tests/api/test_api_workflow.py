import datetime
import os

from payloop import Payloop


def test_workflows_list():
    os.environ["PAYLOOP_API_URL_BASE"] = "https://staging-api.trypayloop.com"

    payloop = Payloop(
        api_key="dev-_z3aNG2Si5cnuPPFDSyMhXICtqVziwCzjJqM-w8u0gYWxHAj6ASojR7NWoKELc3hrrC3atTOESpts87BN-AKj83rzpprU48w8SMmJfRa3jL1mEN7_RA_n6NSQoUwsqMKHjqtWMPWwxp2yKEMpqb2vVgb3tS3UeqIF6BDXypyA60"
    )

    response = payloop.workflows.list()
    assert len(response) == 2
    assert response[0]["name"] == "Test Workflow 1"
    assert response[1]["name"] == "Test Workflow 2"


def test_workflow_update():
    os.environ["PAYLOOP_API_URL_BASE"] = "https://staging-api.trypayloop.com"

    payloop = Payloop(
        api_key="dev-_z3aNG2Si5cnuPPFDSyMhXICtqVziwCzjJqM-w8u0gYWxHAj6ASojR7NWoKELc3hrrC3atTOESpts87BN-AKj83rzpprU48w8SMmJfRa3jL1mEN7_RA_n6NSQoUwsqMKHjqtWMPWwxp2yKEMpqb2vVgb3tS3UeqIF6BDXypyA60"
    )

    response = payloop.workflows.list()
    assert len(response) == 2
    assert response[0]["label"] is None
    assert response[0]["name"] == "Test Workflow 1"
    assert response[1]["label"] is None
    assert response[1]["name"] == "Test Workflow 2"

    payloop.workflow.update(response[0]["uuid"], label="Updated Test Workflow 1")

    response = payloop.workflows.list()
    assert len(response) == 2
    assert response[0]["label"] == "Updated Test Workflow 1"
    assert response[0]["name"] == "Test Workflow 1"
    assert response[1]["label"] is None
    assert response[1]["name"] == "Test Workflow 2"

    payloop.workflow.update(response[0]["uuid"], label=None)

    response = payloop.workflows.list()
    assert len(response) == 2
    assert response[0]["label"] is None
    assert response[0]["name"] == "Test Workflow 1"
    assert response[1]["label"] is None
    assert response[1]["name"] == "Test Workflow 2"


def test_workflow_invocation_unattributed():
    os.environ["PAYLOOP_API_URL_BASE"] = "https://staging-api.trypayloop.com"

    payloop = Payloop(
        api_key="dev-_z3aNG2Si5cnuPPFDSyMhXICtqVziwCzjJqM-w8u0gYWxHAj6ASojR7NWoKELc3hrrC3atTOESpts87BN-AKj83rzpprU48w8SMmJfRa3jL1mEN7_RA_n6NSQoUwsqMKHjqtWMPWwxp2yKEMpqb2vVgb3tS3UeqIF6BDXypyA60"
    )

    response = payloop.workflow.invocation.summary(
        "09045f20-486e-476b-b76f-e26e129574f9", datetime.date(1974, 1, 1)
    )
    assert response == {
        "attributed": [],
        "total": 123,
        "unattributed": [{"date": "1974-01-01", "total": 123}],
        "workflow": {
            "label": None,
            "name": "Test Workflow 1",
            "uuid": "09045f20-486e-476b-b76f-e26e129574f9",
        },
    }


def test_workflow_invocation_attributed():
    os.environ["PAYLOOP_API_URL_BASE"] = "https://staging-api.trypayloop.com"

    payloop = Payloop(
        api_key="dev-_z3aNG2Si5cnuPPFDSyMhXICtqVziwCzjJqM-w8u0gYWxHAj6ASojR7NWoKELc3hrrC3atTOESpts87BN-AKj83rzpprU48w8SMmJfRa3jL1mEN7_RA_n6NSQoUwsqMKHjqtWMPWwxp2yKEMpqb2vVgb3tS3UeqIF6BDXypyA60"
    )

    response = payloop.workflow.invocation.attribution("Test Customer A").summary(
        "f68992f8-ca54-4b19-9ae4-5c3f4ccc2080", datetime.date(1974, 1, 1)
    )
    assert response == {
        "attributed": [
            {
                "attribution": {
                    "parent": {
                        "id": "Test Customer A",
                        "name": None,
                    },
                    "subsidiary": {
                        "id": None,
                        "name": None,
                    },
                },
                "date": "1974-01-02",
                "total": 456,
            },
        ],
        "total": 456,
        "unattributed": [],
        "workflow": {
            "label": None,
            "name": "Test Workflow 2",
            "uuid": "f68992f8-ca54-4b19-9ae4-5c3f4ccc2080",
        },
    }
