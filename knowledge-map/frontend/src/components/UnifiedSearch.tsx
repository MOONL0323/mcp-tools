import React, { useState } from 'react';
import { 
  Input, 
  Button, 
  Select, 
  Card, 
  List, 
  Tag, 
  Typography, 
  Space, 
  Spin, 
  Alert,
  Row,
  Col,
  Divider,
  Badge
} from 'antd';
import { 
  SearchOutlined, 
  FileTextOutlined, 
  CodeOutlined,
  ClockCircleOutlined,
  TagOutlined
} from '@ant-design/icons';
import { KnowledgeGraphApi, SearchResult, SearchResponse } from '../services/api_v2';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;
const { Option } = Select;

interface UnifiedSearchProps {}

const UnifiedSearch: React.FC<UnifiedSearchProps> = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // 搜索参数
  const [contentType, setContentType] = useState<'all' | 'document' | 'code'>('all');
  const [language, setLanguage] = useState<string | undefined>(undefined);
  const [topK, setTopK] = useState(10);

  const handleSearch = async () => {
    if (!query.trim()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await KnowledgeGraphApi.search({
        query: query.trim(),
        top_k: topK,
        content_type: contentType,
        language: language
      });

      setResults(response);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderResultItem = (item: SearchResult) => {
    const isCode = item.content_type === 'code';
    
    return (
      <List.Item key={item.content_id}>
        <Card
          size="small"
          style={{ width: '100%' }}
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                {isCode ? <CodeOutlined /> : <FileTextOutlined />}
                <Text strong>{item.source_file}</Text>
                <Badge 
                  count={`${(item.similarity * 100).toFixed(1)}%`} 
                  style={{ backgroundColor: item.similarity > 0.8 ? '#52c41a' : item.similarity > 0.6 ? '#1890ff' : '#faad14' }}
                />
              </Space>
              <Space>
                <Tag color={isCode ? 'blue' : 'green'}>
                  {isCode ? '代码' : '文档'}
                </Tag>
                {isCode && item.metadata.language && (
                  <Tag color="purple">{item.metadata.language}</Tag>
                )}
                {isCode && item.metadata.block_type && (
                  <Tag color="orange">{item.metadata.block_type}</Tag>
                )}
              </Space>
            </div>
          }
        >
          <Row gutter={16}>
            <Col span={16}>
              <Paragraph 
                ellipsis={{ rows: 4, expandable: true, symbol: '展开' }}
                style={{ 
                  background: '#f5f5f5', 
                  padding: '8px', 
                  borderRadius: '4px',
                  fontFamily: isCode ? 'Monaco, "Courier New", monospace' : 'inherit',
                  fontSize: isCode ? '12px' : '14px'
                }}
              >
                {item.content}
              </Paragraph>
            </Col>
            <Col span={8}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    <TagOutlined /> 来源路径
                  </Text>
                  <br />
                  <Text code style={{ fontSize: '11px' }}>{item.source_path}</Text>
                </div>
                
                {isCode && (
                  <>
                    {item.metadata.name && (
                      <div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>名称</Text>
                        <br />
                        <Text code>{item.metadata.name}</Text>
                      </div>
                    )}
                    
                    {item.metadata.signature && (
                      <div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>签名</Text>
                        <br />
                        <Text code style={{ fontSize: '11px' }}>{item.metadata.signature}</Text>
                      </div>
                    )}
                    
                    {(item.metadata.start_line || item.metadata.end_line) && (
                      <div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>行数</Text>
                        <br />
                        <Text>{item.metadata.start_line} - {item.metadata.end_line}</Text>
                      </div>
                    )}
                  </>
                )}
                
                {!isCode && (
                  <>
                    {(item.metadata.chunk_index !== undefined && item.metadata.total_chunks) && (
                      <div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>片段</Text>
                        <br />
                        <Text>{item.metadata.chunk_index + 1} / {item.metadata.total_chunks}</Text>
                      </div>
                    )}
                  </>
                )}
              </Space>
            </Col>
          </Row>
        </Card>
      </List.Item>
    );
  };

  return (
    <div style={{ padding: '20px' }}>
      <Card title="智能搜索" style={{ marginBottom: 20 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Row gutter={16}>
            <Col span={12}>
              <TextArea
                placeholder="输入搜索内容，支持自然语言查询..."
                value={query}
                onChange={e => setQuery(e.target.value)}
                onPressEnter={handleSearch}
                rows={3}
              />
            </Col>
            <Col span={12}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Row gutter={8}>
                  <Col span={8}>
                    <Select
                      placeholder="内容类型"
                      value={contentType}
                      onChange={setContentType}
                      style={{ width: '100%' }}
                    >
                      <Option value="all">全部</Option>
                      <Option value="document">文档</Option>
                      <Option value="code">代码</Option>
                    </Select>
                  </Col>
                  <Col span={8}>
                    <Select
                      placeholder="编程语言"
                      value={language}
                      onChange={setLanguage}
                      allowClear
                      style={{ width: '100%' }}
                    >
                      <Option value="python">Python</Option>
                      <Option value="javascript">JavaScript</Option>
                      <Option value="typescript">TypeScript</Option>
                      <Option value="java">Java</Option>
                      <Option value="cpp">C++</Option>
                      <Option value="go">Go</Option>
                    </Select>
                  </Col>
                  <Col span={8}>
                    <Select
                      placeholder="结果数量"
                      value={topK}
                      onChange={setTopK}
                      style={{ width: '100%' }}
                    >
                      <Option value={5}>5</Option>
                      <Option value={10}>10</Option>
                      <Option value={20}>20</Option>
                      <Option value={50}>50</Option>
                    </Select>
                  </Col>
                </Row>
                <Button
                  type="primary"
                  icon={<SearchOutlined />}
                  onClick={handleSearch}
                  loading={loading}
                  style={{ width: '100%' }}
                >
                  搜索
                </Button>
              </Space>
            </Col>
          </Row>
        </Space>
      </Card>

      {error && (
        <Alert
          type="error"
          message="搜索失败"
          description={error}
          style={{ marginBottom: 20 }}
          closable
        />
      )}

      {results && (
        <Card 
          title={
            <Space>
              <Text>搜索结果</Text>
              <Badge count={results.total_results} style={{ backgroundColor: '#52c41a' }} />
              <Text type="secondary">
                <ClockCircleOutlined /> 耗时 {(results.search_time * 1000).toFixed(0)}ms
              </Text>
            </Space>
          }
        >
          {results.results.length > 0 ? (
            <List
              dataSource={results.results}
              renderItem={renderResultItem}
              pagination={{
                pageSize: 5,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
              }}
            />
          ) : (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <SearchOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
              <p style={{ marginTop: 16, color: '#999' }}>没有找到相关内容</p>
            </div>
          )}
        </Card>
      )}

      <Spin spinning={loading} style={{ display: loading ? 'block' : 'none' }} />
    </div>
  );
};

export default UnifiedSearch;