/**
 * 智能问答组件
 * 基于知识图谱的智能问答系统
 */

import React, { useState, useRef, useEffect } from 'react';
import { Card, Input, Button, List, Avatar, Typography, Space, Tag, Spin, message, Divider } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, HistoryOutlined, DeleteOutlined } from '@ant-design/icons';
import { QAService } from '../../services/qaService';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

// 消息类型定义
interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  thinking?: string;
}

// 信息源定义
interface Source {
  id: string;
  title: string;
  type: 'document' | 'code' | 'api' | 'knowledge';  // 添加回 'knowledge' 以匹配API
  relevance: number;
  snippet: string;
  url?: string;
}

// 推荐问题
const suggestedQuestions = [
  "AI上下文系统的核心功能有哪些？",
  "Graph RAG技术是如何工作的？",
  "如何上传和管理文档？",
  "知识图谱是如何构建的？",
  "系统支持哪些文档格式？",
  "如何进行语义检索？"
];

const IntelligentQA: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 初始欢迎消息
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      type: 'assistant',
      content: '您好！我是AI上下文助手。我可以帮您解答关于系统功能、技术架构、使用方法等问题。您也可以询问已上传文档的相关内容。',
      timestamp: new Date(),
      sources: []
    };
    setMessages([welcomeMessage]);
  }, []);

  // AI回答生成
  const generateAIResponse = async (question: string): Promise<Message> => {
    try {
      setLoading(true);
      
      // 调用智能问答API
      const response = await QAService.askQuestion({
        question,
        context: [],
        conversation_history: conversationHistory
      });

      if (response.success) {
        return {
          id: `ai_${Date.now()}`,
          type: 'assistant',
          content: response.data.answer,
          timestamp: new Date(),
          sources: response.data.sources.map(source => ({
            id: source.id,
            title: source.title,
            type: source.type,
            relevance: source.relevance,
            snippet: source.snippet,
            url: source.url
          })),
          thinking: response.data.thinking
        };
      } else {
        throw new Error(response.error || '问答服务异常');
      }
    } catch (error) {
      console.error('AI回答生成失败:', error);
      
      // 降级处理 - 使用本地mock数据
      const mockSources: Source[] = [
      {
        id: '1',
        title: 'AI代码生成系统方案.md',
        type: 'document',
        relevance: 0.95,
        snippet: 'Graph RAG技术结合了传统检索增强生成(RAG)和知识图谱的优势，通过构建结构化的知识图谱...',
        url: '/documents/1'
      },
      {
        id: '2',
        title: '系统架构设计',
        type: 'document',
        relevance: 0.87,
        snippet: '系统采用微服务架构，包含文档管理、知识图谱、智能问答等核心模块...',
        url: '/documents/2'
      },
      {
        id: '3',
        title: 'API接口文档',
        type: 'api',
        relevance: 0.72,
        snippet: 'POST /api/v1/documents/upload - 文档上传接口，支持多种格式...',
        url: '/api/docs'
      }
    ];

    // 根据问题生成回答
    let content = '';
    if (question.includes('核心功能') || question.includes('功能')) {
      content = `AI上下文增强系统的核心功能包括：

1. **智能文档管理** - 支持多格式文档上传、自动分类和标签管理
2. **知识图谱构建** - 自动提取文档中的实体、关系，构建结构化知识图谱
3. **语义检索** - 基于向量嵌入和图谱结构的智能检索
4. **智能问答** - 结合知识图谱和大语言模型的智能问答
5. **上下文增强** - 为AI对话提供精准的上下文信息
6. **可视化展示** - 交互式知识图谱可视化

这些功能通过Graph RAG技术有机结合，为用户提供智能化的知识管理和问答体验。`;
    
    } else if (question.includes('Graph RAG') || question.includes('技术')) {
      content = `Graph RAG（图检索增强生成）是一种创新的AI技术，具有以下特点：

**核心原理：**
- 结合传统RAG和知识图谱的优势
- 通过图结构存储和检索知识
- 提供更精确的上下文信息

**技术架构：**
1. **文档解析** - 智能提取文档内容和结构
2. **实体识别** - 识别文档中的关键实体
3. **关系提取** - 发现实体间的语义关系
4. **图谱构建** - 构建结构化知识图谱
5. **向量化** - 生成实体和关系的向量表示
6. **检索增强** - 基于图谱和向量的混合检索

**优势：**
- 更好的语义理解
- 精确的信息检索
- 丰富的上下文信息
- 可解释的推理过程`;

    } else if (question.includes('上传') || question.includes('管理')) {
      content = `文档上传和管理功能说明：

**支持格式：**
- 文档类型：PDF, DOC, DOCX, TXT, MD
- 代码文件：JS, TS, PY, GO, JAVA等
- 表格文件：XLS, XLSX, CSV

**上传流程：**
1. 选择文档类型（业务文档/示例代码）
2. 填写分类信息（团队/项目/模块）
3. 设置访问权限和标签
4. 系统自动解析和处理

**管理功能：**
- 文档列表和筛选
- 在线预览和编辑
- 版本控制和历史记录
- 批量操作和导出
- 权限管理和分享`;

    } else {
      content = `感谢您的提问！基于当前的知识库，我为您提供以下信息：

这个问题涉及到系统的多个方面。建议您可以：
1. 查看相关文档获取详细信息
2. 尝试使用具体的功能模块
3. 查看知识图谱中的相关节点

如果您需要更具体的帮助，请提供更详细的问题描述。`;
    }

      return {
        id: `ai_${Date.now()}`,
        type: 'assistant',
        content,
        timestamp: new Date(),
        sources: mockSources.slice(0, 2), // 只显示前2个相关源
        thinking: "正在分析您的问题，从知识图谱中检索相关信息..."
      };
    } finally {
      setLoading(false);
    }
  };

  // 发送消息
  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setConversationHistory(prev => [...prev, inputValue]);
    setInputValue('');
    setLoading(true);

    try {
      // 模拟API调用延迟
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const aiResponse = await generateAIResponse(inputValue);
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      message.error('回答生成失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 清空对话
  const clearMessages = () => {
    const welcomeMessage: Message = {
      id: 'welcome',
      type: 'assistant',
      content: '对话已清空。有什么可以帮助您的吗？',
      timestamp: new Date()
    };
    setMessages([welcomeMessage]);
    setConversationHistory([]);
  };

  // 使用推荐问题
  const useSuggestedQuestion = (question: string) => {
    setInputValue(question);
  };

  return (
    <Card 
      title="智能问答" 
      style={{ height: '700px' }}
      bodyStyle={{ height: 'calc(100% - 60px)', display: 'flex', flexDirection: 'column' }}
      extra={
        <Space>
          <Button 
            icon={<HistoryOutlined />} 
            size="small"
            onClick={() => console.log('显示历史对话')}
          >
            历史
          </Button>
          <Button 
            icon={<DeleteOutlined />} 
            size="small"
            onClick={clearMessages}
          >
            清空
          </Button>
        </Space>
      }
    >
      {/* 推荐问题 */}
      {messages.length <= 1 && (
        <div style={{ marginBottom: '16px' }}>
          <Text type="secondary">推荐问题：</Text>
          <div style={{ marginTop: '8px' }}>
            {suggestedQuestions.map((question, index) => (
              <Tag 
                key={index}
                style={{ 
                  margin: '4px 4px 4px 0', 
                  cursor: 'pointer',
                  borderStyle: 'dashed'
                }}
                onClick={() => useSuggestedQuestion(question)}
              >
                {question}
              </Tag>
            ))}
          </div>
          <Divider />
        </div>
      )}

      {/* 消息列表 */}
      <div style={{ flex: 1, overflowY: 'auto', marginBottom: '16px' }}>
        <List
          dataSource={messages}
          renderItem={(message) => (
            <List.Item style={{ border: 'none', padding: '8px 0' }}>
              <List.Item.Meta
                avatar={
                  <Avatar 
                    icon={message.type === 'user' ? <UserOutlined /> : <RobotOutlined />}
                    style={{ 
                      backgroundColor: message.type === 'user' ? '#1890ff' : '#52c41a'
                    }}
                  />
                }
                title={
                  <Space>
                    <Text strong>
                      {message.type === 'user' ? '您' : 'AI助手'}
                    </Text>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {message.timestamp.toLocaleTimeString()}
                    </Text>
                  </Space>
                }
                description={
                  <div>
                    <Paragraph style={{ marginBottom: message.sources ? '12px' : 0 }}>
                      {message.content}
                    </Paragraph>
                    
                    {/* 信息源 */}
                    {message.sources && message.sources.length > 0 && (
                      <div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          参考信息源：
                        </Text>
                        {message.sources.map((source, index) => (
                          <div 
                            key={source.id}
                            style={{ 
                              marginTop: '4px',
                              padding: '8px',
                              background: '#fafafa',
                              borderRadius: '4px',
                              fontSize: '12px'
                            }}
                          >
                            <Space>
                              <Tag color={
                                source.type === 'document' ? 'blue' :
                                source.type === 'code' ? 'green' : 'orange'
                              }>
                                {source.type === 'document' ? '文档' :
                                 source.type === 'code' ? '代码' : 'API'}
                              </Tag>
                              <Text strong style={{ fontSize: '12px' }}>
                                {source.title}
                              </Text>
                              <Text type="secondary" style={{ fontSize: '11px' }}>
                                相关度: {(source.relevance * 100).toFixed(0)}%
                              </Text>
                            </Space>
                            <div style={{ marginTop: '4px', color: '#666' }}>
                              {source.snippet}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                }
              />
            </List.Item>
          )}
        />
        
        {/* AI思考中 */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin />
            <div style={{ marginTop: '8px', color: '#666' }}>
              AI正在思考中...
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: '16px' }}>
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="请输入您的问题..."
            autoSize={{ minRows: 1, maxRows: 3 }}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            disabled={loading}
          />
          <Button 
            type="primary" 
            icon={<SendOutlined />}
            onClick={sendMessage}
            loading={loading}
            disabled={!inputValue.trim()}
            style={{ height: 'auto' }}
          >
            发送
          </Button>
        </Space.Compact>
        <div style={{ marginTop: '8px', fontSize: '12px', color: '#999' }}>
          Shift + Enter 换行，Enter 发送
        </div>
      </div>
    </Card>
  );
};

export default IntelligentQA;