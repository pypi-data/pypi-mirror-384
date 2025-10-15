from enum import IntEnum

class DownloadRequestStatus(IntEnum):
    NONE = 0
    # When a user starts their download request.
    ENQUEUED = 1
    # Download approval requested from the digital object's owner.
    APPROVAL_REQUESTED = 2
    # Waiting for approval from the owner to download the requested files.
    WAITING_FOR_APPROVAL = 3
    # All files in the current request were approved (if applicable).
    APPROVED = 4
    # The download request was not authorized by the owner(s).
    DECLINED = 5
    # Approved requests will be prepared to be delivered.
    HANDLE_FILES_TO_BE_DELIVERED = 6
    # Status while the set of files are being compacted.
    COMPACTING_BUNDLE = 7
    # The download request is completed and ready to be downloaded.
    COMPLETED = 8
    # Incomplete request: not all files are available to download.
    INCOMPLETE = 9
    # Request is invalid or cannot be processed due to missing/invalid data.
    FAILED = 10

class DownloadRequestItemStatus(IntEnum):
    # Digital Object download request was enqueued.
    ENQUEUED = 1
    # Download approval requested from the digital object's owner.
    APPROVAL_REQUESTED = 2
    # Waiting for approval by the digital object owner.
    WAITING_FOR_APPROVAL = 3
    # Download of the digital object was approved by its owner.
    APPROVED = 4
    # Download of the digital object was denied by its owner.
    DECLINED = 5
    # Notification of decline has been sent.
    DECLINED_NOTIFICATION_SENT = 6
    # Waiting to be downloaded.
    WAITING_TO_BE_DOWNLOADED = 7
    # In process.
    IN_PROCESS = 8
    # File is ready to be delivered.
    AVAILABLE_TO_DOWNLOAD = 9
    # Internal error occurred.
    ERROR = 10    