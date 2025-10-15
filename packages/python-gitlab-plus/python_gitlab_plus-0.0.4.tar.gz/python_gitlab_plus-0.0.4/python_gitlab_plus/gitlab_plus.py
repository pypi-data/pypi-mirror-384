import os
import time
from enum import Enum

import gitlab
from custom_python_logger import get_logger
from gitlab import const
from gitlab.const import AccessLevel
from gitlab.v4.objects import (
    Project,
    ProjectBranch,
    ProjectFile,
    ProjectMember,
    ProjectMergeRequest,
    ProjectPipeline,
    ProjectTag,
)


class GitLabStatus(Enum):
    OPEN = "opened"
    CLOSE = "closed"
    MERGE = "merged"
    LOCK = "locked"


class GitLabPipelineStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"
    SKIPPED = "skipped"


class GitLabProjectService:
    def __init__(self, gitlab_client: gitlab.Gitlab, project: Project) -> None:
        self.logger = get_logger(self.__class__.__name__)

        self.gitlab = gitlab_client
        self.project = project

    def get_info(self) -> Project:
        return self.project

    def list_members(self) -> list[ProjectMember]:
        return self.project.members.list(all=True)

    def add_member(self, username: str, access_level: int) -> None:
        user = self.gitlab.users.list(username=username)[0]
        self.project.members.create({"user_id": user.id, "access_level": access_level})

    def remove_member(self, username: str) -> None:
        user = self.gitlab.users.list(username=username)[0]
        self.project.members.delete(user.id)


class GitLabPipelineService:
    def __init__(self, project: Project) -> None:
        self.logger = get_logger(self.__class__.__name__)

        self.project = project

    def trigger(self, branch_name: str, variables: dict | None = None) -> ProjectPipeline:
        return self.project.pipelines.create({"ref": branch_name, "variables": variables or {}})

    def status(self, pipeline_id: int) -> str:
        return self.project.pipelines.get(pipeline_id).status

    def wait_until_finished(self, pipeline_id: int, check_interval: int = 10, timeout: int = 60 * 5) -> str:
        final_statuses = [s.value for s in GitLabPipelineStatus]

        start_time = time.time()
        while (time.time() - start_time) >= timeout:  # pylint: disable=W0149
            pipeline = self.project.pipelines.get(pipeline_id)
            if pipeline.status in final_statuses:
                return pipeline.status
            time.sleep(check_interval)
        raise TimeoutError(f"Pipeline {pipeline_id} did not complete within {timeout} seconds.")


class GitLabBranchService:
    def __init__(self, project: Project) -> None:
        self.logger = get_logger(self.__class__.__name__)

        self.project = project

    def create(self, branch_name: str, from_branch: str) -> ProjectBranch:
        branch = self.project.branches.create({"branch": branch_name, "ref": from_branch})
        self.logger.info(f"✅ Branch '{branch_name}' created from '{from_branch}'")
        return branch

    def delete(self, branch_name: str) -> None:
        self.project.branches.delete(branch_name)
        self.logger.info(f"✅ Branch '{branch_name}' deleted")

    def list(self, search: str | None = None) -> list[ProjectBranch]:
        return self.project.branches.list(search=search, all=True)

    def protect(
        self,
        branch_name: str,
        push_access_level: AccessLevel = const.DEVELOPER_ACCESS,
        merge_access_level: AccessLevel = const.MAINTAINER_ACCESS,
    ) -> None:

        self.project.protectedbranches.create(
            {"name": branch_name, "push_access_level": push_access_level, "merge_access_level": merge_access_level}
        )

    def unprotect(self, branch_name: str) -> None:
        try:
            self.project.protectedbranches.delete(branch_name)
        except gitlab.exceptions.GitlabDeleteError:
            self.logger.warning(f"⚠️ Branch '{branch_name}' is not protected.")


class GitLabTagService:
    def __init__(self, project: Project) -> None:
        self.logger = get_logger(self.__class__.__name__)

        self.project = project

    def create(self, tag_name: str, from_branch: str, message: str | None = None) -> ProjectTag:
        tag = self.project.tags.create({"tag_name": tag_name, "ref": from_branch, "message": message})
        self.logger.info(f"✅ Tag '{tag_name}' created from '{from_branch}'")
        return tag

    def delete(self, tag_name: str) -> None:
        self.project.tags.delete(tag_name)
        self.logger.info(f"✅ Tag '{tag_name}' deleted")

    def list(self, search: str | None = None) -> list[ProjectTag]:
        return self.project.tags.list(search=search, all=True)


