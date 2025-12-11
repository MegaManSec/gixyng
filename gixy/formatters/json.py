from __future__ import absolute_import

import json

from gixy.formatters.base import BaseFormatter


class JsonFormatter(BaseFormatter):
    def format_reports(self, reports, stats):
        result = []
        for path, issues in reports.items():
            for issue in issues:
                entry = {
                    "path": path,
                    "plugin": issue["plugin"],
                    "summary": issue["summary"],
                    "severity": issue["severity"],
                    "description": issue["description"],
                    "reference": issue["help_url"],
                    "reason": issue["reason"],
                    "config": issue["config"],
                }
                location = issue.get("location")
                if location:
                    entry["line"] = location.get("line")
                    if location.get("file"):
                        entry["file"] = location["file"]
                result.append(entry)

        return json.dumps(result, sort_keys=True, indent=2, separators=(',', ': '))
