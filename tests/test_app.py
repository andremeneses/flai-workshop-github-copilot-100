"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original participants
    original_participants = {
        name: details["participants"].copy()
        for name, details in activities.items()
    }
    yield
    # Restore original participants after each test
    for name, details in activities.items():
        details["participants"] = original_participants[name]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Basketball Team" in data
        assert "Swimming Club" in data
        assert "Drama Club" in data
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        for name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Swimming%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Signed up newstudent@mergington.edu for Swimming Club"

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_already_registered(self, client):
        """Test signup when student is already registered"""
        # First signup
        client.post("/activities/Swimming%20Club/signup?email=test@mergington.edu")
        # Try to signup again
        response = client.post(
            "/activities/Swimming%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_updates_participants_list(self, client):
        """Test that signup adds student to participants list"""
        email = "newparticipant@mergington.edu"
        client.post(f"/activities/Swimming%20Club/signup?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Swimming Club"]["participants"]


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # First signup
        client.post("/activities/Swimming%20Club/signup?email=tounregister@mergington.edu")
        # Then unregister
        response = client.delete(
            "/activities/Swimming%20Club/unregister?email=tounregister@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Unregistered tounregister@mergington.edu from Swimming Club"

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up(self, client):
        """Test unregister when student is not signed up"""
        response = client.delete(
            "/activities/Swimming%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_removes_from_participants_list(self, client):
        """Test that unregister removes student from participants list"""
        email = "toremove@mergington.edu"
        # Signup first
        client.post(f"/activities/Swimming%20Club/signup?email={email}")
        # Verify added
        response = client.get("/activities")
        assert email in response.json()["Swimming Club"]["participants"]
        # Unregister
        client.delete(f"/activities/Swimming%20Club/unregister?email={email}")
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()["Swimming Club"]["participants"]