class GitLabMergeRequestService:
    def __init__(self, gitlab_client: gitlab.Gitlab, project: Project) -> None:
        self.logger = get_logger(self.__class__.__name__)

        self.gitlab = gitlab_client
        self.project = project

    def get_info(self, mr_number: int) -> ProjectMergeRequest:
        return self.project.mergerequests.get(mr_number)

    def create(self, title: str, from_branch: str, target: str) -> ProjectMergeRequest:
        mr = self.project.mergerequests.create({"source_branch": from_branch, "target_branch": target, "title": title})
        self.logger.info(f"✅ Merge Request '{title}' created: !{mr.iid}")
        return mr

    def status(self, mr_number: int) -> str:
        return self.project.mergerequests.get(mr_number).state

    def has_merge_conflicts(self, mr_number: str | int) -> bool:
        mr = self.project.mergerequests.get(mr_number)
        if hasattr(mr, "has_conflicts") and mr.has_conflicts:
            self.logger.error(f"🔍 MR !{mr_number} has_conflicts = {mr.has_conflicts}")
            return True
        # Fallback: check detailed_merge_status if has_conflicts not available
        conflict_statuses = ["conflicts", "cannot_be_merged"]
        if hasattr(mr, "detailed_merge_status") and mr.detailed_merge_status in conflict_statuses:
            self.logger.error(f"🔍 MR !{mr_number} detailed_merge_status = {mr.detailed_merge_status}")
            return True
        return False

    def merge(self, mr_number: int, merge_when_pipeline_succeeds: bool = True) -> None:
        mr = self.project.mergerequests.get(mr_number)
        mr.merge(merge_when_pipeline_succeeds=merge_when_pipeline_succeeds)
        self.logger.info(f"✅ MR !{mr_number} merged.")

    def approve(self, mr_number: int) -> None:
        mr = self.project.mergerequests.get(mr_number)
        mr.approve()
        self.logger.info(f"✅ MR !{mr_number} approved.")

    def close(self, mr_number: int) -> None:
        mr = self.project.mergerequests.get(mr_number)
        mr.state_event = "close"
        mr.save()
        self.logger.info(f"✅ MR !{mr_number} closed.")

    def reopen(self, mr_number: int) -> None:
        mr = self.project.mergerequests.get(mr_number)
        mr.state_event = "reopen"
        mr.save()
        self.logger.info(f"✅ MR !{mr_number} reopened.")

    def assign(self, mr_number: int, assignee_username: str) -> None:
        user = self.gitlab.users.list(username=assignee_username)[0]
        mr = self.project.mergerequests.get(mr_number)
        mr.assignee_ids = [user.id]
        mr.save()
        self.logger.info(f"✅ MR !{mr_number} assigned to {assignee_username}.")

    def add_reviewer(self, mr_number: int, reviewer_username: str) -> None:
        user = self.gitlab.users.list(username=reviewer_username)[0]
        mr = self.project.mergerequests.get(mr_number)
        mr.reviewer_ids = [user.id]
        mr.save()
        self.logger.info(f"✅ Reviewer {reviewer_username} added to MR !{mr_number}.")

    def add_comment(self, mr_number: int, comment: str) -> None:
        mr = self.project.mergerequests.get(mr_number)
        mr.notes.create({"body": comment})
        self.logger.info(f"✅ Comment added to MR !{mr_number}.")

    def wait_until_finished(self, mr_number: str | int, check_interval: int = 10, timeout: int = 60 * 5) -> None:
        self.logger.info(f"⏳ Waiting for MR !{mr_number} to be merged...")
        close_statuses = [
            GitLabStatus.CLOSE,
            GitLabStatus.MERGE,
            GitLabStatus.LOCK,
        ]

        start_time = time.time()
        while (time.time() - start_time) >= timeout:  # pylint: disable=W0149
            mr = self.project.mergerequests.get(mr_number)
            self.logger.debug(f"MR ({mr.iid}) status is: {mr.state}")
            if self.has_merge_conflicts(mr_number):
                raise Exception(f"🔍 MR !{mr_number} has conflicts.")
            if mr.state in close_statuses:
                break
            time.sleep(check_interval)
        raise TimeoutError(f"⏰ Timeout reached while waiting for MR !{mr_number} to be merged.")


class GitLabFileService:
    def __init__(self, gitlab_client: gitlab.Gitlab, project: Project) -> None:
        self.logger = get_logger(self.__class__.__name__)

        self.project = project
        self.gitlab = gitlab_client

    def get(self, file_path: str, ref: str) -> ProjectFile:
        return self.project.files.get(file_path=file_path, ref=ref)

    def fetch_content(self, file_path: str, ref: str) -> str:
        file = self.project.files.get(file_path=file_path, ref=ref)
        return file.decode().decode("utf-8")

    # def update(self, file_path: str, branch: str, content: str, commit_message: str) -> None:
    #     file = self.project.files.get(file_path=file_path, ref=branch)
    #     file.content = content
    #     file.save(branch=branch, commit_message=commit_message)
    #
    # def create(self, file_path: str, branch: str, content: str, commit_message: str) -> None:
    #     self.project.files.create(
    #         {
    #             'file_path': file_path,
    #             'branch': branch,
    #             'content': content,
    #             'commit_message': commit_message
    #         }
    #     )
    #
    # def delete(self, file_path: str, branch: str, commit_message: str) -> None:
    #     file = self.project.files.get(file_path=file_path, ref=branch)
    #     file.delete(branch=branch, commit_message=commit_message)


# ----------------------- #
# Facade / User Interface #
# ----------------------- #


class GitLabClient:
    def __init__(self, gitlab_url: str, access_token: str | None, project_id: str) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.gitlab_url = gitlab_url
        self.gitlab_access_token = access_token or os.environ.get("GITLAB_ACCESS_TOKEN")

        self.gitlab = gitlab.Gitlab(self.gitlab_url, private_token=self.gitlab_access_token)
        self.is_connected(raise_if_not_connected=True)

        project = self.gitlab.projects.get(project_id)
        self.project = GitLabProjectService(gitlab_client=self.gitlab, project=project)
        self.pipeline = GitLabPipelineService(project=project)
        self.branch = GitLabBranchService(project=project)
        self.tag = GitLabTagService(project=project)
        self.merge_request = GitLabMergeRequestService(gitlab_client=self.gitlab, project=project)
        self.file = GitLabFileService(gitlab_client=self.gitlab, project=project)

    def is_connected(self, raise_if_not_connected: bool = False) -> bool:
        try:
            self.gitlab.auth()
            self.logger.info(f"✅ Successfully connected to GitLab at {self.gitlab_url}")
            return True
        except Exception as e:
            msg = f"❌ Failed to authenticate with GitLab: {e}"
            if raise_if_not_connected:
                raise ValueError(msg) from e
            self.logger.exception(msg)
            return False
