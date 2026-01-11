"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { taskService } from "../../../../../services/task.service";

export default function McqTaskPage({ params, searchParams }) {
  const router = useRouter();
  const unwrappedParams = use(params);
  const unwrappedSearchParams = use(searchParams);
  const taskId = unwrappedParams.taskId;
  const hint = unwrappedSearchParams?.hint;
  const querySlotId = unwrappedSearchParams?.slotId;

  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedOption, setSelectedOption] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [persistedHint, setPersistedHint] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (hint) {
      if (typeof window !== 'undefined') {
         localStorage.setItem(`hint_${taskId}`, hint);
      }
      setPersistedHint(hint);
    } else {
      if (typeof window !== 'undefined') {
         const stored = localStorage.getItem(`hint_${taskId}`);
         if (stored) setPersistedHint(stored);
      }
    }
  }, [hint, taskId]);

  useEffect(() => {
    async function loadTask() {
      if (!taskId) return;
      try {
        setLoading(true);
        const data = await taskService.getTaskExecutionDetails(taskId);
        setTask(data);
      } catch (error) {
        console.error("Failed to load task:", error);
      } finally {
        setLoading(false);
      }
    }
    loadTask();
  }, [taskId]);

  const handleSubmit = async () => {
    if (selectedOption === null) return;
    
    // Try to get slot ID from query params or task details
    const slotId = querySlotId || task?.slot_id;
    
    if (!slotId) {
      setError("Slot ID missing. Please refresh and try again.");
      return;
    }

    setSubmitting(true);
    setEvaluation(null);
    setError(null);
    try {
      const result = await taskService.submitTask(slotId, taskId, { answer: selectedOption });
      
      const evalData = result.evaluation;
      setEvaluation(evalData);

      // Immediately redirect after submission regardless of pass/fail
      router.push("/dashboard");
    } catch (error) {
      console.error("Failed to submit:", error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || "Submission failed. Please check your connection and try again.";
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#030712] text-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-violet-500"></div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="min-h-screen bg-[#030712] text-white flex items-center justify-center">
        <p>Task not found</p>
      </div>
    );
  }

  // Parse options from description or strict field if available
  // Ensure backend sends options
  const options = task.options || [];

  return (
    <div className="min-h-screen bg-[#030712] text-white p-6">
       <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/dashboard/roadmap" className="text-slate-400 hover:text-white mb-4 inline-block text-sm">
            ← Back to Roadmap
          </Link>
          <h1 className="text-2xl font-bold mb-2">{task.title}</h1>
          <div className="flex gap-2">
            <span className="bg-violet-500/20 text-violet-300 px-2 py-0.5 rounded text-xs">MCQ</span>
            <span className="bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded text-xs">{task.difficulty}</span>
          </div>
        </div>

        {/* Question Card */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-6">
          <div className="prose prose-invert max-w-none mb-8">
             <div className="whitespace-pre-wrap">{task.description}</div>

             {task?.invariants_required?.length > 0 && (
                <div className="mt-6 p-4 rounded-xl bg-violet-500/5 border border-violet-500/20">
                  <h4 className="text-sm font-bold text-violet-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Mastery Goals
                  </h4>
                  <ul className="space-y-2">
                    {task.invariants_required.map((invariant, idx) => (
                      <li key={idx} className="text-sm text-slate-300 flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-violet-500 mt-1.5 shrink-0" />
                        {invariant}
                      </li>
                    ))}
                  </ul>
                </div>
             )}
             
             {(persistedHint || task.hint) && (
                <details className="mt-6 border border-amber-500/20 bg-amber-500/5 rounded-lg overflow-hidden group">
                  <summary className="flex items-center gap-2 p-3 cursor-pointer select-none text-amber-400 hover:text-amber-300 transition-colors">
                    <svg className="w-5 h-5 group-open:rotate-90 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <span className="font-medium text-sm">Need a hint?</span>
                  </summary>
                  <div className="px-4 pb-4 pt-1 text-slate-300 text-sm leading-relaxed border-t border-amber-500/10">
                    {persistedHint || task.hint}
                  </div>
                </details>
             )}
          </div>

          <div className="space-y-3">
            {options.map((opt, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedOption(idx)}
                className={`w-full text-left p-4 rounded-lg border transition-all ${
                  selectedOption === idx
                    ? "bg-violet-600/20 border-violet-500 text-white"
                    : "bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-800"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                    selectedOption === idx ? "border-violet-500 bg-violet-500" : "border-slate-500"
                  }`}>
                    {selectedOption === idx && <div className="w-2 h-2 rounded-full bg-white" />}
                  </div>
                  <span>{opt}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Evaluation Result */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3"
            >
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </motion.div>
          )}

          {evaluation && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`mb-6 p-6 rounded-xl border ${
                evaluation.passed
                  ? "bg-emerald-500/10 border-emerald-500/20"
                  : "bg-red-500/10 border-red-500/20"
              }`}
            >
              <div className="flex items-start gap-4">
                <div className={`mt-1 p-2 rounded-lg ${
                  evaluation.passed ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
                }`}>
                  {evaluation.passed ? (
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                </div>
                <div className="flex-1">
                  <h3 className={`text-lg font-bold mb-1 ${
                    evaluation.passed ? "text-emerald-400" : "text-red-400"
                  }`}>
                    {evaluation.passed ? "Correct!" : "Incorrect"}
                  </h3>
                  <p className="text-slate-300 text-sm leading-relaxed mb-4">
                    {evaluation.feedback}
                  </p>
                  {evaluation.passed && (
                    <p className="text-xs text-emerald-500 font-medium">
                      Redirecting back to roadmap...
                    </p>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer */}
        <div className="flex justify-end">
          <button
            onClick={handleSubmit}
            disabled={selectedOption === null || submitting}
            className="px-6 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
          >
            {submitting ? "Submitting..." : "Submit Answer"}
          </button>
        </div>
      </div>
    </div>
  );
}
