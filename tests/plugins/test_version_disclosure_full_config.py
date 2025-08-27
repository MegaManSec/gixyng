#!/usr/bin/env python3
"""
Test the enhanced version_disclosure plugin with full config mode support
"""

import tempfile
import os
from gixy.core.manager import Manager
from gixy.core.config import Config


def test_missing_server_tokens_full_config():
    """Test that missing server_tokens directive is detected in full config mode"""
    
    # Test case 1: Missing server_tokens entirely - should trigger HIGH severity
    config1 = """
http {
    server {
        listen 80;
        server_name example.com;
        location / {
            return 200 "Hello World";
        }
    }
}
"""
    
    # Test case 2: server_tokens set to off at http level - should NOT trigger
    config2 = """
http {
    server_tokens off;
    server {
        listen 80;
        server_name example.com;
        location / {
            return 200 "Hello World";
        }
    }
}
"""
    
    # Test case 3: server_tokens set to on explicitly - should trigger original audit
    config3 = """
http {
    server {
        listen 80;
        server_name example.com;
        server_tokens on;
        location / {
            return 200 "Hello World";
        }
    }
}
"""
    
    # Test case 4: server_tokens set to off at server level - should NOT trigger
    config4 = """
http {
    server {
        listen 80;
        server_name example.com;
        server_tokens off;
        location / {
            return 200 "Hello World";
        }
    }
}
"""
    
    # Test case 5: Mixed server blocks - one missing, one configured
    config5 = """
http {
    server {
        listen 80;
        server_name good.com;
        server_tokens off;
        location / {
            return 200 "Hello World";
        }
    }
    server {
        listen 80;
        server_name bad.com;
        # Missing server_tokens - should trigger
        location / {
            return 200 "Hello World";
        }
    }
}
"""
    
    def test_config(config_text, expected_issues, expected_reasons=None):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_text)
            f.flush()
            
            try:
                config = Config(plugins=['version_disclosure'])
                with Manager(config=config) as manager:
                    with open(f.name, 'rb') as fdata:
                        manager.audit(f.name, fdata)
                    
                    issues = list(manager.results)
                    if issues:
                        plugin_issues = issues[0].issues
                        actual_issues = len(plugin_issues)
                        
                        if expected_reasons:
                            actual_reasons = [issue.reason for issue in plugin_issues]
                            for expected_reason in expected_reasons:
                                assert any(expected_reason in reason for reason in actual_reasons), \
                                    f"Expected reason '{expected_reason}' not found in {actual_reasons}"
                        
                        assert actual_issues == expected_issues, \
                            f"Expected {expected_issues} issues, got {actual_issues}"
                    else:
                        assert expected_issues == 0, f"Expected {expected_issues} issues, got 0"
                        
            finally:
                os.unlink(f.name)
    
    # Test missing server_tokens (should find 1 issue)
    test_config(config1, 1, ["Missing server_tokens directive"])
    
    # Test server_tokens off at http level (should find 0 issues)
    test_config(config2, 0)
    
    # Test server_tokens on (should find 1 issue)
    test_config(config3, 1, ["Using server_tokens value"])
    
    # Test server_tokens off at server level (should find 0 issues)
    test_config(config4, 0)
    
    # Test mixed configuration (should find 1 issue for bad server)
    test_config(config5, 1, ["Missing server_tokens directive"])


def test_partial_config_no_full_analysis():
    """Test that partial configs (without http block) don't trigger full analysis"""
    
    # Partial config - just server block without http wrapper
    partial_config = """
server {
    listen 80;
    server_name example.com;
    # Missing server_tokens but this is partial config, so should not trigger full analysis
    location / {
        return 200 "Hello World";
    }
}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write(partial_config)
        f.flush()
        
        try:
            config = Config(plugins=['version_disclosure'])
            with Manager(config=config) as manager:
                with open(f.name, 'rb') as fdata:
                    manager.audit(f.name, fdata)
                
                issues = list(manager.results)
                # Should find 0 issues because this is not a full config
                assert len(issues) == 0, f"Expected 0 issues for partial config, got {len(issues)}"
                
        finally:
            os.unlink(f.name)


if __name__ == '__main__':
    test_missing_server_tokens_full_config()
    test_partial_config_no_full_analysis()
    print("All enhanced version_disclosure tests passed!") 