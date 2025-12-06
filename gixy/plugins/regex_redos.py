"""
ReDoS (Regular Expression Denial of Service) detection plugin.

This plugin analyzes regular expressions used in nginx configuration for
patterns that may cause catastrophic backtracking, leading to denial of service.

No external dependencies required - uses Python's built-in sre_parse module.

Detects:
  - Nested quantifiers: (a+)+, (a*)+, ((ab)+)+ → exponential O(2^n) backtracking
  - Overlapping alternatives: (a|ab)+, (.|x)+ → polynomial O(n^2) backtracking  
  - Adjacent overlapping quantifiers: .*.*something → polynomial backtracking
  - Quantifiers in lookaheads: (?=.*a)+ → can cause issues

Example attack:
  Pattern: ^/(a+)+$
  Input: /aaaaaaaaaaaaaaaaaaaaaaaaaab
  Result: regex engine tries 2^24 paths before failing
"""

import re
import sre_parse
from sre_parse import LITERAL, NOT_LITERAL, RANGE, AT, IN, ANY, CATEGORY
from sre_parse import BRANCH, SUBPATTERN, ASSERT, ASSERT_NOT
from sre_parse import MAX_REPEAT, MIN_REPEAT

import gixy
from gixy.plugins.plugin import Plugin


# Quantifier opcodes
QUANTIFIERS = (MAX_REPEAT, MIN_REPEAT)


class RedosVulnerability:
    """Represents a detected ReDoS vulnerability with details."""
    
    EXPONENTIAL = "exponential"  # O(2^n) - very dangerous
    POLYNOMIAL = "polynomial"    # O(n^k) - dangerous
    
    def __init__(self, vuln_type, description, pattern_snippet=None, attack_hint=None):
        self.type = vuln_type
        self.description = description
        self.pattern_snippet = pattern_snippet
        self.attack_hint = attack_hint
    
    def __str__(self):
        result = self.description
        if self.attack_hint:
            result += f" (try input like: {self.attack_hint})"
        return result


