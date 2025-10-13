/**
 * 用户管理页面
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Avatar,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  DatePicker,
  message,
  Popconfirm,
  Typography,
  Row,
  Col,
  Statistic,
  Divider
} from 'antd';
import {
  UserOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  SearchOutlined,
  TeamOutlined,
  CrownOutlined,
  LockOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

// 用户数据接口
interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'manager' | 'user';
  team: string;
  status: 'active' | 'inactive' | 'suspended';
  last_login: string;
  created_at: string;
  avatar?: string;
  phone?: string;
  department?: string;
  permissions: string[];
}

// 用户统计接口
interface UserStats {
  total: number;
  active: number;
  inactive: number;
  admins: number;
  thisMonth: number;
}

const UserManager: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [searchText, setSearchText] = useState('');
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [form] = Form.useForm();
  const [stats, setStats] = useState<UserStats>({
    total: 0,
    active: 0,
    inactive: 0,
    admins: 0,
    thisMonth: 0
  });

  // 模拟用户数据
  const mockUsers: User[] = [
    {
      id: '1',
      username: 'admin',
      email: 'admin@example.com',
      full_name: '系统管理员',
      role: 'admin',
      team: 'admin-team',
      status: 'active',
      last_login: '2024-01-15T10:30:00Z',
      created_at: '2024-01-01T00:00:00Z',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=admin',
      phone: '13800138000',
      department: '技术部',
      permissions: ['all']
    },
    {
      id: '2',
      username: 'zhangsan',
      email: 'zhangsan@example.com',
      full_name: '张三',
      role: 'manager',
      team: 'frontend-team',
      status: 'active',
      last_login: '2024-01-14T15:20:00Z',
      created_at: '2024-01-05T00:00:00Z',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=zhangsan',
      phone: '13800138001',
      department: '前端开发部',
      permissions: ['read', 'write', 'manage_team']
    },
    {
      id: '3',
      username: 'lisi',
      email: 'lisi@example.com',
      full_name: '李四',
      role: 'user',
      team: 'backend-team',
      status: 'active',
      last_login: '2024-01-13T09:45:00Z',
      created_at: '2024-01-08T00:00:00Z',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=lisi',
      phone: '13800138002',
      department: '后端开发部',
      permissions: ['read', 'write']
    },
    {
      id: '4',
      username: 'wangwu',
      email: 'wangwu@example.com',
      full_name: '王五',
      role: 'user',
      team: 'ai-team',
      status: 'inactive',
      last_login: '2024-01-10T14:15:00Z',
      created_at: '2024-01-10T00:00:00Z',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=wangwu',
      phone: '13800138003',
      department: 'AI算法部',
      permissions: ['read']
    },
    {
      id: '5',
      username: 'zhaoliu',
      email: 'zhaoliu@example.com',
      full_name: '赵六',
      role: 'user',
      team: 'product-team',
      status: 'suspended',
      last_login: '2024-01-05T11:30:00Z',
      created_at: '2024-01-12T00:00:00Z',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=zhaoliu',
      phone: '13800138004',
      department: '产品部',
      permissions: ['read']
    }
  ];

  // 团队选项
  const teamOptions = [
    { value: 'admin-team', label: '管理团队' },
    { value: 'frontend-team', label: '前端开发团队' },
    { value: 'backend-team', label: '后端开发团队' },
    { value: 'ai-team', label: 'AI算法团队' },
    { value: 'product-team', label: '产品团队' }
  ];

  // 权限选项
  const permissionOptions = [
    { value: 'read', label: '读取权限' },
    { value: 'write', label: '写入权限' },
    { value: 'delete', label: '删除权限' },
    { value: 'manage_team', label: '团队管理' },
    { value: 'manage_system', label: '系统管理' },
    { value: 'all', label: '全部权限' }
  ];

  // 加载用户数据
  const loadUsers = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800));
      setUsers(mockUsers);
      
      // 计算统计数据
      const stats: UserStats = {
        total: mockUsers.length,
        active: mockUsers.filter(u => u.status === 'active').length,
        inactive: mockUsers.filter(u => u.status !== 'active').length,
        admins: mockUsers.filter(u => u.role === 'admin').length,
        thisMonth: mockUsers.filter(u => 
          dayjs(u.created_at).month() === dayjs().month()
        ).length
      };
      setStats(stats);
    } catch (error) {
      message.error('加载用户数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  // 筛选用户数据
  const filteredUsers = users.filter(user => {
    const matchSearch = !searchText || 
      user.full_name.toLowerCase().includes(searchText.toLowerCase()) ||
      user.username.toLowerCase().includes(searchText.toLowerCase()) ||
      user.email.toLowerCase().includes(searchText.toLowerCase());
    
    const matchRole = !selectedRole || user.role === selectedRole;
    const matchTeam = !selectedTeam || user.team === selectedTeam;
    
    return matchSearch && matchRole && matchTeam;
  });

  // 获取角色标签颜色
  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'red';
      case 'manager': return 'orange';
      case 'user': return 'blue';
      default: return 'default';
    }
  };

  // 获取状态标签颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'inactive': return 'default';
      case 'suspended': return 'red';
      default: return 'default';
    }
  };

  // 获取角色图标
  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin': return <CrownOutlined />;
      case 'manager': return <TeamOutlined />;
      case 'user': return <UserOutlined />;
      default: return <UserOutlined />;
    }
  };

  // 表格列定义
  const columns: ColumnsType<User> = [
    {
      title: '用户',
      dataIndex: 'user',
      key: 'user',
      render: (_, record) => (
        <Space>
          <Avatar 
            src={record.avatar} 
            icon={<UserOutlined />}
            size="small"
          />
          <div>
            <div style={{ fontWeight: 'bold' }}>{record.full_name}</div>
            <div style={{ fontSize: '12px', color: '#999' }}>
              @{record.username}
            </div>
          </div>
        </Space>
      ),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role) => (
        <Tag color={getRoleColor(role)} icon={getRoleIcon(role)}>
          {role === 'admin' ? '管理员' :
           role === 'manager' ? '经理' : '普通用户'}
        </Tag>
      ),
    },
    {
      title: '团队',
      dataIndex: 'team',
      key: 'team',
      render: (team) => {
        const teamOption = teamOptions.find(t => t.value === team);
        return teamOption ? teamOption.label : team;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status === 'active' ? '活跃' :
           status === 'inactive' ? '非活跃' : '已暂停'}
        </Tag>
      ),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (time) => dayjs(time).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除用户？"
            description="删除后无法恢复，请谨慎操作"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 编辑用户
  const handleEdit = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue({
      ...user,
      created_at: dayjs(user.created_at)
    });
    setModalVisible(true);
  };

  // 添加用户
  const handleAdd = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 删除用户
  const handleDelete = async (id: string) => {
    try {
      setUsers(users.filter(u => u.id !== id));
      message.success('用户删除成功');
    } catch (error) {
      message.error('删除用户失败');
    }
  };

  // 保存用户
  const handleSave = async (values: any) => {
    try {
      if (editingUser) {
        // 更新现有用户
        const updatedUsers = users.map(u => 
          u.id === editingUser.id 
            ? { ...u, ...values, created_at: values.created_at.toISOString() }
            : u
        );
        setUsers(updatedUsers);
        message.success('用户更新成功');
      } else {
        // 添加新用户
        const newUser: User = {
          id: `${Date.now()}`,
          ...values,
          created_at: values.created_at ? values.created_at.toISOString() : new Date().toISOString(),
          last_login: new Date().toISOString(),
          avatar: `https://api.dicebear.com/7.x/miniavs/svg?seed=${values.username}`
        };
        setUsers([...users, newUser]);
        message.success('用户添加成功');
      }
      
      setModalVisible(false);
      form.resetFields();
      loadUsers(); // 重新加载统计数据
    } catch (error) {
      message.error('保存用户失败');
    }
  };

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总用户数"
              value={stats.total}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={stats.active}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="管理员"
              value={stats.admins}
              prefix={<CrownOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="本月新增"
              value={stats.thisMonth}
              prefix={<PlusOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 用户管理表格 */}
      <Card
        title="用户管理"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            添加用户
          </Button>
        }
      >
        {/* 筛选区域 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
          <Col span={8}>
            <Search
              placeholder="搜索用户名、姓名或邮箱"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="筛选角色"
              value={selectedRole}
              onChange={setSelectedRole}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="admin">管理员</Option>
              <Option value="manager">经理</Option>
              <Option value="user">普通用户</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="筛选团队"
              value={selectedTeam}
              onChange={setSelectedTeam}
              allowClear
              style={{ width: '100%' }}
            >
              {teamOptions.map(team => (
                <Option key={team.value} value={team.value}>
                  {team.label}
                </Option>
              ))}
            </Select>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={filteredUsers}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>

      {/* 用户编辑/添加模态框 */}
      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="用户名"
                name="username"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input placeholder="输入用户名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="姓名"
                name="full_name"
                rules={[{ required: true, message: '请输入姓名' }]}
              >
                <Input placeholder="输入姓名" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="邮箱"
                name="email"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' }
                ]}
              >
                <Input placeholder="输入邮箱" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="手机号"
                name="phone"
              >
                <Input placeholder="输入手机号" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="角色"
                name="role"
                rules={[{ required: true, message: '请选择角色' }]}
              >
                <Select placeholder="选择角色">
                  <Option value="admin">管理员</Option>
                  <Option value="manager">经理</Option>
                  <Option value="user">普通用户</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="团队"
                name="team"
                rules={[{ required: true, message: '请选择团队' }]}
              >
                <Select placeholder="选择团队">
                  {teamOptions.map(team => (
                    <Option key={team.value} value={team.value}>
                      {team.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="状态"
                name="status"
                rules={[{ required: true, message: '请选择状态' }]}
              >
                <Select placeholder="选择状态">
                  <Option value="active">活跃</Option>
                  <Option value="inactive">非活跃</Option>
                  <Option value="suspended">已暂停</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="部门"
                name="department"
              >
                <Input placeholder="输入部门" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="权限"
            name="permissions"
            rules={[{ required: true, message: '请选择权限' }]}
          >
            <Select 
              mode="multiple" 
              placeholder="选择权限"
              allowClear
            >
              {permissionOptions.map(permission => (
                <Option key={permission.value} value={permission.value}>
                  {permission.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          {editingUser && (
            <Form.Item
              label="创建时间"
              name="created_at"
            >
              <DatePicker 
                showTime 
                style={{ width: '100%' }}
                disabled
              />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default UserManager;