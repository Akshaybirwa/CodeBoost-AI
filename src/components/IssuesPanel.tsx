import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AlertCircle, AlertTriangle, Info } from "lucide-react";
import { useState } from "react";

interface Issue {
  line: number;
  type: string;
  severity: "Critical" | "Major" | "Minor";
  message: string;
  suggestion: string;
}

interface IssuesPanelProps {
  issues: Issue[];
  onIssueClick?: (line: number) => void;
}

const IssuesPanel = ({ issues, onIssueClick }: IssuesPanelProps) => {
  const [filter, setFilter] = useState<"All" | "Critical" | "Major" | "Minor">("All");

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "Critical":
        return <AlertCircle className="h-4 w-4" />;
      case "Major":
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case "Critical":
        return "destructive";
      case "Major":
        return "default";
      default:
        return "secondary";
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "Critical":
        return "text-destructive";
      case "Major":
        return "text-warning";
      default:
        return "text-muted-foreground";
    }
  };

  const visible = issues.filter(i => filter === "All" ? true : i.severity === filter);

  return (
    <Card className="border-secondary/20 bg-card/80 backdrop-blur-sm animate-slide-in-right hover:border-secondary/40 transition-all duration-300">
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-secondary animate-pulse" />
          Issues Found ({visible.length}/{issues.length})
        </h3>

        {/* Filters */}
        <div className="flex gap-2 mb-4">
          {["All", "Critical", "Major", "Minor"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setFilter(lvl as any)}
              className={`text-xs px-2 py-1 rounded border ${filter === lvl ? "bg-secondary/20 border-secondary/40" : "border-border/50 hover:border-primary/40"}`}
            >
              {lvl}
            </button>
          ))}
        </div>

        <ScrollArea className="h-[520px] pr-4">
          <div className="space-y-3">
            {visible.map((issue, index) => (
              <div
                key={index}
                className="p-4 rounded-lg bg-background/50 border border-border/50 hover:border-primary/50 hover:scale-[1.02] transition-all duration-300 cursor-pointer group animate-fade-in"
                style={{ animationDelay: `${index * 0.1}s` }}
                onClick={() => onIssueClick?.(issue.line)}
              >
                <div className="flex items-start gap-3">
                  <div className={`${getSeverityColor(issue.severity)} transition-transform group-hover:scale-110`}>
                    {getSeverityIcon(issue.severity)}
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <Badge variant={getSeverityVariant(issue.severity)} className="transition-all group-hover:scale-105">
                        {issue.severity}
                      </Badge>
                      <span className="text-xs text-muted-foreground">Line {issue.line}</span>
                    </div>
                    <p className="text-sm font-medium">{issue.message}</p>
                    <p className="text-xs text-muted-foreground">{issue.suggestion}</p>
                    <Badge variant="outline" className="text-xs">
                      {issue.type}
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>
    </Card>
  );
};

export default IssuesPanel;
