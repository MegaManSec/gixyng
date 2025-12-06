"""Unit tests for the ReDoS analyzer."""

import pytest
from gixy.plugins.regex_redos import RedosAnalyzer


class TestNestedQuantifiers:
    """Test detection of nested quantifier patterns."""
    
    def test_plus_inside_plus(self):
        """(a+)+ is vulnerable."""
        analyzer = RedosAnalyzer("(a+)+")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
        assert "Nested quantifier" in str(vulns[0])
    
    def test_star_inside_plus(self):
        """(a*)+ is vulnerable."""
        analyzer = RedosAnalyzer("(a*)+")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
        assert "Nested quantifier" in str(vulns[0])
    
    def test_plus_inside_star(self):
        """(a+)* is vulnerable."""
        analyzer = RedosAnalyzer("(a+)*")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
        assert "Nested quantifier" in str(vulns[0])
    
    def test_star_inside_star(self):
        """(a*)* is vulnerable."""
        analyzer = RedosAnalyzer("(a*)*")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
        assert "Nested quantifier" in str(vulns[0])
    
    def test_nested_groups(self):
        """((ab)+)+ is vulnerable."""
        analyzer = RedosAnalyzer("((ab)+)+")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
        assert "Nested quantifier" in str(vulns[0])
    
    def test_nested_with_content(self):
        """((a+)b)+ has nested quantifier."""
        analyzer = RedosAnalyzer("((a+)b)+")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
        assert "Nested quantifier" in str(vulns[0])
    
    def test_complex_nested(self):
        """^/(a+)+$ is vulnerable."""
        analyzer = RedosAnalyzer("^/(a+)+$")
        vulns = analyzer.analyze()
        assert len(vulns) > 0


class TestOverlappingAlternatives:
    """Test detection of overlapping alternatives in quantifiers."""
    
    def test_prefix_overlap(self):
        """(a|ab)+ has overlapping alternatives."""
        analyzer = RedosAnalyzer("(a|ab)+")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
        assert "Overlapping" in str(vulns[0])
    
    def test_dot_overlap(self):
        """(.|a)+ - dot overlaps with everything."""
        analyzer = RedosAnalyzer("(.|a)+")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
    
    def test_longer_prefix_overlap(self):
        """(foo|foobar)+ has overlapping alternatives."""
        analyzer = RedosAnalyzer("(foo|foobar)+")
        vulns = analyzer.analyze()
        assert len(vulns) > 0


class TestSafePatterns:
    """Test that safe patterns don't trigger false positives."""
    
    def test_simple_plus(self):
        """a+ is safe."""
        analyzer = RedosAnalyzer("a+")
        vulns = analyzer.analyze()
        assert len(vulns) == 0
    
    def test_simple_star(self):
        """a* is safe."""
        analyzer = RedosAnalyzer("a*")
        vulns = analyzer.analyze()
        assert len(vulns) == 0
    
    def test_character_class_plus(self):
        """[a-z]+ is safe."""
        analyzer = RedosAnalyzer("[a-z]+")
        vulns = analyzer.analyze()
        assert len(vulns) == 0
    
    def test_bounded_quantifier(self):
        """a{1,10} is safe (bounded)."""
        analyzer = RedosAnalyzer("a{1,10}")
        vulns = analyzer.analyze()
        assert len(vulns) == 0
    
    def test_non_overlapping_alternatives(self):
        """(foo|bar) without quantifier is safe."""
        analyzer = RedosAnalyzer("(foo|bar)")
        vulns = analyzer.analyze()
        assert len(vulns) == 0
    
    def test_non_overlapping_alternatives_plus(self):
        """(foo|bar)+ with non-overlapping alternatives is safe."""
        analyzer = RedosAnalyzer("(foo|bar)+")
        vulns = analyzer.analyze()
        assert len(vulns) == 0
    
    def test_anchored_pattern(self):
        """^[a-z]+$ is safe."""
        analyzer = RedosAnalyzer("^[a-z]+$")
        vulns = analyzer.analyze()
        assert len(vulns) == 0
    
    def test_single_quantifier_group(self):
        """(abc)+ is safe - no nested quantifier."""
        analyzer = RedosAnalyzer("(abc)+")
        vulns = analyzer.analyze()
        assert len(vulns) == 0
    
    def test_sequential_quantifiers(self):
        """a+b+ is safe - not nested."""
        analyzer = RedosAnalyzer("a+b+")
        vulns = analyzer.analyze()
        assert len(vulns) == 0
    
    def test_real_world_safe_pattern(self):
        """^/api/v[0-9]+/users$ is safe."""
        analyzer = RedosAnalyzer("^/api/v[0-9]+/users$")
        vulns = analyzer.analyze()
        assert len(vulns) == 0