class RedosAnalyzer:
    """
    Analyzes regex patterns for ReDoS vulnerabilities using sre_parse.
    
    This analyzer uses static analysis of the regex AST to detect patterns
    known to cause catastrophic backtracking. It requires no external 
    dependencies and runs in milliseconds.
    
    Detection categories:
    
    1. NESTED QUANTIFIERS (Exponential - O(2^n))
       - (a+)+, (a*)+, (a+)*, (a*)*
       - ((ab)+)+, ((a|b)+)+
       - Any quantifier containing another quantifier
       
    2. OVERLAPPING ALTERNATIVES (Polynomial - O(n^k))
       - (a|ab)+ where 'a' is prefix of 'ab'
       - (.|x)+ where '.' matches 'x'
       - Regex parser optimizes (a|ab) to a(?:|b)
       
    3. ADJACENT OVERLAPPING QUANTIFIERS (Polynomial)
       - .*.*something - two greedy quantifiers competing
       - .+.+end - similar issue
    """
    
    def __init__(self, pattern, case_insensitive=False):
        self.pattern = pattern
        self.flags = re.IGNORECASE if case_insensitive else 0
        self.vulnerabilities = []
        
    def analyze(self):
        """
        Analyze the pattern and return list of RedosVulnerability objects.
        Returns empty list if pattern is safe.
        """
        self.vulnerabilities = []
        
        try:
            parsed = sre_parse.parse(self.pattern, self.flags)
        except (re.error, Exception):
            # If we can't parse it, we can't analyze it
            return []
        
        # Check for various vulnerability patterns
        self._check_nested_quantifiers(parsed, depth=0, in_quantifier=False)
        self._check_overlapping_alternatives(parsed)
        self._check_adjacent_quantifiers(parsed)
        
        return self.vulnerabilities
    
    def _check_nested_quantifiers(self, parsed, depth, in_quantifier):
        """
        Recursively check for nested quantifiers - causes EXPONENTIAL backtracking.
        
        Examples:
        - (a+)+   → O(2^n) for input "aaa...b"
        - (a*)+   → O(2^n) 
        - ((ab)+)+ → O(2^n)
        """
        for op, av in parsed:
            if op in QUANTIFIERS:
                min_repeat, max_repeat, subpattern = av
                
                # Check if this quantifier can match variable length
                can_repeat = max_repeat > min_repeat or max_repeat == sre_parse.MAXREPEAT
                
                if can_repeat:
                    if in_quantifier:
                        # Found nested quantifier!
                        self.vulnerabilities.append(RedosVulnerability(
                            RedosVulnerability.EXPONENTIAL,
                            "Nested quantifier detected - causes exponential O(2^n) backtracking",
                            attack_hint="repeat the matching char many times + non-matching char"
                        ))
                        return
                    
                    # Check if the subpattern itself contains quantifiers
                    if self._contains_quantifier(subpattern):
                        self.vulnerabilities.append(RedosVulnerability(
                            RedosVulnerability.EXPONENTIAL,
                            "Nested quantifier in group - causes exponential O(2^n) backtracking",
                            attack_hint="repeat the matching char many times + non-matching char"
                        ))
                        return
                    
                    # Recurse into the subpattern
                    self._check_nested_quantifiers(subpattern, depth + 1, in_quantifier=True)
                else:
                    self._check_nested_quantifiers(subpattern, depth + 1, in_quantifier)
                    
            elif op == SUBPATTERN:
                _, _, _, subpattern = av
                self._check_nested_quantifiers(subpattern, depth + 1, in_quantifier)
                
            elif op == BRANCH:
                _, branches = av
                for branch in branches:
                    self._check_nested_quantifiers(branch, depth + 1, in_quantifier)
                    
            elif op in (ASSERT, ASSERT_NOT):
                _, subpattern = av
                # Quantifiers in lookaheads can also be problematic
                self._check_nested_quantifiers(subpattern, depth + 1, in_quantifier)
    
    def _contains_quantifier(self, parsed):
        """Check if parsed pattern contains any unbounded quantifiers."""
        for op, av in parsed:
            if op in QUANTIFIERS:
                min_repeat, max_repeat, _ = av
                if max_repeat > min_repeat or max_repeat == sre_parse.MAXREPEAT:
                    return True
            elif op == SUBPATTERN:
                _, _, _, subpattern = av
                if self._contains_quantifier(subpattern):
                    return True
            elif op == BRANCH:
                _, branches = av
                for branch in branches:
                    if self._contains_quantifier(branch):
                        return True
            elif op in (ASSERT, ASSERT_NOT):
                _, subpattern = av
                if self._contains_quantifier(subpattern):
                    return True
        return False
    
    def _check_overlapping_alternatives(self, parsed, in_quantifier=False):
        """
        Check for overlapping alternatives with quantifiers - causes POLYNOMIAL backtracking.
        
        Examples:
        - (a|ab)+   → Python optimizes to a(?:|b)+, empty branch causes backtracking
        - (.|x)+    → '.' matches 'x', so alternatives overlap
        - (foo|foobar)+ → 'foo' is prefix of 'foobar'
        """
        for op, av in parsed:
            if op in QUANTIFIERS:
                min_repeat, max_repeat, subpattern = av
                can_repeat = max_repeat > min_repeat or max_repeat == sre_parse.MAXREPEAT
                
                if can_repeat:
                    if self._has_overlapping_branch(subpattern):
                        self.vulnerabilities.append(RedosVulnerability(
                            RedosVulnerability.POLYNOMIAL,
                            "Overlapping alternatives in quantified group - causes polynomial O(n²) backtracking",
                            attack_hint="repeat the common prefix many times"
                        ))
                        return
                    self._check_overlapping_alternatives(subpattern, in_quantifier=True)
                else:
                    self._check_overlapping_alternatives(subpattern, in_quantifier)
                    
            elif op == SUBPATTERN:
                _, _, _, subpattern = av
                self._check_overlapping_alternatives(subpattern, in_quantifier)
                
            elif op == BRANCH:
                _, branches = av
                if in_quantifier and self._branches_overlap(branches):
                    self.vulnerabilities.append(RedosVulnerability(
                        RedosVulnerability.POLYNOMIAL,
                        "Overlapping alternatives in quantified group - causes polynomial O(n²) backtracking",
                        attack_hint="repeat the common prefix many times"
                    ))
                    return
                for branch in branches:
                    self._check_overlapping_alternatives(branch, in_quantifier)
    
    def _check_adjacent_quantifiers(self, parsed, prev_was_greedy_quantifier=False):
        """
        Check for adjacent quantifiers that can match overlapping content.
        
        Examples:
        - .*.*end    → two greedy .* compete for the same characters
        - .+.+suffix → similar issue
        - [a-z]*[a-z]*done → overlapping character classes
        """
        for i, (op, av) in enumerate(parsed):
            if op in QUANTIFIERS:
                min_repeat, max_repeat, subpattern = av
                can_be_greedy = max_repeat == sre_parse.MAXREPEAT or max_repeat > 1
                
                # Check if this quantifier matches "anything" (. or broad class)
                matches_anything = self._matches_broad_input(subpattern)
                
                if prev_was_greedy_quantifier and can_be_greedy and matches_anything:
                    self.vulnerabilities.append(RedosVulnerability(
                        RedosVulnerability.POLYNOMIAL,
                        "Adjacent greedy quantifiers matching overlapping content - causes polynomial backtracking",
                        attack_hint="long string of matching characters without the expected suffix"
                    ))
                    return
                
                prev_was_greedy_quantifier = can_be_greedy and matches_anything
                self._check_adjacent_quantifiers(subpattern, False)
                
            elif op == SUBPATTERN:
                _, _, _, subpattern = av
                self._check_adjacent_quantifiers(subpattern, prev_was_greedy_quantifier)
                
            elif op == BRANCH:
                _, branches = av
                for branch in branches:
                    self._check_adjacent_quantifiers(branch, prev_was_greedy_quantifier)
            else:
                # Reset after non-quantifier
                prev_was_greedy_quantifier = False
    
    def _matches_broad_input(self, parsed):
        """Check if pattern matches a broad range of input (like . or [^x])."""
        if len(parsed) != 1:
            return False
        op, av = parsed[0]
        if op == ANY:
            return True
        if op == NOT_LITERAL:
            return True  # [^x] matches almost everything
        if op == IN:
            # Check if it's a negated class or very broad
            for inner_op, inner_av in av:
                if inner_op == CATEGORY:
                    return True  # \w, \d, \s are fairly broad
            # Check size of character class
            char_count = 0
            for inner_op, inner_av in av:
                if inner_op == LITERAL:
                    char_count += 1
                elif inner_op == RANGE:
                    char_count += inner_av[1] - inner_av[0] + 1
            if char_count > 10:  # Arbitrary threshold for "broad"
                return True
        return False
    
    def _has_overlapping_branch(self, parsed):
        """Check if pattern contains a BRANCH with overlapping or empty alternatives."""
        for op, av in parsed:
            if op == BRANCH:
                _, branches = av
                # Empty branch = Python's optimization of (a|ab) → a(?:|b)
                for branch in branches:
                    if len(branch) == 0:
                        return True
                if self._branches_overlap(branches):
                    return True
            elif op == SUBPATTERN:
                _, _, _, subpattern = av
                if self._has_overlapping_branch(subpattern):
                    return True
            elif op in QUANTIFIERS:
                _, _, subpattern = av
                if self._has_overlapping_branch(subpattern):
                    return True
        return False
    
    def _branches_overlap(self, branches):
        """
        Check if any branches in an alternation can match the same input.
        """
        if len(branches) < 2:
            return False
            
        # Check for '.' (ANY) in any branch
        for branch in branches:
            if self._contains_any(branch):
                return True
        
        # Check for overlapping first characters
        first_chars = []
        for branch in branches:
            chars = self._get_first_chars(branch)
            if chars is None:
                return True
            first_chars.append(chars)
        
        for i, chars1 in enumerate(first_chars):
            for chars2 in first_chars[i+1:]:
                if chars1 & chars2:
                    return True
        
        return False
    
    def _contains_any(self, parsed):
        """Check if pattern contains ANY (.) matcher."""
        for op, av in parsed:
            if op == ANY:
                return True
            elif op == SUBPATTERN:
                _, _, _, subpattern = av
                if self._contains_any(subpattern):
                    return True
            elif op == BRANCH:
                _, branches = av
                for branch in branches:
                    if self._contains_any(branch):
                        return True
            elif op in QUANTIFIERS:
                _, _, subpattern = av
                if self._contains_any(subpattern):
                    return True
        return False
    
    def _get_first_chars(self, parsed):
        """Get possible first characters. Returns None if could match anything."""
        if not parsed:
            return set()
            
        op, av = parsed[0]
        
        if op == LITERAL:
            return {chr(av)}
        elif op == NOT_LITERAL:
            return None
        elif op == ANY:
            return None
        elif op == IN:
            chars = set()
            for inner_op, inner_av in av:
                if inner_op == LITERAL:
                    chars.add(chr(inner_av))
                elif inner_op == RANGE:
                    for c in range(inner_av[0], inner_av[1] + 1):
                        chars.add(chr(c))
                elif inner_op == CATEGORY:
                    return None
            return chars if chars else None
        elif op == SUBPATTERN:
            _, _, _, subpattern = av
            return self._get_first_chars(subpattern)
        elif op == BRANCH:
            _, branches = av
            all_chars = set()
            for branch in branches:
                chars = self._get_first_chars(branch)
                if chars is None:
                    return None
                all_chars |= chars
            return all_chars
        elif op in QUANTIFIERS:
            min_repeat, _, subpattern = av
            if min_repeat == 0 and len(parsed) > 1:
                sub_chars = self._get_first_chars(subpattern)
                next_chars = self._get_first_chars(parsed[1:])
                if sub_chars is None or next_chars is None:
                    return None
                return sub_chars | next_chars
            return self._get_first_chars(subpattern)
        elif op == AT:
            return self._get_first_chars(parsed[1:]) if len(parsed) > 1 else set()
        
        return None


