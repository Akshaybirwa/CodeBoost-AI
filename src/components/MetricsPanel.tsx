import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Activity, TrendingUp, CheckCircle2, Zap } from "lucide-react";

interface Metrics {
  cyclomaticComplexity: number;
  readabilityScore: number;
  styleAdherence: number;
}

interface MetricsPanelProps {
  score: number;
  metrics: Metrics;
}

const MetricsPanel = ({ score, metrics }: MetricsPanelProps) => {
  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-success";
    if (score >= 60) return "text-warning";
    return "text-destructive";
  };

  return (
    <Card className="border-accent/20 bg-card/80 backdrop-blur-sm animate-scale-in hover:border-accent/40 transition-all duration-300 relative overflow-hidden group">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      <div className="relative p-6 space-y-6">
        <div className="text-center space-y-2">
          <h3 className="text-lg font-semibold">Code Quality Score</h3>
          <div className={`text-6xl font-bold ${getScoreColor(score)} animate-fade-in transition-all duration-300 group-hover:scale-110`}>
            {score}
            <span className="text-2xl text-muted-foreground">/100</span>
          </div>
          <Progress value={score} className="h-3 transition-all duration-300" />
        </div>

        <div className="space-y-4 pt-4 border-t border-border/50">
          <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Detailed Metrics
          </h4>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-primary/5 border border-primary/10 hover:border-primary/30 transition-all group">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-primary group-hover:animate-pulse" />
                <span className="text-sm">Cyclomatic Complexity</span>
              </div>
              <span className="text-sm font-semibold text-primary">{metrics.cyclomaticComplexity}</span>
            </div>

            <div className="space-y-2 p-3 rounded-lg bg-secondary/5 border border-secondary/10 hover:border-secondary/30 transition-all">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-secondary" />
                  <span className="text-sm">Readability Score</span>
                </div>
                <span className="text-sm font-semibold text-secondary">{metrics.readabilityScore}%</span>
              </div>
              <Progress value={metrics.readabilityScore} className="h-2" />
            </div>

            <div className="space-y-2 p-3 rounded-lg bg-accent/5 border border-accent/10 hover:border-accent/30 transition-all">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-accent" />
                  <span className="text-sm">Style Adherence</span>
                </div>
                <span className="text-sm font-semibold text-accent">{metrics.styleAdherence}%</span>
              </div>
              <Progress value={metrics.styleAdherence} className="h-2" />
            </div>

            <div className="pt-4 border-t border-border/50">
              <div className="flex items-start gap-2">
                <Zap className="h-4 w-4 text-warning mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Performance Impact</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Your code shows moderate complexity. Consider refactoring large functions.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default MetricsPanel;
