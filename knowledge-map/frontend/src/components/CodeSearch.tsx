import React, { useState } from 'react';
import {
  Card,
  Input,
  Button,
  List,
  Typography,
  Space,
  Empty,
  Spin,
  Tag,
  Row,
  Col,
  Slider,
  Tooltip,
  Alert,
  Select
} from 'antd';
import {
  SearchOutlined,
  CodeOutlined,
  FunctionOutlined,
  ApiOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { KnowledgeGraphApi, SearchRequest, SearchResult } from '../services/api';

const { Search } = Input;
const { Text, Paragraph } = Typography;
const { Option } = Select;

interface CodeSearchState {
  loading: boolean;
  results: SearchResult[];
  query: string;
  totalResults: number;
  searchTime: number;
}

interface CodeSearchProps {
  onResultSelect?: (result: SearchResult) => void;
}

const CodeSearch: React.FC<CodeSearchProps> = ({ onResultSelect }) => {
  const [searchState, setSearchState] = useState<CodeSearchState>({
    loading: false,
    results: [],
    query: '',
    totalResults: 0,
    searchTime: 0
  });
  
  const [searchConfig, setSearchConfig] = useState({
    topK: 10,
    codeType: 'all' // all, struct, function, interface, module
  });

  // 执行代码搜索
  const handleSearch = async (query: string) => {
    if (!query.trim()) return;
    
    setSearchState(prev => ({ ...prev, loading: true, query }));
    
    try {
      const startTime = Date.now();
      const searchRequest: SearchRequest = {
        query: query.trim(),
        top_k: searchConfig.topK,
        // 添加代码文件过滤器
        file_type: 'code'
      };

      const response = await KnowledgeGraphApi.searchKnowledge(searchRequest);
      const endTime = Date.now();
      
      // 过滤代码结果
      const codeResults = response.results.filter((result: SearchResult) => {
        // 基于metadata或content判断是否为代码内容
        const isCodeFile = result.metadata?.file_type === 'code' || 
                          result.metadata?.source_file?.match(/\.(go|py|js|ts|java|cpp|c)$/i);
        
        if (!isCodeFile) return false;
        
        // 根据代码类型过滤
        if (searchConfig.codeType === 'all') return true;
        
        const content = result.content.toLowerCase();
        switch (searchConfig.codeType) {
          case 'struct':
            return content.includes('struct') || content.includes('class') || content.includes('interface');
          case 'function':
            return content.includes('func') || content.includes('function') || content.includes('def');
          case 'interface':
            return content.includes('interface') || content.includes('protocol');
          case 'module':
            return result.metadata?.source_file?.match(/\.(mod|sum|json|yaml)$/i);
          default:
            return true;
        }
      });

      setSearchState({
        loading: false,
        results: codeResults,
        query,
        totalResults: codeResults.length,
        searchTime: endTime - startTime
      });
      
    } catch (error: any) {
      console.error('代码搜索失败:', error);
      setSearchState(prev => ({ 
        ...prev, 
        loading: false, 
        results: [], 
        totalResults: 0 
      }));
    }
  };

  // 高亮关键词
  const highlightKeywords = (text: string, query: string) => {
    if (!query) return text;
    
    const keywords = query.split(/\s+/).filter(k => k.length > 0);
    let highlightedText = text;
    
    keywords.forEach(keyword => {
      const regex = new RegExp(`(${keyword})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark style="background-color: #fff566; padding: 1px 2px;">$1</mark>');
    });
    
    return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />;
  };

  // 格式化相似度分数
  const formatSimilarity = (similarity: number) => {
    const percentage = (similarity * 100).toFixed(1);
    const color = similarity > 0.8 ? '#52c41a' : similarity > 0.6 ? '#faad14' : '#ff4d4f';
    return <Tag color={color} style={{ fontSize: '11px' }}>{percentage}%</Tag>;
  };

  // 获取代码类型标签
  const getCodeTypeTag = (result: SearchResult) => {
    const content = result.content.toLowerCase();
    const sourceFile = result.metadata?.source_file || '';
    
    if (sourceFile.endsWith('.go')) {
      if (content.includes('type ') && content.includes('struct')) {
        return <Tag color="blue" icon={<ApiOutlined />}>Go结构体</Tag>;
      }
      if (content.includes('type ') && content.includes('interface')) {
        return <Tag color="cyan" icon={<ApiOutlined />}>Go接口</Tag>;
      }
      if (content.includes('func ')) {
        return <Tag color="green" icon={<FunctionOutlined />}>Go函数</Tag>;
      }
      if (sourceFile.endsWith('.mod')) {
        return <Tag color="orange" icon={<FileTextOutlined />}>Go模块</Tag>;
      }
    }
    
    if (sourceFile.match(/\.(py|js|ts|java)$/i)) {
      if (content.includes('class ')) {
        return <Tag color="purple" icon={<ApiOutlined />}>类定义</Tag>;
      }
      if (content.includes('function ') || content.includes('def ')) {
        return <Tag color="green" icon={<FunctionOutlined />}>函数</Tag>;
      }
    }
    
    return <Tag color="default" icon={<CodeOutlined />}>代码</Tag>;
  };

  // 代码搜索示例
  const exampleQueries = [
    'User结构体定义',
    '用户认证函数',
    '数据库连接接口',
    'HTTP处理器',
    'JWT令牌生成',
    '错误处理机制'
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 搜索配置区域 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col flex="1">
            <Search
              placeholder="搜索代码结构、函数、接口..."
              enterButton={
                <Button type="primary" icon={<SearchOutlined />}>
                  搜索代码
                </Button>
              }
              size="large"
              onSearch={handleSearch}
              loading={searchState.loading}
              allowClear
            />
          </Col>
        </Row>
        
        <Row gutter={16} style={{ marginTop: 12 }}>
          <Col>
            <Space align="center">
              <Text type="secondary" style={{ fontSize: '12px' }}>结果数量:</Text>
              <Slider
                min={5}
                max={50}
                value={searchConfig.topK}
                onChange={(value) => setSearchConfig(prev => ({ ...prev, topK: value }))}
                style={{ width: 80 }}
              />
              <Text style={{ fontSize: '12px', minWidth: '30px' }}>{searchConfig.topK}</Text>
            </Space>
          </Col>
          <Col>
            <Space align="center">
              <Text type="secondary" style={{ fontSize: '12px' }}>代码类型:</Text>
              <Select
                value={searchConfig.codeType}
                onChange={(value) => setSearchConfig(prev => ({ ...prev, codeType: value }))}
                size="small"
                style={{ width: 120 }}
              >
                <Option value="all">全部代码</Option>
                <Option value="struct">结构体/类</Option>
                <Option value="function">函数/方法</Option>
                <Option value="interface">接口</Option>
                <Option value="module">模块文件</Option>
              </Select>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 搜索提示 */}
      {!searchState.query && (
        <Card style={{ marginBottom: 16 }}>
          <Alert
            message="代码搜索说明"
            description={
              <div>
                <p>🔍 专门搜索代码相关内容，包括：Go结构体、函数、接口、模块等</p>
                <p>💡 搜索建议:</p>
                <Space wrap style={{ marginTop: 8 }}>
                  {exampleQueries.map((query, index) => (
                    <Button 
                      key={index}
                      size="small" 
                      type="text"
                      onClick={() => handleSearch(query)}
                      style={{ padding: '2px 8px', height: 'auto' }}
                    >
                      "{query}"
                    </Button>
                  ))}
                </Space>
              </div>
            }
            type="info"
            showIcon
          />
        </Card>
      )}

      {/* 搜索结果 */}
      <Card 
        title={
          searchState.query ? (
            <Space>
              <CodeOutlined />
              <Text strong>代码搜索结果</Text>
              {searchState.totalResults > 0 && (
                <Text type="secondary">
                  找到 {searchState.totalResults} 个结果 (耗时 {searchState.searchTime}ms)
                </Text>
              )}
            </Space>
          ) : null
        }
        style={{ flex: 1, overflow: 'hidden' }}
        bodyStyle={{ height: '100%', overflow: 'auto', padding: searchState.results.length ? '0' : '24px' }}
      >
        {searchState.loading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>正在搜索代码...</div>
          </div>
        ) : searchState.results.length === 0 && searchState.query ? (
          <Empty 
            description="未找到相关代码"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            dataSource={searchState.results}
            renderItem={(result, index) => (
              <List.Item 
                style={{ 
                  padding: '16px 24px', 
                  borderBottom: '1px solid #f0f0f0',
                  cursor: onResultSelect ? 'pointer' : 'default'
                }}
                onClick={() => onResultSelect?.(result)}
              >
                <div style={{ width: '100%' }}>
                  {/* 结果头部 */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: 8
                  }}>
                    <Space>
                      <Text strong style={{ fontSize: '14px' }}>
                        #{index + 1}
                      </Text>
                      {getCodeTypeTag(result)}
                      {formatSimilarity(result.similarity)}
                    </Space>
                    {result.metadata?.source_file && (
                      <Tooltip title={`来源文件: ${result.metadata.source_file}`}>
                        <Tag icon={<FileTextOutlined />} style={{ fontSize: '11px' }}>
                          {result.metadata.source_file.split('/').pop() || result.metadata.source_file}
                        </Tag>
                      </Tooltip>
                    )}
                  </div>
                  
                  {/* 代码内容 */}
                  <div style={{ 
                    backgroundColor: '#f6f8fa',
                    border: '1px solid #e1e4e8',
                    borderRadius: '6px',
                    padding: '12px',
                    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                    fontSize: '12px',
                    lineHeight: 1.5,
                    marginBottom: 8
                  }}>
                    <Paragraph
                      style={{ margin: 0, color: '#24292e' }}
                      ellipsis={{ rows: 6, expandable: true, symbol: '展开更多代码' }}
                    >
                      {highlightKeywords(result.content, searchState.query)}
                    </Paragraph>
                  </div>
                  
                  {/* 元数据 */}
                  {result.metadata && Object.keys(result.metadata).length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Space wrap size="small">
                        {Object.entries(result.metadata)
                          .filter(([key]) => !['source_file'].includes(key)) // 排除已显示的字段
                          .map(([key, value]) => (
                            <Tag key={key} style={{ fontSize: '10px', margin: '1px' }}>
                              {key}: {String(value)}
                            </Tag>
                          ))}
                      </Space>
                    </div>
                  )}
                </div>
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  );
};

export default CodeSearch;