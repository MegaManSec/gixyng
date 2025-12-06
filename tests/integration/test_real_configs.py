"""
Integration tests with real-world nginx configurations.

These tests verify that comprehensive, properly-configured nginx configs
do NOT trigger any gixy warnings (no false positives on realistic setups).
"""

import os
import pytest

from gixy.core.manager import Manager


INTEGRATION_DIR = os.path.dirname(os.path.abspath(__file__))


def get_integration_configs():
    """Find all .conf files in the integration directory."""
    configs = []
    for filename in os.listdir(INTEGRATION_DIR):
        if filename.endswith('.conf'):
            configs.append(os.path.join(INTEGRATION_DIR, filename))
    return configs


class TestRealWorldConfigs:
    """Test real-world nginx configurations for false positives."""
    
    @pytest.mark.parametrize('config_path', get_integration_configs())
    def test_no_false_positives(self, config_path):
        """
        Real-world configs should not trigger any warnings.
        
        These configs represent properly secured, production-ready setups
        that follow nginx best practices. If gixy reports issues on these,
        it's likely a false positive that needs to be fixed.
        """
        manager = Manager()
        
        with open(config_path, 'r') as f:
            manager.audit(config_path, f)
        
        issues = list(manager.results)
        
        if issues:
            # Provide detailed failure message
            issue_details = []
            for issue in issues:
                plugin_name = getattr(issue, 'plugin', issue.__class__.__name__)
                summary = getattr(issue, 'summary', str(issue))
                reason = getattr(issue, 'reason', 'N/A')
                severity = getattr(issue, 'severity', 'N/A')
                issue_details.append(
                    f"  - [{plugin_name}] {summary}\n"
                    f"    Reason: {reason}\n"
                    f"    Severity: {severity}"
                )
            
            config_name = os.path.basename(config_path)
            pytest.fail(
                f"Config '{config_name}' triggered {len(issues)} unexpected issue(s):\n" +
                "\n".join(issue_details) +
                "\n\nThis may indicate a false positive in one of the plugins."
            )
    
    def test_wordpress_production_config_exists(self):
        """Verify the WordPress production config exists."""
        config_path = os.path.join(INTEGRATION_DIR, 'wordpress_production.conf')
        assert os.path.exists(config_path), "WordPress production config not found"
    
    def test_wordpress_production_is_substantial(self):
        """Verify the WordPress config is comprehensive (not trivial)."""
        config_path = os.path.join(INTEGRATION_DIR, 'wordpress_production.conf')
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Should be a substantial config
        assert len(content) > 5000, "WordPress config should be comprehensive"
        
        # Should contain key WordPress elements
        assert 'wp-admin' in content
        assert 'wp-content' in content
        assert 'fastcgi_pass' in content
        assert 'ssl_certificate' in content
        assert 'add_header' in content
        assert 'location' in content
        
        # Should have security measures
        assert 'X-Frame-Options' in content
        assert 'X-Content-Type-Options' in content
        assert 'Strict-Transport-Security' in content


class TestConfigCoverage:
    """Verify integration configs exercise various nginx features."""
    
    def test_wordpress_covers_key_directives(self):
        """WordPress config should exercise many directive types."""
        config_path = os.path.join(INTEGRATION_DIR, 'wordpress_production.conf')
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Directives that should be present
        expected_directives = [
            'server_name',
            'listen',
            'root',
            'index',
            'location',
            'try_files',
            'return',
            'deny',
            'allow',
            'add_header',
            'expires',
            'ssl_certificate',
            'ssl_protocols',
            'fastcgi_pass',
            'fastcgi_param',
            'upstream',
            'keepalive',
            'gzip',
            'limit_req',
            'resolver',
            'worker_rlimit_nofile',
            'worker_connections',
        ]
        
        missing = [d for d in expected_directives if d not in content]
        assert not missing, f"Config missing expected directives: {missing}"
    
    def test_wordpress_has_various_location_types(self):
        """WordPress config should have various location block types."""
        config_path = os.path.join(INTEGRATION_DIR, 'wordpress_production.conf')
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Should have different location types
        assert 'location =' in content, "Should have exact match locations"
        assert 'location ^~' in content or 'location /' in content, "Should have prefix locations"
        assert 'location ~' in content, "Should have regex locations"
        assert 'location ~*' in content, "Should have case-insensitive regex locations"

