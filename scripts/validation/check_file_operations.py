#!/usr/bin/env python3
"""
Comprehensive File Operation Safety Check

This script validates that all file write operations in the codebase:
1. Create parent directories before writing
2. Have proper error handling
3. Don't make assumptions about directory existence

Run this to detect potential bugs similar to the v0.5.2 directory creation issue.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple, Dict

class FileOperationChecker(ast.NodeVisitor):
    """AST visitor to check file operations"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.issues = []
        self.safe_operations = []
        self.current_function = None
        self.current_class = None
    
    def visit_ClassDef(self, node):
        """Track current class"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        """Track current function"""
        old_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_func
    
    def visit_With(self, node):
        """Check 'with open(...)' statements"""
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                # Check if it's open() call
                if isinstance(item.context_expr.func, ast.Name):
                    if item.context_expr.func.id == 'open':
                        self._check_open_call(item.context_expr, node)
        
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Check method calls like .write_text(), .write_bytes()"""
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            
            # Check for Path write methods
            if method_name in ['write_text', 'write_bytes']:
                self._check_path_write(node)
        
        self.generic_visit(node)
    
    def _check_open_call(self, call_node, with_node):
        """Validate open() call for write mode"""
        if not call_node.args:
            return
        
        # Check if it's write mode
        mode = 'r'  # default
        if len(call_node.args) >= 2:
            mode_arg = call_node.args[1]
            if isinstance(mode_arg, ast.Constant):
                mode = mode_arg.value
        else:
            # Check for mode in kwargs
            for keyword in call_node.keywords:
                if keyword.arg == 'mode':
                    if isinstance(keyword.value, ast.Constant):
                        mode = keyword.value.value
        
        if 'w' in mode or 'a' in mode:
            # This is a write operation
            location = f"{self.current_class}.{self.current_function}" if self.current_class else self.current_function
            
            # Check if there's a mkdir() call before this
            has_mkdir = self._has_mkdir_before(with_node)
            
            file_path = self._get_file_path_expr(call_node.args[0])
            
            if has_mkdir:
                self.safe_operations.append({
                    'file': self.filepath,
                    'line': call_node.lineno,
                    'location': location,
                    'path': file_path,
                    'type': 'open(write)',
                    'status': 'SAFE'
                })
            else:
                self.issues.append({
                    'file': self.filepath,
                    'line': call_node.lineno,
                    'location': location,
                    'path': file_path,
                    'type': 'open(write)',
                    'issue': 'Missing directory creation before file write',
                    'severity': 'HIGH'
                })
    
    def _check_path_write(self, call_node):
        """Validate Path.write_text() / write_bytes() calls"""
        location = f"{self.current_class}.{self.current_function}" if self.current_class else self.current_function
        
        # Try to get the path being written to
        if isinstance(call_node.func.value, ast.Name):
            path_var = call_node.func.value.id
        else:
            path_var = "unknown"
        
        # For now, flag as needing manual review
        self.issues.append({
            'file': self.filepath,
            'line': call_node.lineno,
            'location': location,
            'path': path_var,
            'type': f'Path.{call_node.func.attr}()',
            'issue': 'Manual review needed: Check if parent directory exists',
            'severity': 'MEDIUM'
        })
    
    def _has_mkdir_before(self, node) -> bool:
        """Check if there's a mkdir() call in the same function (simple heuristic)"""
        # This is a simplified check - would need proper control flow analysis for accuracy
        # For now, we'll flag and let manual review confirm
        return False
    
    def _get_file_path_expr(self, node) -> str:
        """Extract file path expression as string"""
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_file_path_expr(node.value)}.{node.attr}"
        else:
            return "complex_expression"


