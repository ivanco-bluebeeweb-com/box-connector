"""Pydantic input contracts and SDL result entities for Box Connector."""
from __future__ import annotations

from imperal_sdk import sdl
from pydantic import BaseModel, Field


class NoParams(BaseModel):
    pass


class ConnectionRefParams(BaseModel):
    connection_id: str = Field("", description="Optional saved Box enterprise connection ID. Omit to use the first connected enterprise.")


class ConnectBoxParams(BaseModel):
    label: str = Field("", description="Friendly enterprise label, e.g. 'Acme Corp Box'.")
    client_id: str = Field(..., description="Box Custom App Client ID, from Developer Console > Configuration.")
    client_secret: str = Field(..., description="Box Custom App Client Secret, from Developer Console > Configuration.")
    enterprise_id: str = Field(..., description="Box Enterprise ID, from Developer Console or Admin Console.")
    default_as_user_id: str = Field("", description="Optional: Box user ID to impersonate by default (requires admin-authorized as-user scope). Leave blank to act as the enterprise Service Account.")


class DisconnectBoxParams(ConnectionRefParams):
    connection_id: str = Field(..., description="Saved Box enterprise connection ID to remove from Imperal.")


class FolderIdParams(ConnectionRefParams):
    folder_id: str = Field("0", description="Box folder ID. Use '0' for the root folder.")


class ListFolderItemsParams(FolderIdParams):
    limit: int = Field(100, description="Max items to return (1-1000).")


class CreateFolderParams(ConnectionRefParams):
    name: str = Field(..., description="New folder name, e.g. 'Q3 Contracts'.")
    parent_folder_id: str = Field("0", description="Parent folder ID to create the new folder inside. Use '0' for root.")


class RenameOrMoveFolderParams(FolderIdParams):
    name: str = Field("", description="New folder name. Leave blank to keep the current name.")
    new_parent_folder_id: str = Field("", description="Destination parent folder ID to move into. Leave blank to keep in place.")


class DeleteFolderParams(FolderIdParams):
    recursive: bool = Field(False, description="Delete even if the folder still contains items.")


class FileIdParams(ConnectionRefParams):
    file_id: str = Field(..., description="Box file ID, from list_folder_items or search_files.")


class DownloadFileParams(FileIdParams):
    pass


class UploadFileParams(ConnectionRefParams):
    folder_id: str = Field("0", description="Folder ID to upload into. Use '0' for root.")
    name: str = Field(..., description="File name to save as, e.g. 'contract.pdf'.")
    content_base64: str = Field(..., description="Base64-encoded file content.")


class UpdateFileParams(FileIdParams):
    name: str = Field("", description="New file name. Leave blank to keep the current name.")
    new_parent_folder_id: str = Field("", description="Destination parent folder ID to move into. Leave blank to keep in place.")


class CopyFileParams(FileIdParams):
    target_folder_id: str = Field(..., description="Destination folder ID to copy into.")
    new_name: str = Field("", description="Optional new name for the copy. Leave blank to keep the current name.")


class DeleteFileParams(FileIdParams):
    pass


class SearchFilesParams(ConnectionRefParams):
    query: str = Field(..., description="Free-text search query, e.g. 'quarterly report'.")
    limit: int = Field(30, description="Max results to return (1-200).")


class PromoteVersionParams(FileIdParams):
    version_id: str = Field(..., description="Version ID to restore as the current version, from list_file_versions.")


class DeleteVersionParams(FileIdParams):
    version_id: str = Field(..., description="Version ID to move to trash, from list_file_versions.")


class ItemRefParams(ConnectionRefParams):
    item_id: str = Field(..., description="Box folder or file ID.")
    item_type: str = Field("file", description="Item type: 'file' or 'folder'.")


class CreateCollaborationParams(ConnectionRefParams):
    item_id: str = Field(..., description="Box folder or file ID to grant access to.")
    item_type: str = Field("folder", description="Item type: 'file' or 'folder'.")
    grantee_login: str = Field("", description="Email address of the person to invite, e.g. 'jane@example.com'. Provide either grantee_login or grantee_id.")
    grantee_id: str = Field("", description="Box user or group ID to invite. Provide either grantee_login or grantee_id.")
    grantee_type: str = Field("user", description="Grantee type: 'user' or 'group'.")
    role: str = Field("viewer", description="Collaboration role: 'editor', 'viewer', 'previewer', 'uploader', 'viewer uploader', 'co-owner'.")


class UpdateCollaborationParams(ConnectionRefParams):
    collaboration_id: str = Field(..., description="Collaboration ID, from list_collaborations.")
    role: str = Field(..., description="New collaboration role.")


class RemoveCollaborationParams(ConnectionRefParams):
    collaboration_id: str = Field(..., description="Collaboration ID to revoke, from list_collaborations.")


class CreateSharedLinkParams(ConnectionRefParams):
    item_id: str = Field(..., description="Box folder or file ID to create a shared link on.")
    item_type: str = Field("file", description="Item type: 'file' or 'folder'.")
    access: str = Field("company", description="Shared link access level: 'open' (anyone with the link), 'company' (enterprise only), or 'collaborators' (invited people only).")
    can_download: bool = Field(True, description="Whether people with the link can download the file.")


class GetSharedLinkParams(ConnectionRefParams):
    item_id: str = Field(..., description="Box folder or file ID.")
    item_type: str = Field("file", description="Item type: 'file' or 'folder'.")


