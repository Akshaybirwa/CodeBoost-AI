import { Editor, OnMount } from "@monaco-editor/react";
import { Card } from "@/components/ui/card";

interface CodeEditorProps {
  value: string;
  onChange: (value: string | undefined) => void;
  language: string;
  highlights?: Array<{ line: number; severity: "Critical" | "Major" | "Minor" }>;
  scrollToLine?: number;
}

const CodeEditor = ({ value, onChange, language, highlights = [], scrollToLine }: CodeEditorProps) => {
  let editorRef: any;

  const handleMount: OnMount = (editor) => {
    editorRef = editor;
    if (scrollToLine && scrollToLine > 0) {
      editor.revealLineInCenter(scrollToLine);
      editor.setPosition({ lineNumber: scrollToLine, column: 1 });
      editor.focus();
    }
  };

  return (
    <Card className="overflow-hidden border-primary/20 bg-card/80 backdrop-blur-sm animate-fade-in hover:border-primary/40 transition-all duration-300 relative group">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      <div className="relative h-[600px]">
        <Editor
          onMount={handleMount}
          height="100%"
          defaultLanguage={language.toLowerCase()}
          language={language.toLowerCase()}
          theme="vs-dark"
          value={value}
          onChange={onChange}
          options={{
            minimap: { enabled: true },
            fontSize: 14,
            lineNumbers: "on",
            roundedSelection: true,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            wordWrap: "on",
          }}
        />
      </div>
    </Card>
  );
};

export default CodeEditor;
