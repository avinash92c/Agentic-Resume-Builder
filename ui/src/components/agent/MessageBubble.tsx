import { Card } from 'antd';

import type { ChatMessage } from '../../types/agent';

import QuestionAnswerCard from './QuestionAnswerCard';

interface Props {
    message: ChatMessage;
}

const MessageBubble = ({ message }: Props) => {
    const isUser = message.role === 'user';

    return (
        <div
            style={{
                display: 'flex',
                justifyContent: isUser
                    ? 'flex-end'
                    : 'flex-start',
                marginBottom: 16,
            }}
        >
            {message.qaPairs ? (
                <div
                    style={{
                        maxWidth: '80%',
                    }}
                >
                    <QuestionAnswerCard
                        qaPairs={message.qaPairs}
                    />
                </div>
            ) : (
                <Card
                    style={{
                        maxWidth: '70%',
                        borderRadius: 16,
                        background: isUser
                            ? '#1677ff'
                            : '#fff',
                        color: isUser ? '#fff' : '#000',
                    }}
                    bodyStyle={{
                        padding: '12px 16px',
                    }}
                >
                    <div
                        style={{
                            whiteSpace: 'pre-wrap',
                            color: isUser
                                ? '#fff'
                                : '#000',
                        }}
                    >
                        {message.content}
                    </div>
                </Card>
            )}
        </div>
    );
};

export default MessageBubble;