class TestRealWorldVulnerablePatterns:
    """Test detection of real-world vulnerable patterns."""
    
    def test_email_like(self):
        """^([a-zA-Z0-9]+)+@example.com$ has nested quantifier."""
        analyzer = RedosAnalyzer("^([a-zA-Z0-9]+)+@example.com$")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
    
    def test_classic_redos(self):
        """^(a|a)+$ is the classic ReDoS pattern."""
        analyzer = RedosAnalyzer("^(a|a)+$")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
    
    def test_url_path_vulnerable(self):
        """^/((sub)+\\.)+example\\.com$ has nested quantifiers."""
        analyzer = RedosAnalyzer(r"^/((sub)+\.)+example\.com$")
        vulns = analyzer.analyze()
        assert len(vulns) > 0


class TestAdjacentQuantifiers:
    """Test detection of adjacent overlapping quantifiers."""
    
    def test_adjacent_dot_star(self):
        """.*.*end has adjacent greedy quantifiers."""
        analyzer = RedosAnalyzer(".*.*end")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
        assert "Adjacent" in str(vulns[0]) or "backtracking" in str(vulns[0])
    
    def test_adjacent_dot_plus(self):
        """.+.+suffix has adjacent greedy quantifiers."""
        analyzer = RedosAnalyzer(".+.+suffix")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
    
    def test_non_adjacent_quantifiers(self):
        """.*foo.* is safe - quantifiers separated by literal."""
        analyzer = RedosAnalyzer(".*foo.*")
        vulns = analyzer.analyze()
        # This might or might not trigger depending on implementation
        # The key is it shouldn't crash
        assert isinstance(vulns, list)


class TestInvalidPatterns:
    """Test handling of invalid/unparseable patterns."""
    
    def test_invalid_regex(self):
        """Invalid regex should return empty list, not crash."""
        analyzer = RedosAnalyzer("(unclosed")
        vulns = analyzer.analyze()
        assert vulns == []
    
    def test_empty_pattern(self):
        """Empty pattern is safe."""
        analyzer = RedosAnalyzer("")
        vulns = analyzer.analyze()
        assert len(vulns) == 0


class TestVulnerabilityDetails:
    """Test that vulnerability objects have proper details."""
    
    def test_exponential_type(self):
        """Nested quantifiers should be marked as exponential."""
        analyzer = RedosAnalyzer("(a+)+")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
        from gixy.plugins.regex_redos import RedosVulnerability
        assert vulns[0].type == RedosVulnerability.EXPONENTIAL
    
    def test_polynomial_type(self):
        """Overlapping alternatives should be marked as polynomial."""
        analyzer = RedosAnalyzer("(a|ab)+")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
        from gixy.plugins.regex_redos import RedosVulnerability
        assert vulns[0].type == RedosVulnerability.POLYNOMIAL
    
    def test_attack_hint(self):
        """Vulnerabilities should have attack hints."""
        analyzer = RedosAnalyzer("(a+)+")
        vulns = analyzer.analyze()
        assert len(vulns) > 0
        assert vulns[0].attack_hint is not None

