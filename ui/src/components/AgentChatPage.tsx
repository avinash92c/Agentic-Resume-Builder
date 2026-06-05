import { useState } from 'react';

import {
    Button,
    Card,
    Input,
    Layout,
    Space,
    Typography,
    message,
} from 'antd';

import AgentAPI from '../api/AgentAPI';

import type {
    AgentType,
    ChatMessage,
} from '../types/agent';

import { AGENT_CONFIG } from '../types/agentConfig';
import RefinementInput from '../components/agent/RefinementInput';
import MessageBubble from '../components/agent/MessageBubble';
import QuestionForm from '../components/agent/QuestionForm';
import DraftReview from '../components/agent/DraftReview';

const { Content } = Layout;
const { TextArea } = Input;

interface Props {
    agent: AgentType;
    existingThreadId?: string;
}

const AgentChatPage = ({ agent }: Props) => {
    const config = AGENT_CONFIG[agent];

    const [loading, setLoading] = useState(false);

    const [threadId, setThreadId] = useState('');

    const [initialInput, setInitialInput] = useState('');

    const [messages, setMessages] = useState<ChatMessage[]>([]);

    const [questions, setQuestions] = useState<string[]>([]);

    const [answers, setAnswers] = useState<Record<string, string>>({});

    const [draft, setDraft] = useState('');

    const [completed, setCompleted] = useState(false);
    const [refinementQuestion, setRefinementQuestion] = useState('');

    const appendAssistantMessage = (content: string) => {
        setMessages(prev => [
            ...prev,
            {
                id: crypto.randomUUID(),
                role: 'assistant',
                content,
            },
        ]);
    };

    const appendUserMessage = (content: string) => {
        setMessages(prev => [
            ...prev,
            {
                id: crypto.randomUUID(),
                role: 'user',
                content,
            },
        ]);
    };

    const startConversation = async () => {
        if (!initialInput.trim()) {
            message.warning('Please enter your professional summary');
            return;
        }

        try {
            setLoading(true);

            appendUserMessage(initialInput);

            const response = await AgentAPI.start(agent, {
                email: 'JOhn@example.com',
                user_input: initialInput,
            });

            const result = response.data;

            setThreadId(result.thread_id);

            const responseData = result.data;

            if (!responseData) return;

            // Reset previous state
            setQuestions([]);
            setDraft('');

            if (responseData.message) {
                appendAssistantMessage(responseData.message);
            }

            if (responseData.questions) {
                setQuestions(responseData.questions);
            }

            if (responseData.draft) {
                setDraft(responseData.draft);
            }

            if (result.complete) {
                setCompleted(true);
            }
        } catch (error) {
            message.error('Failed to start conversation');
        } finally {
            setLoading(false);
        }
    };

    const submitAnswers = async () => {
        try {
            setLoading(true);

            // Show submitted answers in chat
            setMessages(prev => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: 'user',
                    qaPairs: Object.entries(answers).map(
                        ([question, answer]) => ({
                            question,
                            answer,
                        })
                    ),
                },
            ]);

            const response = await AgentAPI.resume(agent, {
                thread_id: threadId,
                user_data: answers,
            });

            const result = response.data;

            const responseData = result.data;

            // Clear question form
            setQuestions([]);
            setAnswers({});
            setDraft('');
            setRefinementQuestion('');

            if (!responseData) return;

            if (responseData.message) {
                appendAssistantMessage(responseData.message);
            }

            // QUESTIONS
            if (responseData.questions?.length) {
                setQuestions(responseData.questions);
            }

            // DRAFT REVIEW
            if (responseData.draft) {
                setDraft(responseData.draft);
                appendAssistantMessage(`Here is your draft:\n\n${responseData.draft}`);
            }

            // REFINEMENT INPUT
            if (responseData.refinement_question) {
                setRefinementQuestion(
                    responseData.refinement_question
                );
            }

            if (result.complete) {
                setCompleted(true);
            }

        } catch (error) {
            message.error('Failed to submit answers');
        } finally {
            setLoading(false);
        }
    };

    const approveDraft = async () => {
        try {
            setLoading(true);
            setDraft('');
            setQuestions([]);

            const response = await AgentAPI.resume(agent, {
                thread_id: threadId,
                user_data: {
                    approved: true,
                },
            });

            const result = response.data;

            const responseData = result.data;

            if (responseData?.message) {
                appendAssistantMessage(responseData.message);
            } else {
                appendAssistantMessage(
                    'Draft approved successfully.'
                );
            }

            if (result.complete) {
                setCompleted(true);
            }
        } catch (error) {
            message.error('Failed to approve draft');
        } finally {
            setLoading(false);
        }
    };

    const requestRefinement = async () => {
        try {
            setLoading(true);

            const response = await AgentAPI.resume(agent, {
                thread_id: threadId,
                user_data: {
                    approved: false,
                },
            });

            const result = response.data;

            const responseData = result.data;

            if (!responseData) return;

            setDraft('');

            if (responseData.questions) {
                setRefinementQuestion(
                    responseData.refinement_question
                );
            }

        } catch (error) {
            message.error(
                'Failed to request refinement'
            );
        } finally {
            setLoading(false);
        }
    };

    const submitRefinement = async (
        refinement: string
    ) => {
        setRefinementQuestion('')
        if (!refinement.trim()) {
            message.warning(
                'Please enter refinement instructions'
            );
            return;
        }

        try {
            setLoading(true);

            appendUserMessage(refinement);

            const response = await AgentAPI.resume(agent, {
                thread_id: threadId,
                user_data: {
                    refinement,
                },
            });

            const result = response.data;

            const responseData = result.data;

            if (!responseData) return;

            setRefinementQuestion('');
            setDraft('');

            if (responseData.message) {
                appendAssistantMessage(
                    responseData.message
                );
            }

            if (responseData.draft) {
                setDraft(responseData.draft);
                appendAssistantMessage(`Here is your refined draft:\n\n${responseData.draft}`);
            }

            if (result.complete) {
                setCompleted(true);
            }

        } catch (error) {
            message.error('Failed to refine draft');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Layout
            style={{
                height: '100%',
                background: '#fff',
            }}
        >
            <Content
                style={{
                    maxWidth: 1000,
                    width: '100%',
                    margin: '0 auto',
                    padding: 24,
                }}
            >
                {/* Header */}
                <div
                    style={{
                        marginBottom: 24,
                    }}
                >
                    <Typography.Title level={3}>
                        {config.title}
                    </Typography.Title>

                    <Typography.Text type="secondary">
                        {config.subtitle}
                    </Typography.Text>
                </div>

                {/* Initial Prompt */}
                {!threadId && (
                    <Card>
                        <Space
                            direction="vertical"
                            style={{ width: '100%' }}
                            size="large"
                        >
                            <TextArea
                                rows={10}
                                value={initialInput}
                                onChange={e =>
                                    setInitialInput(
                                        e.target.value
                                    )
                                }
                                placeholder={
                                    config.initialPlaceholder
                                }
                            />

                            <Button
                                type="primary"
                                size="large"
                                loading={loading}
                                onClick={startConversation}
                            >
                                Generate
                            </Button>
                        </Space>
                    </Card>
                )}

                {/* Chat Messages */}
                {messages.length > 0 && (
                    <div
                        style={{
                            marginTop: 24,
                        }}
                    >
                        {messages.map(message => (
                            <MessageBubble
                                key={message.id}
                                message={message}
                            />
                        ))}
                    </div>
                )}

                {/* Questions */}
                {questions.length > 0 && !draft && (
                    <QuestionForm
                        questions={questions}
                        answers={answers}
                        setAnswers={setAnswers}
                        onSubmit={submitAnswers}
                        loading={loading}
                    />
                )}

                {/* Draft Review */}
                {draft && (
                    <DraftReview
                        draft={draft}
                        onApprove={approveDraft}
                        onRefine={requestRefinement}
                        loading={loading}
                    />
                )}

                {refinementQuestion && (
                    <RefinementInput
                        question={refinementQuestion}
                        onSubmit={submitRefinement}
                        loading={loading}
                    />
                )}

                {/* Completed */}
                {completed && (
                    <Card
                        style={{
                            marginTop: 24,
                            border: '1px solid #b7eb8f',
                            background: '#f6ffed',
                        }}
                    >
                        <Typography.Text strong>
                            Workflow completed successfully.
                        </Typography.Text>
                    </Card>
                )}
            </Content>
        </Layout>
    );
};

export default AgentChatPage;