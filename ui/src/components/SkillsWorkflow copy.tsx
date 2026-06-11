// import React, { useState } from 'react';
// import { skillsApi, AgentResponse } from '../api/skillsApi';

// type Step = 'INPUT' | 'INTERVIEW' | 'REVIEW' | 'COMPLETED';

// export default function SkillsWorkflow() {
//   // Graph Routing & Control States
//   const [currentStep, setCurrentStep] = useState<Step>('INPUT');
//   const [threadId, setThreadId] = useState<string | null>(null);
//   const [loading, setLoading] = useState<boolean>(false);
//   const [error, setError] = useState<string | null>(null);

//   // Data Ingestion States
//   const [rawInput, setRawInput] = useState<string>('');
//   const [questions, setQuestions] = useState<string[]>([]);
//   const [answers, setAnswers] = useState<Record<string, string>>({});
//   const [latestDraft, setLatestDraft] = useState<string>('');
//   const [refinementFeedback, setRefinementFeedback] = useState<string>('');
//   const [refinementCount, setRefinementCount] = useState<number>(0);

//   // 1. Kick off the Graph
//   const handleStart = async () => {
//     if (!rawInput.trim()) return;
//     setLoading(true);
//     setError(null);
//     try {
//       const data = await skillsApi.startWorkflow({ skills_raw: rawInput });
//       setThreadId(data.thread_id);
//       if (data.refinement_questions && data.refinement_questions.length > 0) {
//         setQuestions(data.refinement_questions);
//         setCurrentStep('INTERVIEW');
//       } else {
//         // Fallback if graph goes directly to a draft
//         setLatestDraft(data.drafts?.[data.drafts.length - 1] || '');
//         setCurrentStep('REVIEW');
//       }
//     } catch (err: any) {
//       setError(err.response?.data?.detail || 'Failed to start skill identification workflow.');
//     } finally {
//       setLoading(false);
//     }
//   };

//   // 2. Submit Answers back to the Interrupt
//   const handleAnswersSubmit = async (e: React.FormEvent) => {
//     e.preventDefault();
//     if (!threadId) return;
//     setLoading(true);
//     setError(null);
//     try {
//       const data = await skillsApi.resumeWorkflow({
//         thread_id: threadId,
//         user_data: { answers }
//       });
      
//       const draftsArray = data.drafts || [];
//       if (draftsArray.length > 0) {
//         setLatestDraft(draftsArray[draftsArray.length - 1]);
//         setRefinementCount(data.refinement_counts || 0);
//         setCurrentStep('REVIEW');
//       }
//     } catch (err: any) {
//       setError(err.response?.data?.detail || 'Failed to submit interview answers.');
//     } finally {
//       setLoading(false);
//     }
//   };

//   // 3. Approve Draft or Request Refinement Iteration
//   const handleReviewAction = async (isApproved: boolean) => {
//     if (!threadId) return;
//     setLoading(true);
//     setError(null);
//     try {
//       const data = await skillsApi.resumeWorkflow({
//         thread_id: threadId,
//         user_data: {
//           is_approved: isApproved,
//           refinement_feedback: isApproved ? undefined : refinementFeedback
//         }
//       });

//       if (isApproved) {
//         setCurrentStep('COMPLETED');
//       } else {
//         // Agent returned an adjusted draft based on refinement prompt loops
//         const draftsArray = data.drafts || [];
//         setLatestDraft(draftsArray[draftsArray.length - 1]);
//         setRefinementCount(data.refinement_counts || 0);
//         setRefinementFeedback(''); // Reset input text field
//       }
//     } catch (err: any) {
//       setError(err.response?.data?.detail || 'Failed to process revision request.');
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div style={{ maxWidth: '750px', margin: '40px auto', padding: '20px', fontFamily: 'sans-serif' }}>
//       <h2 style={{ borderBottom: '2px solid #eaeaea', paddingBottom: '10px' }}>
//         Agentic Skill Builder Workspace
//       </h2>

//       {/* Progress Tracker Status Bar */}
//       <div style={{ display: 'flex', gap: '20px', marginBottom: '30px', color: '#666', fontSize: '14px' }}>
//         <span style={{ fontWeight: currentStep === 'INPUT' ? 'bold' : 'normal', color: currentStep === 'INPUT' ? '#0066cc' : '#666' }}>1. Initial Input</span>
//         <span>→</span>
//         <span style={{ fontWeight: currentStep === 'INTERVIEW' ? 'bold' : 'normal', color: currentStep === 'INTERVIEW' ? '#0066cc' : '#666' }}>2. Context Interview</span>
//         <span>→</span>
//         <span style={{ fontWeight: currentStep === 'REVIEW' ? 'bold' : 'normal', color: currentStep === 'REVIEW' ? '#0066cc' : '#666' }}>3. Review & Refine</span>
//       </div>

//       {error && (
//         <div style={{ backgroundColor: '#fff0f0', color: '#cc0000', padding: '12px', borderRadius: '4px', marginBottom: '20px' }}>
//           <strong>Error:</strong> {error}
//         </div>
//       )}

