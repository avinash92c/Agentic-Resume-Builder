import { useState } from 'react';
import { Input, Button, List, Card } from 'antd';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

const mockMessages: Message[] = [
    { role: 'assistant', content: 'Hi! I am your AI Resume Builder. Tell me about your work experience and I will help you craft a professional resume.' },
    { role: 'user', content: 'I worked at Infosys from 2019 to 2022 as a Data Scientist. I built recommendation engines using Python and SQL.' },
    { role: 'assistant', content: 'Great! Here are a few questions to help me understand your work better:\n\n1. What was the scale of the recommendation engine — how many users or products did it serve?\n2. What specific ML techniques did you use — collaborative filtering, content based, hybrid?\n3. What was the measurable business impact of the engine?' },
    { role: 'user', content: 'It served about 2 million users, used collaborative filtering, and improved click through rate by 18%.' },
    { role: 'assistant', content: 'Excellent detail! Here is a draft bullet point for this project:\n\n• Developed a collaborative filtering recommendation engine serving 2M+ users, improving click-through rate by 18% using Python and SQL.\n\nShall I refine this further or move on to the next project?' },
];

const Chat = () => {
    const [messages, setMessages] = useState<Message[]>(mockMessages);
    const [input, setInput] = useState('');

    const send = () => {
        if (!input.trim()) return;
        const userMessage: Message = { role: 'user', content: input };
        const mockReply: Message = { role: 'assistant', content: 'This is a mock response. API integration coming soon.' };
        setMessages(prev => [...prev, userMessage, mockReply]);
        setInput('');
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%' }}>
            
            {/* Header */}
            <div style={{ padding: '16px 24px', borderBottom: '1px solid #f0f0f0', background: '#fff' }}>
                <h2 style={{ margin: 0 }}>Work Experience</h2>
                <span style={{ color: '#888', fontSize: 13 }}>Tell me about your professional experience</span>
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: 'auto', padding: 16, background: '#fafafa' }}>
                <List
                    dataSource={messages}
                    renderItem={msg => (
                        <List.Item style={{
                            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                            border: 'none',
                            padding: '4px 0'
                        }}>
                            <Card
                                size="small"
                                style={{
                                    maxWidth: '70%',
                                    background: msg.role === 'user' ? '#1677ff' : '#fff',
                                    border: msg.role === 'user' ? 'none' : '1px solid #f0f0f0',
                                    borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                                    whiteSpace: 'pre-wrap'
                                }}
                                styles={{ body: { padding: '8px 12px' } }}
                            >
                                <span style={{ color: msg.role === 'user' ? '#fff' : '#000' }}>
                                    {msg.content}
                                </span>
                            </Card>
                        </List.Item>
                    )}
                />
            </div>

            {/* Input */}
            <div style={{ padding: 16, borderTop: '1px solid #f0f0f0', background: '#fff', display: 'flex', gap: 8 }}>
                <Input
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onPressEnter={send}
                    placeholder="Type your message..."
                    size="large"
                />
                <Button type="primary" onClick={send} size="large">
                    Send
                </Button>
            </div>
        </div>
    );
};

export default Chat;