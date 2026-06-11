import { useState, useRef, useEffect } from 'react';

import {
    Button,
    Card,
    Collapse,
    Divider,
    Form,
    Input,
    Layout,
    Space,
    Typography,
    message,
    Tag,
    Badge,
    Steps,
} from 'antd';

import {
    PlusOutlined,
    DeleteOutlined,
    CheckCircleOutlined,
    EditOutlined,
    FileTextOutlined,
    CheckOutlined,
} from '@ant-design/icons';

import AgentAPI from '../api/AgentAPI';

import type { WorkExperience } from '../types/models';
import type { AgentResponse, StartRequest } from '../types/agent';

import MessageBubble from '../components/agent/MessageBubble';
import QuestionForm from '../components/agent/QuestionForm';
import DraftReview from '../components/agent/DraftReview';
import RefinementInput from '../components/agent/RefinementInput';

const { Content } = Layout;

// ─── Types ────────────────────────────────────────────────────────────────────

type SessionEventKind = 'draft' | 'refinement' | 'approved';

interface SessionEvent {
    id: string;
    kind: SessionEventKind;
    /** For 'draft': the draft text. For 'refinement': the user's refinement note. For 'approved': label only. */
    content: string;
    /** Human-readable label shown in the timeline */
    label: string;
    timestamp: Date;
}

// ─── Component ────────────────────────────────────────────────────────────────


