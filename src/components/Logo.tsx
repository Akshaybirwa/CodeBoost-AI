import { Code2, Sparkles } from "lucide-react";

const Logo = () => {
  return (
    <div className="relative flex items-center gap-3 group">
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-primary via-secondary to-accent rounded-lg blur-xl opacity-50 group-hover:opacity-75 transition-opacity animate-pulse-glow" />
        <div className="relative p-2.5 rounded-lg bg-gradient-to-br from-primary/20 via-secondary/20 to-accent/20 border border-primary/30 backdrop-blur-sm animate-float">
          <Code2 className="h-6 w-6 text-primary" />
          <Sparkles className="absolute -top-1 -right-1 h-3 w-3 text-accent animate-pulse" />
        </div>
      </div>
      <div className="space-y-0.5">
        <h1 className="text-2xl font-bold gradient-text animate-fade-in">
          CodeAnalyzer
        </h1>
        <p className="text-xs text-muted-foreground animate-fade-in">
          AI-Powered Code Review
        </p>
      </div>
    </div>
  );
};

export default Logo;
