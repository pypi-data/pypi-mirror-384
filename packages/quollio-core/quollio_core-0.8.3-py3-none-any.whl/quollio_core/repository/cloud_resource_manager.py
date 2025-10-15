from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class CloudResourceManagerClient:
    """Client to interact with the Cloud Resource Manager API."""

    def __init__(self, credentials: Credentials) -> None:
        """Initialize the Cloud Resource Manager client with provided credentials."""
        self.client = self.__initialize(credentials=credentials)

    def __initialize(self, credentials: Credentials):
        return build("cloudresourcemanager", "v1", credentials=credentials)

    def list_projects(self):
        """List all projects accessible with the current credentials."""
        request = self.client.projects().list()
        response = request.execute()
        return response

    def get_project(self, project_id: str):
        """Get a specific project by project ID."""
        request = self.client.projects().get(projectId=project_id)
        response = request.execute()
        return response
