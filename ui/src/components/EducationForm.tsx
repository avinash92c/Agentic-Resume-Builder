import { Form, Input, InputNumber, Button, Card, Divider, message, Collapse } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import type { Education } from '../types/models';
import CoreAPI from '../api/CoreAPI';
import { useState } from 'react';

const EducationForm = () => {
    const [form] = Form.useForm();
    const [saved, setSaved] = useState<Education[]>([]);
    const [activeKeys, setActiveKeys] = useState<string[]>(['0']);

    const onFinish = (values: { education: Education[] }) => {
        const email = localStorage.getItem('email') || '';
        CoreAPI.saveEducationInfo(values.education, email)
            .then(() => {
                setSaved(values.education);
                message.success('Education saved successfully');
            })
            .catch(() => message.error('Failed to save education'));
    };

    return (
        <div style={{ padding: 32, maxWidth: 700, margin: '0 auto' }}>
            <Card title="Education">
                <Form form={form} layout="vertical" onFinish={onFinish}>
                    <Form.List name="education" initialValue={[{}]}>
                        {(fields, { add, remove }) => (
                            <>
                                <Collapse
                                    activeKey={activeKeys}
                                    onChange={keys => setActiveKeys(keys as string[])}
                                    items={fields.map((field, index) => ({
                                        key: String(index),
                                        label: (
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <span>Education {index + 1}</span>
                                                {fields.length > 1 && (
                                                    <Button
                                                        danger
                                                        size="small"
                                                        icon={<DeleteOutlined />}
                                                        onClick={e => {
                                                            e.stopPropagation();
                                                            remove(field.name);
                                                        }}
                                                    >
                                                        Remove
                                                    </Button>
                                                )}
                                            </div>
                                        ),
                                        children: (
                                            <>
                                                <Form.Item label="Degree" name={[field.name, 'degree']} rules={[{ required: true }]}>
                                                    <Input placeholder="B.Tech, MBA, B.Sc" />
                                                </Form.Item>
                                                <Form.Item label="Institution" name={[field.name, 'institution']} rules={[{ required: true }]}>
                                                    <Input placeholder="University or college name" />
                                                </Form.Item>
                                                <Form.Item label="Field of Study" name={[field.name, 'field_of_study']}>
                                                    <Input placeholder="Computer Science, Finance" />
                                                </Form.Item>
                                                <div style={{ display: 'flex', gap: 16 }}>
                                                    <Form.Item label="Start Year" name={[field.name, 'start_year']} style={{ flex: 1 }}>
                                                        <InputNumber placeholder="2018" style={{ width: '100%' }} />
                                                    </Form.Item>
                                                    <Form.Item label="End Year" name={[field.name, 'end_year']} style={{ flex: 1 }}>
                                                        <InputNumber placeholder="2022" style={{ width: '100%' }} />
                                                    </Form.Item>
                                                </div>
                                                <Form.Item label="Location" name={[field.name, 'location']}>
                                                    <Input placeholder="Hyderabad, India" />
                                                </Form.Item>
                                                <Form.Item label="Achievements" name={[field.name, 'achievements']}>
                                                    <Input.TextArea placeholder="Scholarships, honors, ranks" rows={2} />
                                                </Form.Item>
                                            </>
                                        )
                                    }))}
                                />
                                <Button
                                    type="dashed"
                                    onClick={() => {
                                        add();
                                        // setActiveKeys(prev => [...prev, String(fields.length)]);
                                    }}
                                    block
                                    icon={<PlusOutlined />}
                                    style={{ marginTop: 12 }}
                                >
                                    Add Another Education
                                </Button>
                            </>
                        )}
                    </Form.List>
                    <Divider />
                    <Button type="primary" htmlType="submit" block size="large">
                        Save Education
                    </Button>
                </Form>

                {saved.length > 0 && (
                    <div style={{ marginTop: 24 }}>
                        <Divider>Saved Education</Divider>
                        {saved.map((edu, i) => (
                            <Card key={i} size="small" style={{ marginBottom: 8 }}>
                                <strong>{edu.degree}</strong> — {edu.institution}<br />
                                <span style={{ color: '#888' }}>{edu.field_of_study} · {edu.start_year} – {edu.end_year}</span>
                            </Card>
                        ))}
                    </div>
                )}
            </Card>
        </div>
    );
};

export default EducationForm;