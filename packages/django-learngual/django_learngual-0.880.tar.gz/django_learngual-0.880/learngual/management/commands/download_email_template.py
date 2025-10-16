import os
import shutil
from logging import getLogger
from pathlib import Path

import git
from django.conf import settings
from django.core.management.base import BaseCommand

logger = getLogger(__file__)


class Command(BaseCommand):
    help = "Download email template"

    # def add_arguments(self, parser):
    #     parser.add_argument('platform', nargs='+', type=str)

    def handle(self, *args, **options):
        token = getattr(
            settings, "LEARNGUAL_GITHUB_TOKEN", os.getenv("LEARNGUAL_GITHUB_TOKEN")
        )
        username = getattr(
            settings,
            "LEARNGUAL_GITHUB_USERNAME",
            os.getenv("LEARNGUAL_GITHUB_USERNAME"),
        )
        repo_name = getattr(
            settings,
            "LEARNGUAL_GITHUB_REPO_NAME",
            os.getenv("LEARNGUAL_GITHUB_REPO_NAME"),
        )
        branch_name = getattr(
            settings, "LEARNGUAL_GITHUB_BRANCH", os.getenv("LEARNGUAL_GITHUB_BRANCH")
        )
        assert all(
            [token, username, repo_name, branch_name]
        ), f'All {", ".join(["LEARNGUAL_GITHUB_TOKEN","LEARNGUAL_GITHUB_USERNAME","LEARNGUAL_GITHUB_REPO_NAME","LEARNGUAL_GITHUB_BRANCH"])} environment variable must be set.'  # noqa
        repo_url = f"https://{token}@github.com/{username}/{repo_name}.git"

        clone_to_path = settings.ROOT_DIR / "templates"

        self.clone_specific_branch(repo_url, branch_name, clone_to_path)
        self.stdout.write(self.style.SUCCESS("Template downloaded"))

    def clone_specific_branch(self, repo_url, branch_name, clone_to_path):
        try:
            clone_to_path = Path(clone_to_path)

            # Remove every file and folder in the clone_to_path before cloning
            if clone_to_path.exists() and clone_to_path.is_dir():
                shutil.rmtree(clone_to_path)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Cleared the contents of '{clone_to_path}' before cloning."
                    )
                )

            # Clone the specific branch
            repo = git.Repo.clone_from(repo_url, clone_to_path, branch=branch_name)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Branch '{branch_name}' has been cloned to '{clone_to_path}'."
                )
            )

            # Path to the .git directory using pathlib.Path
            git_dir = clone_to_path / ".git"

            # Remove the .git directory if it exists
            if git_dir.exists() and git_dir.is_dir():
                shutil.rmtree(git_dir)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"The .git folder has been removed from '{clone_to_path}'."
                    )
                )

            repo.__del__()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
