import { Layout } from 'antd';
import Nav from "../nav/Nav";
import AppRouter from "../nav/AppRouter";

const { Content, Sider } = Layout;

const Main = () => {
    return (
        <Layout style={{ height: '100vh', overflow: 'hidden' }}>
            <Sider width={256} style={{ height: '100vh', overflow: 'auto', background: '#fff' }}>
                <Nav/>
            </Sider>
            <Content style={{ height: '100vh', overflow: 'auto' }}>
                <AppRouter/>
            </Content>
        </Layout>
    );
};

export default Main;