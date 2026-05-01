"use client";
import { useEffect, useState } from "react";
import { getRuns, getReplay, deleteRun } from "@/lib/api";
import { Activity, CheckCircle, XCircle, Clock, DollarSign, Zap, Trash2 } from "lucide-react";

interface Run {
  id: string;
  agent_name: string;
  intent?: string;
  prompt: string;
  status: string;
  total_tokens: number;
  total_cost: number;
  started_at: string;
  finished_at: string;
}

function TimelineStep({ step, i, total, selectedRun }: { step: any, i: number, total: number, selectedRun: any }) {
  const [showDetails, setShowDetails] = useState(false);
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className={`w-4 h-4 rounded-full mt-1 border-2 border-gray-900 ${
          step.type === "run_started" ? "bg-blue-400 shadow-[0_0_10px_rgba(96,165,250,0.5)]" :
          step.type === "run_finished" ? "bg-green-400 shadow-[0_0_10px_rgba(74,222,128,0.5)]" :
          step.type === "tool_call" ? "bg-purple-400 shadow-[0_0_10px_rgba(192,132,252,0.5)]" :
          step.type === "agent_thinking" ? "bg-yellow-400 animate-pulse shadow-[0_0_10px_rgba(250,204,21,0.5)]" :
          step.type === "llm_call" ? "bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" :
          "bg-gray-400"
        }`} />
        {i < total - 1 && (
          <div className="w-0.5 h-full bg-gray-800 my-1" />
        )}
      </div>
      <div className="bg-gray-900/50 rounded-xl p-4 flex-1 border border-gray-800 hover:border-gray-700 transition">
        <div className="flex justify-between items-start mb-2">
          <div>
            <span className="text-xs font-bold text-blue-400 tracking-wider uppercase">
              {step.type.replace("_", " ")}
            </span>
            <p className="text-sm text-gray-300 mt-0.5">
              {step.type === "run_started" && `Started ${selectedRun.agent_name}`}
              {step.type === "agent_thinking" && "Agent is processing your request..."}
              {step.type === "llm_call" && `Model: ${step.data.model || "NVIDIA"}`}
              {step.type === "tool_call" && `Using tool: ${step.data.tool}`}
              {step.type === "run_finished" && `Finished with status: ${step.data.status}`}
            </p>
          </div>
          <span className="text-[10px] text-gray-600 font-mono">
            {new Date(step.timestamp).toLocaleTimeString()}
          </span>
        </div>
        
        <button 
          onClick={() => setShowDetails(!showDetails)}
          className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 transition-colors"
        >
          {showDetails ? "Hide Data" : "View Details"}
        </button>

        {showDetails && (
          <div className="mt-3 bg-gray-950 rounded-lg p-3 border border-gray-800 animate-in fade-in slide-in-from-top-1 duration-200">
            <pre className="text-[11px] text-gray-400 overflow-x-auto whitespace-pre-wrap font-mono">
              {JSON.stringify(step.data, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Home() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [prompt, setPrompt] = useState("");
  const [intent, setIntent] = useState("");
  const [running, setRunning] = useState(false);

  useEffect(() => {
    fetchRuns();
  }, []);

  const fetchRuns = async () => {
    try {
      const res = await getRuns();
      setRuns(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleReplay = async (run: Run) => {
    setSelectedRun(run);
    const res = await getReplay(run.id);
    setTimeline(res.data.timeline);
  };

  const handleDelete = async (runId: string) => {
    if (confirm("Are you sure you want to delete this run?")) {
      try {
        await deleteRun(runId);
        fetchRuns(); // Refresh the list
      } catch (e) {
        console.error(e);
        alert("Failed to delete run");
      }
    }
  };

  const runAgent = async () => {
    if (!prompt.trim()) return;
    setRunning(true);
    try {
      const response = await fetch("http://127.0.0.1:8000/agent/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, intent: intent.trim() || undefined }),
      });
      if (response.ok) {
        fetchRuns(); // Refresh runs
        setPrompt("");
        setIntent("");
      } else {
        alert("Failed to run agent");
      }
    } catch (e) {
      console.error(e);
      alert("Error running agent");
    } finally {
      setRunning(false);
    }
  };

  const getStatusIcon = (status: string) => {
    if (status === "success") return <CheckCircle className="text-green-500 w-5 h-5" />;
    if (status === "failed") return <XCircle className="text-red-500 w-5 h-5" />;
    return <Clock className="text-yellow-500 w-5 h-5" />;
  };

  const getStatusColor = (status: string) => {
    if (status === "success") return "bg-green-100 text-green-800";
    if (status === "failed") return "bg-red-100 text-red-800";
    return "bg-yellow-100 text-yellow-800";
  };

  const totalCost = runs.reduce((sum, r) => sum + (r.total_cost || 0), 0);
  const totalTokens = runs.reduce((sum, r) => sum + (r.total_tokens || 0), 0);
  const successRate = runs.length
    ? Math.round((runs.filter(r => r.status === "success").length / runs.length) * 100)
    : 0;

  return (
    <main className="min-h-screen bg-gray-950 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Activity className="text-blue-400" /> Agent Control Room
        </h1>
        <p className="text-gray-400 mt-1">Monitor, debug and replay your AI agents</p>
        
        {/* Run Agent Form */}
        <div className="mt-4 bg-gray-900 rounded-xl p-4 border border-gray-800">
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            🤖 Run AI Agent
          </h2>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Intent (optional)"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
            <input
              type="text"
              placeholder="Ask the agent something..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && runAgent()}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
            <div className="flex gap-2">
              <button
                onClick={runAgent}
                disabled={running || !prompt.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg font-medium flex items-center gap-2"
              >
                ▶ Run
              </button>
              <button
                onClick={() => { setPrompt(""); setIntent(""); }}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium"
              >
                🔄
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-gray-400 text-sm">Total Runs</p>
          <p className="text-3xl font-bold mt-1">{runs.length}</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-gray-400 text-sm">Success Rate</p>
          <p className="text-3xl font-bold mt-1 text-green-400">{successRate}%</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-gray-400 text-sm flex items-center gap-1">
            <Zap className="w-4 h-4" /> Total Tokens
          </p>
          <p className="text-3xl font-bold mt-1 text-blue-400">{totalTokens.toLocaleString()}</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-gray-400 text-sm flex items-center gap-1">
            <DollarSign className="w-4 h-4" /> Total Cost
          </p>
          <p className="text-3xl font-bold mt-1 text-purple-400">${totalCost.toFixed(4)}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Runs Table */}
        <div className="bg-gray-900 rounded-xl border border-gray-800">
          <div className="p-4 border-b border-gray-800">
            <h2 className="font-semibold text-lg">Agent Runs</h2>
          </div>
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading...</div>
          ) : runs.length === 0 ? (
            <div className="p-8 text-center text-gray-400">No runs yet</div>
          ) : (
            <div className="divide-y divide-gray-800">
              {runs.map((run) => (
                <div
                  key={run.id}
                  className="p-4 hover:bg-gray-800 cursor-pointer transition relative"
                  onClick={() => handleReplay(run)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-blue-400">{run.agent_name}</span>
                      {run.intent && (
                        <span className="text-xs bg-blue-900 text-blue-300 px-2 py-1 rounded">
                          {run.intent}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded-full flex items-center gap-1 ${getStatusColor(run.status)}`}>
                        {getStatusIcon(run.status)} {run.status}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(run.id);
                        }}
                        className="text-red-400 hover:text-red-300 p-1"
                        title="Delete run"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <p className="text-gray-400 text-sm truncate">{run.prompt}</p>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    <span>🪙 {run.total_tokens} tokens</span>
                    <span>💰 ${run.total_cost?.toFixed(4)}</span>
                    <span>🕐 {new Date(run.started_at).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Replay Timeline */}
        <div className="bg-gray-900 rounded-xl border border-gray-800">
          <div className="p-4 border-b border-gray-800">
            <h2 className="font-semibold text-lg">
              {selectedRun ? `Replay: ${selectedRun.agent_name}` : "Replay Viewer"}
            </h2>
            {selectedRun && (
              <p className="text-gray-400 text-sm mt-1 truncate">{selectedRun.prompt}</p>
            )}
          </div>
          {!selectedRun ? (
            <div className="p-8 text-center text-gray-400">
              👈 Click a run to replay it
            </div>
          ) : (
            <div className="p-4 space-y-4 max-h-[600px] overflow-y-auto">
              {timeline.map((step, i) => (
                <TimelineStep 
                  key={i} 
                  step={step} 
                  i={i} 
                  total={timeline.length} 
                  selectedRun={selectedRun} 
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}