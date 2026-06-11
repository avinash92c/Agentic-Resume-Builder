// import { useState, useRef, useEffect } from 'react';
// import AgentAPI from '../api/AgentAPI';

// // ─── Types ────────────────────────────────────────────────────────────────────

// type Stage =
//   | 'input'          // waiting for raw skills text
//   | 'questions'      // AskQuestions node — show Q&A form
//   | 'review'         // PresentForReview node — show draft
//   | 'refinement'     // AskRefinements node — show refinement question
//   | 'done';          // StoreDB → __end__

// interface HistoryEntry {
//   type: 'raw_input' | 'qa' | 'draft' | 'refinement_q' | 'refinement_a';
//   label: string;
//   content: string | Record<string, string>;
//   timestamp: string;
// }

// interface AgentPayload {
//   thread_id?: string;
//   questions?: string[];
//   draft?: string;
//   refinement_question?: string;
//   message?: string;
//   complete?: boolean;
// }

// // ─── Helpers ──────────────────────────────────────────────────────────────────

// const now = () =>
//   new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

// // ─── Sub-components ───────────────────────────────────────────────────────────

// const StageBadge = ({ stage }: { stage: Stage }) => {
//   const map: Record<Stage, { label: string; color: string; bg: string }> = {
//     input:      { label: 'Raw input',      color: '#444441', bg: '#F1EFE8' },
//     questions:  { label: 'Clarifying',     color: '#0C447C', bg: '#E6F1FB' },
//     review:     { label: 'Review draft',   color: '#633806', bg: '#FAEEDA' },
//     refinement: { label: 'Refining',       color: '#712B13', bg: '#FAECE7' },
//     done:       { label: 'Complete',       color: '#085041', bg: '#E1F5EE' },
//   };
//   const s = map[stage];
//   return (
//     <span style={{
//       fontSize: 11,
//       fontWeight: 500,
//       padding: '2px 8px',
//       borderRadius: 99,
//       background: s.bg,
//       color: s.color,
//       letterSpacing: '0.02em',
//     }}>
//       {s.label}
//     </span>
//   );
// };

// const HistoryBlock = ({ entries }: { entries: HistoryEntry[] }) => {
//   if (!entries.length) return null;
//   return (
//     <div style={{ marginTop: 24 }}>
//       <p style={{ fontSize: 11, fontWeight: 500, color: 'var(--color-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 12px' }}>
//         Session history
//       </p>
//       <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
//         {entries.map((e, i) => (
//           <div key={i} style={{
//             background: 'var(--color-background-secondary)',
//             border: '0.5px solid var(--color-border-tertiary)',
//             borderRadius: 'var(--border-radius-md)',
//             padding: '10px 14px',
//           }}>
//             <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
//               <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-secondary)' }}>{e.label}</span>
//               <span style={{ fontSize: 11, color: 'var(--color-text-tertiary)', marginLeft: 'auto' }}>{e.timestamp}</span>
//             </div>
//             {typeof e.content === 'string' ? (
//               <pre style={{
//                 margin: 0,
//                 fontSize: 12,
//                 color: 'var(--color-text-secondary)',
//                 whiteSpace: 'pre-wrap',
//                 wordBreak: 'break-word',
//                 fontFamily: 'var(--font-mono)',
//                 lineHeight: 1.6,
//               }}>{e.content}</pre>
//             ) : (
//               <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
//                 {Object.entries(e.content).map(([q, a]) => (
//                   <div key={q}>
//                     <p style={{ margin: '0 0 2px', fontSize: 12, color: 'var(--color-text-tertiary)' }}>Q: {q}</p>
//                     <p style={{ margin: 0, fontSize: 12, color: 'var(--color-text-secondary)' }}>A: {a}</p>
//                   </div>
//                 ))}
//               </div>
//             )}
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// };

// // ─── Main component ───────────────────────────────────────────────────────────

