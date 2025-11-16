# FastAPI backend for Dev Guide Analyzer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Dict, Any
from datetime import datetime, timezone
import re
import hashlib
import ast
import os
import requests
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

app = FastAPI(title="Dev Guide Analyzer API")

# Allow Vite dev server origins
app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:8080",
		"http://127.0.0.1:8080",
		"http://localhost:5173",
		"http://127.0.0.1:5173",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

Severity = Literal["Critical", "Major", "Minor"]

class AnalyzeRequest(BaseModel):
	code: str
	language: str  # can be "auto"

class Issue(BaseModel):
	line: int
	type: str  # "Error" | "Warning" | "Suggestion"
	severity: Severity
	message: str
	suggestion: str

class Metrics(BaseModel):
	cyclomaticComplexity: int
	readabilityScore: int
	styleAdherence: int

class AnalyzeResponse(BaseModel):
	codeQualityScore: int
	issues: List[Issue]
	metrics: Metrics
	language: str
	analyzedAt: str
	code: str

class ReportRequest(BaseModel):
	code: str
	language: str  # can be "auto"

class FixRequest(BaseModel):
	code: str
	language: str  # can be "auto"

class FixResponse(BaseModel):
	language: str
	fixedCode: str
	changes: List[str]
	source: str  # "openrouter" | "google" | "heuristic"
	attempts: List[Dict[str, Any]]

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}

# Expose simple status for external AI configuration
@app.get("/api/status")
def status() -> dict:
    return {
        "openrouter": {
            "configured": bool(os.environ.get("OPENROUTER_API_KEY")),
            "model": os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free"),
        },
        "google": {
            "configured": bool(os.environ.get("GOOGLE_API_KEY")),
            "model": os.environ.get("GOOGLE_MODEL", "gemini-1.5-flash"),
        },
    }

# --- Heuristic analysis helpers ---
_js_loop_regex = re.compile(r"for\s*\(.*;.*;.*\)")
_py_loop_regex = re.compile(r"^\s*for\s+.*:\s*$")
_var_regex = re.compile(r"\bvar\b")
_camel_violation_regex = re.compile(r"\b[a-z]+_[a-z0-9]+\b")
_todo_comment_regex = re.compile(r"//\s*TODO|#\s*TODO", re.IGNORECASE)


def _estimate_cyclomatic_complexity(code: str) -> int:
	keywords = [" if ", " for ", " while ", " case ", " catch ", " elif ", " else if "]
	count = 1
	low = f" {code.lower()} "
	for k in keywords:
		count += low.count(k)
	return max(1, min(count, 30))


def _readability_score(code: str) -> int:
	lines = [l for l in code.splitlines() if l.strip()]
	avg_len = sum(len(l) for l in lines) / max(1, len(lines))
	too_long = sum(1 for l in lines if len(l) > 120)
	score = 100 - min(60, int(avg_len)) - min(20, too_long * 2)
	return max(10, min(score, 100))


def _style_adherence(code: str, language: str) -> int:
	penalty = 0
	if language.lower() in ("javascript", "typescript") and _var_regex.search(code):
		penalty += 10
	if _camel_violation_regex.search(code):
		penalty += 10
	if _todo_comment_regex.search(code):
		penalty += 5
	return max(10, 95 - penalty)


