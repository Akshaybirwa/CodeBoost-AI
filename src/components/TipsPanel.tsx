import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Lightbulb, BookOpen, Target } from "lucide-react";

interface TipsPanelProps {
  tips?: string[];
}

const defaultTips = [
  {
    title: "Keep Functions Small",
    description: "Functions should do one thing and do it well. Aim for functions under 20 lines.",
    category: "Best Practice",
  },
  {
    title: "Use Meaningful Names",
    description: "Variable and function names should be descriptive and follow naming conventions.",
    category: "Code Style",
  },
  {
    title: "Avoid Magic Numbers",
    description: "Replace hardcoded numbers with named constants to improve code readability.",
    category: "Maintainability",
  },
  {
    title: "Write Self-Documenting Code",
    description: "Code should be clear enough to understand without excessive comments.",
    category: "Best Practice",
  },
  {
    title: "Handle Errors Gracefully",
    description: "Always anticipate and handle potential errors to make your code more robust.",
    category: "Error Handling",
  },
];

const TipsPanel = ({ tips }: TipsPanelProps) => {
  return (
    <Card className="border-warning/20 bg-card/80 backdrop-blur-sm animate-fade-in-up hover:border-warning/40 transition-all duration-300">
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-warning animate-pulse" />
          Best Practices & Tips
        </h3>
        <ScrollArea className="h-[520px] pr-4">
          <div className="space-y-4">
            {defaultTips.map((tip, index) => (
              <div
                key={index}
                className="p-4 rounded-lg bg-background/50 border border-border/50 hover:border-warning/50 hover:scale-[1.02] transition-all duration-300 cursor-pointer group animate-fade-in"
                style={{ animationDelay: `${index * 0.15}s` }}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-1 transition-transform group-hover:scale-110">
                    {index % 3 === 0 ? (
                      <BookOpen className="h-4 w-4 text-primary" />
                    ) : (
                      <Target className="h-4 w-4 text-success" />
                    )}
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold">{tip.title}</h4>
                      <Badge variant="outline" className="text-xs transition-all group-hover:scale-105">
                        {tip.category}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {tip.description}
                    </p>
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

export default TipsPanel;
