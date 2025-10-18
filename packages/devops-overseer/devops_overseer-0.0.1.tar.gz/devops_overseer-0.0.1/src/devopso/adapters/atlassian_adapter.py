from devopso.core.logging import ConfiguredLogger
from devopso.adapters.jira_cloud_adapter import JiraCloud
from devopso.clients.jira_cloud.models.user import User


class Atlassian(ConfiguredLogger):
    """High-level adapter providing convenience methods for retrieving
    user and group data from Atlassian (Jira Cloud) APIs.

    This class leverages the `JiraCloud` adapter to aggregate user
    and teammate information across groups, while inheriting structured
    logging capabilities from `ConfiguredLogger`.

    Attributes:
        _DEFAULT_PATH_CONFIGURATION (str): Default path to the adapter's configuration file.
    """

    _DEFAULT_PATH_CONFIGURATION = "resources/configs/adapters/atlassian.yml"

    def __init__(self) -> None:
        """Initialize the Atlassian adapter.

        Loads the logger configuration defined in the adapter's configuration file.
        """
        super().__init__(Atlassian._DEFAULT_PATH_CONFIGURATION)

    @staticmethod
    def get_current_user_teammates(ignore_groups: list[str]) -> dict[str, User]:
        """Retrieve all teammates of the currently authenticated Jira user.

        Args:
            ignore_groups (list[str]): List of group names to exclude from the search.

        Returns:
            dict[str, User]: A dictionary mapping display names to `User` objects
            representing the teammates of the current user, excluding those
            in ignored groups.
        """
        return Atlassian.get_user_teammates(JiraCloud.get_myself().account_id, ignore_groups)

    @staticmethod
    def get_user_teammates(user_id: str, ignore_groups: list[str]) -> dict[str, User]:
        """Retrieve all teammates of a given Jira user by their account ID.

        This method gathers all users who share at least one group
        with the specified user, excluding groups listed in `ignore_groups`.

        Args:
            user_id (str): The Jira account ID of the user whose teammates should be retrieved.
            ignore_groups (list[str]): List of group names to exclude from the search.

        Returns:
            dict[str, User]: A dictionary mapping display names to `User` objects
            representing the teammates of the given user.
        """
        a = Atlassian()
        users = {}
        user_account = JiraCloud.get_user_by_account_id(user_id)
        for group in user_account.groups.items:
            if group.name not in ignore_groups:
                users = users | Atlassian.get_group_accounts(group.group_id)
        return users

    @staticmethod
    def get_group_accounts(group_id: str) -> dict[str, User]:
        """Retrieve all user accounts belonging to a specific Jira group.

        Args:
            group_id (str): The unique identifier of the Jira group.

        Returns:
            dict[str, User]: A dictionary mapping display names to `User` objects
            representing all members of the specified group.
        """
        users = {}
        group_members = JiraCloud.get_users_from_group_id(group_id)
        for account_x in group_members.values:
            users[account_x.display_name] = account_x
        return users