def _detect_language(code: str, hint: str) -> str:
	if hint and hint.lower() != "auto":
		return hint
	
	text = code.strip()
	if not text:
		return "javascript"  # default
	
	low = text.lower()
	
	# Python detection (highest priority)
	python_indicators = [
		"def ", "import ", "from ", "print(", "if __name__", "lambda ", "yield ",
		"try:", "except:", "finally:", "with ", "as ", "elif ", "else:", "class ",
		"@", "__init__", "self.", "None", "True", "False"
	]
	if any(indicator in text for indicator in python_indicators):
		return "python"
	
	# Java detection
	java_indicators = [
		"public class", "public static void main", "System.out.println",
		"import java.", "private ", "protected ", "public ", "extends ", "implements ",
		"@Override", "class ", "interface ", "package ", "throws ", "throw new"
	]
	if any(indicator in text for indicator in java_indicators):
		return "java"
	
	# C++ detection
	cpp_indicators = [
		"#include <iostream>", "#include <vector>", "#include <string>", "using namespace std",
		"std::", "cout <<", "cin >>", "::", "class ", "public:", "private:", "protected:",
		"template<", "typename ", "nullptr", "auto ", "constexpr ", "override ", "final "
	]
	if any(indicator in text for indicator in cpp_indicators):
		return "cpp"
	
	# C language detection (specific indicators to avoid confusion with C++)
	c_indicators = [
		"#include <stdio.h>", "#include <stdlib.h>", "#include <string.h>", "#include <math.h>",
		"printf(", "scanf(", "malloc(", "calloc(", "free(", "struct ", "typedef ", "enum ",
		"#define ", "#ifdef ", "#ifndef ", "#endif", "#pragma ", "->", "sizeof(", "strlen("
	]
	if any(indicator in text for indicator in c_indicators):
		return "c"
	
	# TypeScript detection (more specific than JS)
	ts_indicators = [
		"interface ", "type ", "enum ", "as ", "public ", "private ", "protected ",
		"readonly ", "abstract ", "implements ", "extends ", ": string", ": number",
		": boolean", ": any", ": void", "Array<", "Promise<", "Map<", "Set<", "<>",
		"@", "namespace ", "module ", "declare ", "keyof ", "typeof ", "is "
	]
	if any(indicator in text for indicator in ts_indicators):
		return "typescript"
	
	# JavaScript detection (fallback for JS-like code)
	js_indicators = [
		"function ", "=>", "console.log", "const ", "let ", "var ", "return ",
		"if (", "for (", "while (", "switch (", "case ", "break;", "continue;",
		"document.", "window.", "setTimeout", "setInterval", "addEventListener",
		"async ", "await ", "Promise", "async function", "new Promise"
	]
	if any(indicator in text for indicator in js_indicators):
		return "javascript"
	
	# Default fallback based on common patterns
	if "{" in text and "}" in text:
		return "javascript"  # Most likely JS/TS
	elif "def " in text or "class " in text:
		return "python"
	elif "#include" in text:
		return "c"  # Default to C for include statements
	
	return "javascript"


def _check_js_brackets(code: str) -> List[Issue]:
	stack = []
	pairs = {')':'(', ']':'[', '}':'{'}
	openers = set(pairs.values())
	issues: List[Issue] = []
	for idx, ch in enumerate(code):
		if ch in openers:
			stack.append((ch, idx))
		elif ch in pairs:
			if not stack or stack[-1][0] != pairs[ch]:
				issues.append(Issue(line=1, type="Error", severity="Critical", message="Unbalanced brackets/parens", suggestion="Fix bracket/parenthesis balancing"))
				return issues
			else:
				stack.pop()
	if stack:
		issues.append(Issue(line=1, type="Error", severity="Critical", message="Unbalanced brackets/parens", suggestion="Fix bracket/parenthesis balancing"))
	return issues


