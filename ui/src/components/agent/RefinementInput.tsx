import { useState } from 'react';

import {
    Card,
    Typography,
    Input,
    Button,
    Space,
} from 'antd';

const { TextArea } = Input;

interface Props {
    question: string;
    onSubmit: (value: string) => void;
    loading: boolean;
}

const RefinementInput = ({
    question,
    onSubmit,
    loading,
}: Props) => {
    const [value, setValue] = useState('');

    return (
        <Card style={{ marginTop: 24 }}>
            <Space
                direction="vertical"
                style={{ width: '100%' }}
                size="large"
            >
                <Typography.Text strong>
                    {question}
                </Typography.Text>

                <TextArea
                    rows={5}
                    value={value}
                    onChange={e =>
                        setValue(e.target.value)
                    }
                    placeholder="Describe what you want improved..."
                />

                <Button
                    type="primary"
                    loading={loading}
                    onClick={() => onSubmit(value)}
                >
                    Submit Refinement
                </Button>
            </Space>
        </Card>
    );
};

export default RefinementInput;