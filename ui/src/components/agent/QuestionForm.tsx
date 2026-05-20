import { Button, Card, Input, Space, Typography } from 'antd';

const { TextArea } = Input;

interface Props {
    questions: string[];
    answers: Record<string, string>;
    setAnswers: React.Dispatch<
        React.SetStateAction<Record<string, string>>
    >;
    onSubmit: () => void;
    loading: boolean;
}

const QuestionForm = ({
    questions,
    answers,
    setAnswers,
    onSubmit,
    loading,
}: Props) => {
    return (
        <Card style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
                {questions.map(question => (
                    <div key={question}>
                        <Typography.Text strong>
                            {question}
                        </Typography.Text>

                        <TextArea
                            rows={4}
                            value={answers[question]}
                            onChange={e =>
                                setAnswers(prev => ({
                                    ...prev,
                                    [question]: e.target.value,
                                }))
                            }
                            placeholder="Type your answer..."
                            style={{ marginTop: 8 }}
                        />
                    </div>
                ))}

                <Button
                    type="primary"
                    onClick={onSubmit}
                    loading={loading}
                >
                    Continue
                </Button>
            </Space>
        </Card>
    );
};

export default QuestionForm;