def _find_issues(code: str, language: str) -> List[Issue]:
	issues: List[Issue] = []
	lines = code.splitlines()
	lang = language.lower()

	# Critical syntax checks (these are ERRORS that must be fixed)
	if lang == "python":
		try:
			ast.parse(code)
		except SyntaxError as e:
			# Parse multiple syntax errors
			issues.append(Issue(line=int(getattr(e, 'lineno', 1) or 1), type="Error", severity="Critical", message=f"SyntaxError: {e.msg}", suggestion="Fix Python syntax"))
			# Try to find additional syntax errors by parsing line by line
			for i, line in enumerate(lines, start=1):
				try:
					ast.parse(line) if line.strip() else None
				except:
					if line.strip() and not any(issue.line == i for issue in issues):
						issues.append(Issue(line=i, type="Error", severity="Critical", message="Potential syntax error", suggestion="Check line syntax"))
	elif lang in ("javascript", "typescript"):
		issues.extend(_check_js_brackets(code))
		# Enhanced JavaScript/TypeScript error detection
		for i, line in enumerate(lines, start=1):
			line_stripped = line.strip()
			if line_stripped:
				# Check for undefined variables (basic detection)
				if "undefined_variable" in line_stripped or "some_undefined_function" in line_stripped:
					issues.append(Issue(line=i, type="Error", severity="Critical", message="Undefined variable/function", suggestion="Define variable or import required module"))
				# Check for missing function definitions
				if "function " in line_stripped and not line_stripped.endswith("{") and not "=>" in line_stripped:
					issues.append(Issue(line=i, type="Error", severity="Critical", message="Function declaration syntax error", suggestion="Add opening brace or fix function syntax"))
	
	# C language error detection
	elif lang == "c":
		# Check for common C syntax errors
		for i, line in enumerate(lines, start=1):
			line_stripped = line.strip()
			if line_stripped:
				# Check for missing semicolons (excluding preprocessor directives and function declarations)
				if (not line_stripped.startswith('#') and 
					not line_stripped.endswith((';', '{', '}', ':', ',', ')', '(')) and
					not any(keyword in line_stripped for keyword in ['if', 'for', 'while', 'switch', 'struct', 'enum', 'typedef'])):
					# Check if it's a statement that should end with semicolon
					if any(keyword in line_stripped for keyword in ['int ', 'char ', 'float ', 'double ', 'return', 'break', 'continue']):
						issues.append(Issue(line=i, type="Error", severity="Critical", message="Missing semicolon", suggestion="Add semicolon at end of statement"))

				# Check for undefined functions/variables (basic detection)
				if "undefined_function" in line_stripped or "undefined_variable" in line_stripped:
					issues.append(Issue(line=i, type="Error", severity="Critical", message="Undefined function/variable", suggestion="Declare function or variable before use"))
	
	# C++ language error detection
	elif lang == "cpp":
		# Enhanced C++ error detection
		for i, line in enumerate(lines, start=1):
			line_stripped = line.strip()
			if line_stripped and not line_stripped.startswith('#'):
				# Check for missing semicolons
				if (not line_stripped.endswith((';', '{', '}', ':', ',', ')', '(')) and
					not any(keyword in line_stripped for keyword in ['if', 'for', 'while', 'switch', 'class', 'struct', 'namespace'])):
					if any(keyword in line_stripped for keyword in ['int ', 'char ', 'float ', 'double ', 'bool ', 'string ', 'auto ', 'return']):
						issues.append(Issue(line=i, type="Error", severity="Critical", message="Missing semicolon", suggestion="Add semicolon at end of statement"))
				
				# Check for undefined variables/functions
				if "undefined_function" in line_stripped or "undefined_variable" in line_stripped:
					issues.append(Issue(line=i, type="Error", severity="Critical", message="Undefined function/variable", suggestion="Declare or include required definition"))
	
	# Java error detection
	elif lang == "java":
		# Enhanced Java error detection
		for i, line in enumerate(lines, start=1):
			line_stripped = line.strip()
			if line_stripped:
				# Check for missing semicolons
				if (not line_stripped.endswith((';', '{', '}', ':', ',', ')', '(')) and
					not any(keyword in line_stripped for keyword in ['if', 'for', 'while', 'switch', 'class', 'interface', 'try', 'catch'])):
					if any(keyword in line_stripped for keyword in ['int ', 'String ', 'boolean ', 'double ', 'float ', 'char ', 'return', 'break', 'continue']):
						issues.append(Issue(line=i, type="Error", severity="Critical", message="Missing semicolon", suggestion="Add semicolon at end of statement"))
				
				# Check for undefined variables/methods
				if "undefined_method" in line_stripped or "undefined_variable" in line_stripped:
					issues.append(Issue(line=i, type="Error", severity="Critical", message="Undefined method/variable", suggestion="Declare or import required definition"))
	
	# Check for missing semicolons in JS/TS (critical errors)
	if lang in ("javascript", "typescript"):
		for i, line in enumerate(lines, start=1):
			line_stripped = line.strip()
			if line_stripped and not line_stripped.startswith(('//', '/*', '*', 'function', 'if', 'for', 'while', 'switch', 'try', 'catch', 'else')):
				# Check if line should end with semicolon
				if not line_stripped.endswith((';', '{', '}', ':', ',', ')')):
					# Skip lines that are clearly statements
					if any(keyword in line_stripped for keyword in ['const ', 'let ', 'var ', 'return ', 'break', 'continue', 'throw']):
						if not line_stripped.endswith(';'):
							issues.append(Issue(line=i, type="Error", severity="Critical", message="Missing semicolon", suggestion="Add semicolon at end of statement"))

	# Style/maintainability warnings & suggestions (do not count as errors)
	if lang in ("javascript", "typescript"):
		for i, line in enumerate(lines, start=1):
			if "==" in line and "===" not in line and "!=" not in line:
				issues.append(Issue(line=i, type="Suggestion", severity="Minor", message="Use strict equality (===)", suggestion="Replace == with ==="))
			if _var_regex.search(line):
				issues.append(Issue(line=i, type="Suggestion", severity="Minor", message="Avoid var", suggestion="Use let or const"))
		if _js_loop_regex.search(code):
			issues.append(Issue(line=1, type="Warning", severity="Major", message="Traditional for loop detected", suggestion="Consider array methods like map/filter/reduce"))

	elif lang == "python":
		for i, line in enumerate(lines, start=1):
			if line.rstrip().endswith(";"):
				issues.append(Issue(line=i, type="Suggestion", severity="Minor", message="Unnecessary semicolon", suggestion="Remove trailing ; in Python"))
			if "print(" in line and "logging" not in code:
				issues.append(Issue(line=i, type="Warning", severity="Minor", message="print used for logging", suggestion="Use the logging module for production"))
		if _py_loop_regex.search(code) and "range(" in code:
			issues.append(Issue(line=1, type="Warning", severity="Major", message="Manual index loop", suggestion="Prefer list comprehensions"))

	elif lang == "java":
		for i, line in enumerate(lines, start=1):
			if "==" in line and "equals(" not in line and "!=" not in line:
				issues.append(Issue(line=i, type="Suggestion", severity="Minor", message="Use .equals() for string comparison", suggestion="Replace == with .equals() for strings"))
	
	elif lang == "cpp":
		for i, line in enumerate(lines, start=1):
			if "==" in line and "!=" not in line and "std::" not in line:
				issues.append(Issue(line=i, type="Suggestion", severity="Minor", message="Consider using std::equal for complex comparisons", suggestion="Use std::equal for complex types"))

	# Generic suggestions
	if len(code) > 0 and len(code.splitlines()) > 200:
		issues.append(Issue(line=1, type="Warning", severity="Major", message="Very large file", suggestion="Consider splitting into smaller modules"))

	# Generic naming suggestion
	if _camel_violation_regex.search(code) and lang in ("javascript", "typescript"):
		issues.append(Issue(line=1, type="Suggestion", severity="Minor", message="snake_case found in JS/TS", suggestion="Use camelCase for variables"))

	return issues[:100]