const WorkHistoryPage = () => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [threadId, setThreadId] = useState('');
    const [messages, setMessages] = useState<any[]>([]);
    const [questions, setQuestions] = useState<string[]>([]);
    const [answers, setAnswers] = useState<Record<string, string>>({});

    // Active (latest) draft only — used for the live DraftReview panel
    const [activeDraft, setActiveDraft] = useState<string>('');

    // FIX 4 & 9: Immutable session log — events never removed, always visible
    const [sessionLog, setSessionLog] = useState<SessionEvent[]>([]);
    const draftVersionCount = sessionLog.filter(e => e.kind === 'draft').length;

    const [refinementQuestion, setRefinementQuestion] = useState('');
    const [showRefinementInput, setShowRefinementInput] = useState(false);
    const [submittedExperiences, setSubmittedExperiences] = useState<WorkExperience[]>([]);

    const [agentStarted, setAgentStarted] = useState(false);
    const [isCompleted, setIsCompleted] = useState(false);

    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, questions, activeDraft, showRefinementInput, sessionLog]);

    // ── Helpers ───────────────────────────────────────────────────────────────

    const appendAssistantMessage = (content: string) => {
        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', content }]);
    };

    const appendUserMessage = (content: string) => {
        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'user', content }]);
    };

    const pushSessionEvent = (kind: SessionEventKind, content: string, label: string) => {
        setSessionLog(prev => [
            ...prev,
            { id: crypto.randomUUID(), kind, content, label, timestamp: new Date() },
        ]);
    };

    // ── Response handler ──────────────────────────────────────────────────────

    const handleResponse = (data: AgentResponse) => {
        if (!data.data) return;
        const payload = data.data;

        // FIX 2: Always clear questions first so old form unmounts cleanly
        setQuestions([]);
        setAnswers({});

        // QUESTIONS
        if (payload.questions?.length) {
            setQuestions(payload.questions);
            appendAssistantMessage('Please answer the following questions.');
        }

        // DRAFT
        // FIX 4 & 9: Push to immutable session log; update active draft separately.
        // activeDraft drives the live DraftReview panel.
        // sessionLog accumulates ALL draft versions — never cleared.
        if (payload.draft) {
            setActiveDraft(payload.draft);

            // Only add to log if different from last draft event
            setSessionLog(prev => {
                const lastDraft = [...prev].reverse().find(e => e.kind === 'draft');
                if (lastDraft?.content === payload.draft) return prev;
                const version = prev.filter(e => e.kind === 'draft').length + 1;
                return [
                    ...prev,
                    {
                        id: crypto.randomUUID(),
                        kind: 'draft',
                        content: payload.draft!,
                        label: `Draft v${version}`,
                        timestamp: new Date(),
                    },
                ];
            });

            if (!payload.questions?.length) {
                appendAssistantMessage('Draft generated. Please review.');
            }
        }

        // REFINEMENT
        // FIX 5: Only hide refinement input when explicitly not needed.
        // Do NOT hide it just because a new draft arrived — let the user
        // see the refinement panel until they explicitly submit it.
        if (payload.refinement_question) {
            setRefinementQuestion(payload.refinement_question);
            setShowRefinementInput(true);
            appendAssistantMessage(payload.refinement_question);
        }
        // NOTE: We intentionally do NOT set showRefinementInput=false here on
        // every response — only explicit actions (submitRefinement, approveDraft)
        // should close it.

        // MESSAGE
        if (payload.message) {
            appendAssistantMessage(payload.message);
        }
    };

    // ── Actions ───────────────────────────────────────────────────────────────

    const startWorkHistory = async (values: { experiences: WorkExperience[] }) => {
        try {
            setLoading(true);
            setSubmittedExperiences(values.experiences);
            setAgentStarted(true);

            const email = localStorage.getItem('email') || 'rahul@test.com';
            const payload: StartRequest<WorkExperience[]> = { email, user_input: values.experiences };
            const response = await AgentAPI.start('wh', payload);
            const data = response.data;

            setThreadId(data.thread_id);
            appendUserMessage('Submitted work history details.');
            handleResponse(data);
        } catch {
            message.error('Failed to start work history flow');
        } finally {
            setLoading(false);
        }
    };

    const submitAnswers = async () => {
        try {
            setLoading(true);
            const currentAnswers = { ...answers };

            Object.entries(currentAnswers).forEach(([question, answer]) => {
                appendUserMessage(`Q: ${question}\n\nA: ${answer}`);
            });

            setQuestions([]);
            setAnswers({});

            const response = await AgentAPI.resume('wh', {
                thread_id: threadId,
                user_data: currentAnswers,
            });

            handleResponse(response.data);
        } catch {
            message.error('Failed to submit answers');
        } finally {
            setLoading(false);
        }
    };

    const approveDraft = async () => {
        try {
            setLoading(true);
            appendUserMessage('Approved this draft.');

            const response = await AgentAPI.resume('wh', {
                thread_id: threadId,
                user_data: { approved: true },
            });

            // FIX 4 & 9: Record the approval in the session log before clearing active draft
            pushSessionEvent('approved', activeDraft, `Draft v${draftVersionCount} — Approved ✓`);

            handleResponse(response.data);

            if (response.data.complete) {
                setQuestions([]);
                setShowRefinementInput(false);
                setRefinementQuestion('');
                setActiveDraft('');
                setIsCompleted(true);
                message.success('Work history completed successfully');
            }
        } catch {
            message.error('Failed to approve draft');
        } finally {
            setLoading(false);
        }
    };

    const requestRefinement = async () => {
        try {
            setLoading(true);
            appendUserMessage('Requesting refinement.');

            const response = await AgentAPI.resume('wh', {
                thread_id: threadId,
                user_data: { approved: false },
            });

            handleResponse(response.data);
        } catch {
            message.error('Failed to request refinement');
        } finally {
            setLoading(false);
        }
    };

    const submitRefinement = async (refinement: string) => {
        try {
            setLoading(true);
            appendUserMessage(refinement);

            // FIX 5 & 9: Log the refinement note before closing the panel
            pushSessionEvent('refinement', refinement, `Refinement Request`);

            // Now safe to hide — user explicitly submitted
            setShowRefinementInput(false);
            setRefinementQuestion('');

            const response = await AgentAPI.resume('wh', {
                thread_id: threadId,
                user_data: { refinement },
            });

            handleResponse(response.data);
        } catch {
            message.error('Failed to submit refinement');
        } finally {
            setLoading(false);
        }
    };

    // ── Derived UI helpers ────────────────────────────────────────────────────

    // Whether the live DraftReview panel should be shown
    const showDraftReview =
        !!activeDraft &&
        questions.length === 0 &&
        !showRefinementInput &&
        !isCompleted;

    // ── Render ────────────────────────────────────────────────────────────────

    return (
        <Layout style={{ height: '100%', background: '#fff' }}>
            <Content style={{ maxWidth: 1100, margin: '0 auto', padding: 24, width: '100%' }}>

                {/* ── Page header ─────────────────────────────────────────── */}
                <div style={{ marginBottom: 24 }}>
                    <Typography.Title level={2}>Work History</Typography.Title>
                    <Typography.Text type="secondary">
                        Add your companies and projects. The AI agent will refine each project one by one.
                    </Typography.Text>
                </div>

                {/* ── Input form (always visible; locked after start) ──────── */}
                <Card
                    title={
                        agentStarted ? (
                            <Space>
                                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                                <span>Submitted Work History</span>
                                <Tag color="green">Locked</Tag>
                            </Space>
                        ) : 'Work History Input'
                    }
                >
                    <Form
                        form={form}
                        layout="vertical"
                        onFinish={startWorkHistory}
                        disabled={agentStarted}
                    >
                        <Form.List name="experiences" initialValue={[{}]}>
                            {(companyFields, { add: addCompany, remove: removeCompany }) => (
                                <>
                                    <Collapse
                                        defaultActiveKey={['0']}
                                        items={companyFields.map((companyField, companyIndex) => ({
                                            key: String(companyIndex),
                                            label: (
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <span>Company {companyIndex + 1}</span>
                                                    {companyFields.length > 1 && !agentStarted && (
                                                        <Button
                                                            danger size="small"
                                                            icon={<DeleteOutlined />}
                                                            onClick={e => { e.stopPropagation(); removeCompany(companyField.name); }}
                                                        >
                                                            Remove
                                                        </Button>
                                                    )}
                                                </div>
                                            ),
                                            children: (
                                                <>
                                                    <Form.Item label="Company Name" name={[companyField.name, 'company_name']} rules={[{ required: true }]}>
                                                        <Input placeholder="ABC Bank" />
                                                    </Form.Item>
                                                    <Form.Item label="Job Title" name={[companyField.name, 'job_title']} rules={[{ required: true }]}>
                                                        <Input placeholder="Senior RPA Developer" />
                                                    </Form.Item>
                                                    <Space style={{ display: 'flex' }}>
                                                        <Form.Item label="Start Date" name={[companyField.name, 'start_date']} rules={[{ required: true }]}>
                                                            <Input placeholder="2020-01" />
                                                        </Form.Item>
                                                        <Form.Item label="End Date" name={[companyField.name, 'end_date']} rules={[{ required: true }]}>
                                                            <Input placeholder="Present" />
                                                        </Form.Item>
                                                    </Space>
                                                    <Form.Item label="Employment Type" name={[companyField.name, 'employment_type']}>
                                                        <Input placeholder="Full Time" />
                                                    </Form.Item>

                                                    <Divider>Projects</Divider>

                                                    <Form.List name={[companyField.name, 'projects']} initialValue={['']}>
                                                        {(projectFields, { add: addProject, remove: removeProject }) => (
                                                            <>
                                                                {projectFields.map(projectField => (
                                                                    <Card key={projectField.key} size="small" style={{ marginBottom: 12 }}>
                                                                        <Form.Item
                                                                            label="Raw Project Description"
                                                                            name={[projectField.name]}
                                                                            rules={[{ required: true }]}
                                                                        >
                                                                            <Input.TextArea rows={5} placeholder="Paste rough project details here..." />
                                                                        </Form.Item>
                                                                        {projectFields.length > 1 && !agentStarted && (
                                                                            <Button danger icon={<DeleteOutlined />} onClick={() => removeProject(projectField.name)}>
                                                                                Remove Project
                                                                            </Button>
                                                                        )}
                                                                    </Card>
                                                                ))}
                                                                {!agentStarted && (
                                                                    <Button type="dashed" block icon={<PlusOutlined />} onClick={() => addProject()}>
                                                                        Add Project
                                                                    </Button>
                                                                )}
                                                            </>
                                                        )}
                                                    </Form.List>
                                                </>
                                            ),
                                        }))}
                                    />
                                    {!agentStarted && (
                                        <Button type="dashed" block icon={<PlusOutlined />} style={{ marginTop: 16 }} onClick={() => addCompany()}>
                                            Add Another Company
                                        </Button>
                                    )}
                                </>
                            )}
                        </Form.List>

                        <Divider />

                        {!agentStarted && (
                            <Button type="primary" htmlType="submit" size="large" loading={loading} block>
                                Start Work History Agent
                            </Button>
                        )}
                    </Form>
                </Card>

                {/* ── Message thread ───────────────────────────────────────── */}
                {messages.length > 0 && (
                    <div style={{ marginTop: 24 }}>
                        {messages.map(msg => (
                            <MessageBubble key={msg.id} message={msg} />
                        ))}
                    </div>
                )}

                {/* ── Questions form ───────────────────────────────────────── */}
                {questions.length > 0 && (
                    <QuestionForm
                        questions={questions}
                        answers={answers}
                        setAnswers={setAnswers}
                        onSubmit={submitAnswers}
                        loading={loading}
                    />
                )}

                {/* ── FIX 4 & 9: Session log — ALWAYS visible once populated ─ */}
                {/* Shows every draft version + refinement notes + approvals.    */}
                {/* This panel is NEVER cleared — it persists for the full session */}
                {sessionLog.length > 0 && (
                    <Card
                        style={{ marginTop: 24 }}
                        styles={{ body: { padding: 0 } }}
                        title={
                            <Space>
                                <FileTextOutlined />
                                <span>Session Log</span>
                                <Badge count={sessionLog.length} color="#722ed1" />
                            </Space>
                        }
                    >
                        <Steps
                            direction="vertical"
                            style={{ padding: '16px 24px' }}
                            items={sessionLog.map((event, idx) => {
                                const isLatest = idx === sessionLog.length - 1;

                                const icon =
                                    event.kind === 'approved' ? (
                                        <CheckOutlined style={{ color: '#52c41a' }} />
                                    ) : event.kind === 'refinement' ? (
                                        <EditOutlined style={{ color: '#1677ff' }} />
                                    ) : (
                                        <FileTextOutlined style={{ color: '#722ed1' }} />
                                    );

                                const status =
                                    event.kind === 'approved'
                                        ? 'finish'
                                        : isLatest && !isCompleted
                                        ? 'process'
                                        : 'finish';

                                return {
                                    title: (
                                        <Space>
                                            <Typography.Text strong>{event.label}</Typography.Text>
                                            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                                                {event.timestamp.toLocaleTimeString()}
                                            </Typography.Text>
                                            {isLatest && !isCompleted && event.kind === 'draft' && (
                                                <Tag color="blue">Current</Tag>
                                            )}
                                            {event.kind === 'approved' && (
                                                <Tag color="green">Approved</Tag>
                                            )}
                                        </Space>
                                    ),
                                    status,
                                    icon,
                                    description: (
                                        <details style={{ marginTop: 4, marginBottom: 8 }}>
                                            <summary
                                                style={{
                                                    cursor: 'pointer',
                                                    color: '#888',
                                                    fontSize: 12,
                                                    userSelect: 'none',
                                                }}
                                            >
                                                {event.kind === 'refinement'
                                                    ? 'View refinement note'
                                                    : event.kind === 'approved'
                                                    ? 'View approved draft'
                                                    : 'View draft content'}
                                            </summary>
                                            <pre
                                                style={{
                                                    marginTop: 8,
                                                    whiteSpace: 'pre-wrap',
                                                    fontSize: 12,
                                                    color: event.kind === 'refinement' ? '#1677ff' : '#555',
                                                    background: event.kind === 'refinement' ? '#f0f5ff' : '#fafafa',
                                                    border: `1px solid ${event.kind === 'refinement' ? '#adc6ff' : '#f0f0f0'}`,
                                                    padding: '10px 14px',
                                                    borderRadius: 6,
                                                    lineHeight: 1.6,
                                                }}
                                            >
                                                {event.content}
                                            </pre>
                                        </details>
                                    ),
                                };
                            })}
                        />
                    </Card>
                )}

                {/* ── Live Draft Review panel ──────────────────────────────── */}
                {/* Only shown when: active draft exists, no pending questions,  */}
                {/* no refinement input open, not yet completed.                 */}
                {showDraftReview && (
                    <DraftReview
                        draft={activeDraft}
                        onApprove={approveDraft}
                        onRefine={requestRefinement}
                        loading={loading}
                    />
                )}

                {/* ── Refinement input ─────────────────────────────────────── */}
                {/* FIX 5: Driven only by showRefinementInput.                  */}
                {/* Never auto-closed by handleResponse — only by submitRefinement / approveDraft */}
                {showRefinementInput && questions.length === 0 && !isCompleted && (
                    <RefinementInput
                        question={refinementQuestion}
                        loading={loading}
                        onSubmit={submitRefinement}
                    />
                )}

                {/* ── Completion banner ────────────────────────────────────── */}
                {isCompleted && (
                    <Card style={{ marginTop: 24, borderColor: '#52c41a', background: '#f6ffed' }}>
                        <Space>
                            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
                            <Typography.Text strong style={{ color: '#52c41a' }}>
                                Work history completed and saved successfully.
                            </Typography.Text>
                        </Space>
                    </Card>
                )}

                <div ref={bottomRef} />
            </Content>
        </Layout>
    );
};

export default WorkHistoryPage;