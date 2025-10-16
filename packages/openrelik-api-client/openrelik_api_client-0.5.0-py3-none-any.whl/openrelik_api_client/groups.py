# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any

from openrelik_api_client.api_client import APIClient


class GroupsAPI:
    """
    Manages groups for Oppenrelik.
    Provides functionalities for creating, retrieving, updating,
    deleting groups, and managing group memberships.
    """

    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.groups_url = f"{self.api_client.base_url}/groups"

    def create_group(self, name: str, description: str = "") -> dict[str, Any] | None:
        """
        Creates a new group.

        Args:
            name: The name of the group.
            description: An optional description for the group.

        Returns:
            A dictionary representing the newly created group if successful,
            None otherwise.

        Raises:
            ValueError: If the group name is empty.
            requests.exceptions.HTTPError: If the API request failed.
        """
        if not name:
            raise ValueError("Group name cannot be empty.")

        endpoint = f"{self.groups_url}/"
        data = {
            "name": name,
            "description": description,
        }
        response = self.api_client.session.post(endpoint, json=data)
        response.raise_for_status()
        if response.status_code == 201:
            return response.json()
        return None

    def remove_group(self, group_name: str) -> bool:
        """
        Removes a group by its name.

        Args:
            group_name: The name of the group to remove.

        Returns:
            True if the group was successfully removed.

        Raises:
            requests.exceptions.HTTPError: If the API request failed.
        """
        endpoint = f"{self.groups_url}/{group_name}"
        response = self.api_client.session.delete(endpoint)
        response.raise_for_status()
        return response.status_code == 204

    def list_group_members(self, group_name: str) -> dict[str, Any] | None:
        """
        Retrieves a group by its name.

        Args:
            group_name: The name of the group to retrieve.

        Returns:
            A dictionary representing the group if found, None otherwise.

        Raises:
            requests.exceptions.HTTPError: If the API request failed (e.g., 404 Not Found).
        """
        endpoint = f"{self.groups_url}/{group_name}/users"
        response = self.api_client.session.get(endpoint)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        return None

    def list_groups(self) -> list[dict[str, Any]]:
        """
        Lists all existing groups.

        Returns:
            A list of dictionaries, where each dictionary represents a group.

        Raises:
            requests.exceptions.HTTPError: If the API request failed.
        """
        endpoint = f"{self.groups_url}/"
        response = self.api_client.session.get(endpoint)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        return []

    def delete_group(self, group_name: str) -> bool:
        """
        Deletes a group by its name.

        Args:
            group_name: The name of the group to delete.

        Returns:
            True if the group was successfully deleted.

        Raises:
            requests.exceptions.HTTPError: If the API request failed.
        """
        endpoint = f"{self.groups_url}/{group_name}"
        response = self.api_client.session.delete(endpoint)
        response.raise_for_status()
        return response.status_code == 204

    def add_users_to_group(self, group_name: str, users: list[str]) -> bool:
        """
        Adds a user to a group.

        Args:
            group_name: The name of the group.
            users: The users to add.

        Returns:
            List of users that were added.

        Raises:
            requests.exceptions.HTTPError: If the API request failed (e.g., group not found, user already member).
        """
        endpoint = f"{self.groups_url}/{group_name}/users/"
        response = self.api_client.session.post(endpoint, json=users)
        response.raise_for_status()
        return response.json()

    def remove_users_from_group(self, group_name: int, users: list[str]) -> bool:
        """
        Removes a user from a group.

        Args:
            group_name: The name of the group.
            users: The users to remove.

        Returns:
            List of users that were removed.

        Raises:
            requests.exceptions.HTTPError: If the API request failed (e.g., group/user not found).
        """
        endpoint = f"{self.groups_url}/{group_name}/users"
        response = self.api_client.session.delete(endpoint, json=users)
        response.raise_for_status()
        return response.json()

    def is_member(self, group_name: str, user_name: str) -> bool:
        """
        Checks if a user is a member of a specific group.

        Args:
            group_name: The ID of the group.
            user_name: The ID of the user.

        Returns:
            True if the user is a member, False otherwise.
        """
        endpoint = f"{self.groups_url}/{group_name}/users/"
        response = self.api_client.session.get(endpoint)
        username = None
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx
        for user in response.json():
            username = user["username"]
        return user_name == username