// const Skills = () => {
//   const [stage, setStage] = useState<Stage>('input');
//   const [loading, setLoading] = useState(false);
//   const [threadId, setThreadId] = useState('');
//   const [history, setHistory] = useState<HistoryEntry[]>([]);

//   // Stage-specific state
//   const [rawSkills, setRawSkills] = useState('');
//   const [questions, setQuestions] = useState<string[]>([]);
//   const [answers, setAnswers] = useState<Record<string, string>>({});
//   const [draft, setDraft] = useState('');
//   const [refinementQuestion, setRefinementQuestion] = useState('');
//   const [refinementAnswer, setRefinementAnswer] = useState('');
//   const [draftVersion, setDraftVersion] = useState(0);
//   const [errorMsg, setErrorMsg] = useState('');

//   const bottomRef = useRef<HTMLDivElement>(null);

//   useEffect(() => {
//     bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
//   }, [stage, history]);

//   const pushHistory = (entry: HistoryEntry) =>
//     setHistory(prev => [...prev, entry]);

//   const handlePayload = (payload: AgentPayload) => {
//     setErrorMsg('');
//     if (payload.questions?.length) {
//       setQuestions(payload.questions);
//       setAnswers({});
//       setStage('questions');
//     }
//     if (payload.draft) {
//       setDraft(payload.draft);
//       setDraftVersion(v => v + 1);
//     }
//     if (payload.draft && !payload.questions?.length && !payload.refinement_question) {
//       setStage('review');
//     }
//     if (payload.refinement_question) {
//       setRefinementQuestion(payload.refinement_question);
//       setRefinementAnswer('');
//       setStage('refinement');
//     }
//     if (payload.complete) {
//       setStage('done');
//     }
//   };

//   // ── Node handlers ──────────────────────────────────────────────────────────