class regex_redos(Plugin):
    r"""
    🛡️ ReDoS (Regular Expression Denial of Service) Detection
    
    Detects regex patterns that can cause catastrophic backtracking,
    allowing attackers to DoS your nginx server with minimal resources.
    
    ═══════════════════════════════════════════════════════════════════
    VULNERABILITY TYPES DETECTED
    ═══════════════════════════════════════════════════════════════════
    
    1. NESTED QUANTIFIERS (Exponential - O(2^n)) 🔴 CRITICAL
       location ~ ^/(a+)+$           
       location ~ ^/((ab)*)+$        
       → Input "/aaaaaaaaaaaaaaab" tries 2^n paths
       
    2. OVERLAPPING ALTERNATIVES (Polynomial - O(n²)) 🟠 HIGH
       location ~ ^/(a|ab)+$         
       location ~ ^/(.|x)+$          
       → Alternatives match same input, causing backtracking
       
    3. ADJACENT QUANTIFIERS (Polynomial) 🟠 HIGH
       location ~ ^/.*.*end$
       → Two greedy quantifiers compete for same characters
    
    ═══════════════════════════════════════════════════════════════════
    SAFE PATTERNS
    ═══════════════════════════════════════════════════════════════════
    
       location ~ ^/[a-z]+$          # Simple character class ✓
       location ~ ^/\d{1,10}$        # Bounded quantifier ✓
       location ~ ^/(foo|bar)$       # Non-overlapping alternatives ✓
       location = /exact             # Exact match (no regex) ✓
    
    ═══════════════════════════════════════════════════════════════════
    
    Zero external dependencies - uses Python's built-in sre_parse module.
    Analysis runs in milliseconds.
    """

    summary = "Regex vulnerable to ReDoS (Regular Expression Denial of Service)"
    severity = gixy.severity.HIGH
    description = (
        "Regular expressions with nested quantifiers or overlapping alternatives "
        "can cause catastrophic backtracking, allowing attackers to consume excessive "
        "CPU resources with specially crafted requests. A single malicious request "
        "can tie up an nginx worker for minutes or longer."
    )
    help_url = "https://gixy.getpagespeed.com/en/plugins/regex_redos/"
    directives = ["location", "if", "rewrite", "server_name", "map"]

    def audit(self, directive):
        """Extract regex patterns from directive and check for ReDoS vulnerabilities."""
        
        patterns = self._extract_patterns(directive)
        
        for pattern, context in patterns:
            if not pattern:
                continue
                
            case_insensitive = self._is_case_insensitive(directive, context)
            
            analyzer = RedosAnalyzer(pattern, case_insensitive)
            vulnerabilities = analyzer.analyze()
            
            if vulnerabilities:
                vuln = vulnerabilities[0]
                severity = gixy.severity.HIGH
                if vuln.type == RedosVulnerability.EXPONENTIAL:
                    severity = gixy.severity.HIGH  # Could make CRITICAL if we had it
                
                reason = f"Regex `{pattern}` is vulnerable: {vuln}"
                self.add_issue(directive=directive, reason=reason, severity=severity)
    
    def _extract_patterns(self, directive):
        """
        Extract regex patterns from various directive types.
        Returns list of (pattern, context) tuples.
        """
        patterns = []
        
        if directive.name == "location":
            if directive.modifier in ("~", "~*"):
                patterns.append((directive.path, "location"))
                
        elif directive.name == "if":
            if directive.operand in ("~", "~*", "!~", "!~*"):
                patterns.append((directive.value, "if"))
                
        elif directive.name == "rewrite":
            if hasattr(directive, "pattern") and directive.pattern:
                patterns.append((directive.pattern, "rewrite"))
                
        elif directive.name == "server_name":
            for arg in directive.args:
                if arg.startswith("~"):
                    pattern = arg[1:]
                    if pattern.startswith("*"):
                        pattern = pattern[1:]
                    patterns.append((pattern, "server_name"))
        
        elif directive.name == "map":
            # Map blocks can have regex keys
            if hasattr(directive, "children"):
                for child in directive.children:
                    if hasattr(child, "source") and child.source:
                        src = child.source
                        if src.startswith("~"):
                            pattern = src[1:]
                            if pattern.startswith("*"):
                                pattern = pattern[1:]
                            patterns.append((pattern, "map"))
        
        return patterns
    
    def _is_case_insensitive(self, directive, context):
        """Determine if the regex is case-insensitive."""
        if directive.name == "location":
            return directive.modifier == "~*"
        elif directive.name == "if":
            return directive.operand in ("~*", "!~*")
        elif directive.name == "server_name":
            for arg in directive.args:
                if arg.startswith("~*"):
                    return True
        elif context == "map":
            return True  # Map regex keys with ~* are case insensitive
        return False
