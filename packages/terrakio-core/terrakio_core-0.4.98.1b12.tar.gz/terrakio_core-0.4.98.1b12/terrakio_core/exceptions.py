class APIError(Exception):
    """Exception raised for errors in the API responses."""
    
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

class ConfigurationError(Exception):
    """Exception raised for errors in the configuration."""
    pass


class DownloadError(Exception):
    """Exception raised for errors during data download."""
    pass


class ValidationError(Exception):
    """Exception raised for invalid request parameters."""
    pass

class NetworkError(Exception):
    """Exception raised for network errors."""
    pass

class AuthenticationExpireError(Exception):
   """Exception raised for authentication expire errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class QuotaError(Exception):
   """Exception raised for quota errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class UserInfoError(Exception):
   """Exception raised for user info errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class APIKeyError(Exception):
   """Exception raised for API key errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class RefreshAPIKeyError(Exception):
   """Exception raised for refresh API key errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class InvalidUsernamePasswordError(Exception):
   """Exception raised for invalid username or password errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class LoginError(Exception):
   """Exception raised for login errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class ResetPasswordError(Exception):
   """Exception raised for reset password errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class SignupError(Exception):
   """Exception raised for signup errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class InvalidEmailFormatError(Exception):
   """Exception raised for invalid email format errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class EmailAlreadyExistsError(Exception):
   """Exception raised for email already exists errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class UserNotFoundError(Exception):
   """Exception raised for user not found errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class GetUserByIdError(Exception):
   """Exception raised for get user by id errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class GetUserByEmailError(Exception):
   """Exception raised for get user by email errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class ListUsersError(Exception):
   """Exception raised for list users errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class EditUserError(Exception):
   """Exception raised for edit user errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class ResetQuotaError(Exception):
   """Exception raised for reset quota errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class DeleteUserError(Exception):
   """Exception raised for delete user errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class ChangeRoleError(Exception):
   """Exception raised for change role errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class ListGroupsError(Exception):
   """Exception raised for list groups errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class GetGroupError(Exception):
   """Exception raised for get group errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class GetGroupDatasetsError(Exception):
   """Exception raised for get group datasets errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class NoDatasetsFoundForGroupError(Exception):
   """Exception raised for no datasets found for group errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class CreateGroupError(Exception):
   """Exception raised for create group errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class DeleteGroupError(Exception):
   """Exception raised for delete group errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class AddUserToGroupError(Exception):
   """Exception raised for add user to group errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class AddGroupToDatasetError(Exception):
   """Exception raised for add group to dataset errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class AddUserToDatasetError(Exception):
   """Exception raised for add user to dataset errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class RemoveUserFromGroupError(Exception):
   """Exception raised for remove user from group errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class RemoveUserFromDatasetError(Exception):
   """Exception raised for remove user from dataset errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class GroupNotFoundError(Exception):
   """Exception raised for group not found errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class GroupPermissionError(Exception):
   """Exception raised for group permission errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class CommandPermissionError(Exception):
   """Exception raised for command permission errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class DatasetNotFoundError(Exception):
   """Exception raised for dataset not found errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class RemoveGroupFromDatasetError(Exception):
   """Exception raised for remove group from dataset errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class ListDatasetsError(Exception):
   """Exception raised for list datasets errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class GetUsersByRoleError(Exception):
   """Exception raised for get users by role errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class RoleDoNotExistError(Exception):
   """Exception raised for role does not exist errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class ChangeRoleError(Exception):
   """Exception raised for change role errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class GetDatasetError(Exception):
   """Exception raised for get dataset errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class DatasetPermissionError(Exception):
   """Exception raised for dataset permission errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class CreateDatasetError(Exception):
   """Exception raised for create dataset errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class DatasetAlreadyExistsError(Exception):
   """Exception raised for dataset already exists errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class DeleteDatasetError(Exception):
   """Exception raised for delete dataset errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class OverwriteDatasetError(Exception):
   """Exception raised for overwrite dataset errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class ListCollectionsError(Exception):
   """Exception raised for list collections errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class GetCollectionError(Exception):
   """Exception raised for get collection errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class CreateCollectionError(Exception):
   """Exception raised for create collection errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class CollectionNotFoundError(Exception):
   """Exception raised for collection not found errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class CollectionAlreadyExistsError(Exception):
   """Exception raised for collection already exists errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class InvalidCollectionTypeError(Exception):
   """Exception raised for invalid collection type errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class DeleteCollectionError(Exception):
   """Exception raised for delete collection errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class ListTasksError(Exception):
   """Exception raised for list tasks errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class UploadRequestsError(Exception):
   """Exception raised for upload requests errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class UploadArtifactsError(Exception):
   """Exception raised for upload artifacts errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class GetTaskError(Exception):
   """Exception raised for get task errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class TaskNotFoundError(Exception):
   """Exception raised for task not found errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class DownloadFilesError(Exception):
   """Exception raised for download files errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class CancelTaskError(Exception):
   """Exception raised for cancel task errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class CancelCollectionTasksError(Exception):
   """Exception raised for cancel collection tasks errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code

class CancelAllTasksError(Exception):
   """Exception raised for cancel all tasks errors."""
   def __init__(self, message: str, status_code: int = None):
       super().__init__(message)
       self.status_code = status_code