//   const handleStart = async () => {
//     if (!rawSkills.trim()) { setErrorMsg('Please enter your skills.'); return; }
//     setLoading(true);
//     setErrorMsg('');
//     try {
//       const email = localStorage.getItem('email') || 'JOhn@example.com';
//       const res = await AgentAPI.start('skills', { email, user_input: rawSkills });
//       const data = res.data;
//       setThreadId(data.thread_id);
//       pushHistory({ type: 'raw_input', label: 'Skills submitted', content: rawSkills, timestamp: now() });
//       handlePayload(data);
//     } catch {
//       setErrorMsg('Failed to start. Please try again.');
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleSubmitAnswers = async () => {
//     const incomplete = questions.some(q => !answers[q]?.trim());
//     if (incomplete) { setErrorMsg('Please answer all questions.'); return; }
//     setLoading(true);
//     setErrorMsg('');
//     const captured = { ...answers };
//     try {
//       pushHistory({ type: 'qa', label: 'Questions answered', content: captured, timestamp: now() });
//       const res = await AgentAPI.resume('skills', { thread_id: threadId, user_data: captured });
//       handlePayload(res.data);
//     } catch {
//       setErrorMsg('Failed to submit answers.');
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleApprove = async () => {
//     setLoading(true);
//     setErrorMsg('');
//     try {
//       pushHistory({ type: 'draft', label: `Draft v${draftVersion} approved`, content: draft, timestamp: now() });
//       const res = await AgentAPI.resume('skills', { thread_id: threadId, user_data: { approved: true } });
//       handlePayload({ ...res.data, complete: res.data.complete ?? true });
//     } catch {
//       setErrorMsg('Failed to approve.');
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleRequestRefinement = async () => {
//     setLoading(true);
//     setErrorMsg('');
//     try {
//       pushHistory({ type: 'draft', label: `Draft v${draftVersion} — refinement requested`, content: draft, timestamp: now() });
//       const res = await AgentAPI.resume('skills', { thread_id: threadId, user_data: { approved: false } });
//       handlePayload(res.data);
//     } catch {
//       setErrorMsg('Failed to request refinement.');
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleSubmitRefinement = async () => {
//     if (!refinementAnswer.trim()) { setErrorMsg('Please enter your refinement.'); return; }
//     setLoading(true);
//     setErrorMsg('');
//     const captured = refinementAnswer;
//     try {
//       pushHistory({ type: 'refinement_q', label: 'Refinement question', content: refinementQuestion, timestamp: now() });
//       pushHistory({ type: 'refinement_a', label: 'Your refinement answer', content: captured, timestamp: now() });
//       const res = await AgentAPI.resume('skills', { thread_id: threadId, user_data: { refinement: captured } });
//       handlePayload(res.data);
//     } catch {
//       setErrorMsg('Failed to submit refinement.');
//     } finally {
//       setLoading(false);
//     }
//   };

//   // ── Render ─────────────────────────────────────────────────────────────────

//   return (
//     <div style={{ maxWidth: 720, margin: '0 auto', padding: '32px 24px', fontFamily: 'var(--font-sans)' }}>

//       {/* Header */}
//       <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32 }}>
//         <div>
//           <h1 style={{ margin: 0, fontSize: 22, fontWeight: 500, color: 'var(--color-text-primary)' }}>Skills</h1>
//           <p style={{ margin: '2px 0 0', fontSize: 14, color: 'var(--color-text-secondary)' }}>
//             The agent will clarify, draft, and refine your skills profile.
//           </p>
//         </div>
//         <div style={{ marginLeft: 'auto' }}>
//           <StageBadge stage={stage} />
//         </div>
//       </div>

//       {/* ── STAGE: input ──────────────────────────────────────────────────── */}
//       {stage === 'input' && (
//         <div style={{
//           background: 'var(--color-background-primary)',
//           border: '0.5px solid var(--color-border-tertiary)',
//           borderRadius: 'var(--border-radius-lg)',
//           padding: '20px 24px',
//         }}>
//           <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
//             Raw skills text
//           </label>
//           <textarea
//             value={rawSkills}
//             onChange={e => setRawSkills(e.target.value)}
//             rows={8}
//             placeholder="Paste or type your skills in any format — bullet points, paragraphs, or comma-separated lists. The agent will structure them for you."
//             style={{ width: '100%', boxSizing: 'border-box', resize: 'vertical', fontFamily: 'var(--font-sans)', fontSize: 14 }}
//           />
//           {errorMsg && <p style={{ margin: '8px 0 0', fontSize: 13, color: 'var(--color-text-danger)' }}>{errorMsg}</p>}
//           <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
//             <button onClick={handleStart} disabled={loading} style={{ minWidth: 140 }}>
//               {loading ? 'Starting…' : 'Start agent'}
//               {!loading && <i className="ti ti-arrow-right" style={{ marginLeft: 6, fontSize: 14 }} aria-hidden="true" />}
//             </button>
//           </div>
//         </div>
//       )}

//       {/* ── Locked input (visible in all later stages) ────────────────────── */}
//       {stage !== 'input' && (
//         <div style={{
//           background: 'var(--color-background-secondary)',
//           border: '0.5px solid var(--color-border-tertiary)',
//           borderRadius: 'var(--border-radius-lg)',
//           padding: '14px 18px',
//           marginBottom: 20,
//         }}>
//           <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
//             <i className="ti ti-lock" style={{ fontSize: 14, color: 'var(--color-text-tertiary)' }} aria-hidden="true" />
//             <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-tertiary)' }}>Submitted skills</span>
//           </div>
//           <pre style={{
//             margin: 0, fontSize: 13,
//             color: 'var(--color-text-secondary)',
//             whiteSpace: 'pre-wrap', wordBreak: 'break-word',
//             fontFamily: 'var(--font-mono)', lineHeight: 1.6,
//             maxHeight: 120, overflowY: 'auto',
//           }}>{rawSkills}</pre>
//         </div>
//       )}

//       {/* ── STAGE: questions ──────────────────────────────────────────────── */}
//       {stage === 'questions' && (
//         <div style={{
//           background: 'var(--color-background-primary)',
//           border: '0.5px solid var(--color-border-tertiary)',
//           borderRadius: 'var(--border-radius-lg)',
//           padding: '20px 24px',
//         }}>
//           <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
//             <i className="ti ti-help-circle" style={{ fontSize: 16, color: 'var(--color-text-info)' }} aria-hidden="true" />
//             <span style={{ fontSize: 14, fontWeight: 500 }}>A few clarifying questions</span>
//           </div>
//           <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
//             {questions.map((q, i) => (
//               <div key={q}>
//                 <label style={{ display: 'block', fontSize: 13, color: 'var(--color-text-primary)', marginBottom: 6, lineHeight: 1.5 }}>
//                   <span style={{ fontWeight: 500, color: 'var(--color-text-tertiary)', marginRight: 6 }}>{i + 1}.</span>
//                   {q}
//                 </label>
//                 <textarea
//                   rows={2}
//                   value={answers[q] || ''}
//                   onChange={e => setAnswers(prev => ({ ...prev, [q]: e.target.value }))}
//                   placeholder="Your answer…"
//                   style={{ width: '100%', boxSizing: 'border-box', resize: 'vertical', fontFamily: 'var(--font-sans)', fontSize: 13 }}
//                 />
//               </div>
//             ))}
//           </div>
//           {errorMsg && <p style={{ margin: '12px 0 0', fontSize: 13, color: 'var(--color-text-danger)' }}>{errorMsg}</p>}
//           <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end' }}>
//             <button onClick={handleSubmitAnswers} disabled={loading} style={{ minWidth: 140 }}>
//               {loading ? 'Submitting…' : 'Submit answers'}
//             </button>
//           </div>
//         </div>
//       )}

//       {/* ── STAGE: review ─────────────────────────────────────────────────── */}
//       {stage === 'review' && (
//         <div style={{
//           background: 'var(--color-background-primary)',
//           border: '0.5px solid var(--color-border-tertiary)',
//           borderRadius: 'var(--border-radius-lg)',
//           padding: '20px 24px',
//         }}>
//           <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
//             <i className="ti ti-file-text" style={{ fontSize: 16, color: 'var(--color-text-warning)' }} aria-hidden="true" />
//             <span style={{ fontSize: 14, fontWeight: 500 }}>Draft ready for review</span>
//             {draftVersion > 1 && (
//               <span style={{
//                 fontSize: 11, padding: '1px 7px', borderRadius: 99,
//                 background: '#FAEEDA', color: '#633806', marginLeft: 4,
//               }}>v{draftVersion}</span>
//             )}
//           </div>
//           <p style={{ margin: '0 0 16px', fontSize: 13, color: 'var(--color-text-secondary)' }}>
//             Review the drafted skills profile below. Approve to save or request refinement.
//           </p>
//           <div style={{
//             background: 'var(--color-background-secondary)',
//             border: '0.5px solid var(--color-border-tertiary)',
//             borderRadius: 'var(--border-radius-md)',
//             padding: '14px 16px',
//             marginBottom: 20,
//           }}>
//             <pre style={{
//               margin: 0, fontSize: 13,
//               color: 'var(--color-text-primary)',
//               whiteSpace: 'pre-wrap', wordBreak: 'break-word',
//               fontFamily: 'var(--font-mono)', lineHeight: 1.7,
//             }}>{draft}</pre>
//           </div>
//           {errorMsg && <p style={{ margin: '0 0 12px', fontSize: 13, color: 'var(--color-text-danger)' }}>{errorMsg}</p>}
//           <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
//             <button onClick={handleRequestRefinement} disabled={loading}>
//               {loading ? '…' : 'Request refinement'}
//             </button>
//             <button onClick={handleApprove} disabled={loading} style={{ fontWeight: 500 }}>
//               {loading ? 'Approving…' : 'Approve'}
//               {!loading && <i className="ti ti-check" style={{ marginLeft: 6, fontSize: 14 }} aria-hidden="true" />}
//             </button>
//           </div>
//         </div>
//       )}

//       {/* ── STAGE: refinement ─────────────────────────────────────────────── */}
//       {stage === 'refinement' && (
//         <div style={{
//           background: 'var(--color-background-primary)',
//           border: '0.5px solid var(--color-border-tertiary)',
//           borderRadius: 'var(--border-radius-lg)',
//           padding: '20px 24px',
//         }}>
//           <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
//             <i className="ti ti-edit" style={{ fontSize: 16, color: 'var(--color-text-danger)' }} aria-hidden="true" />
//             <span style={{ fontSize: 14, fontWeight: 500 }}>Refinement</span>
//           </div>

//           {/* Show the current draft for reference */}
//           {draft && (
//             <div style={{
//               background: 'var(--color-background-secondary)',
//               border: '0.5px solid var(--color-border-tertiary)',
//               borderRadius: 'var(--border-radius-md)',
//               padding: '10px 14px',
//               marginBottom: 16,
//             }}>
//               <p style={{ margin: '0 0 6px', fontSize: 11, fontWeight: 500, color: 'var(--color-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Current draft</p>
//               <pre style={{
//                 margin: 0, fontSize: 12,
//                 color: 'var(--color-text-secondary)',
//                 whiteSpace: 'pre-wrap', wordBreak: 'break-word',
//                 fontFamily: 'var(--font-mono)', lineHeight: 1.6,
//                 maxHeight: 100, overflowY: 'auto',
//               }}>{draft}</pre>
//             </div>
//           )}

//           <label style={{ display: 'block', fontSize: 13, color: 'var(--color-text-primary)', marginBottom: 8, lineHeight: 1.5 }}>
//             {refinementQuestion}
//           </label>
//           <textarea
//             rows={4}
//             value={refinementAnswer}
//             onChange={e => setRefinementAnswer(e.target.value)}
//             placeholder="Describe what you'd like changed…"
//             style={{ width: '100%', boxSizing: 'border-box', resize: 'vertical', fontFamily: 'var(--font-sans)', fontSize: 13 }}
//           />
//           {errorMsg && <p style={{ margin: '8px 0 0', fontSize: 13, color: 'var(--color-text-danger)' }}>{errorMsg}</p>}
//           <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
//             <button onClick={handleSubmitRefinement} disabled={loading} style={{ minWidth: 140 }}>
//               {loading ? 'Submitting…' : 'Submit refinement'}
//             </button>
//           </div>
//         </div>
//       )}

//       {/* ── STAGE: done ───────────────────────────────────────────────────── */}
//       {stage === 'done' && (
//         <div style={{
//           background: '#E1F5EE',
//           border: '0.5px solid #5DCAA5',
//           borderRadius: 'var(--border-radius-lg)',
//           padding: '20px 24px',
//           display: 'flex',
//           alignItems: 'flex-start',
//           gap: 14,
//         }}>
//           <i className="ti ti-circle-check" style={{ fontSize: 22, color: '#0F6E56', marginTop: 1, flexShrink: 0 }} aria-hidden="true" />
//           <div>
//             <p style={{ margin: '0 0 4px', fontWeight: 500, fontSize: 15, color: '#085041' }}>Skills profile saved</p>
//             <p style={{ margin: 0, fontSize: 13, color: '#0F6E56' }}>
//               Your skills have been reviewed and stored successfully.
//             </p>
//           </div>
//         </div>
//       )}

//       {/* ── History ───────────────────────────────────────────────────────── */}
//       <HistoryBlock entries={history} />

//       <div ref={bottomRef} />
//     </div>
//   );
// };

// export default Skills;