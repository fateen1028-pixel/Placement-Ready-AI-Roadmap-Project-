"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { taskService } from "../../../../../services/task.service";

export default function ExplanationTaskPage({ params, searchParams }) {
  const router = useRouter();
  const unwrappedParams = use(params);
  const unwrappedSearchParams = use(searchParams);
  const taskId = unwrappedParams.taskId;
  const hint = unwrappedSearchParams?.hint;
  const querySlotId = unwrappedSearchParams?.slotId;

  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [persistedHint, setPersistedHint] = useState(null);
  const [explanationText, setExplanationText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
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

  const handleComplete = async () => {
    // Try to get slot ID from query params or task details
    const slotId = querySlotId || task?.slot_id;
    
    if (!slotId) {
      setError("Slot ID missing. Please refresh and try again.");
      return;
    }

    if (!explanationText.trim()) {
      setError("Please provide an explanation before submitting.");
      return;
    }

    try {
      setIsSubmitting(true);
      setEvaluation(null);
      setError(null);
      // Ensure payload matches strict backend handshake: { answer, language? }
      const response = await taskService.submitTask(slotId, taskId, { 
        answer: explanationText,
        language: "english" // For conceptual explanation
      });
      
      const evalData = response.evaluation;
      setEvaluation(evalData);

      if (evalData?.passed) {
        router.push("/dashboard");
      }
    } catch (error) {
      console.error("Failed to submit explanation:", error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || "Failed to submit explanation. Please try again.";
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
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

  return (
    <div className="min-h-screen bg-[#030712] text-white p-6">
       <div className="max-w-3xl mx-auto">
        {/* Remediation Banner */}
        {task.strategy === 'explanation' && (
          <div className="mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center shrink-0">
               <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5S19.832 5.477 21 6.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
               </svg>
            </div>
            <div>
              <h3 className="font-bold text-amber-400">Remediation Mode: Conceptual Review</h3>
              <p className="text-sm text-amber-200/70">Review this material carefully before retrying the challenge.</p>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="mb-8">
          <Link href="/dashboard/roadmap" className="text-slate-400 hover:text-white mb-4 inline-block text-sm">
            ← Back to Roadmap
          </Link>
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">{task.title}</h1>
            <span className="bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded text-xs font-mono uppercase">Explanation</span>
          </div>
        </div>

        {/* Content Card */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 mb-8 shadow-xl shadow-black/20">
          <div className="prose prose-invert max-w-none">
             <div className="whitespace-pre-wrap leading-relaxed text-slate-300 mb-10 pb-10 border-b border-slate-800/50">
                {task.description}

                {task?.invariants_required?.length > 0 && (
                  <div className="mt-8 p-4 rounded-xl bg-violet-500/5 border border-violet-500/20">
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
             </div>

             {/* Interactive Submission Form */}
             <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="block text-sm font-bold text-violet-400 uppercase tracking-widest">
                    Your Analysis & Explanation
                  </label>
                  <span className="text-[10px] text-slate-500 font-mono">HTML/Markdown supported</span>
                </div>
                <textarea
                  value={explanationText}
                  onChange={(e) => setExplanationText(e.target.value)}
                  placeholder="Summarize the key concepts or explain your logic here..."
                  disabled={isSubmitting}
                  className="w-full h-64 bg-slate-950/50 border border-slate-800 rounded-xl p-6 text-slate-200 focus:outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-500/30 transition-all resize-none leading-relaxed placeholder:text-slate-600 shadow-inner"
                />
                <p className="text-xs text-slate-500 flex items-center gap-1.5 px-1">
                   <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                   </svg>
                   Your response will be evaluated to verify conceptual understanding.
                </p>
             </div>

             {/* Evaluation Feedback Section */}
             <AnimatePresence>
               {error && (
                 <motion.div
                   initial={{ opacity: 0, y: 10 }}
                   animate={{ opacity: 1, y: 0 }}
                   exit={{ opacity: 0, y: -10 }}
                   className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3"
                 >
                   <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                   </svg>
                   {error}
                 </motion.div>
               )}

               {evaluation && (
                 <motion.div 
                   initial={{ opacity: 0, y: 10 }}
                   animate={{ opacity: 1, y: 0 }}
                   exit={{ opacity: 0, y: -10 }}
                   className={`mt-6 p-6 rounded-xl border ${
                     evaluation.passed 
                       ? "bg-emerald-500/10 border-emerald-500/20" 
                       : "bg-rose-500/10 border-rose-500/20"
                   }`}
                 >
                   <div className="flex items-center gap-3 mb-4">
                     <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                       evaluation.passed ? "bg-emerald-500/20 text-emerald-500" : "bg-rose-500/20 text-rose-500"
                     }`}>
                       {evaluation.passed ? (
                         <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                           <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                         </svg>
                       ) : (
                         <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                           <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                         </svg>
                       )}
                     </div>
                     <h4 className={`font-bold ${evaluation.passed ? "text-emerald-400" : "text-rose-400"}`}>
                       {evaluation.passed ? "Concept Mastered!" : "Improvement Needed"}
                     </h4>
                   </div>
                   
                   {evaluation.feedback && (
                     <div className="text-sm text-slate-300 leading-relaxed mb-4 whitespace-pre-wrap">
                       {evaluation.feedback}
                     </div>
                   )}

                   {evaluation.mastered_invariants?.length > 0 && evaluation.passed && (
                      <div className="mt-4 pt-4 border-t border-emerald-500/10">
                         <p className="text-xs font-bold text-emerald-500/60 uppercase tracking-widest mb-2">Invariants Verified</p>
                         <div className="flex flex-wrap gap-2">
                            {evaluation.mastered_invariants.map((inv, i) => (
                              <span key={i} className="px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-mono border border-emerald-500/20">
                                {inv}
                              </span>
                            ))}
                         </div>
                      </div>
                   )}

                   {evaluation.passed && (
                     <p className="mt-4 text-xs text-emerald-500/70 italic flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                        Successfully verified. Redirecting back to roadmap...
                     </p>
                   )}
                 </motion.div>
               )}
             </AnimatePresence>

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
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-4 border-t border-slate-800/50">
          <button
            onClick={handleComplete}
            disabled={isSubmitting || !explanationText.trim()}
            className="group px-8 py-3 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white rounded-xl font-bold transition-all flex items-center gap-3 shadow-lg shadow-violet-500/20 active:scale-95"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Submitting...</span>
              </>
            ) : (
              <>
                <span>Submit Explanation</span>
                <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
