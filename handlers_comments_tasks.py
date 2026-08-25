"""Comment and Task handlers for Box Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import box_client as bc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    AddCommentParams, AssignTaskParams, BoxComment, BoxTask,
    CommentList, CreateTaskParams, DeleteCommentParams, DeleteResult,
    DeleteTaskParams, FileIdParams, TaskList,
)


def _comment_entity(c: dict) -> BoxComment:
    return BoxComment(
        comment_id=c.get("id", ""),
        message=c.get("message", ""),
        created_by=((c.get("created_by") or {}).get("name", "")) or "",
        created_at=c.get("created_at", "") or "",
    )


def _task_entity(t: dict) -> BoxTask:
    return BoxTask(
        task_id=t.get("id", ""),
        action=t.get("action", ""),
        message=t.get("message", "") or "",
        due_at=t.get("due_at", "") or "",
        status=(t.get("task_assignment_collection") or {}).get("total_count", 0) and "assigned" or "unassigned",
    )


@chat.function(
    "list_comments",
    action_type="read",
    event="box-connector.list_comments",
    data_model=CommentList,
    description="List comments on a file.",
)
async def fn_list_comments(ctx, params: FileIdParams) -> ActionResult:
    """List comments on a Box file."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/files/{params.file_id}/comments")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    comments = [_comment_entity(c) for c in (data or {}).get("entries", [])]
    return ActionResult.success(data=CommentList(comments=comments).model_dump(), summary=f"{len(comments)} comment(s) found.")


@chat.function(
    "add_comment",
    action_type="write",
    event="box-connector.add_comment",
    data_model=BoxComment,
    description="Add a comment to a file.",
)
async def fn_add_comment(ctx, params: AddCommentParams) -> ActionResult:
    """Post a new comment on a Box file."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    body = {"item": {"type": "file", "id": params.file_id}, "message": params.message}
    try:
        data = await client.request("POST", "/comments", json_body=body)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=_comment_entity(data).model_dump(), summary="Comment added.")


@chat.function(
    "delete_comment",
    action_type="write",
    event="box-connector.delete_comment",
    data_model=DeleteResult,
    description="Permanently delete a comment.",
)
async def fn_delete_comment(ctx, params: DeleteCommentParams) -> ActionResult:
    """Delete a Box comment."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("DELETE", f"/comments/{params.comment_id}")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=DeleteResult(deleted=True, item_id=params.comment_id).model_dump(), summary="Comment deleted.")


@chat.function(
    "create_task",
    action_type="write",
    event="box-connector.create_task",
    data_model=BoxTask,
    description="Create a review/approval task on a file.",
)
async def fn_create_task(ctx, params: CreateTaskParams) -> ActionResult:
    """Create a Box task on a file."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    body: dict = {"item": {"type": "file", "id": params.file_id}, "action": params.action, "message": params.message}
    if params.due_at:
        body["due_at"] = params.due_at
    try:
        data = await client.request("POST", "/tasks", json_body=body)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=_task_entity(data).model_dump(), summary="Task created.")


@chat.function(
    "assign_task",
    action_type="write",
    event="box-connector.assign_task",
    description="Assign a Box task to a user by login (email) or user id.",
)
async def fn_assign_task(ctx, params: AssignTaskParams) -> ActionResult:
    """Assign a Box task to a user."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    assign_to: dict = {}
    if params.assignee_login:
        assign_to["login"] = params.assignee_login
    else:
        assign_to["id"] = params.assignee_id
    body = {"task": {"type": "task", "id": params.task_id}, "assign_to": assign_to}
    try:
        await client.request("POST", "/task_assignments", json_body=body)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data={}, summary="Task assigned.")


@chat.function(
    "list_tasks",
    action_type="read",
    event="box-connector.list_tasks",
    data_model=TaskList,
    description="List tasks on a file.",
)
async def fn_list_tasks(ctx, params: FileIdParams) -> ActionResult:
    """List Box tasks on a file."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/files/{params.file_id}/tasks")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    tasks = [_task_entity(t) for t in (data or {}).get("entries", [])]
    return ActionResult.success(data=TaskList(tasks=tasks).model_dump(), summary=f"{len(tasks)} task(s) found.")


@chat.function(
    "delete_task",
    action_type="write",
    event="box-connector.delete_task",
    data_model=DeleteResult,
    description="Permanently delete a task.",
)
async def fn_delete_task(ctx, params: DeleteTaskParams) -> ActionResult:
    """Delete a Box task."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("DELETE", f"/tasks/{params.task_id}")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=DeleteResult(deleted=True, item_id=params.task_id).model_dump(), summary="Task deleted.")
