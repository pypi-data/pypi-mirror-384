# vim: set et ai ts=4 sw=4 tw=80:

import shutil
import subprocess
import logging as log
from pathlib import Path
from contextlib import contextmanager
from .utils.hash_utils import SHORT_HASH_LEN
from .utils.tex_utils import ExitCode


# This is a context manager that modifies the user's git working tree in place,
# i.e., it checks out the specified revision (if valid) in a `--detached` mode,
# yields for work to be done on the working tree in this detached checkout mode,
# and cleans up by restoring the branch HEAD.
#
# While useful, this might lead to race effects if the user manages to change
# any files in the repository while the context manager is active. Instead,
# consider switching to using pure git refs from `ls-tree --long` and getting
# binary data from the refs using `git cat-file`. This approach will avoid
# modifying anything in the user dir at all, rather than the current
# checkout-and-restore approach.
@contextmanager
def git_checkout(git_bin: str, repo: str, rev: str):
    """
    A context manager for git checkout that checks out `rev` and restores
    previous working tree afterwards
    """

    # Raise exception right away if git tree is unclean
    cmd = [
        git_bin, "-C", repo, "status", "--porcelain", "--untracked-files=no",
    ]
    check_clean_git_tree = subprocess.run(
        cmd,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    if check_clean_git_tree.stdout:
        log.critical("Git repository unclean; unable to checkout revisions")
        raise GitError(
            check_clean_git_tree.returncode,
            " ".join(cmd),
            check_clean_git_tree.stdout,
            check_clean_git_tree.stderr
        )

    head_abbrev_ref = _get_ref(git_bin, repo, "HEAD", abbrev=True)
    head_full_ref = _get_ref(git_bin, repo, "HEAD", abbrev=False)
    if head_abbrev_ref == "HEAD":
        # This means we are in a detached working tree to begin with
        # and will require the full hash to restore tree at the end
        head_short_ref = head_full_ref[:SHORT_HASH_LEN]
    else:
        # HEAD points to branch tip
        head_short_ref = head_abbrev_ref

    try:
        rev_full_ref = _get_ref(git_bin, repo, rev)
        rev_short_ref = rev_full_ref[:SHORT_HASH_LEN]
    except GitError as err:  # typically for invalid rev
        log.critical(
            "Failed to checkout revision %s; invalid git revision?", rev
        )
        log.critical("Git: %s", err.stderr.strip())
        raise err

    if head_full_ref != rev_full_ref:
        log_tgt_rev = (
            rev if rev == rev_short_ref else f"{rev} (commit {rev_short_ref})"
        )
        try:
            # Note: git prints checkout msgs to stderr, not stdout
            rev_proc = subprocess.run(
                [git_bin, "-C", repo, "checkout", "--detach", rev],
                capture_output=True,
                encoding="utf-8",
                check=True,
            )

            log.info(
                "Checking out git revision %s in detached mode", log_tgt_rev
            )
            for line in rev_proc.stderr.splitlines():
                log.debug("Git: %s", line)

            yield rev_short_ref

        except subprocess.CalledProcessError as err:
            log.critical("Failed to checkout git revision %s", log_tgt_rev)
            for line in err.stderr.splitlines():
                log.critical("Git: %s", line)
            raise GitError(
                err.returncode, err.cmd, err.stdout, err.stderr
            ) from err

        finally:
            restore_ref = (
                head_full_ref if head_abbrev_ref == "HEAD" else head_abbrev_ref
            )
            head_proc = subprocess.run(
                [git_bin, "-C", repo, "checkout", "-f", restore_ref],
                capture_output=True,
                encoding="utf-8",
                check=True,
            )
            log.info(
                "Restoring git working tree to revision %s", head_short_ref
            )
            for line in head_proc.stderr.splitlines():
                log.debug("Git: %s", line)
    else:
        log_msg_tree = (
            "(unclean)"
            if check_clean_git_tree.stdout
            else f"at {head_short_ref}"
        )
        log.info("Using current working tree %s", log_msg_tree)
        yield rev_short_ref


def _get_ref(
        git_bin: str, repo: str, rev: str, abbrev: bool = False
) -> str:
    """Returns the full ref for a given git revision `rev` in a git `repo`"""

    cmd = [git_bin, "-C", repo, "rev-parse"]
    if abbrev:
        cmd += ["--abbrev-ref"]
    try:
        return subprocess.run(
            [*cmd, rev],
            capture_output=True,
            encoding="utf-8",
            check=True,
        ).stdout.splitlines()[0]
    except subprocess.CalledProcessError as err:
        raise GitError(
            err.returncode, " ".join(err.cmd), err.stdout, err.stderr
        ) from err


class GitRev:
    """Class to set up and obtain file list from a git repo"""

    def __init__(self, repo: str, rev: str = "HEAD") -> None:
        """Initialise GitRev class

        :repo: dir containing a git repo (str)
        :rev: a valid git revision (str), default: "HEAD"

        """
        self.repo: str = str(repo)
        self.rev: str = rev
        self.git_bin = shutil.which("git")
        if not self.git_bin:
            raise RuntimeError("Unable to find git executable in PATH")

    def mtime(self) -> int:
        """Return the target commit's unix timestamp"""
        try:
            return int(
                self._git_cmd(
                    ["show", "--no-patch", r"--format=%ct", self.rev],
                )[0].strip()
            )
        except GitError:
            raise
        except Exception as err:
            raise err

    def id(self) -> str:
        """
        Return either tag name, if commit corresponds to a valid tag, or commit
        short-id otherwise

        :returns: str

        """
        # The first line of the commit is something like the following:
        # ```
        # commit SHORT_ID
        # ```
        try:
            self.git_commit_id = self._git_cmd(
                [
                    "show",
                    "--abbrev-commit",
                    "--no-patch",
                    "--no-color",
                    self.rev,
                ]
            )[0]

        except GitError as err:
            for line in err.stderr.splitlines():
                log.critical("Git: %s", line)
            raise err

        self.tag_id: str | None
        try:
            self.tag_id = self._git_cmd(
                [
                    "describe",
                    "--tags",
                    "--exact-match",
                    self.rev,
                ]
            )[0]
        except GitError as err:
            log.info("Git: No tag corresponding to ref: %s", self.rev)
            for line in err.stderr.splitlines():
                log.debug("Git: %s", line)
            self.tag_id = None

        return self.tag_id or f"git.{self.git_commit_id.split()[1]}"

    def ls_tree_files(self) -> set[Path]:
        """Get list of files from ls-tree
        :returns: dict[Path]

        """
        try:
            _files = self._git_cmd(
                [
                    "ls-tree",
                    "-r",
                    "--name-only",
                    self.rev,
                ]
            )
            self.ls_tree_paths = set([Path(f) for f in _files])

        except GitError:
            self.ls_tree_paths = set()

        return self.ls_tree_paths

    def _git_cmd(self, cmd: list[str]) -> list[str]:
        """Run specified cmd and return captured output

        :cmd: git command to run (list[str])
        :returns: list of lines from output (list[str])
        :raises: GitError

        """

        git_comm: list[str] = [
            self.git_bin if self.git_bin else "git",
            "-C",
            self.repo,
        ] + cmd
        try:
            out = subprocess.run(
                git_comm, capture_output=True, encoding="utf-8", check=True
            )
        except subprocess.CalledProcessError as _proc_err:
            raise GitError(
                _proc_err.returncode,
                " ".join(_proc_err.cmd),
                _proc_err.stdout,
                _proc_err.stderr,
            ) from _proc_err
        except OSError as _os_err:
            raise GitError(
                _os_err.errno or ExitCode.FAIL_GENERIC,
                " ".join(git_comm),
                _os_err.strerror or f"git failed at: {' '.join(git_comm)}",
            ) from _os_err
        except Exception:
            raise
        return out.stdout.splitlines()


class GitError(Exception):

    """Exception class to handle errors raised from git-rev issues"""

    def __init__(
            self, retcode: int, cmd: str, output: str = "", error: str = ""
    ):
        """
        Initialise GitError exception class.

        :retcode: return code
        :cmd: command used
        :output: messages from stdout
        :error: messages from stderr

        """
        self._retcode = retcode
        self._command = cmd
        self._output = output
        self._error = error

    @property
    def code(self) -> int:
        """Exit code from cmdline process"""
        return self._retcode

    @property
    def cmd(self) -> str:
        """Git command used for process"""
        return self._command

    @property
    def stdout(self) -> str:
        """stdout output from git process"""
        return self._output

    @property
    def stderr(self) -> str:
        """stderr output from git process"""
        return self._error