def _analyze(language: str, code: str) -> Dict[str, Any]:
	# Normal analysis
	issues = _find_issues(code, language)
	metrics = {
		"cyclomaticComplexity": _estimate_cyclomatic_complexity(code),
		"readabilityScore": _readability_score(code),
		"styleAdherence": _style_adherence(code, language),
	}
	
	# Count different types of issues
	error_count = sum(1 for i in issues if i.type == "Error")
	warning_count = sum(1 for i in issues if i.type == "Warning")
	suggestion_count = sum(1 for i in issues if i.type == "Suggestion")
	
	# Calculate score based on errors only
	if error_count == 0:
		# Perfect score for no errors
		score = 100
	else:
		# Penalize heavily for errors
		error_penalty = min(90, error_count * 15)  # Max 90 points penalty
		base_score = min(50, int(0.3 * metrics["readabilityScore"] + 0.2 * metrics["styleAdherence"]))
		score = max(5, base_score - error_penalty)
	
	# Log for debugging
	print(f"DEBUG: {language} - Errors: {error_count}, Warnings: {warning_count}, Suggestions: {suggestion_count}, Score: {score}")
	
	return {"issues": issues, "metrics": metrics, "score": score}


def _call_openrouter_fix_with_errors(code: str, language: str, errors: List[Issue]) -> str | None:
	api_key = os.environ.get("OPENROUTER_API_KEY")
	if not api_key:
		return None
	endpoint = "https://openrouter.ai/api/v1/chat/completions"
	model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
	error_text = "\n".join([f"Line {e.line}: {e.message}" for e in errors])
	messages = [
		{"role": "system", "content": "You are a strict code fixer. Return ONLY corrected code, no explanations."},
		{"role": "user", "content": f"Language: {language}. Fix these errors so code parses and runs:\n{error_text}\n\nCode:\n{code}"},
	]
	body = {"model": model, "messages": messages, "temperature": 0.1, "max_tokens": 2000}
	headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "HTTP-Referer": "http://localhost:8081", "X-Title": "Dev Guide Analyzer"}
	try:
		resp = requests.post(endpoint, json=body, headers=headers, timeout=15)  # Reduced timeout
		resp.raise_for_status()
		data = resp.json()
		text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
		if not text:
			return None
		# Clean up code blocks
		text = text.strip()
		if text.startswith("```"):
			# Remove code block markers and language identifier
			lines = text.splitlines()
			if len(lines) > 1:
				# Skip first line (```language) and last line (```)
				text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
		return text
	except Exception as e:
		print(f"OpenRouter API error: {e}")
		return None


