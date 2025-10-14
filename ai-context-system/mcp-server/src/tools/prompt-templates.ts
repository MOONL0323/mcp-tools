/**
 * Prompt 模板工具
 * 
 * 提供预定义的 Prompt 模板，帮助 AI 更好地利用上下文：
 * 1. 代码生成模板
 * 2. 文档分析模板
 * 3. 架构设计模板
 * 4. 代码审查模板
 * 5. 调试辅助模板
 */

export interface PromptTemplate {
  name: string;
  description: string;
  template: string;
  variables: string[];
  example?: string;
  category: 'code_generation' | 'documentation' | 'architecture' | 'review' | 'debug';
}

/**
 * Prompt 模板服务
 */
export class PromptTemplatesService {
  private templates: Map<string, PromptTemplate>;

  constructor() {
    this.templates = new Map();
    this.initializeTemplates();
  }

  /**
   * 初始化所有模板
   */
  private initializeTemplates(): void {
    // 代码生成模板
    this.registerTemplate({
      name: 'code_generation_basic',
      description: '基础代码生成模板',
      category: 'code_generation',
      template: `请基于以下上下文生成 {language} 代码：

**需求描述**:
{requirement}

**参考示例**:
{examples}

**编码规范**:
{coding_standards}

**请生成**:
1. 完整的代码实现
2. 必要的注释和文档字符串
3. 单元测试用例（如适用）

**注意事项**:
- 遵循团队编码规范
- 参考示例中的最佳实践
- 确保代码可读性和可维护性`,
      variables: ['language', 'requirement', 'examples', 'coding_standards'],
      example: `请基于以下上下文生成 Python 代码：

**需求描述**:
实现一个用户认证服务，支持JWT令牌生成和验证

**参考示例**:
[从知识库检索到的 Flask JWT 示例]

**编码规范**:
[Python 编码规范]`
    });

    this.registerTemplate({
      name: 'code_generation_with_context',
      description: '带知识图谱上下文的代码生成',
      category: 'code_generation',
      template: `基于现有代码库生成新代码：

**目标功能**: {feature}
**目标语言**: {language}

**相关类和函数**:
{related_entities}

**依赖关系**:
{dependencies}

**使用模式**:
{usage_patterns}

**生成要求**:
1. 与现有代码风格保持一致
2. 正确处理依赖关系
3. 复用现有工具函数
4. 添加适当的错误处理

**输出格式**:
- 完整代码
- 导入语句
- 使用示例`,
      variables: ['feature', 'language', 'related_entities', 'dependencies', 'usage_patterns']
    });

    // 文档分析模板
    this.registerTemplate({
      name: 'document_analysis',
      description: '文档分析和总结模板',
      category: 'documentation',
      template: `请分析以下技术文档：

**文档内容**:
{document_content}

**分析要点**:
1. **核心概念**: 提取关键技术概念和术语
2. **架构设计**: 总结系统架构和组件关系
3. **技术决策**: 识别重要的技术选型和理由
4. **实现细节**: 提炼关键实现要点
5. **相关代码**: 关联相关的代码实现

**输出格式**:
- 文档摘要（200字以内）
- 关键概念列表
- 架构图（文字描述）
- 相关实体和关系`,
      variables: ['document_content']
    });

    this.registerTemplate({
      name: 'documentation_generation',
      description: '文档生成模板',
      category: 'documentation',
      template: `为以下代码生成完整文档：

**代码**:
\`\`\`{language}
{code}
\`\`\`

**上下文信息**:
- 模块: {module}
- 相关类: {related_classes}
- 使用场景: {usage_context}

**文档要求**:
1. **概述**: 模块/类/函数的用途和功能
2. **参数说明**: 详细的参数类型和含义
3. **返回值**: 返回值类型和说明
4. **使用示例**: 实际使用代码示例
5. **注意事项**: 特殊情况和边界条件
6. **相关链接**: 关联的设计文档和代码

**格式**: Markdown`,
      variables: ['language', 'code', 'module', 'related_classes', 'usage_context']
    });

    // 架构设计模板
    this.registerTemplate({
      name: 'architecture_design',
      description: '架构设计建议模板',
      category: 'architecture',
      template: `请为以下需求提供架构设计方案：

**业务需求**:
{requirements}

**技术约束**:
{constraints}

**现有系统**:
{existing_system}

**参考架构**:
{reference_architectures}

**设计要求**:
1. **整体架构**: 系统分层和模块划分
2. **技术选型**: 框架、数据库、中间件选择及理由
3. **接口设计**: 主要接口和数据流
4. **扩展性**: 如何支持未来扩展
5. **性能考虑**: 关键性能指标和优化策略
6. **安全性**: 安全措施和风险防范

**输出格式**:
- 架构图（组件和关系）
- 技术栈清单
- 关键设计决策
- 实施建议`,
      variables: ['requirements', 'constraints', 'existing_system', 'reference_architectures']
    });

    this.registerTemplate({
      name: 'api_design',
      description: 'API 设计模板',
      category: 'architecture',
      template: `设计以下功能的 RESTful API：

**功能描述**: {feature}
**用户角色**: {roles}
**数据模型**: {data_models}

**参考现有 API**:
{existing_apis}

**API 设计要求**:
1. **端点定义**: URL 路径、HTTP 方法
2. **请求格式**: 参数、请求体结构
3. **响应格式**: 成功响应、错误响应
4. **认证授权**: 认证方式、权限控制
5. **错误处理**: 错误码、错误信息
6. **版本控制**: API 版本管理策略

**输出格式**:
- OpenAPI/Swagger 规范
- 使用示例
- 测试用例`,
      variables: ['feature', 'roles', 'data_models', 'existing_apis']
    });

    // 代码审查模板
    this.registerTemplate({
      name: 'code_review',
      description: '代码审查模板',
      category: 'review',
      template: `请审查以下代码：

**代码**:
\`\`\`{language}
{code}
\`\`\`

**审查维度**:
1. **代码质量**: 可读性、可维护性、复杂度
2. **编码规范**: 是否符合团队规范
3. **最佳实践**: 是否遵循语言/框架最佳实践
4. **性能**: 潜在的性能问题
5. **安全**: 安全漏洞和风险
6. **测试**: 测试覆盖率和测试质量

**团队规范**:
{coding_standards}

**相似代码**:
{similar_code}

**输出格式**:
- 总体评价（优秀/良好/需改进）
- 具体问题列表（严重/一般/建议）
- 改进建议和示例代码
- 学习资源推荐`,
      variables: ['language', 'code', 'coding_standards', 'similar_code']
    });

    this.registerTemplate({
      name: 'security_review',
      description: '安全审查模板',
      category: 'review',
      template: `对以下代码进行安全审查：

**代码**:
\`\`\`{language}
{code}
\`\`\`

**安全检查点**:
1. **输入验证**: SQL注入、XSS、命令注入
2. **认证授权**: 身份验证、权限控制
3. **敏感数据**: 密码、密钥、个人信息处理
4. **加密**: 数据传输和存储加密
5. **错误处理**: 信息泄露风险
6. **依赖安全**: 第三方库漏洞

**安全标准**:
{security_standards}

**输出格式**:
- 安全风险评级（高/中/低）
- 漏洞详情和利用场景
- 修复建议和安全代码示例
- 安全测试用例`,
      variables: ['language', 'code', 'security_standards']
    });

    // 调试辅助模板
    this.registerTemplate({
      name: 'debug_assistance',
      description: '调试辅助模板',
      category: 'debug',
      template: `请帮助调试以下问题：

**错误信息**:
{error_message}

**相关代码**:
\`\`\`{language}
{code}
\`\`\`

**运行环境**:
{environment}

**复现步骤**:
{reproduction_steps}

**知识库检索**:
{similar_issues}

**分析要求**:
1. **问题诊断**: 识别根本原因
2. **错误原因**: 详细解释为什么会出错
3. **解决方案**: 提供多种解决方案
4. **预防措施**: 如何避免类似问题
5. **相关知识**: 相关技术概念和文档

**输出格式**:
- 问题摘要
- 根因分析
- 解决步骤（优先级排序）
- 验证方法`,
      variables: ['error_message', 'language', 'code', 'environment', 'reproduction_steps', 'similar_issues']
    });

    this.registerTemplate({
      name: 'performance_optimization',
      description: '性能优化模板',
      category: 'debug',
      template: `分析并优化以下代码的性能：

**代码**:
\`\`\`{language}
{code}
\`\`\`

**性能指标**:
{performance_metrics}

**瓶颈分析**:
{bottleneck_analysis}

**优化参考**:
{optimization_examples}

**优化建议要求**:
1. **瓶颈识别**: 找出性能瓶颈
2. **时间复杂度**: 分析算法复杂度
3. **优化策略**: 具体优化方案
4. **权衡考虑**: 性能 vs 可读性 vs 维护性
5. **基准测试**: 优化前后对比

**输出格式**:
- 性能分析报告
- 优化后的代码
- 性能提升预估
- 测试建议`,
      variables: ['language', 'code', 'performance_metrics', 'bottleneck_analysis', 'optimization_examples']
    });
  }

