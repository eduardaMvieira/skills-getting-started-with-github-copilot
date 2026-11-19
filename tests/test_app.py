from collections.abc import Iterator
from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

INITIAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities() -> None:
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_root_redirects_to_activity_page(client: TestClient) -> None:
    # Arrange
    path = "/"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client: TestClient) -> None:
    # Arrange
    path = "/activities"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant(client: TestClient) -> None:
    # Arrange
    activity_name = "Art Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_unknown_activity(client: TestClient) -> None:
    # Arrange
    path = "/activities/Unknown%20Club/signup"
    email = "student@mergington.edu"

    # Act
    response = client.post(path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client: TestClient) -> None:
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(path, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert activities[activity_name]["participants"].count(email) == 1


def test_unregister_removes_participant(client: TestClient) -> None:
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(path, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client: TestClient) -> None:
    # Arrange
    path = "/activities/Unknown%20Club/signup"
    email = "student@mergington.edu"

    # Act
    response = client.delete(path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client: TestClient) -> None:
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"
    path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
