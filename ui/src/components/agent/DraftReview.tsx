import { Card, Typography, Space, Button } from 'antd';

interface Props {
    draft: string;
    onApprove: () => void;
    onRefine: () => void;
    loading: boolean;
}

const DraftReview = ({
    draft,
    onApprove,
    onRefine,
    loading,
}: Props) => {
    return (
        <Card style={{ marginTop: 24 }}>
            <Space
                direction="vertical"
                style={{ width: '100%' }}
                size="large"
            >
                <div>
                    <Typography.Title level={5}>
                        Draft Review
                    </Typography.Title>

                    <Typography.Paragraph
                        style={{
                            whiteSpace: 'pre-wrap',
                        }}
                    >
                        {draft}
                    </Typography.Paragraph>
                </div>

                <Space>
                    <Button
                        type="primary"
                        loading={loading}
                        onClick={onApprove}
                    >
                        Approve
                    </Button>

                    <Button
                        loading={loading}
                        onClick={onRefine}
                    >
                        Refine
                    </Button>
                </Space>
            </Space>
        </Card>
    );
};

export default DraftReview;