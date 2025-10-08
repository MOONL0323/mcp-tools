import React, { useState } from 'react';
import { 
  Input, 
  Button, 
  Card, 
  List, 
  Tag, 
  Typography, 
  Space, 
  Spin, 
  Alert,
  Row,
  Col,
  Badge,
  Select
} from 'antd';
import { 
  SearchOutlined, 
  FileTextOutlined,
  ClockCircleOutlined,
  TagOutlined
} from '@ant-design/icons';
import { KnowledgeGraphApi, SearchResult, SearchResponse } from '../services/api_v2';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;
const { Option } = Select;

const EnhancedDocumentSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [topK, setTopK] = useState(10);
  const [fileType, setFileType] = useState<string | undefined>(undefined);

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
        content_type: 'document',
        file_type: fileType
      });

      setResults(response);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderResultItem = (item: SearchResult) => {
    return (
      <List.Item key={item.content_id}>
        <Card
          size="small"
          style={{ width: '100%' }}
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                <FileTextOutlined />
                <Text strong>{item.source_file}</Text>
                <Badge 
                  count={`${(item.similarity * 100).toFixed(1)}%`} 
                  style={{ backgroundColor: item.similarity > 0.8 ? '#52c41a' : item.similarity > 0.6 ? '#1890ff' : '#faad14' }}
                />
              </Space>
              <Tag color="green">文档</Tag>
            </div>
          }
        >
          <Row gutter={16}>
            <Col span={18}>
              <Paragraph 
                ellipsis={{ rows: 4, expandable: true, symbol: '展开' }}
                style={{ 
                  background: '#f5f5f5', 
                  padding: '8px', 
                  borderRadius: '4px'
                }}
              >
                {item.content}
              </Paragraph>
            </Col>
            <Col span={6}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    <TagOutlined /> 来源路径
                  </Text>
                  <br />
                  <Text code style={{ fontSize: '11px' }}>{item.source_path}</Text>
                </div>
                
                {(item.metadata.chunk_index !== undefined && item.metadata.total_chunks) && (
                  <div>
                    <Text type="secondary" style={{ fontSize: '12px' }}>片段位置</Text>
                    <br />
                    <Text>{item.metadata.chunk_index + 1} / {item.metadata.total_chunks}</Text>
                  </div>
                )}

                {item.metadata.file_type && (
                  <div>
                    <Text type="secondary" style={{ fontSize: '12px' }}>文件类型</Text>
                    <br />
                    <Tag color="blue">{item.metadata.file_type}</Tag>
                  </div>
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
      <Card title="文档搜索" style={{ marginBottom: 20 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Row gutter={16}>
            <Col span={16}>
              <TextArea
                placeholder="输入文档搜索内容..."
                value={query}
                onChange={e => setQuery(e.target.value)}
                onPressEnter={handleSearch}
                rows={3}
              />
            </Col>
            <Col span={8}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Row gutter={8}>
                  <Col span={12}>
                    <Select
                      placeholder="文件类型"
                      value={fileType}
                      onChange={setFileType}
                      allowClear
                      style={{ width: '100%' }}
                    >
                      <Option value=".pdf">PDF</Option>
                      <Option value=".docx">Word</Option>
                      <Option value=".txt">文本</Option>
                      <Option value=".md">Markdown</Option>
                    </Select>
                  </Col>
                  <Col span={12}>
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
                  搜索文档
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
              <FileTextOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
              <p style={{ marginTop: 16, color: '#999' }}>没有找到相关文档</p>
            </div>
          )}
        </Card>
      )}

      <Spin spinning={loading} style={{ display: loading ? 'block' : 'none' }} />
    </div>
  );
};

export default EnhancedDocumentSearch;