import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Play, RotateCcw, Download, Sparkles } from "lucide-react";
import CodeEditor from "@/components/CodeEditor";
import IssuesPanel from "@/components/IssuesPanel";
import MetricsPanel from "@/components/MetricsPanel";
import TipsPanel from "@/components/TipsPanel";
import Logo from "@/components/Logo";
import { toast } from "sonner";

const defaultCode = `// Paste your code here and it will auto-detect the language!
// Examples:
// JavaScript: function hello() { console.log("world"); }
// Python: def hello(): print("world")
// Java: public class Hello { public static void main(String[] args) { System.out.println("world"); } }
// C++: #include <iostream> using namespace std; int main() { cout << "world"; return 0; }
// C: #include <stdio.h> int main() { printf("world"); return 0; }
// TypeScript: interface User { name: string; }`;

type Severity = "Critical" | "Major" | "Minor";

type Issue = {
  line: number;
  type: string;
  severity: Severity;
  message: string;
  suggestion: string;
};

type Metrics = {
  cyclomaticComplexity: number;
  readabilityScore: number;
  styleAdherence: number;
};

type AnalyzeResponse = {
  codeQualityScore: number;
  issues: Issue[];
  metrics: Metrics;
  language: string;
  analyzedAt: string;
  code: string;
};

type HistoryItem = AnalyzeResponse & { id: string };