//       {/* STAGE 1: RAW INGESTION */}
//       {currentStep === 'INPUT' && (
//         <div>
//           <p>Provide your skills, technologies, or past tool stack experience. The AI agent will break down technical depths.</p>
//           <textarea
//             style={{ width: '100%', height: '140px', padding: '10px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }}
//             placeholder="e.g., Python, SQL, optimization of queries, data structures, built API backends using Fast API..."
//             value={rawInput}
//             onChange={(e) => setRawInput(e.target.value)}
//             disabled={loading}
//           />
//           <button
//             onClick={handleStart}
//             disabled={loading || !rawInput.trim()}
//             style={{ marginTop: '15px', padding: '10px 20px', cursor: 'pointer', backgroundColor: '#0066cc', color: '#fff', border: 'none', borderRadius: '4px' }}
//           >
//             {loading ? 'Agent Initializing...' : 'Analyze My Skills'}
//           </button>
//         </div>
//       )}

//       {/* STAGE 2: THE SYSTEM INTERRUPT / QUESTIONS STAGE */}
//       {currentStep === 'INTERVIEW' && (
//         <form onSubmit={handleAnswersSubmit}>
//           <div style={{ backgroundColor: '#f9f9f9', padding: '15px', borderRadius: '6px', marginBottom: '20px' }}>
//             <strong>Agent Analysis Note:</strong> To construct metric-driven resume action bullet points, please answer the targeted questions generated by the model.
//           </div>
          
//           {questions.map((question, index) => (
//             <div key={index} style={{ marginBottom: '20px' }}>
//               <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>{question}</label>
//               <input
//                 type="text"
//                 required
//                 style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }}
//                 placeholder="Provide details or metrics here..."
//                 value={answers[`question_${index + 1}`] || ''}
//                 onChange={(e) => setAnswers({ ...answers, [`question_${index + 1}`]: e.target.value })}
//                 disabled={loading}
//               />
//             </div>
//           ))}

//           <button
//             type="submit"
//             disabled={loading}
//             style={{ padding: '10px 20px', cursor: 'pointer', backgroundColor: '#0066cc', color: '#fff', border: 'none', borderRadius: '4px' }}
//           >
//             {loading ? 'Compiling Initial Draft...' : 'Generate Skill Profiles'}
//           </button>
//         </form>
//       )}

//       {/* STAGE 3: REVISION AND APPROVAL LOOP */}
//       {currentStep === 'REVIEW' && (
//         <div>
//           <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>Compiled Skill Section Draft:</label>
//           <div style={{ whiteSpace: 'pre-wrap', backgroundColor: '#f4f7f6', padding: '20px', borderRadius: '6px', borderLeft: '4px solid #00a86b', marginBottom: '25px', lineHeight: '1.6' }}>
//             {latestDraft}
//           </div>

//           <div style={{ borderTop: '1px solid #eee', paddingTop: '20px' }}>
//             <h4 style={{ margin: '0 0 10px 0' }}>Request Refinement Revisions ({refinementCount}/2 Turns Used)</h4>
            
//             {refinementCount < 2 ? (
//               <div style={{ marginBottom: '20px' }}>
//                 <input
//                   type="text"
//                   style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box', marginBottom: '10px' }}
//                   placeholder="e.g., Make the python metrics look stronger, or change framework mentions to Senior level..."
//                   value={refinementFeedback}
//                   onChange={(e) => setRefinementFeedback(e.target.value)}
//                   disabled={loading}
//                 />
//                 <button
//                   type="button"
//                   onClick={() => handleReviewAction(false)}
//                   disabled={loading || !refinementFeedback.trim()}
//                   style={{ padding: '8px 15px', backgroundColor: '#e0e0e0', color: '#333', border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '10px' }}
//                 >
//                   {loading ? 'Processing Refinement...' : 'Submit Revision Instruction'}
//                 </button>
//               </div>
//             ) : (
//               <p style={{ color: '#ff8c00', fontSize: '14px', marginBottom: '20px' }}>
//                 ⚠️ You have utilized all available refinement slots for this session. Please finalize current metrics.
//               </p>
//             )}

//             <button
//               type="button"
//               onClick={() => handleReviewAction(true)}
//               disabled={loading}
//               style={{ padding: '10px 25px', backgroundColor: '#00a86b', color: '#fff', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}
//             >
//               Approve and Save to Resume Base
//             </button>
//           </div>
//         </div>
//       )}

//       {/* STAGE 4: COMPLETED PIPELINE */}
//       {currentStep === 'COMPLETED' && (
//         <div style={{ textAlign: 'center', padding: '40px 20px' }}>
//           <div style={{ fontSize: '48px', marginBottom: '15px' }}>✅</div>
//           <h3>Skills Successfully Finalized!</h3>
//           <p style={{ color: '#666' }}>The section has been persisted upstream into your central document system via the execution graph's database router tool.</p>
//           <button
//             onClick={() => {
//               setCurrentStep('INPUT');
//               setRawInput('');
//               setAnswers({});
//               setQuestions([]);
//               setThreadId(null);
//             }}
//             style={{ marginTop: '20px', padding: '8px 16px', border: '1px solid #0066cc', color: '#0066cc', background: 'transparent', borderRadius: '4px', cursor: 'pointer' }}
//           >
//             Start New Section
//           </button>
//         </div>
//       )}
//     </div>
//   );
// }