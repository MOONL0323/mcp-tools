/**
 * 高级搜索组件 - 完全移除mock数据版本
 * 支持语义搜索、精确搜索、多维度筛选
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Input, 
  Button, 
  Row, 
  Col, 
  Select, 
  DatePicker, 
  Checkbox, 
  Space, 
  List, 
  Tag, 
  Typography, 
  Avatar,
  Spin,
  Empty,
  message,
  Divider,
  Tooltip,
  Progress
} from 'antd';
import { SearchService, SearchResultItem } from '../../services/searchService';
import { 
  SearchOutlined, 
  FilterOutlined, 
  FileTextOutlined, 
  CodeOutlined, 
  ApiOutlined,
  DownloadOutlined,
  EyeOutlined,
  StarOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { Title, Text, Paragraph } = Typography;

// 搜索模式类型
type SearchMode = 'semantic' | 'exact' | 'hybrid';

// 筛选条件接口
interface SearchFilters {
  type?: string;
  team?: string;
  project?: string;
  tags?: string[];
  dateRange?: [string, string];
  access_level?: string;
}

// 组件状态接口
interface ComponentSearchResultItem {
  id: string;
  type: 'document' | 'code' | 'api' | 'knowledge';
  title: string;
  description: string;
  content: string;
  author: string;
  authorAvatar: string;
  team: string;
  project: string;
  module: string;
  tags: string[];
  uploadTime: string;
  relevanceScore: number;
  matchedSegments: string[];
  fileSize: number;
  downloadCount: number;
  access_level: 'public' | 'team' | 'private';
}

const AdvancedSearch: React.FC = () => {
  // 状态管理
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchMode, setSearchMode] = useState<SearchMode>('hybrid');
  const [searchResults, setSearchResults] = useState<ComponentSearchResultItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [isSearched, setIsSearched] = useState<boolean>(false);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [showFilters, setShowFilters] = useState<boolean>(false);

  // 选项数据
  const searchModes = [
    { value: 'hybrid', label: '智能搜索', description: '结合语义和关键词搜索' },
    { value: 'semantic', label: '语义搜索', description: '基于内容含义搜索' },
    { value: 'exact', label: '精确搜索', description: '精确关键词匹配' }
  ];

  const documentTypes = [
    { value: 'document', label: '文档' },
    { value: 'code', label: '代码' },
    { value: 'api', label: 'API' },
    { value: 'knowledge', label: '知识库' }
  ];

  const teamOptions = [
    { value: 'frontend-team', label: '前端团队' },
    { value: 'backend-team', label: '后端团队' },
    { value: 'product-team', label: '产品团队' },
    { value: 'ai-team', label: 'AI算法团队' }
  ];

  const accessLevels = [
    { value: 'public', label: '公开' },
    { value: 'team', label: '团队内部' },
    { value: 'private', label: '私有' }
  ];

  // 执行搜索
  const performSearch = async (query: string, mode: SearchMode): Promise<ComponentSearchResultItem[]> => {
    try {
      const searchRequest = {
        query,
        mode: (mode === 'exact' ? 'keyword' : mode === 'semantic' ? 'semantic' : 'hybrid') as 'semantic' | 'keyword' | 'hybrid',
        filters: {
          doc_type: filters.type,
          team: filters.team,
          project: filters.project,
          tags: filters.tags,
          date_range: filters.dateRange ? {
            start: filters.dateRange[0],
            end: filters.dateRange[1]
          } : undefined
        },
        limit: 20
      };

      const response = await SearchService.search(searchRequest);
      
      if (response.success) {
        // 转换API响应到组件期望的格式
        return response.data.results.map(item => ({
          id: item.id,
          type: item.type as any,
          title: item.title,
          description: item.description,
          content: item.content.substring(0, 200) + '...',
          author: item.metadata.team || '系统',
          authorAvatar: `https://api.dicebear.com/7.x/miniavs/svg?seed=${item.id}`,
          team: item.metadata.team || '',
          project: item.metadata.project || '',
          module: '',
          tags: item.metadata.tags || [],
          uploadTime: item.metadata.created_at || new Date().toISOString(),
          relevanceScore: item.score,
          matchedSegments: [item.description],
          fileSize: 0,
          downloadCount: 0,
          access_level: 'team' as any
        }));
      } else {
        throw new Error(response.error || '搜索失败');
      }
    } catch (error) {
      console.error('搜索失败:', error);
      message.error('搜索服务暂时不可用，请稍后重试');
      return [];
    }
  };

  // 执行搜索
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }

    setLoading(true);
    try {
      const results = await performSearch(searchQuery, searchMode);
      setSearchResults(results);
      setIsSearched(true);
      
      if (results.length > 0) {
        message.success(`找到 ${results.length} 个相关结果`);
      } else {
        message.info('未找到相关结果，请尝试其他关键词');
      }
    } catch (error) {
      console.error('搜索失败:', error);
      message.error('搜索失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 重置搜索
  const handleReset = () => {
    setSearchQuery('');
    setSearchResults([]);
    setIsSearched(false);
    setFilters({});
    message.info('搜索条件已重置');
  };

  // 获取文档类型图标
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'document': return <FileTextOutlined style={{ color: '#1890ff' }} />;
      case 'code': return <CodeOutlined style={{ color: '#52c41a' }} />;
      case 'api': return <ApiOutlined style={{ color: '#fa8c16' }} />;
      case 'knowledge': return <StarOutlined style={{ color: '#eb2f96' }} />;
      default: return <FileTextOutlined />;
    }
  };

  // 格式化时间
  const formatTime = (timeStr: string) => {
    return dayjs(timeStr).format('YYYY-MM-DD HH:mm');
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '--';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="advanced-search">
      {/* 搜索头部 */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Search
              placeholder="请输入搜索关键词..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSearch={handleSearch}
              size="large"
              loading={loading}
              enterButton={
                <Button type="primary" icon={<SearchOutlined />}>
                  搜索
                </Button>
              }
            />
          </Col>
        </Row>

        {/* 搜索模式选择 */}
        <Row style={{ marginTop: 16 }} gutter={16} align="middle">
          <Col>
            <Text strong>搜索模式：</Text>
          </Col>
          <Col>
            <Select
              value={searchMode}
              onChange={setSearchMode}
              style={{ width: 150 }}
            >
              {searchModes.map(mode => (
                <Option key={mode.value} value={mode.value}>
                  <Tooltip title={mode.description}>
                    {mode.label}
                  </Tooltip>
                </Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Button
              icon={<FilterOutlined />}
              onClick={() => setShowFilters(!showFilters)}
            >
              {showFilters ? '隐藏筛选' : '显示筛选'}
            </Button>
          </Col>
          <Col>
            <Button onClick={handleReset}>
              重置
            </Button>
          </Col>
        </Row>

        {/* 高级筛选 */}
        {showFilters && (
          <Card size="small" style={{ marginTop: 16, backgroundColor: '#fafafa' }}>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Text strong>文档类型：</Text>
                <Select
                  placeholder="选择类型"
                  style={{ width: '100%', marginTop: 8 }}
                  value={filters.type}
                  onChange={(value) => setFilters({ ...filters, type: value })}
                  allowClear
                >
                  {documentTypes.map(type => (
                    <Option key={type.value} value={type.value}>
                      {getTypeIcon(type.value)} {type.label}
                    </Option>
                  ))}
                </Select>
              </Col>

              <Col span={6}>
                <Text strong>团队：</Text>
                <Select
                  placeholder="选择团队"
                  style={{ width: '100%', marginTop: 8 }}
                  value={filters.team}
                  onChange={(value) => setFilters({ ...filters, team: value })}
                  allowClear
                >
                  {teamOptions.map(team => (
                    <Option key={team.value} value={team.value}>{team.label}</Option>
                  ))}
                </Select>
              </Col>

              <Col span={6}>
                <Text strong>访问级别：</Text>
                <Select
                  placeholder="选择级别"
                  style={{ width: '100%', marginTop: 8 }}
                  value={filters.access_level}
                  onChange={(value) => setFilters({ ...filters, access_level: value })}
                  allowClear
                >
                  {accessLevels.map(level => (
                    <Option key={level.value} value={level.value}>{level.label}</Option>
                  ))}
                </Select>
              </Col>

              <Col span={6}>
                <Text strong>时间范围：</Text>
                <RangePicker
                  style={{ width: '100%', marginTop: 8 }}
                  onChange={(dates) => {
                    if (dates) {
                      setFilters({
                        ...filters,
                        dateRange: [dates[0]!.toISOString(), dates[1]!.toISOString()]
                      });
                    } else {
                      setFilters({ ...filters, dateRange: undefined });
                    }
                  }}
                />
              </Col>
            </Row>
          </Card>
        )}
      </Card>

      {/* 搜索结果 */}
      {isSearched && (
        <Card 
          title={
            <Space>
              <Title level={4} style={{ margin: 0 }}>搜索结果</Title>
              {searchResults.length > 0 && (
                <Text type="secondary">共找到 {searchResults.length} 个结果</Text>
              )}
            </Space>
          }
        >
          <Spin spinning={loading}>
            {searchResults.length === 0 ? (
              <Empty
                description="未找到相关结果"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ) : (
              <List
                itemLayout="vertical"
                dataSource={searchResults}
                pagination={{
                  pageSize: 5,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 条结果`,
                }}
                renderItem={(item) => (
                  <List.Item
                    key={item.id}
                    actions={[
                      <Button type="link" icon={<EyeOutlined />}>查看</Button>,
                      <Button type="link" icon={<DownloadOutlined />}>下载</Button>,
                      <Text type="secondary">{item.downloadCount} 下载</Text>,
                    ]}
                    extra={
                      <div style={{ textAlign: 'right' }}>
                        <Progress
                          type="circle"
                          size={60}
                          percent={Math.round(item.relevanceScore * 100)}
                          format={(percent) => `${percent}%`}
                        />
                        <div style={{ marginTop: 8 }}>
                          <Text type="secondary">相关度</Text>
                        </div>
                      </div>
                    }
                  >
                    <List.Item.Meta
                      avatar={
                        <div style={{ textAlign: 'center' }}>
                          {getTypeIcon(item.type)}
                          <div style={{ marginTop: 4 }}>
                            <Avatar size={40} src={item.authorAvatar} />
                          </div>
                        </div>
                      }
                      title={
                        <Space>
                          <Text strong style={{ fontSize: 16 }}>{item.title}</Text>
                          <Tag color="blue">{item.type}</Tag>
                          {item.team && <Tag color="green">{item.team}</Tag>}
                        </Space>
                      }
                      description={
                        <div>
                          <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0 }}>
                            {item.description}
                          </Paragraph>
                          <div style={{ marginTop: 8 }}>
                            <Space wrap>
                              {item.tags.map(tag => (
                                <Tag key={tag} color="default" style={{ fontSize: 12 }}>
                                  {tag}
                                </Tag>
                              ))}
                            </Space>
                          </div>
                        </div>
                      }
                    />
                    
                    {/* 匹配片段 */}
                    {item.matchedSegments.length > 0 && (
                      <div style={{ marginTop: 12, padding: 12, backgroundColor: '#f6f6f6', borderRadius: 4 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>匹配内容：</Text>
                        {item.matchedSegments.map((segment, index) => (
                          <div key={index} style={{ marginTop: 4 }}>
                            <Text style={{ fontSize: 13 }}>...{segment}...</Text>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* 元信息 */}
                    <div style={{ marginTop: 12 }}>
                      <Space split={<Divider type="vertical" />} size="small">
                        <Text type="secondary">
                          <ClockCircleOutlined /> {formatTime(item.uploadTime)}
                        </Text>
                        <Text type="secondary">作者：{item.author}</Text>
                        <Text type="secondary">大小：{formatFileSize(item.fileSize)}</Text>
                        {item.project && <Text type="secondary">项目：{item.project}</Text>}
                      </Space>
                    </div>
                  </List.Item>
                )}
              />
            )}
          </Spin>
        </Card>
      )}
    </div>
  );
};

export default AdvancedSearch;