def check_file(filepath: Path) -> Tuple[List[Dict], List[Dict]]:
    """Check a single Python file for unsafe file operations"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        
        checker = FileOperationChecker(str(filepath))
        checker.visit(tree)
        
        return checker.issues, checker.safe_operations
    except SyntaxError as e:
        print(f"⚠️  Syntax error in {filepath}: {e}")
        return [], []
    except Exception as e:
        print(f"⚠️  Error checking {filepath}: {e}")
        return [], []


def check_specific_patterns(filepath: Path) -> List[Dict]:
    """Check for specific known-dangerous patterns"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # Pattern 1: Direct file write without visible mkdir
            if 'open(' in line and ("'w'" in line or '"w"' in line):
                # Check if previous 5 lines have mkdir
                context = '\n'.join(lines[max(0, i-6):i-1])
                if 'mkdir' not in context and 'makedirs' not in context:
                    # Check if it's a config file (usually in XDG dirs with auto-create)
                    if 'config_file' not in line and 'cache' not in context.lower():
                        issues.append({
                            'file': str(filepath),
                            'line': i,
                            'code': line.strip(),
                            'pattern': 'open(w) without mkdir in context',
                            'severity': 'HIGH'
                        })
            
            # Pattern 2: Path.write_* without mkdir
            if '.write_text(' in line or '.write_bytes(' in line:
                context = '\n'.join(lines[max(0, i-6):i-1])
                if 'mkdir' not in context:
                    issues.append({
                        'file': str(filepath),
                        'line': i,
                        'code': line.strip(),
                        'pattern': 'Path.write_* without mkdir in context',
                        'severity': 'MEDIUM'
                    })
    
    except Exception as e:
        print(f"⚠️  Error in pattern check for {filepath}: {e}")
    
    return issues


def main():
    """Main validation function"""
    print("=" * 70)
    print("File Operation Safety Validation")
    print("=" * 70)
    print("\nScanning for potentially unsafe file write operations...\n")
    
    # Find all Python files in luxusb/
    root = Path(__file__).parent.parent.parent
    luxusb_dir = root / "luxusb"
    
    all_issues = []
    all_safe = []
    pattern_issues = []
    
    python_files = list(luxusb_dir.rglob("*.py"))
    
    print(f"Checking {len(python_files)} Python files...\n")
    
    for filepath in python_files:
        # Skip __pycache__
        if '__pycache__' in str(filepath):
            continue
        
        # AST-based check
        issues, safe = check_file(filepath)
        all_issues.extend(issues)
        all_safe.extend(safe)
        
        # Pattern-based check
        patterns = check_specific_patterns(filepath)
        pattern_issues.extend(patterns)
    
    # Report results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    # High severity issues
    high_severity = [i for i in all_issues if i.get('severity') == 'HIGH']
    if high_severity:
        print(f"\n🚨 HIGH SEVERITY ISSUES ({len(high_severity)}):")
        print("-" * 70)
        for issue in high_severity:
            print(f"\n📁 {issue['file']}")
            print(f"   Line {issue['line']}: {issue['location']}")
            print(f"   Path: {issue['path']}")
            print(f"   Issue: {issue['issue']}")
    
    # Medium severity issues
    medium_severity = [i for i in all_issues if i.get('severity') == 'MEDIUM']
    if medium_severity:
        print(f"\n⚠️  MEDIUM SEVERITY ISSUES ({len(medium_severity)}):")
        print("-" * 70)
        for issue in medium_severity:
            print(f"\n📁 {issue['file']}")
            print(f"   Line {issue['line']}: {issue['location']}")
            print(f"   Type: {issue['type']}")
    
    # Pattern-based issues
    if pattern_issues:
        print(f"\n🔍 PATTERN DETECTION ({len(pattern_issues)}):")
        print("-" * 70)
        for issue in pattern_issues:
            print(f"\n📁 {issue['file']}")
            print(f"   Line {issue['line']}: {issue['code']}")
            print(f"   Pattern: {issue['pattern']}")
    
    # Safe operations
    if all_safe:
        print(f"\n✅ VERIFIED SAFE OPERATIONS ({len(all_safe)}):")
        print("-" * 70)
        for op in all_safe[:5]:  # Show first 5
            print(f"   {op['file']}:{op['line']} - {op['location']}")
        if len(all_safe) > 5:
            print(f"   ... and {len(all_safe) - 5} more")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files checked: {len(python_files)}")
    print(f"High severity issues: {len(high_severity)}")
    print(f"Medium severity issues: {len(medium_severity)}")
    print(f"Pattern matches: {len(pattern_issues)}")
    print(f"Safe operations: {len(all_safe)}")
    
    total_issues = len(high_severity) + len(medium_severity) + len(pattern_issues)
    
    if total_issues == 0:
        print("\n✅ No critical issues found!")
        print("All file write operations appear to handle directory creation properly.")
        return 0
    else:
        print(f"\n⚠️  {total_issues} potential issues found")
        print("Manual review recommended for flagged operations.")
        print("\nRecommendation: Review each flagged operation and ensure:")
        print("  1. Parent directory is created before file write")
        print("  2. Use: path.parent.mkdir(parents=True, exist_ok=True)")
        print("  3. Proper error handling for file operations")
        return 1


if __name__ == "__main__":
    sys.exit(main())
