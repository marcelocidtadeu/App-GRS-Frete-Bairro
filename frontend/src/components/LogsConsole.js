import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";

export const LogsConsole = ({ logs }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogColor = (type) => {
    switch (type) {
      case "error":
        return "text-rose-400";
      case "success":
        return "text-emerald-400";
      case "info":
        return "text-blue-400";
      default:
        return "text-slate-300";
    }
  };

  return (
    <div className="bg-slate-900 rounded-lg p-4 font-mono text-xs h-64 overflow-y-auto border border-slate-800 shadow-inner" ref={scrollRef}>
      {logs.length === 0 ? (
        <p className="text-slate-500">Aguardando logs...</p>
      ) : (
        <div className="space-y-1">
          {logs.map((log, idx) => (
            <div key={idx} className={getLogColor(log[0])}>
              [{new Date().toLocaleTimeString()}] {log[1]}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LogsConsole;