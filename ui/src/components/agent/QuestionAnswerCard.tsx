import { Card, Typography, Space, Divider } from 'antd';

interface Props {
    qaPairs: {
        question: string;
        answer: string;
    }[];
}

const QuestionAnswerCard = ({ qaPairs }: Props) => {
    return (
        <Card
            style={{
                marginBottom: 16,
                borderRadius: 12,
                background: '#f6ffed',
                border: '1px solid #b7eb8f',
            }}
        >
            <Space
                direction="vertical"
                style={{ width: '100%' }}
                size="middle"
            >
                <Typography.Text strong>
                    Submitted Answers
                </Typography.Text>

                {qaPairs.map((pair, index) => (
                    <div key={index}>
                        <Typography.Text strong>
                            Q:
                        </Typography.Text>

                        <Typography.Paragraph
                            style={{ marginBottom: 8 }}
                        >
                            {pair.question}
                        </Typography.Paragraph>

                        <Typography.Text strong>
                            A:
                        </Typography.Text>

                        <Typography.Paragraph
                            style={{ marginBottom: 0 }}
                        >
                            {pair.answer}
                        </Typography.Paragraph>

                        {index !== qaPairs.length - 1 && (
                            <Divider />
                        )}
                    </div>
                ))}
            </Space>
        </Card>
    );
};

export default QuestionAnswerCard;