  /**
   * 注册模板
   */
  private registerTemplate(template: PromptTemplate): void {
    this.templates.set(template.name, template);
  }

  /**
   * 获取所有模板
   */
  getAllTemplates(): PromptTemplate[] {
    return Array.from(this.templates.values());
  }

  /**
   * 根据名称获取模板
   */
  getTemplate(name: string): PromptTemplate | undefined {
    return this.templates.get(name);
  }

  /**
   * 根据类别获取模板
   */
  getTemplatesByCategory(category: string): PromptTemplate[] {
    return Array.from(this.templates.values())
      .filter(t => t.category === category);
  }

  /**
   * 填充模板变量
   */
  fillTemplate(templateName: string, variables: Record<string, string>): string {
    const template = this.templates.get(templateName);
    
    if (!template) {
      throw new Error(`模板 "${templateName}" 不存在`);
    }

    let result = template.template;

    // 替换所有变量
    for (const [key, value] of Object.entries(variables)) {
      const placeholder = `{${key}}`;
      result = result.replace(new RegExp(placeholder, 'g'), value || '');
    }

    // 检查是否有未填充的变量
    const missingVars = template.variables.filter(v => !variables[v]);
    if (missingVars.length > 0) {
      console.warn(`模板 "${templateName}" 缺少变量: ${missingVars.join(', ')}`);
    }

    return result;
  }

  /**
   * 搜索模板
   */
  searchTemplates(keyword: string): PromptTemplate[] {
    const lowerKeyword = keyword.toLowerCase();
    
    return Array.from(this.templates.values())
      .filter(t => 
        t.name.toLowerCase().includes(lowerKeyword) ||
        t.description.toLowerCase().includes(lowerKeyword) ||
        t.category.toLowerCase().includes(lowerKeyword)
      );
  }
}

// 导出单例
export const promptTemplates = new PromptTemplatesService();
