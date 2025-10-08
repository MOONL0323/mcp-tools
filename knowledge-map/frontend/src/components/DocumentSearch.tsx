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
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileMarkdownOutlined
} from '@ant-design/icons';
import { KnowledgeGraphApi, SearchRequest, SearchResult } from '../services/api';

const { Search } = Input;
const { Text, Paragraph } = Typography;
const { Option } = Select;

interface DocumentSearchState {
  loading: boolean;
  results: SearchResult[];
  query: string;
  totalResults: number;
  searchTime: number;
}

interface DocumentSearchProps {
  onResultSelect?: (result: SearchResult) => void;
}

const DocumentSearch: React.FC<DocumentSearchProps> = ({ onResultSelect }) => {
  const [searchState, setSearchState] = useState<DocumentSearchState>({
    loading: false,
    results: [],
    query: '',
    totalResults: 0,
    searchTime: 0
  });
  
  const [searchConfig, setSearchConfig] = useState({
    topK: 15,
    documentType: 'all' // all, pdf, docx, txt, md
  });

  // 执行文档搜索
  const handleSearch = async (query: string) => {
    if (!query.trim()) return;
    
    setSearchState(prev => ({ ...prev, loading: true, query }));
    
    try {
      const startTime = Date.now();
      const searchRequest: SearchRequest = {
        query: query.trim(),
        top_k: searchConfig.topK,
        file_type: 'document'
      };

      const response = await KnowledgeGraphApi.searchKnowledge(searchRequest);
      const endTime = Date.now();
      
      // 过滤文档结果
      const documentResults = response.results.filter((result: SearchResult) => {
        // 基于metadata判断是否为文档内容
        const isDocumentFile = result.metadata?.file_type === 'document' || 
                              !result.metadata?.source_file?.match(/\.(go|py|js|ts|java|cpp|c)$/i);
        
        if (!isDocumentFile) return false;
        
        // 根据文档类型过滤
        if (searchConfig.documentType === 'all') return true;
        
        const sourceFile = result.metadata?.source_file || '';
        return sourceFile.toLowerCase().endsWith(`.${searchConfig.documentType}`);
      });

      setSearchState({
        loading: false,
        results: documentResults,
        query,
        totalResults: documentResults.length,
        searchTime: endTime - startTime
      });
      
    } catch (error: any) {
      console.error('文档搜索失败:', error);
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
      highlightedText = highlightedText.replace(regex, '<mark style="background-color: #ffe58f; padding: 1px 2px;">$1</mark>');
    });
    
    return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />;
  };

  // 格式化相似度分数
  const formatSimilarity = (similarity: number) => {
    const percentage = (similarity * 100).toFixed(1);
    const color = similarity > 0.8 ? '#52c41a' : similarity > 0.6 ? '#faad14' : '#ff4d4f';
    return <Tag color={color} style={{ fontSize: '11px' }}>{percentage}%</Tag>;
  };

  // 获取文档类型图标和标签
  const getDocumentTypeTag = (result: SearchResult) => {
    const sourceFile = result.metadata?.source_file || '';
    
    if (sourceFile.endsWith('.pdf')) {
      return <Tag color="red" icon={<FilePdfOutlined />}>PDF文档</Tag>;
    }
    if (sourceFile.match(/\.(docx?|doc)$/i)) {
      return <Tag color="blue" icon={<FileWordOutlined />}>Word文档</Tag>;
    }
    if (sourceFile.endsWith('.md')) {
      return <Tag color="purple" icon={<FileMarkdownOutlined />}>Markdown</Tag>;
    }
    if (sourceFile.endsWith('.txt')) {
      return <Tag color="default" icon={<FileTextOutlined />}>文本文档</Tag>;
    }
    
    return <Tag color="green" icon={<FileTextOutlined />}>文档</Tag>;
  };

  // 获取文档来源信息
  const getSourceInfo = (result: SearchResult) => {
    const sourceFile = result.metadata?.source_file;
    const pageNumber = result.metadata?.page_number;
    const chunkIndex = result.metadata?.chunk_index;
    
    if (!sourceFile) return null;
    
    const fileName = sourceFile.split('/').pop() || sourceFile;
    let sourceText = fileName;
    
    if (pageNumber !== undefined) {
      sourceText += ` (第${pageNumber}页)`;
    } else if (chunkIndex !== undefined) {
      sourceText += ` (第${chunkIndex + 1}段)`;
    }
    
    return sourceText;
  };

  // 文档搜索示例
  const exampleQueries = [
    'Raft算法原理',
    '分布式系统一致性',
    '数据库事务处理',
    '微服务架构设计',
    '系统性能优化',
    '安全认证机制'
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 搜索配置区域 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col flex="1">
            <Search
              placeholder="搜索文档内容、概念、知识点..."
              enterButton={
                <Button type="primary" icon={<SearchOutlined />}>
                  搜索文档
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
              <Text type="secondary" style={{ fontSize: '12px' }}>文档类型:</Text>
              <Select
                value={searchConfig.documentType}
                onChange={(value) => setSearchConfig(prev => ({ ...prev, documentType: value }))}
                size="small"
                style={{ width: 120 }}
              >
                <Option value="all">全部文档</Option>
                <Option value="pdf">PDF文档</Option>
                <Option value="docx">Word文档</Option>
                <Option value="md">Markdown</Option>
                <Option value="txt">文本文档</Option>
              </Select>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 搜索提示 */}
      {!searchState.query && (
        <Card style={{ marginBottom: 16 }}>
          <Alert
            message="文档搜索说明"
            description={
              <div>
                <p>📄 专门搜索文档内容，包括：PDF、Word、Markdown、文本等格式</p>
                <p>🎯 搜索结果会显示具体的来源文件和页码信息</p>
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
              <FileTextOutlined />
              <Text strong>文档搜索结果</Text>
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
            <div style={{ marginTop: 16 }}>正在搜索文档...</div>
          </div>
        ) : searchState.results.length === 0 && searchState.query ? (
          <Empty 
            description="未找到相关文档"
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
                    marginBottom: 12
                  }}>
                    <Space>
                      <Text strong style={{ fontSize: '14px' }}>
                        #{index + 1}
                      </Text>
                      {getDocumentTypeTag(result)}
                      {formatSimilarity(result.similarity)}
                    </Space>
                    {getSourceInfo(result) && (
                      <Tooltip title={`来源: ${result.metadata?.source_file || '未知'}`}>
                        <Tag icon={<FileTextOutlined />} color="blue" style={{ fontSize: '11px' }}>
                          {getSourceInfo(result)}
                        </Tag>
                      </Tooltip>
                    )}
                  </div>
                  
                  {/* 文档内容 */}
                  <div style={{ 
                    backgroundColor: '#fafafa',
                    border: '1px solid #e8e8e8',
                    borderRadius: '4px',
                    padding: '12px',
                    marginBottom: 8
                  }}>
                    <Paragraph
                      style={{ 
                        margin: 0,
                        fontSize: '13px',
                        lineHeight: 1.6,
                        color: '#262626'
                      }}
                      ellipsis={{ rows: 4, expandable: true, symbol: '展开更多内容' }}
                    >
                      {highlightKeywords(result.content, searchState.query)}
                    </Paragraph>
                  </div>
                  
                  {/* 元数据信息 */}
                  {result.metadata && Object.keys(result.metadata).length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Space wrap size="small">
                        {Object.entries(result.metadata)
                          .filter(([key]) => !['source_file', 'page_number', 'chunk_index', 'file_type'].includes(key))
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

export default DocumentSearch;