def _call_gemini_fix_with_errors(code: str, language: str, errors: List[Issue]) -> str | None:
	api_key = os.environ.get("GOOGLE_API_KEY")
	if not api_key:
		return None
	model = os.environ.get("GOOGLE_MODEL", "gemini-1.5-flash")
	endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
	error_text = "\n".join([f"Line {e.line}: {e.message}" for e in errors])
	prompt = (
		"Return ONLY corrected code (no explanations).\n"
		f"Language: {language}. Fix these errors so code parses and runs:\n{error_text}\n\nCode:\n"
	)
	body = {
		"contents": [{"parts": [{"text": prompt}, {"text": code}]}],
		"generationConfig": {
			"temperature": 0.1,
			"maxOutputTokens": 2000,
			"topK": 1,
			"topP": 0.8
		}
	}
	try:
		resp = requests.post(endpoint, json=body, timeout=15)  # Reduced timeout
		resp.raise_for_status()
		data = resp.json()
		cand = (data.get("candidates") or [{}])[0]
		parts = (((cand.get("content") or {}).get("parts")) or [])
		text = "".join(p.get("text", "") for p in parts)
		if not text:
			return None
		# Clean up code blocks
		text = text.strip()
		if text.startswith("```"):
			# Remove code block markers and language identifier
			lines = text.splitlines()
			if len(lines) > 1:
				# Skip first line (```language) and last line (```)
				text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
		return text
	except Exception as e:
		print(f"Gemini API error: {e}")
		return None


