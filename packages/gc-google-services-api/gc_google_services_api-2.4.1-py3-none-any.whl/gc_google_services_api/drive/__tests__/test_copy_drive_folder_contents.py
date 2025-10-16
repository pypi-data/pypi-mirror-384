import unittest
from unittest.mock import MagicMock, patch

from gc_google_services_api.drive import Drive


class TestCopyDriveFolderContents(unittest.TestCase):
    @patch("gc_google_services_api.drive.build")
    def setUp(self, mock_build):
        self.mock_credentials = MagicMock()
        self.mock_service = MagicMock()
        mock_build.return_value = self.mock_service

        self.drive = Drive(self.mock_credentials)

    def test_copy_drive_folder_contents_success(self):
        """Test successful copying of files and folders"""
        source_folder_id = "source_folder_id"
        destination_folder_id = "destination_folder_id"

        # Mock the files().list() response
        mock_files_response = {
            'files': [
                {
                    'id': 'file1_id',
                    'name': 'document.pdf',
                    'mimeType': 'application/pdf'
                },
                {
                    'id': 'folder1_id',
                    'name': 'Subfolder',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
            ],
            'nextPageToken': None
        }

        # Mock the files().create() response for folder creation
        mock_folder_response = {'id': 'new_folder_id'}

        # Mock the files().copy() response
        mock_copy_response = {'id': 'copied_file_id'}

        # Mock the recursive call to return empty folder for subfolder
        empty_folder_response = {'files': [], 'nextPageToken': None}

        self.mock_service.files().list().execute.side_effect = [
            mock_files_response,
            empty_folder_response  # For the recursive call to the subfolder
        ]
        self.mock_service.files().create().execute.return_value = (
            mock_folder_response
        )
        self.mock_service.files().copy().execute.return_value = (
            mock_copy_response
        )

        result = self.drive.copy_drive_folder_contents(
            source_folder_id, destination_folder_id
        )

        self.assertTrue(result)

        # Verify files().list() was called twice (main folder and subfolder)
        self.assertEqual(
            self.mock_service.files().list().execute.call_count, 2
        )

        # Verify folder creation was called
        self.mock_service.files().create.assert_called_with(
            body={
                'name': 'Subfolder',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [destination_folder_id]
            },
            fields='id',
            supportsAllDrives=True
        )

        # Verify file copy was called
        self.mock_service.files().copy.assert_called_with(
            fileId='file1_id',
            body={
                'name': 'document.pdf',
                'parents': [destination_folder_id]
            },
            supportsAllDrives=True
        )

    def test_copy_drive_folder_contents_with_subfolders(self):
        """Test recursive copying with nested subfolders"""
        source_folder_id = "source_folder_id"
        destination_folder_id = "destination_folder_id"

        # Mock the files().list() response for the main folder
        mock_main_response = {
            'files': [
                {
                    'id': 'subfolder_id',
                    'name': 'Subfolder',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
            ],
            'nextPageToken': None
        }

        # Mock the files().list() response for the subfolder
        mock_subfolder_response = {
            'files': [
                {
                    'id': 'nested_file_id',
                    'name': 'nested_file.txt',
                    'mimeType': 'text/plain'
                }
            ],
            'nextPageToken': None
        }

        # Mock the files().create() response for folder creation
        mock_folder_response = {'id': 'new_subfolder_id'}

        # Mock the files().copy() response
        mock_copy_response = {'id': 'copied_nested_file_id'}

        # Set up the mock to return different responses for different calls
        self.mock_service.files().list().execute.side_effect = [
            mock_main_response,
            mock_subfolder_response
        ]
        self.mock_service.files().create().execute.return_value = (
            mock_folder_response
        )
        self.mock_service.files().copy().execute.return_value = (
            mock_copy_response
        )

        result = self.drive.copy_drive_folder_contents(
            source_folder_id, destination_folder_id
        )

        self.assertTrue(result)

        # Verify files().list() was called twice (main folder and subfolder)
        self.assertEqual(
            self.mock_service.files().list().execute.call_count, 2
        )

        # Verify folder creation was called
        self.mock_service.files().create.assert_called_with(
            body={
                'name': 'Subfolder',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [destination_folder_id]
            },
            fields='id',
            supportsAllDrives=True
        )

        # Verify file copy was called for the nested file
        self.mock_service.files().copy.assert_called_with(
            fileId='nested_file_id',
            body={
                'name': 'nested_file.txt',
                'parents': ['new_subfolder_id']
            },
            supportsAllDrives=True
        )

    def test_copy_drive_folder_contents_empty_folder(self):
        """Test copying an empty folder"""
        source_folder_id = "source_folder_id"
        destination_folder_id = "destination_folder_id"

        # Mock the files().list() response with no files
        mock_empty_response = {
            'files': [],
            'nextPageToken': None
        }

        self.mock_service.files().list().execute.return_value = (
            mock_empty_response
        )

        result = self.drive.copy_drive_folder_contents(
            source_folder_id, destination_folder_id
        )

        self.assertTrue(result)

        # Verify files().list() was called
        self.mock_service.files().list.assert_called()

        # Verify no files were created or copied
        self.mock_service.files().create.assert_not_called()
        self.mock_service.files().copy.assert_not_called()

    def test_copy_drive_folder_contents_http_error(self):
        """Test handling of HttpError exceptions"""
        source_folder_id = "source_folder_id"
        destination_folder_id = "destination_folder_id"

        # Mock HttpError
        from googleapiclient.errors import HttpError
        mock_http_error = HttpError(resp=MagicMock(), content=b'Error')
        self.mock_service.files().list().execute.side_effect = (
            mock_http_error
        )

        result = self.drive.copy_drive_folder_contents(
            source_folder_id, destination_folder_id
        )

        self.assertFalse(result)

    def test_copy_drive_folder_contents_pagination(self):
        """Test handling of paginated results"""
        source_folder_id = "source_folder_id"
        destination_folder_id = "destination_folder_id"

        # Mock the first page response
        mock_first_page = {
            'files': [
                {
                    'id': 'file1_id',
                    'name': 'file1.pdf',
                    'mimeType': 'application/pdf'
                }
            ],
            'nextPageToken': 'next_token'
        }

        # Mock the second page response
        mock_second_page = {
            'files': [
                {
                    'id': 'file2_id',
                    'name': 'file2.pdf',
                    'mimeType': 'application/pdf'
                }
            ],
            'nextPageToken': None
        }

        # Mock the files().copy() response
        mock_copy_response = {'id': 'copied_file_id'}

        self.mock_service.files().list().execute.side_effect = [
            mock_first_page,
            mock_second_page
        ]
        self.mock_service.files().copy().execute.return_value = (
            mock_copy_response
        )

        result = self.drive.copy_drive_folder_contents(
            source_folder_id, destination_folder_id
        )

        self.assertTrue(result)

        # Verify files().list() was called twice (for pagination)
        self.assertEqual(
            self.mock_service.files().list().execute.call_count, 2
        )

        # Verify both files were copied
        self.assertEqual(
            self.mock_service.files().copy().execute.call_count, 2
        )

        # Verify the second call used the nextPageToken
        # The second call should have pageToken='next_token'
        calls = self.mock_service.files().list.call_args_list
        # Find the call with pageToken='next_token'
        found_token_call = False
        for call in calls:
            if len(call) > 1 and call[1].get('pageToken') == 'next_token':
                found_token_call = True
                break
        self.assertTrue(
            found_token_call,
            "Expected to find a call with pageToken='next_token'"
        )

    def test_copy_drive_folder_contents_mixed_content(self):
        """Test copying a folder with mixed files and subfolders"""
        source_folder_id = "source_folder_id"
        destination_folder_id = "destination_folder_id"

        # Mock response with mixed content
        mock_response = {
            'files': [
                {
                    'id': 'file1_id',
                    'name': 'document.pdf',
                    'mimeType': 'application/pdf'
                },
                {
                    'id': 'folder1_id',
                    'name': 'Subfolder1',
                    'mimeType': 'application/vnd.google-apps.folder'
                },
                {
                    'id': 'file2_id',
                    'name': 'spreadsheet.xlsx',
                    'mimeType': (
                        'application/vnd.openxmlformats-officedocument.'
                        'spreadsheetml.sheet'
                    )
                },
                {
                    'id': 'folder2_id',
                    'name': 'Subfolder2',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
            ],
            'nextPageToken': None
        }

        # Mock responses for empty subfolders
        empty_folder_response = {'files': [], 'nextPageToken': None}

        # Mock responses
        mock_folder_response = {'id': 'new_folder_id'}
        mock_copy_response = {'id': 'copied_file_id'}

        # Set up side effects for multiple list calls
        # (main folder + 2 subfolders)
        self.mock_service.files().list().execute.side_effect = [
            mock_response,
            empty_folder_response,  # For Subfolder1
            empty_folder_response   # For Subfolder2
        ]
        self.mock_service.files().create().execute.return_value = (
            mock_folder_response
        )
        self.mock_service.files().copy().execute.return_value = (
            mock_copy_response
        )

        result = self.drive.copy_drive_folder_contents(
            source_folder_id, destination_folder_id
        )

        self.assertTrue(result)

        # Verify files().list() was called 3 times (main folder + 2 subfolders)
        self.assertEqual(
            self.mock_service.files().list().execute.call_count, 3
        )

        # Verify folders were created (2 folders)
        self.assertEqual(
            self.mock_service.files().create().execute.call_count, 2
        )

        # Verify files were copied (2 files)
        self.assertEqual(
            self.mock_service.files().copy().execute.call_count, 2
        )
