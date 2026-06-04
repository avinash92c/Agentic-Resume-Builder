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
    Timeline,
} from 'antd';

import {
    PlusOutlined,
    DeleteOutlined,
    CheckCircleOutlined,
    HistoryOutlined,
} from '@ant-design/icons';

import AgentAPI from '../api/AgentAPI';

import type { WorkExperience } from '../types/models';
import type { AgentResponse, StartRequest } from '../types/agent';

import MessageBubble from '../components/agent/MessageBubble';
import QuestionForm from '../components/agent/QuestionForm';
import DraftReview from '../components/agent/DraftReview';
import RefinementInput from '../components/agent/RefinementInput';

const { Content } = Layout;

const WorkHistoryPage = () => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [threadId, setThreadId] = useState('');
    const [messages, setMessages] = useState<any[]>([]);
    const [questions, setQuestions] = useState<string[]>([]);
    const [answers, setAnswers] = useState<Record<string, string>>({});
    const [drafts, setDrafts] = useState<string[]>([]);
    const [refinementQuestion, setRefinementQuestion] = useState('');
    const [showRefinementInput, setShowRefinementInput] = useState(false);
    const [submittedExperiences, setSubmittedExperiences] = useState<WorkExperience[]>([]);

    // FIX 1: Separate "agent started" flag from threadId so form stays visible
    const [agentStarted, setAgentStarted] = useState(false);
    // FIX 6: Track completion to hide interactive elements and form submit button
    const [isCompleted, setIsCompleted] = useState(false);

    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, questions, drafts, showRefinementInput]);

    const appendAssistantMessage = (content: string) => {
        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', content }]);
    };

    const appendUserMessage = (content: string) => {
        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'user', content }]);
    };

    const handleResponse = (data: AgentResponse) => {
        if (!data.data) return;
        const payload = data.data;

        // FIX 2: Always clear questions first so the old form unmounts cleanly
        setQuestions([]);
        setAnswers({});

        // QUESTIONS
        if (payload.questions?.length) {
            setQuestions(payload.questions);
            appendAssistantMessage('Please answer the following questions.');
        }

        // DRAFT — FIX 4: push every new unique draft into history array
        if (payload.draft) {
            setDrafts(prev => {
                if (prev[prev.length - 1] === payload.draft) return prev;
                return [...prev, payload.draft!];
            });
            // Only announce draft if there are no questions to answer first
            if (!payload.questions?.length) {
                appendAssistantMessage('Draft generated. Please review.');
            }
        }

        // REFINEMENT — FIX 5: drive visibility purely from payload flag
        if (payload.refinement_question) {
            setRefinementQuestion(payload.refinement_question);
            setShowRefinementInput(true);
            appendAssistantMessage(payload.refinement_question);
        } else {
            setShowRefinementInput(false);
        }

        // MESSAGE
        if (payload.message) {
            appendAssistantMessage(payload.message);
        }
    };

    const startWorkHistory = async (values: { experiences: WorkExperience[] }) => {
        try {
            setLoading(true);
            setSubmittedExperiences(values.experiences);
            setAgentStarted(true); // FIX 1: mark started so form stays visible but locked

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
            // Capture answers before clearing
            const currentAnswers = { ...answers };

            Object.entries(currentAnswers).forEach(([question, answer]) => {
                appendUserMessage(`Q: ${question}\n\nA: ${answer}`);
            });

            // FIX 2: Clear questions immediately so the form hides before the API responds
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
            appendUserMessage('Approved');

            const response = await AgentAPI.resume('wh', {
                thread_id: threadId,
                user_data: { approved: true },
            });

            handleResponse(response.data);

            // FIX 6: On completion, clear all interactive panels and mark done
            if (response.data.complete) {
                setQuestions([]);
                setShowRefinementInput(false);
                setRefinementQuestion('');
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

            // FIX 5: Hide refinement input immediately on submit
            setShowRefinementInput(false);

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

    // FIX 3: Build rich context string from submitted experiences to
    // pass to DraftReview so it always has full detail to display
    const buildExperienceContext = (): string => {
        if (!submittedExperiences.length) return '';
        return submittedExperiences
            .map(exp => {
                const header = `${exp.job_title} at ${exp.company_name} (${exp.start_date} – ${exp.end_date})`;
                const projects = (exp.projects || [])
                    .map((p: string, i: number) => `  Project ${i + 1}:\n  ${p}`)
                    .join('\n');
                return `${header}\n${projects}`;
            })
            .join('\n\n');
    };

    return (
        <Layout style={{ height: '100%', background: '#fff' }}>
            <Content style={{ maxWidth: 1100, margin: '0 auto', padding: 24, width: '100%' }}>
                <div style={{ marginBottom: 24 }}>
                    <Typography.Title level={2}>Work History</Typography.Title>
                    <Typography.Text type="secondary">
                        Add your companies and projects. The AI agent will refine each project one by one.
                    </Typography.Text>
                </div>

                {/*
                  FIX 1: Form is always visible. After agent starts it becomes
                  disabled (read-only) so the user can still see what they submitted.
                  A "Locked" banner makes the state clear.
                */}
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
                                                            danger
                                                            size="small"
                                                            icon={<DeleteOutlined />}
                                                            onClick={e => {
                                                                e.stopPropagation();
                                                                removeCompany(companyField.name);
                                                            }}
                                                        >
                                                            Remove
                                                        </Button>
                                                    )}
                                                </div>
                                            ),
                                            children: (
                                                <>
                                                    <Form.Item
                                                        label="Company Name"
                                                        name={[companyField.name, 'company_name']}
                                                        rules={[{ required: true }]}
                                                    >
                                                        <Input placeholder="ABC Bank" />
                                                    </Form.Item>

                                                    <Form.Item
                                                        label="Job Title"
                                                        name={[companyField.name, 'job_title']}
                                                        rules={[{ required: true }]}
                                                    >
                                                        <Input placeholder="Senior RPA Developer" />
                                                    </Form.Item>

                                                    <Space style={{ display: 'flex' }}>
                                                        <Form.Item
                                                            label="Start Date"
                                                            name={[companyField.name, 'start_date']}
                                                            rules={[{ required: true }]}
                                                        >
                                                            <Input placeholder="2020-01" />
                                                        </Form.Item>

                                                        <Form.Item
                                                            label="End Date"
                                                            name={[companyField.name, 'end_date']}
                                                            rules={[{ required: true }]}
                                                        >
                                                            <Input placeholder="Present" />
                                                        </Form.Item>
                                                    </Space>

                                                    <Form.Item
                                                        label="Employment Type"
                                                        name={[companyField.name, 'employment_type']}
                                                    >
                                                        <Input placeholder="Full Time" />
                                                    </Form.Item>

                                                    <Divider>Projects</Divider>

                                                    <Form.List
                                                        name={[companyField.name, 'projects']}
                                                        initialValue={['']}
                                                    >
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
                                                                            <Button
                                                                                danger
                                                                                icon={<DeleteOutlined />}
                                                                                onClick={() => removeProject(projectField.name)}
                                                                            >
                                                                                Remove Project
                                                                            </Button>
                                                                        )}
                                                                    </Card>
                                                                ))}

                                                                {!agentStarted && (
                                                                    <Button
                                                                        type="dashed"
                                                                        block
                                                                        icon={<PlusOutlined />}
                                                                        onClick={() => addProject()}
                                                                    >
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
                                        <Button
                                            type="dashed"
                                            block
                                            icon={<PlusOutlined />}
                                            style={{ marginTop: 16 }}
                                            onClick={() => addCompany()}
                                        >
                                            Add Another Company
                                        </Button>
                                    )}
                                </>
                            )}
                        </Form.List>

                        <Divider />

                        {/* FIX 6: Only show submit button before start, hide after */}
                        {!agentStarted && (
                            <Button type="primary" htmlType="submit" size="large" loading={loading} block>
                                Start Work History Agent
                            </Button>
                        )}
                    </Form>
                </Card>

                {/* Message thread */}
                {messages.length > 0 && (
                    <div style={{ marginTop: 24 }}>
                        {messages.map(msg => (
                            <MessageBubble key={msg.id} message={msg} />
                        ))}
                    </div>
                )}

                {/* FIX 2: Questions form — only mounts when questions array is non-empty */}
                {questions.length > 0 && (
                    <QuestionForm
                        questions={questions}
                        answers={answers}
                        setAnswers={setAnswers}
                        onSubmit={submitAnswers}
                        loading={loading}
                    />
                )}

                {/*
                  FIX 3 & 4: Show draft review + history.
                  Only shown when: have drafts, no pending questions, no refinement input open, not completed.
                */}
                {drafts.length > 0 && questions.length === 0 && !showRefinementInput && !isCompleted && (
                    <>
                        {/* FIX 4: Draft version history (shown when more than 1 draft exists) */}
                        {drafts.length > 1 && (
                            <Card
                                size="small"
                                style={{ marginTop: 24 }}
                                title={
                                    <Space>
                                        <HistoryOutlined />
                                        <span>Draft History ({drafts.length} versions)</span>
                                    </Space>
                                }
                            >
                                <Timeline
                                    items={drafts.slice(0, -1).map((d, i) => ({
                                        key: i,
                                        color: 'gray',
                                        children: (
                                            <details>
                                                <summary style={{ cursor: 'pointer', color: '#888' }}>
                                                    Version {i + 1} (superseded)
                                                </summary>
                                                <pre
                                                    style={{
                                                        marginTop: 8,
                                                        whiteSpace: 'pre-wrap',
                                                        fontSize: 12,
                                                        color: '#999',
                                                        background: '#fafafa',
                                                        padding: 8,
                                                        borderRadius: 4,
                                                    }}
                                                >
                                                    {d}
                                                </pre>
                                            </details>
                                        ),
                                    }))}
                                />
                            </Card>
                        )}

                        {/*
                          FIX 3: Pass experienceContext so DraftReview can fall back
                          to showing raw input if the draft content is empty/minimal.
                          You'll need to update DraftReview's props to accept and use this.
                        */}
                        <DraftReview
                            draft={drafts[drafts.length - 1]}
                            // experienceContext={buildExperienceContext()}
                            onApprove={approveDraft}
                            onRefine={requestRefinement}
                            loading={loading}
                        />
                    </>
                )}

                {/* FIX 5: Refinement input — driven by showRefinementInput flag alone */}
                {showRefinementInput && questions.length === 0 && !isCompleted && (
                    <RefinementInput
                        question={refinementQuestion}
                        loading={loading}
                        onSubmit={submitRefinement}
                    />
                )}

                {/* FIX 6: Success banner replaces all interactive elements on completion */}
                {isCompleted && (
                    <Card
                        style={{ marginTop: 24, borderColor: '#52c41a', background: '#f6ffed' }}
                    >
                        <Space>
                            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
                            <Typography.Text strong style={{ color: '#52c41a' }}>
                                Work history has been completed and saved successfully.
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