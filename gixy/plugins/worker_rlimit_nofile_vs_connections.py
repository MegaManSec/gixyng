"""Module for try_files_is_evil_too plugin."""

import gixy
from gixy.plugins.plugin import Plugin


class worker_rlimit_nofile_vs_connections(Plugin):
    """
    Insecure example:
        worker_connections 1024;
        worker_rlimit_nofile 1024;  # should be higher than worker_connections
    """

    summary = (
        "The worker_rlimit_nofile should be at least twice than worker_connections."
    )
    severity = gixy.severity.MEDIUM
    description = (
        "The worker_rlimit_nofile should be at least twice than worker_connections."
    )
    help_url = (
        "https://gixy.getpagespeed.com/en/plugins/worker_rlimit_nofile_vs_connections/"
    )
    directives = ["worker_connections"]

    def audit(self, directive):
        # get worker_connections value
        worker_connections = directive.args[0]
        worker_rlimit_nofile_directive = directive.find_single_directive_in_scope(
            "worker_rlimit_nofile"
        )
        if worker_rlimit_nofile_directive:
            worker_rlimit_nofile = worker_rlimit_nofile_directive.args[0]
            if int(worker_rlimit_nofile) < int(worker_connections) * 2:
                self.add_issue(
                    severity=self.severity,
                    directive=[directive, worker_rlimit_nofile_directive],
                    reason=(
                        "worker_rlimit_nofile should be at least twice than worker_connections"
                    ),
                )
        else:
            self.add_issue(
                severity=self.severity,
                directive=[directive],
                reason=(
                    "Missing worker_rlimit_nofile with at least twice the value of worker_connections"
                ),
            )
