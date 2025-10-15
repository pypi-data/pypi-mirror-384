import os

import yaml

from suite_py.lib import logger
from suite_py.lib.config import Config
from suite_py.lib.handler.git_handler import GitHandler


class PreCommit:
    """
    Handler checking whether the user has the prima pre-commit hooks setup and print a warning if they are missing
    """

    def __init__(self, project: str, config: Config):
        self._git = GitHandler(project, config)

    def check_and_warn(self):
        if self._is_enabled() and not self._is_pre_commit_hooks_installed():
            self._warn_missing_pre_commit_hook()

    def _is_enabled(self):
        return self._git.get_git_config("suite-py.disable-pre-commit-warning") != "true"

    def _is_pre_commit_hooks_installed(self):
        """
        Apply some heuristics to check whether the gitleaks pre-commit hook is installed.
        This is extremely imperfect, and only supports direct calls in shell scripts.
        """
        return self._is_shell_script_hook_setup() or self._is_pre_commit_py_hook_setup()

    def _warn_missing_pre_commit_hook(self):
        logger.warning(
            """
Looks like the current repo is missing the gitleaks pre-commit hook!
Please install it per the security guide:
https://www.notion.so/helloprima/Install-Gitleaks-pre-commit-hook-aaaa6beafafa4c298b537afcb52bb25a

If you have installed them already you can report the false positive to team-platform-shared-services (on Slack) and run:
    git config suite-py.disable-pre-commit-warning true
to disable the check for this repo, or
    git config --global suite-py.disable-pre-commit-warning true
to disable it globally
        """
        )

    def _is_shell_script_hook_setup(self):
        """
        Check whether the gitleaks hook is setup as a regular bash script:

        * is there a `.git/hooks/pre-commit` shell script that contains keyword "gitleaks"
        * is there a `.husky/pre-commit` shell script that contains keyword "security-hooks" (primait/security-hooks repo)
        """
        checks = [
            (os.path.join(self._git.hooks_path(), "pre-commit"), "gitleaks"),
            (
                os.path.join(self._git.get_path(), ".husky", "pre-commit"),
                "security-hooks",
            ),
        ]

        return any(
            self._script_contains_keyword(path, keyword) for path, keyword in checks
        )

    def _is_pre_commit_py_hook_setup(self):
        """
        Check whether the gitleaks hook is setup with the pre-commit python framework
        """
        # is there a `.git/hooks/pre-commit` shell script that contains keyword "pre-commit"
        pre_commit_file_path = os.path.join(self._git.hooks_path(), "pre-commit")
        if not self._script_contains_keyword(pre_commit_file_path, "pre-commit"):
            logger.debug("pre-commit.com not installed, skipping config check")
            return False

        config_path = os.path.join(self._git.get_path(), ".pre-commit-config.yaml")
        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.debug("pre-commit config file(%s) not found", config_path)
            return False
        except yaml.YAMLError:
            logger.warning(".pre-commit-config.yaml file is invalid!", exc_info=True)
            return False

        return any(
            repo.get("repo", "") == "git@github.com:primait/security-hooks.git"
            for repo in config.get("repos", [])
        )

    def _script_contains_keyword(self, file_path, keyword):
        """
        Check if a keyword appears in a shell script, ignoring comment lines
        (binaries and python code are out of scope for us).
        """
        try:
            logger.debug("checking pre-commit script(%s)", file_path)
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            logger.debug("pre-commit script(%s) not found", file_path)
            return False

        # Filter out comments (lines starting with '#').
        lines_without_comments = (
            line for line in content.splitlines() if not line.strip().startswith("#")
        )
        return any(keyword in line for line in lines_without_comments)