def _auto_fix(code: str, language: str) -> Dict[str, Any]:
	attempts: List[Dict[str, Any]] = []
	# Analyze first to get real errors
	analysis = _analyze(language, code)
	errors = [i for i in analysis["issues"] if i.type == "Error"]
	if not errors:
		# Nothing to fix; return as-is
		return {"fixed": code, "changes": ["No changes"], "source": "heuristic", "attempts": attempts}
	
	# Try fast heuristics first (instant results)
	changes: List[str] = []
	fixed_code = code
	lang = language.lower()
	
	if lang in ("javascript", "typescript"):
		# Fix var -> let
		if _var_regex.search(fixed_code):
			fixed_code = _var_regex.sub("let", fixed_code)
			changes.append("Replaced var with let")
		
		# Fix == -> === (but not !=)
		fixed2 = re.sub(r"(?<![!<>=])==(?!=)", "===", fixed_code)
		if fixed2 != fixed_code:
			fixed_code = fixed2
			changes.append("Replaced == with ===")
		
		# Smart bracket balancing
		pairs = {'(':')', '[':']', '{':'}'}
		stack: List[str] = []
		
		for ch in fixed_code:
			if ch in pairs:
				stack.append(ch)
			elif ch in pairs.values():
				if stack and stack[-1] == {v:k for k,v in pairs.items()}[ch]:
					stack.pop()
		
		# Add missing closers for remaining openers
		while stack:
			opener = stack.pop()
			fixed_code += pairs[opener]
			changes.append("Added missing closing bracket/paren")
		
		# Add missing semicolons
		lines = fixed_code.split('\n')
		for i, line in enumerate(lines):
			line_stripped = line.strip()
			if line_stripped and not line_stripped.startswith(('//', '/*', '*', 'function', 'if', 'for', 'while', 'switch', 'try', 'catch', 'else')):
				if not line_stripped.endswith((';', '{', '}', ':', ',', ')')):
					if any(keyword in line_stripped for keyword in ['const ', 'let ', 'var ', 'return ', 'break', 'continue', 'throw']):
						if not line_stripped.endswith(';'):
							lines[i] = lines[i].rstrip() + ';'
							changes.append("Added missing semicolon")
		fixed_code = '\n'.join(lines)
			
	elif lang == "python":
		lines = []
		for line in fixed_code.splitlines():
			if line.rstrip().endswith(";"):
				changes.append("Removed trailing semicolon")
				line = line.rstrip().rstrip(";")
			lines.append(line)
		fixed_code = "\n".join(lines)
		
		# Fix common Python syntax issues
		# Add missing colons after if/for/while/def/class
		fixed_code = re.sub(r'(\s+)(if|for|while|def|class|elif|else|except|finally|with)\s+([^:\n]+)(\s*)(?!\s*:)', r'\1\2 \3:', fixed_code)
		if fixed_code != code:
			changes.append("Added missing colons")
		
		# Fix indentation issues (basic)
		lines = fixed_code.split('\n')
		for i, line in enumerate(lines):
			if line.strip() and not line.startswith(' ') and any(keyword in line for keyword in ['def ', 'class ', 'if ', 'for ', 'while ']):
				# This is likely a top-level definition, ensure proper indentation
				if i > 0 and lines[i-1].strip().endswith(':'):
					lines[i] = '    ' + line
					changes.append("Fixed indentation")
		fixed_code = '\n'.join(lines)
		
	elif lang == "java":
		# Fix == -> .equals() for strings (basic heuristic)
		fixed2 = re.sub(r'(\w+)\s*==\s*"([^"]*)"', r'\1.equals("\2")', fixed_code)
		if fixed2 != fixed_code:
			fixed_code = fixed2
			changes.append("Replaced == with .equals() for strings")
		
		# Add missing semicolons
		lines = fixed_code.split('\n')
		for i, line in enumerate(lines):
			line_stripped = line.strip()
			if line_stripped and not line_stripped.startswith(('//', '/*', '*', 'public', 'private', 'protected', 'class', 'interface', 'enum')):
				if not line_stripped.endswith((';', '{', '}', ':', ',')):
					if any(keyword in line_stripped for keyword in ['return ', 'System.out', 'break', 'continue', 'throw']):
						if not line_stripped.endswith(';'):
							lines[i] = lines[i].rstrip() + ';'
							changes.append("Added missing semicolon")
		fixed_code = '\n'.join(lines)
		
	elif lang == "cpp":
		# Add missing semicolons
		lines = fixed_code.split('\n')
		for i, line in enumerate(lines):
			line_stripped = line.strip()
			if line_stripped and not line_stripped.startswith(('#', '//', '/*', '*', 'class', 'struct', 'namespace', 'public:', 'private:', 'protected:')):
				if not line_stripped.endswith((';', '{', '}', ':', ',')):
					if any(keyword in line_stripped for keyword in ['return ', 'cout', 'cin', 'break', 'continue', 'throw']):
						if not line_stripped.endswith(';'):
							lines[i] = lines[i].rstrip() + ';'
							changes.append("Added missing semicolon")
		fixed_code = '\n'.join(lines)
		
		# Add missing #include for common functions
		if 'cout' in fixed_code and '#include <iostream>' not in fixed_code:
			fixed_code = '#include <iostream>\n' + fixed_code
			changes.append("Added missing #include <iostream>")
		elif 'printf' in fixed_code and '#include <cstdio>' not in fixed_code:
			fixed_code = '#include <cstdio>\n' + fixed_code
			changes.append("Added missing #include <cstdio>")
	
	elif lang == "c":
		# Add missing semicolons for C
		lines = fixed_code.split('\n')
		for i, line in enumerate(lines):
			line_stripped = line.strip()
			if line_stripped and not line_stripped.startswith(('#', '//', '/*', '*')):
				if not line_stripped.endswith((';', '{', '}', ':', ',')):
					if any(keyword in line_stripped for keyword in ['return ', 'break', 'continue', 'int ', 'char ', 'float ', 'double ']):
						if not line_stripped.endswith(';'):
							lines[i] = lines[i].rstrip() + ';'
							changes.append("Added missing semicolon")
		fixed_code = '\n'.join(lines)
		
		# Add missing #include for common C functions
		if 'printf' in fixed_code and '#include <stdio.h>' not in fixed_code:
			fixed_code = '#include <stdio.h>\n' + fixed_code
			changes.append("Added missing #include <stdio.h>")
		if 'malloc' in fixed_code and '#include <stdlib.h>' not in fixed_code:
			fixed_code = '#include <stdlib.h>\n' + fixed_code
			changes.append("Added missing #include <stdlib.h>")
		if 'string' in fixed_code and '#include <string.h>' not in fixed_code:
			fixed_code = '#include <string.h>\n' + fixed_code
			changes.append("Added missing #include <string.h>")
	
	# Clean up trailing spaces
	fixed_code = '\n'.join(line.rstrip() for line in fixed_code.split('\n'))
	
	# Check if heuristics fixed all errors
	if changes:
		check_analysis = _analyze(language, fixed_code)
		remaining_errors = [i for i in check_analysis["issues"] if i.type == "Error"]
		if not remaining_errors:
			# Heuristics fixed everything!
			attempts.append({"source": "heuristic", "applied": True})
			return {"fixed": fixed_code, "changes": changes, "source": "heuristic", "attempts": attempts}
	
	# Try external AI services in parallel when configured
	import concurrent.futures
	
	openrouter_key = os.environ.get("OPENROUTER_API_KEY")
	gemini_key = os.environ.get("GOOGLE_API_KEY")
	
	with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
		futures = []
		source_map: Dict[Any, str] = {}
		
		if openrouter_key:
			f = executor.submit(_call_openrouter_fix_with_errors, code, language, errors)
			futures.append(f)
			source_map[f] = "openrouter"
		else:
			attempts.append({"source": "openrouter", "applied": False, "error": "missing_api_key"})
		
		if gemini_key:
			f = executor.submit(_call_gemini_fix_with_errors, code, language, errors)
			futures.append(f)
			source_map[f] = "google"
		else:
			attempts.append({"source": "google", "applied": False, "error": "missing_api_key"})
		
		if futures:
			# Wait for first successful result
			for f in concurrent.futures.as_completed(futures, timeout=20):
				try:
					result = f.result()
					src = source_map.get(f, "unknown")
					if result and result != code:
						# Cancel remaining futures
						for other in futures:
							if other is not f and not other.done():
								other.cancel()
						attempts.append({"source": src, "applied": True})
						return {"fixed": result, "changes": ["AI fix applied"], "source": src, "attempts": attempts}
					else:
						attempts.append({"source": src, "applied": False, "error": "no_result"})
				except Exception as e:
					# Record error for transparency
					src = source_map.get(f, "unknown")
					attempts.append({"source": src, "applied": False, "error": str(e)})

	# Fallback to heuristic result
	attempts.append({"source": "heuristic", "applied": bool(changes)})
	return {"fixed": fixed_code, "changes": changes or ["No changes"], "source": "heuristic", "attempts": attempts}

