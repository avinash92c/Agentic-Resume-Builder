import { Form, Input, Button, Card, message } from 'antd';
import type { PersonalInfo } from '../types/models';
import CoreAPI from '../api/CoreAPI';

const PersonalInfoForm = () => {
    const [form] = Form.useForm();

    const onFinish = (values: PersonalInfo) => {
        localStorage.setItem('resume_email', values.email);
        
        CoreAPI.savePersonalInfo(values)
            .then(() => message.success('Personal info saved successfully'))
            .catch(() => message.error('Failed to save personal info'));
    };

    return (
        <div style={{ padding: 32, maxWidth: 700, margin: '0 auto' }}>
            <Card title="Personal Information">
                <Form form={form} layout="vertical" onFinish={onFinish}>
                    <Form.Item label="Full Name" name="name" rules={[{ required: true }]}>
                        <Input placeholder="John Doe" />
                    </Form.Item>
                    <Form.Item label="Email" name="email" rules={[{ required: true, type: 'email' }]}>
                        <Input placeholder="john@example.com" />
                    </Form.Item>
                    <Form.Item label="Phone" name="phone" rules={[{ required: true }]}>
                        <Input placeholder="+91 9999999999" />
                    </Form.Item>
                    <Form.Item label="LinkedIn URL" name="linkedin">
                        <Input placeholder="https://linkedin.com/in/yourprofile" />
                    </Form.Item>
                    <Form.Item label="GitHub URL" name="github">
                        <Input placeholder="https://github.com/yourusername" />
                    </Form.Item>
                    <Form.Item>
                        <Button type="primary" htmlType="submit" block size="large">
                            Save Personal Info
                        </Button>
                    </Form.Item>
                </Form>
            </Card>
        </div>
    );
};

export default PersonalInfoForm;