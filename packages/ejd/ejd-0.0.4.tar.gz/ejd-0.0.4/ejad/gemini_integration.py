"""
Gemini Flash 2.5 integration for static code analysis and fixing.
"""
import os
import google.generativeai as genai
from typing import Dict, Optional

class GeminiAnalyzer:
    """Handles integration with Google Gemini Flash 2.5 for code analysis."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini analyzer.
        
        Args:
            api_key: Google API key. If None, will try to get from environment variable.
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Google API key is required. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
    def analyze_and_fix_code(self, source_code: str, rule_set_content: str, 
                           source_path: str) -> Dict[str, str]:
        """
        Analyze source code using rule set and return fixed version with markdown report.
        
        Args:
            source_code: The source code to analyze
            rule_set_content: Rules for static analysis
            source_path: Path to the source file (for context)
            
        Returns:
            Dict containing analysis results, fixed code, and markdown report
        """
        prompt = self._create_analysis_prompt(source_code, rule_set_content, source_path)
        
        try:
            print("Sending code to Gemini Flash 2.5 for analysis...")
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                result = self._parse_gemini_response(response.text)
                
                # Save markdown report to file
                report_path = self._save_markdown_report(response.text, source_path)
                result["report_path"] = report_path
                
                return result
            else:
                return {
                    "status": "error",
                    "message": "No response received from Gemini",
                    "fixed_code": source_code,
                    "issues_found": [],
                    "suggestions": []
                }
                
        except Exception as e:
            print(f"Error communicating with Gemini: {e}")
            return {
                "status": "error",
                "message": str(e),
                "fixed_code": source_code,
                "issues_found": [],
                "suggestions": []
            }
    
    def _save_markdown_report(self, markdown_content: str, source_path: str) -> str:
        """Save the markdown report to a file."""
        import os
        from datetime import datetime
        
        # Create report filename
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{base_name}_analysis_report_{timestamp}.md"
        
        # Get directory of source file
        source_dir = os.path.dirname(source_path) if os.path.dirname(source_path) else "."
        report_path = os.path.join(source_dir, report_filename)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"# Static Analysis Report for {os.path.basename(source_path)}\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Source File:** `{source_path}`\n\n")
                f.write("---\n\n")
                f.write(markdown_content)
            
            return report_path
        except Exception as e:
            print(f"Warning: Could not save markdown report: {e}")
            return ""
    
    def _create_analysis_prompt(self, source_code: str, rule_set_content: str, 
                              source_path: str) -> str:
        """Create a detailed prompt for Gemini analysis."""
        return f"""
You are an expert static code analyzer. Please analyze the following source code and apply the provided rules to identify and fix static analysis issues.

**SOURCE FILE:** {source_path}

**RULES TO APPLY:**
{rule_set_content}

**SOURCE CODE TO ANALYZE:**
```
{source_code}
```

**INSTRUCTIONS:**
1. Carefully analyze the source code against the provided rules
2. Identify all static analysis issues (code quality, security, performance, style)
3. Provide a fixed version of the code that addresses all issues
4. List each issue found with its line number and description
5. Provide suggestions for best practices

**RESPONSE FORMAT (MARKDOWN):**
Please respond in markdown format using this exact structure:

# Static Analysis Report

## Summary
Brief summary of changes made and overall assessment.

## Issues Found
| Line | Type | Description | Rule Violated |
|------|------|-------------|---------------|
| 1 | code_quality | Description of the issue | Which rule was violated |
| 2 | security | Another issue description | Rule name |

## Fixed Code
```python
The complete fixed version of the source code with all issues resolved
```

## Additional Suggestions
- Additional best practice suggestion 1
- Additional best practice suggestion 2
- Additional best practice suggestion 3

---
*Analysis completed successfully*
"""

    def _parse_gemini_response(self, response_text: str) -> Dict[str, str]:
        """Parse Gemini's markdown response and extract structured data."""
        try:
            result = {
                "status": "success",
                "markdown_response": response_text,
                "issues_found": [],
                "fixed_code": "",
                "suggestions": [],
                "summary": ""
            }
            
            # Extract summary
            summary_match = self._extract_section(response_text, "## Summary", "##")
            if summary_match:
                result["summary"] = summary_match.strip()
            
            # Extract fixed code from code block
            code_start = response_text.find("```python")
            if code_start != -1:
                code_start += len("```python")
                code_end = response_text.find("```", code_start)
                if code_end != -1:
                    result["fixed_code"] = response_text[code_start:code_end].strip()
            
            # Extract issues from table
            issues = self._parse_issues_table(response_text)
            result["issues_found"] = issues
            
            # Extract suggestions
            suggestions = self._extract_suggestions(response_text)
            result["suggestions"] = suggestions
            
            return result
            
        except Exception as e:
            print(f"Warning: Could not parse Gemini markdown response: {e}")
            # Return a fallback response with the raw text
            return {
                "status": "partial_success",
                "message": f"Response received but parsing failed: {e}",
                "markdown_response": response_text,
                "raw_response": response_text,
                "fixed_code": "",
                "issues_found": [],
                "suggestions": ["Review the markdown response for analysis results"]
            }
    
    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extract content between markdown section headers."""
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""
        
        start_idx += len(start_marker)
        end_idx = text.find(end_marker, start_idx)
        if end_idx == -1:
            return text[start_idx:].strip()
        
        return text[start_idx:end_idx].strip()
    
    def _parse_issues_table(self, text: str) -> list:
        """Parse the issues table from markdown."""
        issues = []
        
        # Find the table section
        table_start = text.find("| Line | Type | Description | Rule Violated |")
        if table_start == -1:
            return issues
        
        # Skip header and separator lines
        lines = text[table_start:].split('\n')[2:]  # Skip header and separator
        
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('|') or line.startswith('##'):
                break
                
            parts = [part.strip() for part in line.split('|')[1:-1]]  # Remove empty first/last
            if len(parts) >= 4:
                try:
                    issues.append({
                        "line": int(parts[0]) if parts[0].isdigit() else parts[0],
                        "type": parts[1],
                        "description": parts[2],
                        "rule": parts[3]
                    })
                except (ValueError, IndexError):
                    continue
                    
        return issues
    
    def _extract_suggestions(self, text: str) -> list:
        """Extract suggestions from markdown list."""
        suggestions = []
        
        # Find the suggestions section
        suggestions_start = text.find("## Additional Suggestions")
        if suggestions_start == -1:
            return suggestions
        
        # Extract the section
        section_text = text[suggestions_start:]
        next_section = section_text.find("##", 1)  # Find next section
        if next_section != -1:
            section_text = section_text[:next_section]
        
        # Parse bullet points
        lines = section_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('- '):
                suggestions.append(line[2:].strip())
        
        return suggestions
    
    def test_connection(self) -> bool:
        """Test if the connection to Gemini is working."""
        try:
            test_response = self.model.generate_content("Hello, respond with 'Connection successful'")
            return "successful" in test_response.text.lower()
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False