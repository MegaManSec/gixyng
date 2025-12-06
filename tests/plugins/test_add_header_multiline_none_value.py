"""
Test for GitHub issue #35: TypeError when header value is None.

https://github.com/dvershinin/gixy/issues/35

The add_header_multiline plugin crashed with:
    TypeError: argument of type 'NoneType' is not iterable
when processing headers with None values.

Note: In valid NGINX syntax, add_header requires both name and value.
However, gixy may encounter None values from:
- Malformed/incomplete configuration files
- Parser edge cases
- Internal processing bugs

The fix is defensive - gixy should handle gracefully instead of crashing.
"""

import pytest
from unittest.mock import MagicMock

from gixy.plugins.add_header_multiline import add_header_multiline
from gixy.directives.directive import AddHeaderDirective, MoreSetHeadersDirective


class TestAddHeaderMultilineNoneValue:
    """
    Test that add_header_multiline plugin handles None values gracefully.
    
    This is defensive programming - even though NGINX syntax requires values,
    gixy shouldn't crash when encountering malformed configs or parser edge cases.
    """

    def test_add_header_with_none_value_does_not_crash(self):
        """
        Regression test for GitHub issue #35.
        
        When a header value is None (from malformed config or parser edge case),
        the plugin should skip gracefully instead of crashing with:
        TypeError: argument of type 'NoneType' is not iterable
        """
        # Create plugin instance with minimal config
        plugin = add_header_multiline(config=MagicMock())
        
        # Create a mock directive with None value in headers
        directive = MagicMock(spec=AddHeaderDirective)
        directive.name = "add_header"
        directive.headers = {"X-Test-Header": None}
        
        # This should NOT raise TypeError
        # Before fix: TypeError: argument of type 'NoneType' is not iterable
        # After fix: silently skips None values
        plugin.audit(directive)
        
        # No issue should be added for None values
        assert not plugin.issues

    def test_more_set_headers_with_none_value_does_not_crash(self):
        """
        Test that more_set_headers directive with None value doesn't crash.
        """
        plugin = add_header_multiline(config=MagicMock())
        
        # Create a mock directive with None value
        directive = MagicMock(spec=MoreSetHeadersDirective)
        directive.name = "more_set_headers"
        directive.headers = {"X-Custom": None, "Y-Valid": "value"}
        
        # Should not raise TypeError
        plugin.audit(directive)

    def test_mixed_none_and_valid_values(self):
        """
        Test that plugin processes valid values while skipping None.
        """
        plugin = add_header_multiline(config=MagicMock())
        
        directive = MagicMock(spec=AddHeaderDirective)
        directive.name = "add_header"
        # Mix of None, empty string, and multiline value
        directive.headers = {
            "X-Null": None,
            "X-Empty": "",
            "X-Multiline": "line1\n line2",  # This has \n followed by space - should trigger issue
        }
        
        # Should not crash and should detect the multiline header
        plugin.audit(directive)
        
        # Should have found the multiline issue
        assert len(plugin.issues) == 1

    def test_all_none_values(self):
        """
        Test directive where all header values are None.
        """
        plugin = add_header_multiline(config=MagicMock())
        
        directive = MagicMock(spec=AddHeaderDirective)
        directive.name = "add_header"
        directive.headers = {
            "X-First": None,
            "X-Second": None,
            "X-Third": None,
        }
        
        # Should not crash
        plugin.audit(directive)
        
        # No issues for None values
        assert not plugin.issues


class TestAddHeaderMultilineNoneValueFailsWithoutFix:
    """
    These tests document the root cause of issue #35 and verify the fix.
    
    The 'in' operator on None raises TypeError. This is defensive programming
    to handle edge cases in malformed configs - even though valid NGINX syntax
    always requires a header value.
    """

    def test_in_operator_on_none_raises_typeerror(self):
        """
        Demonstrate that using 'in' operator on None raises TypeError.
        This documents the root cause of issue #35.
        """
        value = None
        
        with pytest.raises(TypeError, match="argument of type 'NoneType' is not iterable"):
            _ = "\n " in value  # noqa: This intentionally tests TypeError on None

    def test_fix_demonstrates_defensive_handling(self):
        """
        Demonstrate the defensive fix pattern.
        
        The original code:
            if "\\n\\x20" in value or "\\n\\t" in value:
        
        Crashes when value is None from malformed config. The fix:
            if value is None:
                continue
        """
        # Simulating malformed config where header has no value
        headers = {"X-Malformed": None, "X-Valid": "proper value"}
        
        processed = []
        for header, value in headers.items():
            # The fix: skip None values gracefully
            if value is None:
                continue
            
            # Now safe to use 'in' operator
            if "\n\x20" in value or "\n\t" in value:
                processed.append(header)
        
        # X-Malformed was skipped, X-Valid was processed
        assert "X-Malformed" not in processed

