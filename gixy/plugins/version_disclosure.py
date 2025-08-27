import gixy
from gixy.plugins.plugin import Plugin


class version_disclosure(Plugin):
    """
    Syntax for the directive: server_tokens off;
    """
    summary = 'Do not enable server_tokens on or server_tokens build'
    severity = gixy.severity.HIGH
    description = ("Using server_tokens on; or server_tokens build;  allows an "
                   "attacker to learn the version of NGINX you are running, which can "
                   "be used to exploit known vulnerabilities.")
    help_url = 'https://gixy.getpagespeed.com/en/plugins/version_disclosure/'
    directives = ['server_tokens']
    supports_full_config = True

    def audit(self, directive):
        if directive.args[0] in ['on', 'build']:
            self.add_issue(
                severity=gixy.severity.HIGH,
                directive=[directive, directive.parent],
                reason="Using server_tokens value which promotes information disclosure"
            )

    def post_audit(self, root):
        """Check for missing server_tokens directive in full config mode"""
        # Find http block
        http_block = None
        for child in root.children:
            if child.name == 'http':
                http_block = child
                break
        
        if not http_block:
            return
        
        # Check if server_tokens is set at http level
        http_server_tokens = http_block.some('server_tokens')
        if http_server_tokens and http_server_tokens.args[0] == 'off':
            # server_tokens is properly set at http level, no need to check further
            return
        
        # Check each server block for server_tokens
        for server_block in http_block.find_all_contexts_of_type('server'):
            server_tokens = server_block.some('server_tokens')
            server_level_issue = False
            
            if not server_tokens:
                # Missing server_tokens directive in this server block
                self.add_issue(
                    severity=gixy.severity.HIGH,
                    directive=[server_block],
                    reason="Missing server_tokens directive - defaults to 'on' which promotes information disclosure"
                )
                server_level_issue = True
            elif server_tokens.args[0] in ['on', 'build']:
                # This case is already handled by the regular audit method
                server_level_issue = True
            
            # Only check location blocks if server level is properly configured
            if not server_level_issue:
                for location_block in server_block.find_all_contexts_of_type('location'):
                    location_tokens = location_block.some('server_tokens')
                    
                    if not location_tokens:
                        # Check if server_tokens is inherited from server or http level
                        inherited_tokens = None
                        if server_tokens:
                            inherited_tokens = server_tokens
                        elif http_server_tokens:
                            inherited_tokens = http_server_tokens
                        
                        # Only report if there's no safe inherited value
                        if not inherited_tokens or inherited_tokens.args[0] in ['on', 'build']:
                            self.add_issue(
                                severity=gixy.severity.MEDIUM,  # Lower severity for location blocks
                                directive=[location_block],
                                reason="Missing server_tokens directive in location - inherits unsafe default"
                            )
