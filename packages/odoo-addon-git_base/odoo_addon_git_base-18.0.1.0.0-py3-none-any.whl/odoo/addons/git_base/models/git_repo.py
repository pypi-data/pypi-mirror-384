import base64
import io
import logging
import os
import re
import zipfile
from datetime import datetime
from subprocess import STDOUT, CalledProcessError, check_output, run

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class GitRepo(models.Model):
    _name = "git.repo"
    _description = "Git Repo"
    _inherit = ["res.users.keychain", "mail.thread", "mail.activity.mixin"]

    # Repo fields

    name = fields.Char(required=True)
    http_url = fields.Char(string="HTTP Url", compute="_compute_http_url", readonly=True)
    ssh_url = fields.Char(string="SSH Url", compute="_compute_ssh_url", store=True, readonly=True)
    local_path = fields.Char(compute="_compute_local_path")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("initialized", "Initialized"),
            ("connected", "Connected"),
            ("deleted", "Deleted"),
        ],
        default="draft",
        readonly=True,
    )
    ref = fields.Char(readonly=True, compute="_compute_ref")
    active_branch_id = fields.Many2one("git.repo.branch", readonly=True)
    log_ids = fields.One2many("git.repo.log", "repo_id", readonly=True, compute="_compute_log_ids")

    def _is_readonly(self):
        self.ensure_one()
        return self.state in ["initialized", "connected"]

    def _compute_log_ids(self):
        for rec in self:
            log_data = rec._get_git_log()
            rec.log_ids = self.env["git.repo.log"].create(log_data)

    def _compute_http_url(self):
        for rec in self:
            rec.http_url = f"{rec.account_id.http_url}/{rec.name}"

    @api.depends("forge_id", "account_id", "name")
    def _compute_ssh_url(self):
        for rec in self:
            rec.ssh_url = f"git@{rec.forge_id.hostname}:{rec.account_id.name}/{rec.name}.git"

    @api.constrains("ssh_url")
    def _validate_ssh_url(self):
        for rec in self:
            if rec.ssh_url and not re.match(
                r"((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?",
                rec.ssh_url,
            ):
                raise ValidationError(f"Invalid SSH url: {rec.ssh_url}.")

    def _compute_local_path(self):
        for rec in self:
            rec.local_path = f"{rec.account_id.local_path}/{rec.name}"

    def _compute_ref(self):
        for rec in self:
            if rec.active_branch_id:
                rec.ref = rec.active_branch_id.name
            else:
                rec.ref = self._get_git_current_branch_name()

    # Command fields

    def _get_default_cmd_id(self):
        if self.state in ["initialized", "connected"]:
            return self.env.ref("git_base.cmd_status")
        else:
            return self.env.ref("git_base.cmd_init")

    cmd_id = fields.Many2one("git.repo.cmd", string="Command", default=_get_default_cmd_id)
    cmd_help = fields.Char(related="cmd_id.help")
    has_input = fields.Boolean(related="cmd_id.has_input")
    cmd_input = fields.Text("Input")
    cmd_input_file = fields.Binary(
        "File Upload",
        inverse="_inverse_cmd_input_file",
        help="Upload file to local path. Zip file will be extracted.",
    )
    cmd_input_filename = fields.Char("Filename")
    cmd_input_folder_path = fields.Char("Upload Path", default="./")
    cmd_output = fields.Text("Output", readonly=True)

    def _inverse_cmd_input_file(self):
        """Store file in local path. If file is zip then extract it."""
        for rec in self:
            if rec.cmd_input_file:
                rec.ensure_local_path_exists()

                upload_path = rec.local_path
                if rec.cmd_input_folder_path:
                    upload_path = os.path.join(upload_path, rec.cmd_input_folder_path)

                if not os.path.exists(upload_path):
                    raise UserError(_("Upload path does not exist."))

                if rec.cmd_input_filename.endswith(".zip"):
                    with zipfile.ZipFile(io.BytesIO(base64.decodebytes(rec.cmd_input_file))) as zip_file:
                        zip_file.extractall(upload_path)
                else:
                    with open(os.path.join(upload_path, rec.cmd_input_filename), "wb") as file:
                        file.write(base64.decodebytes(rec.cmd_input_file))
                rec.cmd_input_file = False
                rec.cmd_input_filename = False

    # Branch fields

    branch_ids = fields.One2many("git.repo.branch", "repo_id")
    account_id = fields.Many2one("git.account", required=True)
    forge_id = fields.Many2one("git.forge", related="account_id.forge_id")

    # Configuration fields

    push_url = fields.Char(compute="_compute_remote_url", store=True)
    pull_url = fields.Char(compute="_compute_remote_url", store=True)
    user_id = fields.Many2one("res.users")
    ssh_public_key = fields.Char("SSH Public Key")
    ssh_private_key_file = fields.Binary("SSH Private Key")
    ssh_private_key_filename = fields.Char("SSH Private Key Filename", compute="_compute_ssh_private_key_filename")
    ssh_private_key_password = fields.Char("SSH Private Key Password")
    active_keychain = fields.Char("Active Keychain", compute="_compute_active_keychain")

    def _compute_ssh_private_key_filename(self):
        for user in self:
            user.ssh_private_key_filename = f"/tmp/repo_private_key_{self.id}"

    @api.depends("ssh_url")
    def _compute_remote_url(self):
        for rec in self:
            rec.push_url = f"{rec.ssh_url}"
            rec.pull_url = f"{rec.ssh_url}"

    def _compute_active_keychain(self):
        for rec in self:
            keychain = self._get_keychain()
            rec.active_keychain = (
                f"{str(keychain).replace(',','')}: {keychain.ssh_private_key_filename}" if keychain else ""
            )

    # Model methods

    @api.model
    def switch_to_environment_branch(self):
        environment_id = self.env["server.config.environment"].get_active_environment()
        branch_id = self.branch_ids.filtered(lambda b: b.environment_id == environment_id)
        if not branch_id:
            raise UserError(_("No branch found for environment: %s") % environment_id.name)
        self.cmd_switch(branch_id.name)

    def ensure_local_path_exists(self):
        self.ensure_one()
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)

    def unlink(self):
        for rec in self:
            if not rec.state == "deleted":
                raise UserError(_("Repo can only be deleted if is in state 'Deleted'."))
        return super().unlink()

    def _get_git_user(self):
        return self.user_id or self.env.user

    # Git Methods

    def _get_git_author(self):
        user = self._get_git_user()
        return f"{user.name} <{user.email}>"

    def _get_git_branch_list(self):
        self.ensure_one()
        if os.path.exists(f"{self.local_path}"):
            return (
                check_output(["git", "-C", self.local_path, "branch", "--list"])
                .decode("utf-8")
                .replace("* ", "")  # Active branch is marked with *
                .replace("  ", "")
                .strip()  # Remove newlines
            ).split("\n")
        else:
            return ""

    def _get_git_remote_branch_list(self):
        self.ensure_one()
        if os.path.exists(f"{self.local_path}"):
            remote_branch_list = (
                check_output(["git", "-C", self.local_path, "branch", "-r", "--list"])
                .decode("utf-8")
                .replace("  origin/", "")
                .strip()  # Remove newlines
            ).split("\n")
            return [branch for branch in remote_branch_list if not re.match(r"HEAD -> .+", branch)]
        else:
            return ""

    def _get_git_remote(self):
        self.ensure_one()
        if os.path.exists(f"{self.local_path}"):
            return check_output(["git", "-C", self.local_path, "remote"]).decode("utf-8")
        else:
            return ""

    def _get_git_current_branch_name(self):
        self.ensure_one()
        if os.path.exists(f"{self.local_path}/.git"):
            return check_output(["git", "-C", self.local_path, "branch", "--show-current"]).decode("utf-8").strip()
        else:
            return ""

    def _get_git_log(self):
        self.ensure_one()
        if os.path.exists(f"{self.local_path}/.git"):
            git_log_format = "%H|||%an|||%ai|||%s"
            try:
                git_log = (
                    check_output(
                        [
                            "git",
                            "-C",
                            self.local_path,
                            "log",
                            f"--pretty=format:{git_log_format}",
                        ]
                    )
                    .decode("utf-8")
                    .strip()
                    .split("\n")
                )
            except CalledProcessError:
                git_log = []
            log_data = []
            for line in git_log:
                parts = line.split("|||")
                if len(parts) == 4:
                    commit, author, date, message = parts
                    log_data.append(
                        {
                            "commit": commit,
                            "author": author,
                            "date": datetime.strptime(date, "%Y-%m-%d %H:%M:%S %z")
                            .astimezone(pytz.UTC)
                            .replace(tzinfo=None),
                            "message": message,
                            "repo_id": self.id,
                        }
                    )
            return log_data
        else:
            return ""

    # Command Methods

    def cmd_message_post(self, input=False):
        """
        If current command is tracked, create chatter post.
        """
        if self.cmd_id.tracking:
            message = f'Executed git command "{self.cmd_id.name}"'
            if input:
                message += f" with input: {input}"
            self.message_post(body=message)

    def action_run_cmd(self):
        """
        Run selected command write output.
        Then reset input fields.
        """
        self.ensure_one()
        if self.cmd_id:
            _logger.info("Running git command: cmd_%s", self.cmd_id.code)
            if self.cmd_id.has_input:
                output = getattr(self, "cmd_" + self.cmd_id.code)(self.cmd_input)
            else:
                output = getattr(self, "cmd_" + self.cmd_id.code)()
            self.write({"cmd_output": output})

            if self.cmd_id.next_command_id and (self.state in self.cmd_id.next_command_id.states):
                self.cmd_id = self.cmd_id.next_command_id
            if self.cmd_id.clear_input:
                self.cmd_input = False

    def action_generate_deploy_keys(self):
        self.ensure_one()
        ssh_public_key, ssh_private_key_file = self.env["res.users.keychain"].generate_ssh_keys(
            f"{self.account_id.name}-{self.name}@{self.forge_id.hostname}",
            f"{self.ssh_private_key_filename}",
            self.ssh_private_key_password or "",
        )
        self.write(
            {
                "ssh_public_key": ssh_public_key,
                "ssh_private_key_file": ssh_private_key_file,
            }
        )

    # Status Commands

    def cmd_status(self):
        self.ensure_one()
        output = check_output(["git", "-C", self.local_path, "status"], stderr=STDOUT, text=True)
        self.cmd_message_post()
        return output

    def cmd_log(self):
        self.ensure_one()
        output = check_output(["git", "-C", self.local_path, "log"], stderr=STDOUT, text=True)
        self.cmd_message_post()
        return output

    def cmd_list(self, subfolder=False):
        self.ensure_one()
        list_path = self.local_path
        if subfolder:
            list_path = os.path.join(self.local_path, subfolder)
        if os.path.exists(list_path):
            output = check_output(["ls", "-a", list_path], stderr=STDOUT, text=True)
        else:
            output = _("Folder does not exist.")
        self.cmd_message_post(subfolder)
        return output

    # Stage Commands

    def cmd_add_all(self):
        self.ensure_one()
        output = check_output(["git", "-C", self.local_path, "add", "--all"], stderr=STDOUT, text=True)
        self.cmd_message_post()
        return output

    def cmd_unstage_all(self):
        self.ensure_one()
        output = check_output(["git", "-C", self.local_path, "restore", "--staged", "."], stderr=STDOUT, text=True)
        self.cmd_message_post()
        return output

    def cmd_clean(self):
        self.ensure_one()
        output = check_output(["git", "-C", self.local_path, "clean", "-fd"], stderr=STDOUT, text=True)
        self.cmd_message_post()
        return output

    def cmd_reset_hard(self):
        self.ensure_one()
        output = check_output(["git", "-C", self.local_path, "reset", "--hard"], stderr=STDOUT, text=True)
        self.cmd_message_post()
        return output

    def cmd_diff(self):
        self.ensure_one()
        output = check_output(["git", "-C", self.local_path, "diff"], stderr=STDOUT, text=True)
        self.cmd_message_post()
        return output

    def cmd_commit(self, message):
        self.ensure_one()
        if not message:
            raise UserError(_("Missing commit message."))
        user = self._get_git_user()
        os.environ["GIT_COMMITTER_NAME"] = user.name
        os.environ["GIT_COMMITTER_EMAIL"] = user.email
        git_command = [
            "git",
            "-C",
            self.local_path,
            "commit",
            "--author",
            self._get_git_author(),
            "--message",
            message,
            "--no-gpg-sign",
        ]
        result = run(git_command, text=True, capture_output=True)
        self.cmd_message_post(message)
        return result.stdout

    def cmd_commit_all(self, message):
        self.ensure_one()
        if not message:
            raise UserError(_("Missing commit message."))
        user = self._get_git_user()
        os.environ["GIT_COMMITTER_NAME"] = user.name
        os.environ["GIT_COMMITTER_EMAIL"] = user.email
        git_command = [
            "git",
            "-C",
            self.local_path,
            "commit",
            "--author",
            self._get_git_author(),
            "--all",
            "--message",
            message,
            "--no-gpg-sign",
        ]
        result = run(git_command, text=True, capture_output=True)
        self.cmd_message_post(message)
        return result.stdout

    # Branch Commands

    def cmd_branch_list(self):
        self.ensure_one()
        output = "\n".join(self._get_git_branch_list())
        self.cmd_message_post()
        return output

    def cmd_remote_branch_list(self):
        self.ensure_one()
        output = "\n".join(self._get_git_remote_branch_list())
        self.cmd_message_post()
        return output

    def cmd_switch(self, branch_name):
        self.ensure_one()
        if not branch_name:
            raise UserError(_("Missing branch name."))

        # Get list of local branches
        git_branch_list = self._get_git_branch_list()

        # Get branch record
        branch_id = self.branch_ids.filtered(lambda b: b.name == branch_name)

        # Create branch if is not in list
        if branch_name not in git_branch_list:
            output = check_output(
                ["git", "-C", self.local_path, "switch", "-c", branch_name],
                stderr=STDOUT,
            )
            branch_id = self.env["git.repo.branch"].create({"name": branch_name, "repo_id": self.id})

        # Switch to branch if is in list
        if branch_name in git_branch_list:
            output = check_output(["git", "-C", self.local_path, "switch", branch_name], stderr=STDOUT, text=True)

        self.write({"active_branch_id": branch_id})
        self.cmd_message_post(branch_name)
        return output

    def cmd_checkout(self, branch_name):
        self.ensure_one()
        if not branch_name:
            raise UserError(_("Missing branch name."))

        # Get list of local branches
        git_branch_list = self._get_git_branch_list()

        # Check if branch record exists
        branch_id = self.branch_ids.filtered(lambda b: b.name == branch_name)

        # If branch is not in list, create it
        if branch_name not in git_branch_list:
            # Checkout form upstream
            if branch_id and branch_id.upstream:
                output = check_output(
                    ["git", "-C", self.local_path, "checkout", branch_id.name, branch_id.upstream],
                    stderr=STDOUT,
                    text=True,
                )
            else:
                output = check_output(
                    ["git", "-C", self.local_path, "checkout", "-b", branch_name], stderr=STDOUT, text=True
                )
                branch_id = self.env["git.repo.branch"].create({"name": branch_name, "repo_id": self.id})

        # Checkout branch if is list of branches
        if branch_name in git_branch_list:
            output = check_output(
                ["git", "-C", self.local_path, "checkout", branch_name],
                stderr=STDOUT,
            )

        self.write({"active_branch_id": branch_id})
        self.cmd_message_post(branch_name)
        return output

    def cmd_delete_branch(self, branch_name):
        self.ensure_one()
        if not branch_name:
            raise UserError(_("Missing branch name."))

        # Get branch record
        branch_id = self.branch_ids.filtered(lambda b: b.name == branch_name)

        # Check if branch is not active
        if self.active_branch_id == branch_id:
            raise UserError(_("Cannot remove active branch."))

        # If branch exists in git, delete
        git_branch_list = self._get_git_branch_list()
        if branch_name in git_branch_list:
            output = check_output(
                ["git", "-C", self.local_path, "branch", "-D", branch_name],
                stderr=STDOUT,
            )
            self.cmd_message_post(branch_name)
            return output

    def cmd_rebase(self, branch_name):
        self.ensure_one()
        if not branch_name:
            raise UserError(_("Missing branch name."))
        output = self.run_ssh_command(["git", "-C", self.local_path, "rebase", branch_name])
        self.cmd_message_post(branch_name)
        return output

    def cmd_rebase_abort(self):
        self.ensure_one()
        output = self.run_ssh_command(["git", "-C", self.local_path, "rebase", "--abort"])
        self.cmd_message_post()
        return output

    # Remote Commands

    def cmd_add_remote(self):
        self.ensure_one()
        remote = self._get_git_remote()
        if "orign" in remote:
            output = _("Remote already exists.")
        else:
            output = check_output(
                [
                    "git",
                    "-C",
                    self.local_path,
                    "remote",
                    "add",
                    "origin",
                    self.ssh_url,
                ],
                stderr=STDOUT,
            )
        self.write({"state": "connected"})
        self.cmd_message_post()
        return output

    def cmd_set_upstream(self):
        self.ensure_one()
        output = self.run_ssh_command(
            [
                "git",
                "-C",
                self.local_path,
                "branch",
                f"--set-upstream-to=origin/{self.active_branch_id.name}",
                self.active_branch_id.name,
            ],
        )
        self.active_branch_id.write({"upstream": f"origin/{self.active_branch_id.name}"})
        self.cmd_message_post()
        return output

    def cmd_fetch(self, branch_name):
        self.ensure_one()
        if not branch_name:
            branch_name = self.active_branch_id.name
        output = self.run_ssh_command(
            [
                "git",
                "-C",
                self.local_path,
                "fetch",
                "origin",
                branch_name,
            ]
        )
        self.cmd_message_post()
        return output

    def cmd_fetch_all(self):
        self.ensure_one()
        output = self.run_ssh_command(["git", "-C", self.local_path, "fetch", "--all"])
        self.cmd_message_post()
        return output

    def cmd_pull(self):
        self.ensure_one()
        output = self.run_ssh_command(
            [
                "git",
                "-C",
                self.local_path,
                "pull",
                "--ff-only",
                "origin",
                self.active_branch_id.name,
            ]
        )
        if self.state != "connected":
            self.write(
                {
                    "state": "connected",
                }
            )
        self.cmd_message_post()
        return output

    def cmd_push(self):
        self.ensure_one()
        output = self.run_ssh_command(["git", "-C", self.local_path, "push"])
        self.cmd_message_post()
        return output

    def cmd_push_force(self):
        self.ensure_one()
        output = self.run_ssh_command(["git", "-C", self.local_path, "push", "--force"])
        self.cmd_message_post()
        return output

    def cmd_push_upstream(self):
        self.ensure_one()
        output = self.run_ssh_command(
            [
                "git",
                "-C",
                self.local_path,
                "push",
                "--set-upstream",
                "origin",
                self.active_branch_id.name,
            ]
        )
        self.active_branch_id.write({"upstream": f"origin/{self.active_branch_id.name}"})
        self.cmd_message_post()
        return output

    # Repo Commands

    def cmd_init(self):
        self.ensure_local_path_exists()
        output = check_output(["git", "init", self.local_path], stderr=STDOUT, text=True)
        branch_name = self._get_git_current_branch_name()
        self.write(
            {
                "state": "initialized",
            }
        )
        branch_id = self.branch_ids.filtered(lambda b: b.name == branch_name)[:1]
        if branch_id:
            self.active_branch_id = branch_id
        else:
            self.active_branch_id = self.env["git.repo.branch"].create({"name": branch_name, "repo_id": self.id})
        self.cmd_message_post()
        return output

    def cmd_clone(self):
        self.ensure_one()
        cmd = self.env["git.repo.cmd"].get_by_code("clone")
        output = self.run_ssh_command(["git", "clone", self.ssh_url, self.local_path], cmd.timeout)
        self.write(
            {
                "state": "connected",
            }
        )
        for branch in self._get_git_branch_list():
            repo_branch = self.branch_ids.filtered(lambda b: b.name == branch)
            if not repo_branch:
                self.env["git.repo.branch"].create(
                    {
                        "name": branch,
                        "repo_id": self.id,
                        "upstream": f"origin/{branch}",
                    }
                )
            else:
                repo_branch.write({"upstream": f"origin/{branch}"})
        self.active_branch_id = self.branch_ids.filtered(lambda b: b.name == self._get_git_current_branch_name())
        self.cmd_message_post()
        return output

    def cmd_clone_all_branches(self):
        self.ensure_one()
        output = self.run_ssh_command(["git", "clone", self.ssh_url, self.local_path])
        self.write(
            {
                "state": "connected",
            }
        )
        for branch in self._get_git_remote_branch_list():
            repo_branch = self.branch_ids.filtered(lambda b: b.name == branch)
            if not repo_branch:
                self.env["git.repo.branch"].create(
                    {
                        "name": branch,
                        "repo_id": self.id,
                        "upstream": f"origin/{branch}",
                    }
                )
            else:
                repo_branch.write({"upstream": f"origin/{branch}"})
            self.cmd_checkout(branch)
        self.active_branch_id = self.branch_ids.filtered(lambda b: b.name == self._get_git_current_branch_name())
        self.cmd_message_post()
        return output

    def cmd_remove(self, subfolder=False):
        self.ensure_one()
        remove_path = self.local_path
        if subfolder:
            remove_path = os.path.join(self.local_path, subfolder)
        output = check_output(["rm", "-rf", remove_path], stderr=STDOUT, text=True)
        if self.local_path == remove_path:
            self.write({"state": "deleted", "active_branch_id": False})
            self.branch_ids.unlink()
        self.cmd_message_post(subfolder)
        return output

    def cmd_mkdir(self, subfolder=False):
        self.ensure_one()
        mkdir_path = self.local_path
        if subfolder:
            mkdir_path = os.path.join(self.local_path, subfolder)
        output = check_output(["mkdir", "-p", mkdir_path], stderr=STDOUT, text=True)
        self.cmd_message_post(subfolder)
        return output

    def cmd_ssh_test(self):
        self.ensure_one()
        keychain = self._get_keychain()
        output = self.run_ssh_command(
            [
                "ssh",
                "-i",
                keychain.ssh_private_key_filename,
                "-o",
                "StrictHostKeyChecking=no",
                "-T",
                f"git@{self.forge_id.hostname}",
            ]
        )
        self.cmd_message_post()
        return output