const Index = () => {
  const [code, setCode] = useState(defaultCode);
  const [language, setLanguage] = useState("auto");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isFixing, setIsFixing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalyzeResponse | null>(null);
  const [scrollToLine, setScrollToLine] = useState<number | undefined>();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const fixTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-detect language when code changes
  const handleCodeChange = (newCode: string) => {
    setCode(newCode);
    
    // Only auto-detect if language is set to "auto"
    if (language === "auto" && newCode.trim()) {
      // Simple client-side detection for immediate feedback
      const code = newCode.trim().toLowerCase();
      let detectedLanguage = "";
      
      if (code.includes("def ") || code.includes("import ") || code.includes("print(")) {
        detectedLanguage = "python";
      } else if (code.includes("public class") || code.includes("system.out.println") || code.includes("import java.")) {
        detectedLanguage = "java";
      } else if (code.includes("using namespace") || code.includes("std::") || (code.includes("#include") && code.includes("iostream"))) {
        detectedLanguage = "cpp";
      } else if (code.includes("#include") && (code.includes("stdio.h") || code.includes("stdlib.h") || code.includes("string.h"))) {
        detectedLanguage = "c";
      } else if (code.includes("interface ") || code.includes("type ") || code.includes(": string") || code.includes("array<")) {
        detectedLanguage = "typescript";
      } else if (code.includes("function ") || code.includes("=>") || code.includes("console.log") || code.includes("const ")) {
        detectedLanguage = "javascript";
      }
      
      // Set the detected language if found and different from current
      if (detectedLanguage && detectedLanguage !== language) {
        setLanguage(detectedLanguage);
        toast.info(`Auto-detected: ${detectedLanguage.charAt(0).toUpperCase() + detectedLanguage.slice(1)}`);
      }
    }
  };

  const handleAnalyze = async (overrideCode?: string) => {
    const source = overrideCode ?? code;
    const trimmed = (source || "").trim();
    if (!trimmed) {
      toast.error("Please paste or type some code before analyzing.");
      return;
    }
    try {
      setIsAnalyzing(true);
      // Keep previous results visible during analysis
      setScrollToLine(undefined);
      toast.info("Analyzing your code...");
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: trimmed, language }),
      });
      if (!res.ok) {
        throw new Error(`Analyze failed: ${res.status}`);
      }
      const data: AnalyzeResponse = await res.json();
      setAnalysisResult(data);
      
      // Auto-update language if auto-detect was used and language changed
      if (language === "auto" && data.language !== "auto") {
        setLanguage(data.language);
        toast.success(`Auto-detected language: ${data.language}`);
      }
      
      setHistory((prev) => [{ id: crypto.randomUUID(), ...data }, ...prev].slice(0, 10));
      
      // More detailed success message
      const errorCount = data.issues.filter(issue => issue.type === "Error").length;
      const warningCount = data.issues.filter(issue => issue.type === "Warning").length;
      const suggestionCount = data.issues.filter(issue => issue.type === "Suggestion").length;
      
      if (errorCount === 0) {
        toast.success(`Analysis complete! Score: ${data.codeQualityScore}/100 (${data.language}) - No errors! 🎉`);
      } else {
        toast.success(`Analysis complete! Score: ${data.codeQualityScore}/100 (${data.language}) - ${errorCount} errors, ${warningCount} warnings, ${suggestionCount} suggestions`);
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to analyze code");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleFix = async () => {
    // Prevent multiple rapid clicks
    if (isFixing) {
      toast.info("Fix already in progress...");
      return;
    }

    const trimmed = (code || "").trim();
    if (!trimmed) {
      toast.error("Add some code first.");
      return;
    }

    // Clear any existing timeout
    if (fixTimeoutRef.current) {
      clearTimeout(fixTimeoutRef.current);
    }

    try {
      setIsFixing(true);
      toast.info("Applying AI fixes...");
      
      const res = await fetch("/api/fix", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: trimmed, language }),
      });
      
      if (!res.ok) {
        throw new Error(`Fix failed: ${res.status}`);
      }
      
      const { fixedCode, changes, source, language: lang } = (await res.json()) as { 
        fixedCode: string; 
        changes: string[]; 
        source: string; 
        language: string; 
      };
      
      setCode(fixedCode);
      
      if (changes.length && !(changes.length === 1 && changes[0] === "No changes")) {
        toast.success(`Fixed with ${source}: ${changes.join(", ")}`);
      } else {
        toast.info("No fixes needed.");
      }
      
      // Immediately analyze the fixed code
      await handleAnalyze(fixedCode);
      
    } catch (err) {
      console.error(err);
      toast.error("Failed to apply fixes");
    } finally {
      setIsFixing(false);
      // Add a small delay before allowing another fix
      fixTimeoutRef.current = setTimeout(() => {
        // Reset isFixing state after debounce period
      }, 1000);
    }
  };

  const handleReset = () => {
    setCode(defaultCode);
    setAnalysisResult(null);
    setScrollToLine(undefined);
    toast.info("Code reset to default");
  };

  const handleDownloadReport = async () => {
    try {
      const res = await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, language }),
      });
      if (!res.ok) {
        throw new Error(`Report failed: ${res.status}`);
      }
      const { filename, content } = (await res.json()) as { filename: string; content: string };
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success("Report downloaded successfully!");
    } catch (err) {
      console.error(err);
      toast.error("Failed to download report");
    }
  };

  const handleDownloadHtml = async () => {
    try {
      const res = await fetch("/api/report/html", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, language }),
      });
      if (!res.ok) {
        throw new Error(`Report failed: ${res.status}`);
      }
      const { filename, html } = (await res.json()) as { filename: string; html: string };
      const blob = new Blob([html], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success("HTML report downloaded!");
    } catch (err) {
      console.error(err);
      toast.error("Failed to download HTML report");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-primary/20 bg-card/50 backdrop-blur-md sticky top-0 z-50 animate-fade-in">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-secondary/5 to-accent/5" />
        <div className="container mx-auto px-4 py-4 relative">
          <div className="flex items-center justify-between">
            <Logo />
            <div className="flex items-center gap-3">
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger className="w-[200px] border-primary/20 hover:border-primary/40 transition-all bg-card/80">
                  <SelectValue placeholder="Language" />
                </SelectTrigger>
                <SelectContent className="bg-card border-primary/20">
                  <SelectItem value="auto">Auto Detect</SelectItem>
                  <SelectItem value="javascript">JavaScript</SelectItem>
                  <SelectItem value="python">Python</SelectItem>
                  <SelectItem value="java">Java</SelectItem>
                  <SelectItem value="cpp">C++</SelectItem>
                  <SelectItem value="c">C</SelectItem>
                  <SelectItem value="typescript">TypeScript</SelectItem>
                </SelectContent>
              </Select>
              <Button 
                onClick={handleReset} 
                variant="outline" 
                size="icon"
                className="border-secondary/20 hover:border-secondary/40 hover:bg-secondary/10 transition-all group"
              >
                <RotateCcw className="h-4 w-4 group-hover:rotate-180 transition-transform duration-300" />
              </Button>
              <Button
                onClick={() => handleAnalyze()}
                disabled={isAnalyzing}
                className="gap-2 bg-gradient-to-r from-primary via-secondary to-primary bg-[length:200%_100%] hover:bg-right transition-all duration-500 glow-primary"
              >
                {isAnalyzing ? (
                  <Sparkles className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                {isAnalyzing ? "Analyzing..." : "Analyze Code"}
              </Button>
              <Button
                onClick={handleFix}
                disabled={isFixing || isAnalyzing}
                variant="outline"
                className="gap-2 border-success/30 hover:border-success/50 hover:bg-success/10 disabled:opacity-50"
              >
                {isFixing ? (
                  <Sparkles className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                {isFixing ? "Fixing..." : "AI Debug"}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Code Editor */}
          <div className="lg:col-span-2 space-y-4">
            <CodeEditor
              value={code}
              onChange={handleCodeChange}
              language={language === "auto" ? (analysisResult?.language ?? "javascript") : language}
              highlights={analysisResult?.issues.map((issue) => ({
                line: issue.line,
                severity: issue.severity,
              }))}
              scrollToLine={scrollToLine}
            />
            
            {analysisResult && (
              <div className="flex gap-2">
                <Button
                  onClick={handleDownloadReport}
                  variant="outline"
                  className="w-full gap-2 border-accent/20 hover:border-accent/40 hover:bg-accent/10 transition-all group"
                >
                  <Download className="h-4 w-4 group-hover:animate-bounce" />
                  Download Text Report
                </Button>
                <Button
                  onClick={handleDownloadHtml}
                  variant="outline"
                  className="w-full gap-2 border-primary/20 hover:border-primary/40 hover:bg-primary/10 transition-all group"
                >
                  <Download className="h-4 w-4" />
                  Download HTML Report
                </Button>
              </div>
            )}
          </div>

          {/* Right Column - Analysis Results */}
          <div className="space-y-6">
            {isAnalyzing ? (
              <div className="h-full flex items-center justify-center animate-fade-in">
                <div className="text-center space-y-6 p-8">
                  <div className="relative mx-auto w-20 h-20 rounded-full bg-gradient-to-br from-primary/20 via-secondary/20 to-accent/20 flex items-center justify-center animate-pulse-glow">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary via-secondary to-accent rounded-full blur-xl opacity-30 animate-pulse" />
                    <Sparkles className="relative h-10 w-10 text-primary animate-float" />
                  </div>
                  <div className="space-y-3">
                    <h3 className="text-2xl font-bold gradient-text">Analyzing Code...</h3>
                    <p className="text-sm text-muted-foreground max-w-sm">
                      Please wait while we analyze your code for issues and suggestions.
                    </p>
                  </div>
                </div>
              </div>
            ) : analysisResult ? (
              <>
                {/* Metadata */}
                <div className="p-4 rounded-lg bg-background/50 border border-border/50">
                  <div className="text-sm text-muted-foreground">Analyzed</div>
                  <div className="text-sm font-medium">
                    {new Date(analysisResult.analyzedAt).toLocaleString()} • {analysisResult.language} • {analysisResult.issues.length} issues
                  </div>
                  {language === "auto" && (
                    <div className="text-xs text-muted-foreground mt-1">
                      Auto-detected as: {analysisResult.language}
                    </div>
                  )}
                </div>

                <MetricsPanel
                  score={analysisResult.codeQualityScore}
                  metrics={analysisResult.metrics}
                />
                <IssuesPanel issues={analysisResult.issues} onIssueClick={(line) => setScrollToLine(line)} />
                <TipsPanel />

                {/* History */}
                {history.length > 0 && (
                  <div className="p-4 rounded-lg bg-background/50 border border-border/50">
                    <div className="text-sm font-semibold mb-2">History</div>
                    <div className="space-y-2 text-sm">
                      {history.map((h) => (
                        <div key={h.id} className="flex items-center justify-between">
                          <div>{new Date(h.analyzedAt).toLocaleString()} • {h.language} • {h.issues.length} issues • {h.codeQualityScore}/100</div>
                          <button className="text-primary hover:underline" onClick={() => setAnalysisResult(h)}>Load</button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="h-full flex items-center justify-center animate-fade-in">
                <div className="text-center space-y-6 p-8">
                  <div className="relative mx-auto w-20 h-20 rounded-full bg-gradient-to-br from-primary/20 via-secondary/20 to-accent/20 flex items-center justify-center animate-pulse-glow">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary via-secondary to-accent rounded-full blur-xl opacity-30 animate-pulse" />
                    <Sparkles className="relative h-10 w-10 text-primary animate-float" />
                  </div>
                  <div className="space-y-3">
                    <h3 className="text-2xl font-bold gradient-text">Ready to Analyze</h3>
                    <p className="text-sm text-muted-foreground max-w-sm">
                      Paste your code in the editor and click "Analyze Code" to get
                      detailed feedback and suggestions powered by AI.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
