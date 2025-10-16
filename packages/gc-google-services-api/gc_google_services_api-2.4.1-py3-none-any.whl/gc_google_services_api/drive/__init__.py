import logging
import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
EMPTY_ARRAY = []


class Drive:
    """
    Google API documentation:
        - https://developers.google.com/drive/api/guides/manage-shareddrives  # noqa: E501
    """

    def __init__(self, credentials) -> None:
        self.service = build("drive", "v3", credentials=credentials)

    def store_drives(self, drives):
        for drive in drives:
            if drive["name"].startswith("AC -"):
                self._add_shared_drive(drive)

    def get_permissions_from_file(self, file_id):
        results = (
            self.service.permissions()
            .list(
                fileId=file_id,
                useDomainAdminAccess=True,
                supportsAllDrives=True,
                fields="permissions/id,permissions/displayName,permissions/role,permissions/emailAddress",  # noqa: E501
            )
            .execute()
        )

        return results.get("permissions", EMPTY_ARRAY)

    def get_shared_drives(self, next_page_token=None):
        results = (
            self.service.drives()
            .list(
                fields="nextPageToken, drives(id, name)",
                q=None,
                useDomainAdminAccess=True,
                pageToken=next_page_token,
                pageSize=100,
            )
            .execute()
        )

        drives = results.get("drives", EMPTY_ARRAY)

        next_page_token = results.get("nextPageToken", None)
        if next_page_token:
            logging.info(
                "Requesting shared drives ({})...".format(next_page_token)
            )  # noqa: E501
            drives += self.get_shared_drives(next_page_token)

        return drives

    def get_shared_drive_by_name(self, name: str):
        results = (
            self.service.drives()
            .list(
                q=f'name = "{name}"',
                fields="nextPageToken, drives(id, name)",
                useDomainAdminAccess=True,
                pageToken=None,
            )
            .execute()
        )

        return results.get("drives", EMPTY_ARRAY)

    def create_shared_drive(self, name: str) -> None:
        drive_metadata = {
            "name": name,
            "restrictions": {
                "adminManagedRestrictions": True,
                "domainUsersOnly": True,
                "copyRequiresWriterPermission": True,
                "driveMembersOnly": True,
            },
        }

        try:
            shared_drive = (
                self.service.drives()
                .create(
                    body=drive_metadata,
                    requestId=name,
                )
                .execute()
            )
        except HttpError as e:
            shared_drive = None
            logging.error(f"Error creating shared drive {name} - {e}")
        else:
            # We must wait a few seconds to add the first permission.
            # It's a bug on Google API when use a Service account.
            time.sleep(5)

        return shared_drive

    def copy_drive_folder_contents(
            self,
            source_folder_id,
            destination_folder_id
    ):
        """
        Recursively copies all files and subfolders from a source folder to
        a destination folder.
        """
        page_token = None
        while True:
            try:
                # List files and folders in the source folder
                response = self.list_files_in_drive(
                    query=f"'{source_folder_id}' in parents",
                    fields="nextPageToken, files(id, name, mimeType)",
                    page_token=page_token,
                    include_items_from_all_drives=True,
                    supports_all_drives=True
                )

                for item in response.get('files', []):
                    item_id = item.get('id')
                    item_name = item.get('name')
                    item_mime_type = item.get('mimeType')

                    if item_mime_type == 'application/vnd.google-apps.folder':
                        # It's a subfolder, create it in the destination
                        folder_metadata = {
                            'name': item_name,
                            'mimeType': 'application/vnd.google-apps.folder',
                            'parents': [destination_folder_id]
                        }
                        new_folder = self.create_file_in_drive(
                            body=folder_metadata,
                            fields='id',
                            supports_all_drives=True
                        )
                        new_folder_id = new_folder.get('id')

                        # Recursively copy the contents of the subfolder
                        self.copy_drive_folder_contents(item_id, new_folder_id)
                    else:
                        # It's a file, copy it to the destination
                        file_metadata = {
                            'name': item_name,
                            'parents': [destination_folder_id]
                        }
                        self.service.files().copy(
                            fileId=item_id,
                            body=file_metadata,
                            supportsAllDrives=True
                        ).execute()

                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break
            except HttpError as error:
                logging.error(f"An error occurred: {error}")
                return False
        return True

    def create_file_in_drive(
            self,
            body,
            fields=None,
            supports_all_drives=False
    ):
        return self.service.files().create(
            body=body,
            fields=fields,
            supportsAllDrives=supports_all_drives,
        ).execute()

    def list_files_in_drive(
        self,
        query=None,
        fields=None,
        page_token=None,
        include_items_from_all_drives=False,
        supports_all_drives=False
    ):
        return self.service.files().list(
            q=query,
            fields=fields,
            pageToken=page_token,
            includeItemsFromAllDrives=include_items_from_all_drives,
            supportsAllDrives=supports_all_drives,
        ).execute()

    def set_group_in_shared_drive_permissions(
        self,
        drive_id: str,
        group_email: str,
    ) -> bool:
        success = False
        permission_config = {
            "type": "group",
            "role": "fileOrganizer",
            "emailAddress": group_email,
        }

        try:
            permission_result = (
                self.service.permissions()
                .create(
                    fileId=drive_id,
                    body=permission_config,
                    transferOwnership=False,
                    useDomainAdminAccess=True,
                    supportsAllDrives=True,
                    fields="id",
                )
                .execute()
            )
        except HttpError as e:
            logging.error(
                f"Error setting group permissions in shared drive {drive_id} - {e}"  # noqa: E501
            )
        else:
            success = isinstance(
                permission_result, dict
            ) and permission_result.get(  # noqa: E501
                "id"
            )
            # We must wait a few seconds to add the permission.
            # It's a bug on Google API when use a Service account.
            logging.info(
                "Waiting to add permissions to group into shared drive"
            )  # noqa: E501
            time.sleep(5)

        return success

    def set_shared_drive_admin_permissions(
        self, drive_id: str, users: list
    ) -> bool:  # noqa: E501
        success = True
        for user_email in users:
            permission_config = {
                "type": "user",
                "role": "organizer",
                "emailAddress": user_email,
            }
            try:
                permission_result = (
                    self.service.permissions()
                    .create(
                        fileId=drive_id,
                        body=permission_config,
                        transferOwnership=False,
                        useDomainAdminAccess=True,
                        supportsAllDrives=True,
                        fields="id",
                    )
                    .execute()
                )
            except HttpError as e:
                logging.error(
                    f"Error setting user permissions in shared drive {drive_id} - {e}"  # noqa: E501
                )
                success = False
            else:
                success = isinstance(
                    permission_result, dict
                ) and permission_result.get(  # noqa: E501
                    "id"
                )
                # We must wait a few seconds to add the permissions.
                # It's a bug on Google API when use a Service account.
                logging.info(
                    "Waiting to add permissions to next user into shared drive"
                )
                time.sleep(5)

        return success
