import { Menu, type MenuProps, Layout } from 'antd';
import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import type { Pages } from '../types/pages';
import CoreAPI from '../api/CoreAPI';

type MenuItem = Required<MenuProps>['items'][number];

const routeMap: Record<string, string> = {
    'Personal Info': '/personal-info',
    'Education': '/education',
    'Certifications': '/certifications',
    'Professional Experience': '/work-experience',
    'Professional Summary': '/professional-summary',
    'Skills': '/skills',
    'Review': '/review',
    'Cover Letter': '/cover-letter',
    'Job Fit': '/job-fit',
    'Assessment': '/assessment',
    'Learning Roadmap': '/learning-roadmap',
};

const { Header, Content } = Layout;

const Nav = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
    const [openKeys, setOpenKeys] = useState<string[]>([]);

    const buildMenu = (pageMenu: Pages): MenuItem[] => {
        return Object.entries(pageMenu).map(([key, items]) => ({
            key: key,
            label: key,
            children: items.map(item => ({
                key: routeMap[item] || item,
                label: item
            }))
        }));
    };

    useEffect(() => {
        CoreAPI.pages().then(result => {
            setMenuItems(buildMenu(result.data));
            setOpenKeys(Object.keys(result.data));
        }).catch(e => console.error(e));
    }, []);

    const onClick: MenuProps['onClick'] = (e) => {
        navigate(e.key);
    };

    return (
        <Layout style={{ height: '100%' }}>
            <Header style={{ background: '#1a3a5c', color: '#ffffff', display: 'flex', alignItems: 'center' }}>
                Resume Builder
            </Header>
            <Content>
                <Menu
                    onClick={onClick}
                    style={{ height: '100%', borderRight: '1px solid #f0f0f0' }}
                    selectedKeys={[location.pathname]}
                    openKeys={openKeys}
                    onOpenChange={() => {}}
                    mode="inline"
                    inlineCollapsed={false}
                    items={menuItems}
                />
            </Content>
        </Layout>
    );
};

export default Nav;