"""GitLab service for managing GitLab API interactions."""

from typing import Any, Dict, List, Optional, cast

import gitlab
from gitlab.exceptions import GitlabError

from gitlab_review_mcp.config import get_settings
from gitlab_review_mcp.utils.logging import get_logger

logger = get_logger(__name__)


class GitLabService:
    """Singleton service for interacting with GitLab API."""

    _instance: Optional["GitLabService"] = None
    _client: Optional[gitlab.Gitlab] = None

    def __new__(cls) -> "GitLabService":
        """Create or return singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize GitLab service with configuration."""
        if self._client is None:
            settings = get_settings()
            self.gitlab_url = settings.gitlab_url
            self.gitlab_token = settings.gitlab_private_token.get_secret_value()

    def _initialize_client(self) -> None:
        """Initialize the GitLab client and authenticate."""
        try:
            logger.info(f"Connecting to GitLab at {self.gitlab_url}")
            self._client = gitlab.Gitlab(
                url=self.gitlab_url, private_token=self.gitlab_token
            )
            self._client.auth()
            logger.info("Successfully authenticated with GitLab")
        except GitlabError as e:
            logger.error(f"Failed to authenticate with GitLab: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing GitLab client: {e}")
            raise

    @property
    def client(self) -> gitlab.Gitlab:
        """Get the GitLab client instance."""
        if self._client is None:
            self._initialize_client()
        return cast(gitlab.Gitlab, self._client)

    async def search_projects(
        self,
        search: str,
        owned: bool = False,
        membership: bool = True,
        page: int = 1,
        per_page: int = 20,
        order_by: str = "last_activity_at",
        sort: str = "desc",
    ) -> Dict[str, Any]:
        """
        Search GitLab projects with pagination.

        Args:
            search: Search string to filter projects (required)
            owned: Only return projects owned by the authenticated user
            membership: Only return projects the user is a member of
            page: Page number for pagination
            per_page: Number of results per page (max 100)
            order_by: Sort by field (id, name, created_at, star_count, last_activity_at)
            sort: Sort order (asc, desc)

        Returns:
            Dictionary with projects list and pagination metadata
        """
        try:
            params: Dict[str, Any] = {
                "membership": membership,
                "owned": owned,
                "search": search,
                "page": page,
                "per_page": min(per_page, 100),
                "order_by": order_by,
                "sort": sort,
            }

            projects = self.client.projects.list(**params)

            result_projects = []
            for project in projects:
                result_projects.append(
                    {
                        "id": project.id,
                        "name": project.name,
                        "path": project.path,
                        "path_with_namespace": project.path_with_namespace,
                        "description": project.description or "",
                        "web_url": project.web_url,
                        "default_branch": getattr(project, "default_branch", None),
                    }
                )

            total = (
                projects.total if hasattr(projects, "total") else len(result_projects)
            )
            total_pages = (
                projects.total_pages if hasattr(projects, "total_pages") else 1
            )

            logger.info(
                f"Found {len(result_projects)} projects on page {page} (total: {total})"
            )

            return {
                "projects": result_projects,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error searching projects: {e}")
            raise

    async def list_merge_requests(
        self,
        project_id: int,
        state: Optional[str] = None,
        author_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        labels: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """
        List merge requests for a project with pagination.

        Args:
            project_id: Project ID
            state: Filter by state ('opened', 'closed', 'merged', 'all')
            author_id: Filter by author ID
            assignee_id: Filter by assignee ID
            labels: Comma-separated label names
            page: Page number for pagination
            per_page: Number of results per page (max 100)

        Returns:
            Dictionary with merge requests list and pagination metadata
        """
        try:
            project = self.client.projects.get(project_id)

            params: Dict[str, Any] = {
                "page": page,
                "per_page": min(per_page, 100),
            }
            if state:
                params["state"] = state
            if author_id:
                params["author_id"] = author_id
            if assignee_id:
                params["assignee_id"] = assignee_id
            if labels:
                params["labels"] = labels

            mrs = project.mergerequests.list(**params)

            result_mrs = []
            for mr in mrs:
                result_mrs.append(
                    {
                        "id": mr.id,
                        "iid": mr.iid,
                        "title": mr.title,
                        "state": mr.state,
                        "merged": getattr(mr, "merged", False),
                        "web_url": mr.web_url,
                        "source_branch": mr.source_branch,
                        "target_branch": mr.target_branch,
                        "author": mr.author.get("username") if mr.author else None,
                        "created_at": mr.created_at,
                        "updated_at": mr.updated_at,
                    }
                )

            total = mrs.total if hasattr(mrs, "total") else len(result_mrs)
            total_pages = mrs.total_pages if hasattr(mrs, "total_pages") else 1

            logger.info(
                f"Found {len(result_mrs)} merge requests on page {page} in project {project_id} (total: {total})"
            )

            return {
                "merge_requests": result_mrs,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing merge requests: {e}")
            raise

    async def get_merge_request(self, project_id: int, mr_iid: int) -> Dict[str, Any]:
        """
        Get merge request details.

        Args:
            project_id: Project ID
            mr_iid: Merge request IID (internal ID)

        Returns:
            Dictionary with MR details
        """
        try:
            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            result = {
                "id": mr.id,
                "iid": mr.iid,
                "title": mr.title,
                "description": mr.description or "",
                "state": mr.state,
                "merged": getattr(mr, "merged", False),
                "web_url": mr.web_url,
                "source_branch": mr.source_branch,
                "target_branch": mr.target_branch,
                "author": mr.author.get("username") if mr.author else None,
                "created_at": mr.created_at,
                "updated_at": mr.updated_at,
            }

            logger.info(f"Retrieved MR !{mr_iid} from project {project_id}")
            return result

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting merge request: {e}")
            raise

    async def get_merge_request_diffs(
        self, project_id: int, mr_iid: int, page: int = 1, per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get merge request diffs with pagination.

        Args:
            project_id: Project ID
            mr_iid: Merge request IID
            page: Page number for pagination
            per_page: Number of results per page (max 100)

        Returns:
            Dictionary with diffs list and pagination metadata
        """
        try:
            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            diffs = mr.diffs.list(page=page, per_page=min(per_page, 100))

            result = []
            for diff in diffs:
                full_diff = mr.diffs.get(diff.id)

                diff_data = {
                    "id": full_diff.id,
                    "base_commit_sha": full_diff.base_commit_sha,
                    "head_commit_sha": full_diff.head_commit_sha,
                    "start_commit_sha": full_diff.start_commit_sha,
                    "created_at": full_diff.created_at,
                    "state": full_diff.state,
                    "diffs": [],
                }

                for file_diff in full_diff.diffs:
                    diff_data["diffs"].append(
                        {
                            "old_path": file_diff.get("old_path"),
                            "new_path": file_diff.get("new_path"),
                            "a_mode": file_diff.get("a_mode"),
                            "b_mode": file_diff.get("b_mode"),
                            "new_file": file_diff.get("new_file", False),
                            "renamed_file": file_diff.get("renamed_file", False),
                            "deleted_file": file_diff.get("deleted_file", False),
                            "diff": file_diff.get("diff", ""),
                        }
                    )

                result.append(diff_data)

            total = diffs.total if hasattr(diffs, "total") else len(result)
            total_pages = diffs.total_pages if hasattr(diffs, "total_pages") else 1

            logger.info(
                f"Retrieved {len(result)} diffs on page {page} for MR !{mr_iid} (total: {total})"
            )

            return {
                "diffs": result,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting merge request diffs: {e}")
            raise

    async def get_merge_request_comments(
        self, project_id: int, mr_iid: int, page: int = 1, per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get all comments/discussions from a merge request, including suggestions.

        Args:
            project_id: Project ID
            mr_iid: Merge request IID
            page: Page number for pagination
            per_page: Number of results per page (max 100)

        Returns:
            Dictionary with comments list and pagination metadata
        """
        try:
            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            discussions = mr.discussions.list(page=page, per_page=min(per_page, 100))

            comments = []
            for discussion in discussions:
                for note in discussion.attributes.get("notes", []):
                    suggestions = []
                    for suggestion in note.get("suggestions", []):
                        suggestions.append(
                            {
                                "id": suggestion.get("id"),
                                "from_line": suggestion.get("from_line"),
                                "to_line": suggestion.get("to_line"),
                                "from_content": suggestion.get("from_content"),
                                "to_content": suggestion.get("to_content"),
                                "applicable": suggestion.get("applicable", False),
                                "applied": suggestion.get("applied", False),
                                "appliable": suggestion.get("appliable", False),
                            }
                        )

                    comment_data = {
                        "note_id": note.get("id"),
                        "discussion_id": discussion.id,
                        "author": note.get("author", {}).get("username"),
                        "created_at": note.get("created_at"),
                        "updated_at": note.get("updated_at"),
                        "body": note.get("body"),
                        "system": note.get("system", False),
                        "resolvable": note.get("resolvable", False),
                        "resolved": note.get("resolved", False),
                        "suggestions": suggestions,
                    }

                    if note.get("position"):
                        comment_data["file_path"] = note.get("position", {}).get(
                            "new_path", ""
                        )

                    comments.append(comment_data)

            total = (
                discussions.total if hasattr(discussions, "total") else len(comments)
            )
            total_pages = (
                discussions.total_pages if hasattr(discussions, "total_pages") else 1
            )

            logger.info(
                f"Retrieved {len(comments)} comments on page {page} from MR !{mr_iid} in project {project_id} (total: {total})"
            )

            return {
                "comments": comments,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting merge request comments: {e}")
            raise

    async def get_merge_request_commits(
        self, project_id: int, mr_iid: int, page: int = 1, per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get merge request commits with pagination.

        Args:
            project_id: Project ID
            mr_iid: Merge request IID
            page: Page number for pagination
            per_page: Number of results per page (max 100)

        Returns:
            Dictionary with commits list and pagination metadata
        """
        try:
            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            commits_data = mr.commits(page=page, per_page=min(per_page, 100))

            result_commits = []
            if isinstance(commits_data, list):
                for commit in commits_data:
                    result_commits.append(
                        {
                            "id": getattr(commit, "id", None),
                            "short_id": getattr(commit, "short_id", None),
                            "title": getattr(commit, "title", None),
                            "message": getattr(commit, "message", None),
                            "author_name": getattr(commit, "author_name", None),
                            "author_email": getattr(commit, "author_email", None),
                            "authored_date": getattr(commit, "authored_date", None),
                            "committer_name": getattr(commit, "committer_name", None),
                            "committer_email": getattr(commit, "committer_email", None),
                            "committed_date": getattr(commit, "committed_date", None),
                            "web_url": getattr(commit, "web_url", None),
                        }
                    )
                total = len(result_commits)
                total_pages = 1
            else:
                for commit in commits_data:
                    result_commits.append(
                        {
                            "id": getattr(commit, "id", None),
                            "short_id": getattr(commit, "short_id", None),
                            "title": getattr(commit, "title", None),
                            "message": getattr(commit, "message", None),
                            "author_name": getattr(commit, "author_name", None),
                            "author_email": getattr(commit, "author_email", None),
                            "authored_date": getattr(commit, "authored_date", None),
                            "committer_name": getattr(commit, "committer_name", None),
                            "committer_email": getattr(commit, "committer_email", None),
                            "committed_date": getattr(commit, "committed_date", None),
                            "web_url": getattr(commit, "web_url", None),
                        }
                    )
                total = (
                    int(commits_data.total)
                    if hasattr(commits_data, "total") and commits_data.total is not None
                    else len(result_commits)
                )
                total_pages = (
                    int(commits_data.total_pages)
                    if hasattr(commits_data, "total_pages")
                    and commits_data.total_pages is not None
                    else 1
                )

            logger.info(
                f"Retrieved {len(result_commits)} commits on page {page} for MR !{mr_iid} (total: {total})"
            )

            return {
                "commits": result_commits,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting merge request commits: {e}")
            raise

    async def update_merge_request_comment(
        self, project_id: int, mr_iid: int, note_id: int, comment: str
    ) -> Dict[str, Any]:
        """
        Update an existing merge request comment.

        Args:
            project_id: Project ID
            mr_iid: Merge request IID
            note_id: Note ID
            comment: Updated comment text

        Returns:
            Updated comment details
        """
        try:
            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            note = mr.notes.get(note_id)
            note.body = comment
            note.save()

            result = {
                "id": note.id,
                "body": note.body,
                "author": note.author.get("username") if note.author else None,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
            }

            logger.info(f"Updated comment {note_id} in MR !{mr_iid}")
            return result

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating merge request comment: {e}")
            raise

    async def reply_to_merge_request_comment(
        self, project_id: int, mr_iid: int, discussion_id: str, comment: str
    ) -> Dict[str, Any]:
        """
        Reply to an existing merge request discussion/comment.

        Args:
            project_id: Project ID
            mr_iid: Merge request IID
            discussion_id: Discussion ID
            comment: Reply comment text

        Returns:
            Created reply details
        """
        try:
            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            discussion = mr.discussions.get(discussion_id)
            new_note = discussion.notes.create({"body": comment})

            result = {
                "id": new_note.id,
                "body": comment,
                "discussion_id": discussion_id,
                "created_at": new_note.created_at,
            }

            logger.info(f"Added reply to discussion {discussion_id} in MR !{mr_iid}")
            return result

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error replying to comment: {e}")
            raise

    async def add_merge_request_comment(
        self, project_id: int, mr_iid: int, comment: str
    ) -> Dict[str, Any]:
        """
        Add a comment to a merge request.

        Args:
            project_id: Project ID
            mr_iid: Merge request IID
            comment: Comment text

        Returns:
            Created comment details
        """
        try:
            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            note = mr.notes.create({"body": comment})

            result = {
                "id": note.id,
                "body": note.body,
                "author": note.author.get("username") if note.author else None,
                "created_at": note.created_at,
            }

            logger.info(f"Added comment to MR !{mr_iid} in project {project_id}")
            return result

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error adding merge request comment: {e}")
            raise

    async def add_merge_request_line_comment(
        self,
        project_id: int,
        mr_iid: int,
        file_path: str,
        line_number: int,
        comment: str,
        base_sha: str,
        head_sha: str,
        start_sha: str,
        old_line: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add a line-specific comment to a merge request diff.

        Args:
            project_id: Project ID
            mr_iid: Merge request IID
            file_path: Path to the file in the diff
            line_number: New line number to comment on
            comment: Comment text
            base_sha: Base commit SHA
            head_sha: Head commit SHA
            start_sha: Start commit SHA
            old_line: Old line number (optional, for changed lines)

        Returns:
            Created discussion details
        """
        try:
            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            position = {
                "base_sha": base_sha,
                "start_sha": start_sha,
                "head_sha": head_sha,
                "position_type": "text",
                "new_path": file_path,
                "old_path": file_path,
                "new_line": line_number,
            }

            if old_line is not None:
                position["old_line"] = old_line

            discussion = mr.discussions.create({"body": comment, "position": position})

            result = {
                "id": discussion.id,
                "body": comment,
                "position": position,
            }

            logger.info(
                f"Added line comment to MR !{mr_iid} at {file_path}:{line_number}"
            )
            return result

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error adding line comment: {e}")
            raise

    async def get_issue(self, project_id: int, issue_iid: int) -> Dict[str, Any]:
        """
        Get issue details.

        Args:
            project_id: Project ID
            issue_iid: Issue IID

        Returns:
            Dictionary with issue details
        """
        try:
            project = self.client.projects.get(project_id)
            issue = project.issues.get(issue_iid)

            result = {
                "id": issue.id,
                "iid": issue.iid,
                "title": issue.title,
                "description": issue.description or "",
                "state": issue.state,
                "web_url": issue.web_url,
                "author": issue.author.get("username") if issue.author else None,
                "assignees": [
                    assignee.get("username")
                    for assignee in getattr(issue, "assignees", [])
                ],
                "labels": getattr(issue, "labels", []),
                "created_at": issue.created_at,
                "updated_at": issue.updated_at,
                "closed_at": getattr(issue, "closed_at", None),
            }

            logger.info(f"Retrieved issue #{issue_iid} from project {project_id}")
            return result

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting issue: {e}")
            raise

    async def update_merge_request(
        self,
        project_id: int,
        mr_iid: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update merge request title and/or description.

        Args:
            project_id: Project ID
            mr_iid: Merge request IID
            title: New title (optional)
            description: New description (optional)

        Returns:
            Updated merge request details
        """
        try:
            project = self.client.projects.get(project_id)
            mr = project.mergerequests.get(mr_iid)

            if title is not None:
                mr.title = title
            if description is not None:
                mr.description = description

            mr.save()

            result = {
                "id": mr.id,
                "iid": mr.iid,
                "title": mr.title,
                "description": mr.description or "",
                "state": mr.state,
                "web_url": mr.web_url,
                "updated_at": mr.updated_at,
            }

            logger.info(f"Updated MR !{mr_iid} in project {project_id}")
            return result

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating merge request: {e}")
            raise

    async def apply_suggestion(self, suggestion_id: int) -> Dict[str, Any]:
        """
        Apply a single suggestion.

        Args:
            suggestion_id: Suggestion ID to apply

        Returns:
            Result of applying the suggestion
        """
        try:
            response = self.client.http_put(f"/suggestions/{suggestion_id}/apply")

            result = {
                "id": suggestion_id,
                "applied": True,
                "commit_id": response.get("commit_id"),
            }

            logger.info(f"Applied suggestion {suggestion_id}")
            return result

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error applying suggestion: {e}")
            raise

    async def apply_suggestions(self, suggestion_ids: List[int]) -> Dict[str, Any]:
        """
        Apply multiple suggestions in batch.

        Args:
            suggestion_ids: List of suggestion IDs to apply

        Returns:
            Result of batch apply operation
        """
        try:
            response = self.client.http_put(
                "/suggestions/batch_apply",
                post_data={"ids": suggestion_ids},
            )

            result = {
                "count": len(suggestion_ids),
                "applied": True,
                "commit_id": response.get("commit_id"),
                "suggestion_ids": suggestion_ids,
            }

            logger.info(f"Applied {len(suggestion_ids)} suggestions in batch")
            return result

        except GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error applying suggestions: {e}")
            raise