class ClearSharedLinkParams(GetSharedLinkParams):
    pass


class AddCommentParams(FileIdParams):
    message: str = Field(..., description="Comment text.")


class DeleteCommentParams(ConnectionRefParams):
    comment_id: str = Field(..., description="Comment ID to delete, from list_comments.")


class CreateTaskParams(FileIdParams):
    action: str = Field("review", description="Task action: 'review' or 'complete'.")
    message: str = Field("", description="Instructions for the assignee(s).")
    due_at: str = Field("", description="Due date/time (ISO 8601), optional.")


class AssignTaskParams(ConnectionRefParams):
    task_id: str = Field(..., description="Task ID to assign, from create_task or list_tasks.")
    assignee_login: str = Field("", description="Email address of the assignee. Provide either assignee_login or assignee_id.")
    assignee_id: str = Field("", description="Box user ID of the assignee. Provide either assignee_login or assignee_id.")


class DeleteTaskParams(ConnectionRefParams):
    task_id: str = Field(..., description="Task ID to delete, from list_tasks.")


class GetMetadataParams(FileIdParams):
    scope: str = Field("enterprise", description="Metadata scope: 'enterprise' or 'global'.")
    template_key: str = Field(..., description="Metadata template key, from list_metadata_templates.")


class SetMetadataParams(GetMetadataParams):
    fields_json: str = Field(..., description='JSON object of field-name to value pairs matching the template\'s schema, e.g. \'{"status": "Approved"}\'.')


class DeleteMetadataParams(GetMetadataParams):
    pass


class CreateWebhookParams(ConnectionRefParams):
    target_id: str = Field(..., description="Folder or file ID to watch for changes.")
    target_type: str = Field("file", description="Target type: 'file' or 'folder'.")
    address: str = Field(..., description="HTTPS URL Box should POST event notifications to.")
    triggers: list[str] = Field(default_factory=lambda: ["FILE.UPLOADED", "FILE.TRASHED"], description="Event types to subscribe to, e.g. ['FILE.UPLOADED', 'FILE.TRASHED', 'FOLDER.CREATED'].")


class WebhookIdParams(ConnectionRefParams):
    webhook_id: str = Field(..., description="Webhook ID, from list_webhooks.")


class AuditContentParams(ConnectionRefParams):
    folder_id: str = Field("0", description="Folder ID to audit. Use '0' for root.")
    stale_link_days: int = Field(90, description="Flag shared links older than this many days as potentially stale.")


# ---- SDL result entities ----

class DeleteResult(sdl.Entity):
    deleted: bool
    item_id: str = ""


class BoxConnection(sdl.Entity):
    connection_id: str
    label: str
    enterprise_id: str


class ConnectionList(sdl.Entity):
    connections: list[BoxConnection]


class BoxFolder(sdl.Entity):
    folder_id: str
    name: str
    parent_id: str = ""
    item_count: int = 0
    modified_at: str = ""
    owned_by: str = ""


class BoxFile(sdl.Entity):
    file_id: str
    name: str
    size_bytes: int = 0
    extension: str = ""
    modified_at: str = ""
    modified_by: str = ""
    shared_link: str = ""


class FolderItem(sdl.Entity):
    item_id: str
    name: str
    item_type: str
    size_bytes: int = 0
    modified_at: str = ""


class FolderItemList(sdl.Entity):
    items: list[FolderItem]


class DownloadResult(sdl.Entity):
    name: str
    content_base64: str
    content_type: str = "application/octet-stream"


class UploadResult(sdl.Entity):
    file_id: str
    name: str


class BoxFileVersion(sdl.Entity):
    version_id: str
    size_bytes: int = 0
    modified_at: str = ""
    modified_by: str = ""


class VersionList(sdl.Entity):
    versions: list[BoxFileVersion]


class BoxCollaboration(sdl.Entity):
    collaboration_id: str
    role: str
    status: str = ""
    accessible_by_name: str = ""
    accessible_by_type: str = ""


class CollaborationList(sdl.Entity):
    collaborations: list[BoxCollaboration]


class BoxSharedLink(sdl.Entity):
    url: str = ""
    access: str = ""
    download_url: str = ""


class BoxComment(sdl.Entity):
    comment_id: str
    message: str
    created_by: str = ""
    created_at: str = ""


class CommentList(sdl.Entity):
    comments: list[BoxComment]


class BoxTask(sdl.Entity):
    task_id: str
    action: str
    message: str = ""
    due_at: str = ""
    status: str = "unassigned"


class TaskList(sdl.Entity):
    tasks: list[BoxTask]


class MetadataTemplate(sdl.Entity):
    template_key: str
    display_name: str
    scope: str
    field_count: int = 0


class MetadataTemplateList(sdl.Entity):
    templates: list[MetadataTemplate]


class MetadataInstance(sdl.Entity):
    template_key: str
    fields: dict = {}


class BoxWebhook(sdl.Entity):
    webhook_id: str
    target_type: str
    target_id: str
    address: str
    triggers: list[str] = []


class WebhookList(sdl.Entity):
    webhooks: list[BoxWebhook]


class ContentAuditFinding(sdl.Entity):
    finding_type: str
    item_name: str
    detail: str


class ContentAudit(sdl.Entity):
    findings: list[ContentAuditFinding]