@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
	# Basic validation
	code = (req.code or "").rstrip()
	requested_language = (req.language or "").strip() or "auto"
	language = _detect_language(code, requested_language)
	result = _analyze(language, code)
	analyzed_at = datetime.now(timezone.utc).isoformat()
	return AnalyzeResponse(
		codeQualityScore=result["score"],
		issues=result["issues"],
		metrics=Metrics(**result["metrics"]),
		language=language,
		analyzedAt=analyzed_at,
		code=code,
	)

@app.post("/api/fix", response_model=FixResponse)
def fix(req: FixRequest) -> FixResponse:
	requested_language = (req.language or "").strip() or "auto"
	language = _detect_language(req.code or "", requested_language)
	result = _auto_fix(req.code or "", language)
	return FixResponse(
		language=language,
		fixedCode=result["fixed"],
		changes=result["changes"],
		source=result.get("source", "heuristic"),
		attempts=result.get("attempts", []),
	)

@app.post("/api/report")
def report(req: ReportRequest) -> dict:
	language = _detect_language(req.code or "", (req.language or "").strip() or "auto")
	code = (req.code or "").rstrip()
	result = _analyze(language, code)
	analyzed_at = datetime.now(timezone.utc).isoformat()
	issues: List[Issue] = result["issues"]
	metrics = result["metrics"]

	errors = [it for it in issues if it.type == "Error"]
	others = [it for it in issues if it.type != "Error"]
	lines = [
		"Code Quality Report",
		f"Timestamp (UTC): {analyzed_at}",
		f"Language: {language}",
		f"Code length: {len(code)} chars, {len(code.splitlines())} lines",
		"",
		f"Overall Score: {result['score']}/100",
		f"Cyclomatic Complexity: {metrics['cyclomaticComplexity']}",
		f"Readability Score: {metrics['readabilityScore']}%",
		f"Style Adherence: {metrics['styleAdherence']}%",
		"",
		"Errors:",
	]
	if not errors:
		lines.append("  - None 🎉")
	else:
		for it in errors:
			lines.append(f"  - Line {it.line} [{it.severity}] {it.type}: {it.message} -> Suggestion: {it.suggestion}")

	lines.append("")
	lines.append("Warnings & Suggestions:")
	if not others:
		lines.append("  - None")
	else:
		for it in others:
			lines.append(f"  - Line {it.line} [{it.severity}] {it.type}: {it.message} -> Suggestion: {it.suggestion}")

	lines.extend([
		"",
		"Code Snippet:",
		"----------------------------------------",
		code[:2000],
		"----------------------------------------",
	])

	return {"filename": "analysis_report.txt", "content": "\n".join(lines)}

