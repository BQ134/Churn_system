#!/usr/bin/env python3
import re
import sys

def validate_html_file(filename):
    """Validate HTML file and identify issues"""
    issues = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        issues.append(f"File read error: {e}")
        return issues
    
    # 1. Check for basic HTML structure
    if not re.search(r'<!DOCTYPE html>', content, re.IGNORECASE):
        issues.append("Missing DOCTYPE declaration")
    
    if not re.search(r'<html[^>]*>', content, re.IGNORECASE):
        issues.append("Missing <html> tag")
    
    if not re.search(r'</html>', content, re.IGNORECASE):
        issues.append("Missing </html> tag")
    
    if not re.search(r'<head[^>]*>', content, re.IGNORECASE):
        issues.append("Missing <head> tag")
    
    if not re.search(r'</head>', content, re.IGNORECASE):
        issues.append("Missing </head> tag")
    
    if not re.search(r'<body[^>]*>', content, re.IGNORECASE):
        issues.append("Missing <body> tag")
    
    if not re.search(r'</body>', content, re.IGNORECASE):
        issues.append("Missing </body> tag")
    
    # 2. Check for unclosed tags
    for i, line in enumerate(lines, 1):
        # Check for unclosed script tags
        if '<script>' in line and '</script>' not in line:
            # Look ahead for closing tag
            found_closing = False
            for j in range(i, min(i + 50, len(lines))):
                if '</script>' in lines[j-1]:
                    found_closing = True
                    break
            if not found_closing:
                issues.append(f"Line {i}: Unclosed <script> tag")
        
        # Check for unclosed style tags
        if '<style>' in line and '</style>' not in line:
            found_closing = False
            for j in range(i, min(i + 50, len(lines))):
                if '</style>' in lines[j-1]:
                    found_closing = True
                    break
            if not found_closing:
                issues.append(f"Line {i}: Unclosed <style> tag")
    
    # 3. Check for JavaScript syntax issues
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, content, re.DOTALL | re.IGNORECASE)
    
    for i, script in enumerate(scripts):
        # Check for missing braces
        brace_count = script.count('{') - script.count('}')
        if brace_count != 0:
            issues.append(f"Script {i+1}: Unmatched braces (difference: {brace_count})")
        
        # Check for missing parentheses
        paren_count = script.count('(') - script.count(')')
        if paren_count != 0:
            issues.append(f"Script {i+1}: Unmatched parentheses (difference: {paren_count})")
        
        # Check for missing brackets
        bracket_count = script.count('[') - script.count(']')
        if bracket_count != 0:
            issues.append(f"Script {i+1}: Unmatched brackets (difference: {bracket_count})")
        
        # Check for missing quotes
        single_quotes = script.count("'") % 2
        double_quotes = script.count('"') % 2
        if single_quotes != 0:
            issues.append(f"Script {i+1}: Unmatched single quotes")
        if double_quotes != 0:
            issues.append(f"Script {i+1}: Unmatched double quotes")
    
    # 4. Check for specific DataTable issues
    if 'DataTable({' in content:
        # Look for the specific missing brace issue
        for i, line in enumerate(lines):
            if 'DataTable({' in line:
                # Check if the next few lines have proper structure
                brace_count = 0
                for j in range(i, min(i + 30, len(lines))):
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    if '});' in lines[j] and brace_count != 0:
                        issues.append(f"Line {i+1}: DataTable initialization has brace mismatch")
                        break
    
    # 5. Check for template syntax issues
    jinja_patterns = [
        r'{%[^%]*%}',  # Jinja2 blocks
        r'{{[^}]*}}',  # Jinja2 expressions
    ]
    
    for pattern in jinja_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            # Check for unclosed Jinja2 blocks
            if match.startswith('{%') and not match.endswith('%}'):
                issues.append(f"Unclosed Jinja2 block: {match}")
            elif match.startswith('{{') and not match.endswith('}}'):
                issues.append(f"Unclosed Jinja2 expression: {match}")
    
    # 6. Check for accessibility issues
    for i, line in enumerate(lines, 1):
        # Check for missing alt attributes on images
        if '<img' in line and 'alt=' not in line:
            issues.append(f"Line {i}: Image missing alt attribute")
        
        # Check for missing labels on form elements
        if '<input' in line and 'id=' in line:
            input_id = re.search(r'id=["\']([^"\']+)["\']', line)
            if input_id:
                id_value = input_id.group(1)
                # Look for corresponding label
                label_found = False
                for j in range(max(0, i-10), min(len(lines), i+10)):
                    if f'for="{id_value}"' in lines[j] or f"for='{id_value}'" in lines[j]:
                        label_found = True
                        break
                if not label_found:
                    issues.append(f"Line {i}: Input with id '{id_value}' missing corresponding label")
    
    # 7. Check for CSS issues
    style_pattern = r'<style[^>]*>(.*?)</style>'
    styles = re.findall(style_pattern, content, re.DOTALL | re.IGNORECASE)
    
    for i, style in enumerate(styles):
        # Check for unclosed CSS rules
        brace_count = style.count('{') - style.count('}')
        if brace_count != 0:
            issues.append(f"Style {i+1}: Unmatched CSS braces (difference: {brace_count})")
    
    # 8. Check for missing required attributes
    for i, line in enumerate(lines, 1):
        if '<input' in line and 'type=' not in line:
            issues.append(f"Line {i}: Input element missing type attribute")
        
        if '<a' in line and 'href=' not in line:
            issues.append(f"Line {i}: Anchor tag missing href attribute")
    
    # 9. Check for deprecated HTML elements
    deprecated_elements = ['<center>', '<font>', '<strike>', '<u>']
    for i, line in enumerate(lines, 1):
        for elem in deprecated_elements:
            if elem in line:
                issues.append(f"Line {i}: Deprecated HTML element {elem}")
    
    # 10. Check for potential XSS vulnerabilities
    for i, line in enumerate(lines, 1):
        if 'innerHTML' in line and '{{' in line:
            issues.append(f"Line {i}: Potential XSS vulnerability - innerHTML with template variables")
    
    return issues

if __name__ == "__main__":
    filename = "templates/reports.html"
    issues = validate_html_file(filename)
    
    if issues:
        print(f"Found {len(issues)} issues in {filename}:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
    else:
        print(f"No issues found in {filename}") 