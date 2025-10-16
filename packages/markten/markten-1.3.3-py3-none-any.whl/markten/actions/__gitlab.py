"""
# Markten / Actions / GitLab

Helper functions for interacting with GitLab using Git.
"""

from typing import Self


class PushOptions:
    """Builder class to generate GitLab push options.

    https://docs.gitlab.com/topics/git/commit/#push-options
    """

    def __init__(self) -> None:
        """Helper class to generate GitLab push options.

        https://docs.gitlab.com/topics/git/commit/#push-options
        """
        self.__opts: list[str] = []

    def as_list(self) -> list[str]:
        """
        Return the push options for use in the `markten.git.push` action.
        """
        return self.__opts

    def ci_skip(self) -> Self:
        """
        Skip GitLab pipeline.
        """
        self.__opts.append("ci.skip")
        return self

    def ci_input(self, key: str, value: str) -> Self:
        """
        GitLab pipeline input parameters.

        https://docs.gitlab.com/ci/inputs/
        """
        self.__opts.append(f'ci.input="{key}={value}"')
        return self

    def ci_variable(self, key: str, value: str) -> Self:
        """
        GitLab pipeline variables.

        https://docs.gitlab.com/ci/variables/
        """
        self.__opts.append(f'ci.variable="{key}={value}"')
        return self

    def integrations_skip_ci(self) -> Self:
        """
        Instruct GitLab to skip external pipelines.
        """
        self.__opts.append("integrations.skip_ci")
        return self

    def merge_request(
        self,
        create: bool = False,
        title: str | None = None,
        description: str | None = None,
        target_branch: str | None = None,
        target_project: str | None = None,
        auto_merge: bool | None = None,
        remove_source_branch: bool | None = None,
        squash: bool | None = None,
        draft: bool | None = None,
        milestone: str | None = None,
        label: list[str] | None = None,
        unlabel: list[str] | None = None,
        assign: list[str] | None = None,
        unassign: list[str] | None = None,
    ) -> Self:
        """
        Create a merge request from this branch. By default, this targets the
        default branch.

        For boolean properties, there is no clear way to set the values to
        false, using GitLab's API push options system. For now, these are a
        no-op.

        Parameters
        ----------
        create : bool
            Whether to create the merge request.
        title : str
            Merge request title
        description : str
            Merge request description
        target_branch : str
            The merge request's target branch, ie the branch it will merge
            into.
        target_project : str
            The merge request's target repository, ie the repository it will
            merge into.
        auto_merge : bool
            Whether to enable GitLab's auto-merge feature.
        remove_source_branch : bool
            Whether to remove the source branch upon merge.
        squash : bool
            Whether to squash commits upon merging.
        draft : bool
            Whether to set this merge request to be a draft.
        milestone : str
            The merge request's project management milestone.
        label : list[str]
            List of labels to apply to the merge request.
        unlabel : list[str]
            List of labels to remove from the merge request.
        assign : list[str]
            List of users to assign to the merge request.
        unassign : list[str]
            List of users to unassign from the merge request.
        """
        if create:
            self.__opts.append("merge_request.create")
        if title:
            self.__opts.append(f'merge_request.title="{title}"')
        if description:
            self.__opts.append(f'merge_request.description="{description}"')
        if target_branch:
            self.__opts.append(f'merge_request.target="{target_branch}"')
        if target_project:
            self.__opts.append(
                f'merge_request.target_project="{target_project}"'
            )
        # I am not sure how to specify to GitLab when these should be False,
        # so for now, having these be false is a no-op.
        # https://gitlab.com/gitlab-org/gitlab/-/issues/576493
        if auto_merge:
            self.__opts.append("merge_request.auto_merge")
        if remove_source_branch:
            self.__opts.append("merge_request.remove_source_branch")
        if squash:
            self.__opts.append("merge_request.squash")
        if draft:
            self.__opts.append("merge_request.draft")
        if milestone:
            self.__opts.append(f'merge_request.milestone="{milestone}"')
        if label:
            for lab in label:
                self.__opts.append(f'merge_request.label="{lab}"')
        if unlabel:
            for lab in unlabel:
                self.__opts.append(f'merge_request.unlabel="{lab}"')
        if assign:
            for assignee in assign:
                self.__opts.append(f'merge_request.assign="{assignee}"')
        if unassign:
            for assignee in unassign:
                self.__opts.append(f'merge_request.unassign="{assignee}"')

        return self

    def skip_secret_push_protection(self) -> Self:
        """
        Disable secret push protection.

        https://docs.gitlab.com/user/application_security/secret_detection/secret_push_protection/
        """
        self.__opts.append("secret_push_protection.skip_all")
        return self

    def bypass_security_policy(self, reason: str) -> Self:
        """
        Make this commit bypass the repository's security policy, documenting
        a reason why.
        """
        self.__opts.append(f'security_policy.bypass_reason="{reason}"')
        return self
