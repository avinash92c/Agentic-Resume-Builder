import { useState, useRef, useEffect } from 'react';

import {
  Button,
  Card,
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
  CheckCircleOutlined,
  EditOutlined,
  FileTextOutlined,
  CheckOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';

import AgentAPI from '../api/AgentAPI';

import type { AgentResponse, StartRequest } from '../types/agent';

import MessageBubble from '../components/agent/MessageBubble';
import QuestionForm from '../components/agent/QuestionForm';
import DraftReview from '../components/agent/DraftReview';
import RefinementInput from '../components/agent/RefinementInput';

const { Content } = Layout;
const { TextArea } = Input;

// ─── Types ────────────────────────────────────────────────────────────────────

type SessionEventKind = 'draft' | 'refinement' | 'approved';

interface SessionEvent {
  id: string;
  kind: SessionEventKind;
  content: string;
  label: string;
  timestamp: Date;
}

// ─── Component ────────────────────────────────────────────────────────────────

const SkillsPage = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState('');
  const [messages, setMessages] = useState<any[]>([]);
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});

  // Active (latest) draft — drives the live DraftReview panel
  const [activeDraft, setActiveDraft] = useState<string>('');

  // Immutable session log — events never removed, always visible
  const [sessionLog, setSessionLog] = useState<SessionEvent[]>([]);
  const draftVersionCount = sessionLog.filter(e => e.kind === 'draft').length;

  const [refinementQuestion, setRefinementQuestion] = useState('');
  const [showRefinementInput, setShowRefinementInput] = useState(false);

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

    // Always clear questions first so old form unmounts cleanly
    setQuestions([]);
    setAnswers({});

    // QUESTIONS — from AskQuestions node
    if (payload.questions?.length) {
      setQuestions(payload.questions);
      appendAssistantMessage('Please answer the following questions to help generate your skill set.');
    }

    // DRAFT — from PrepareDraft node
    // DRAFT — from PrepareDraft node
    if (payload.draft || payload.latest_draft) {
      const draft = payload.draft ?? payload.latest_draft ?? '';  // ← always string

      setActiveDraft(draft);

      setSessionLog(prev => {
        const lastDraft = [...prev].reverse().find(e => e.kind === 'draft');
        if (lastDraft?.content === draft) return prev;
        const version = prev.filter(e => e.kind === 'draft').length + 1;
        return [
          ...prev,
          {
            id: crypto.randomUUID(),
            kind: 'draft' as SessionEventKind,   // ← explicit cast
            content: draft,                        // ← now guaranteed string
            label: `Draft v${version}`,
            timestamp: new Date(),
          },
        ];
      });

      if (!payload.questions?.length) {
        appendAssistantMessage('Skills draft generated. Please review below.');
      }
    }

    // REFINEMENT — from AskRefinements node
    if (payload.refinement_question || payload.message) {
      const question = payload.refinement_question ?? payload.message ?? "";
      setRefinementQuestion(question);
      setShowRefinementInput(true);
      appendAssistantMessage(question);
    }
  };

  // ── Actions ───────────────────────────────────────────────────────────────

  const startSkills = async (values: { raw_skills: string }) => {
    try {
      setLoading(true);
      setAgentStarted(true);

      const email = localStorage.getItem('email') || 'JOhn@example.com';
      const payload: StartRequest<string> = { email, user_input: values.raw_skills };
      const response = await AgentAPI.start('skills', payload);
      const data = response.data;

      setThreadId(data.thread_id);
      appendUserMessage('Submitted skills background.');
      handleResponse(data);
    } catch {
      message.error('Failed to start skills flow');
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

      const response = await AgentAPI.resume('skills', {
        thread_id: threadId,
        user_data: { answers: currentAnswers },
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

      const response = await AgentAPI.resume('skills', {
        thread_id: threadId,
        user_data: { approved: true },
      });

      pushSessionEvent('approved', activeDraft, `Draft v${draftVersionCount} — Approved ✓`);

      handleResponse(response.data);

      if (response.data.complete) {
        setQuestions([]);
        setShowRefinementInput(false);
        setRefinementQuestion('');
        setActiveDraft('');
        setIsCompleted(true);
        message.success('Skills completed and saved successfully');
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

      const response = await AgentAPI.resume('skills', {
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

      pushSessionEvent('refinement', refinement, 'Refinement Request');

      // Only close after user explicitly submits
      setShowRefinementInput(false);
      setRefinementQuestion('');

      const response = await AgentAPI.resume('skills', {
        thread_id: threadId,
        user_data: { refinement, feedback: refinement },
      });

      handleResponse(response.data);
    } catch {
      message.error('Failed to submit refinement');
    } finally {
      setLoading(false);
    }
  };

  // ── Derived UI state ──────────────────────────────────────────────────────

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
          <Typography.Title level={2}>Skills</Typography.Title>
          <Typography.Text type="secondary">
            Describe your technical and professional skills. The AI agent will ask clarifying
            questions, then generate a polished skills section for your resume.
          </Typography.Text>
        </div>

        {/* ── Input form (locked after agent starts) ───────────────── */}
        <Card
          title={
            agentStarted ? (
              <Space>
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                <span>Submitted Skills Background</span>
                <Tag color="green">Locked</Tag>
              </Space>
            ) : (
              <Space>
                <ThunderboltOutlined />
                <span>Skills Input</span>
              </Space>
            )
          }
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={startSkills}
            disabled={agentStarted}
          >
            <Form.Item
              label="Your Skills & Background"
              name="raw_skills"
              rules={[{ required: true, message: 'Please describe your skills' }]}
              extra="Paste a rough list of your skills, technologies, tools, frameworks, or anything relevant. Don't worry about formatting."
            >
              <TextArea
                rows={8}
                placeholder={`e.g. Python, FastAPI, LangGraph, LangChain, MongoDB, React, TypeScript. 5 years backend dev. Built agentic AI systems, REST APIs, worked with LLMs. Also know Docker, CI/CD, some DevOps.`}
              />
            </Form.Item>

            <Divider />

            {!agentStarted && (
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                loading={loading}
                block
                icon={<ThunderboltOutlined />}
              >
                Start Skills Agent
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

        {/* ── Session log — always visible once populated ──────────── */}
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
        {showDraftReview && (
          <DraftReview
            draft={activeDraft}
            onApprove={approveDraft}
            onRefine={requestRefinement}
            loading={loading}
          />
        )}

        {/* ── Refinement input ─────────────────────────────────────── */}
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
                Skills completed and saved successfully.
              </Typography.Text>
            </Space>
          </Card>
        )}

        <div ref={bottomRef} />
      </Content>
    </Layout>
  );
};

export default SkillsPage;