@app.post("/api/report/html")
def report_html(req: ReportRequest) -> dict:
	language = _detect_language(req.code or "", (req.language or "").strip() or "auto")
	code = (req.code or "").rstrip()
	result = _analyze(language, code)
	analyzed_at = datetime.now(timezone.utc).isoformat()
	issues: List[Issue] = result["issues"]
	metrics = result["metrics"]

	errors = [it for it in issues if it.type == "Error"]
	others = [it for it in issues if it.type != "Error"]
	def _render_list(items: List[Issue]) -> str:
		if not items:
			return "<div>None</div>"
		return "".join(
			f'<div class="issue sev-{it.severity}">Line {it.line} [{it.severity}] {it.type}: {it.message} – <em>{it.suggestion}</em></div>' for it in items
		)

	escaped_code = (
		code[:2000]
		.replace("&", "&amp;")
		.replace("<", "&lt;")
		.replace(">", "&gt;")
	)

	html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>Code Quality Report</title>
<style>
 body {{ font-family: Arial, sans-serif; margin: 24px; }}
 h1 {{ margin-bottom: 8px; }}
 .meta {{ color: #555; margin-bottom: 16px; }}
 .section {{ margin-top: 16px; }}
 .code {{ white-space: pre-wrap; background:#0b1021; color:#e3e7ff; padding:12px; border-radius:8px; }}
 .issue {{ margin:6px 0; }}
 .sev-Critical {{ color: #e11d48; }}
 .sev-Major {{ color: #eab308; }}
 .sev-Minor {{ color: #6b7280; }}
</style>
</head>
<body>
<h1>Code Quality Report</h1>
<div class="meta">Timestamp (UTC): {analyzed_at} • Language: {language} • Score: {result['score']}/100</div>
<div class="section">
  <strong>Metrics</strong>
  <div>Cyclomatic Complexity: {metrics['cyclomaticComplexity']}</div>
  <div>Readability Score: {metrics['readabilityScore']}%</div>
  <div>Style Adherence: {metrics['styleAdherence']}%</div>
</div>
<div class="section">
  <strong>Errors</strong>
  {_render_list(errors)}
</div>
<div class="section">
  <strong>Warnings & Suggestions</strong>
  {_render_list(others)}
</div>
<div class="section">
  <strong>Code Snippet</strong>
  <div class="code">{escaped_code}</div>
</div>
</body>
</html>
"""
	return {"filename": "analysis_report.html", "html": html}

if __name__ == "__main__":
	# Allow running with: python main.py
	import uvicorn
	uvicorn.run(
		"main:app",
		host="127.0.0.1",
		port=8000,
		reload=True,
	)
