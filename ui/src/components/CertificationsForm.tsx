import { Form, Input, Button, Card, Divider, message, Collapse } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import type { Certifications } from '../types/models';
import CoreAPI from '../api/CoreAPI';
import { useState } from 'react';

const CertificationsForm = () => {
    const [form] = Form.useForm();
    const [saved, setSaved] = useState<Certifications[]>([]);

    const onFinish = (values: { certifications: Certifications[] }) => {
        const email = localStorage.getItem('email') || '';
        CoreAPI.saveCertificationInfo(values.certifications, email)
            .then(() => {
                setSaved(values.certifications);
                message.success('Certifications saved successfully');
            })
            .catch(() => message.error('Failed to save certifications'));
    };

    return (
        <div style={{ padding: 32, maxWidth: 700, margin: '0 auto' }}>
            <Card title="Certifications">
                <Form form={form} layout="vertical" onFinish={onFinish}>
                    <Form.List name="certifications" initialValue={[{}]}>
                        {(fields, { add, remove }) => (
                            <>
                                <Collapse
                                    defaultActiveKey={['0']}
                                    items={fields.map((field, index) => ({
                                        key: String(index),
                                        label: (
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <span>
                                                    Certification {index + 1}
                                                </span>
                                                {fields.length > 1 && (
                                                    <Button
                                                        danger
                                                        size="small"
                                                        icon={<DeleteOutlined />}
                                                        onClick={e => {
                                                            e.stopPropagation(); // prevent collapse toggle
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
                                                <Form.Item label="Certification Name" name={[field.name, 'name']} rules={[{ required: true }]}>
                                                    <Input placeholder="AWS Solutions Architect" />
                                                </Form.Item>
                                                <Form.Item label="Issuing Organization" name={[field.name, 'issuing_organization']}>
                                                    <Input placeholder="Amazon, Google, Microsoft" />
                                                </Form.Item>
                                                <Form.Item label="Issue Date" name={[field.name, 'issue_date']}>
                                                    <Input placeholder="2023-06" />
                                                </Form.Item>
                                                <Form.Item label="Expiration Date" name={[field.name, 'expiration_date']}>
                                                    <Input placeholder="2026-06 or leave blank" />
                                                </Form.Item>
                                                <Form.Item label="Credential ID" name={[field.name, 'credential_id']}>
                                                    <Input placeholder="ABC123XYZ" />
                                                </Form.Item>
                                                <Form.Item label="Credential URL" name={[field.name, 'credential_url']}>
                                                    <Input placeholder="https://verify.example.com/cert/123" />
                                                </Form.Item>
                                            </>
                                        )
                                    }))}
                                />
                                <Button
                                    type="dashed"
                                    onClick={() => add()}
                                    block
                                    icon={<PlusOutlined />}
                                    style={{ marginTop: 12 }}
                                >
                                    Add Another Certification
                                </Button>
                            </>
                        )}
                    </Form.List>
                    <Divider />
                    <Button type="primary" htmlType="submit" block size="large">
                        Save Certifications
                    </Button>
                </Form>

                {saved.length > 0 && (
                    <div style={{ marginTop: 24 }}>
                        <Divider>Saved Certifications</Divider>
                        {saved.map((cert, i) => (
                            <Card key={i} size="small" style={{ marginBottom: 8 }}>
                                <strong>{cert.name}</strong><br />
                                <span style={{ color: '#888' }}>{cert.issuing_organization} · {cert.issue_date}</span><br />
                                {cert.credential_url && (
                                    <a href={cert.credential_url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                                        Verify Credential
                                    </a>
                                )}
                            </Card>
                        ))}
                    </div>
                )}
            </Card>
        </div>
    );
};

export default CertificationsForm;