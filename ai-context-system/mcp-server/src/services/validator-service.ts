/**
 * 参数验证服务
 */

import Ajv, { JSONSchemaType } from 'ajv';
import addFormats from 'ajv-formats';
import { 
  SearchCodeExamplesParams, 
  GetDesignDocsParams, 
  GetCodingStandardsParams,
  QueryKnowledgeGraphParams 
} from '../types/tool-params.js';

export class ValidatorService {
  private ajv: Ajv;

  constructor() {
    this.ajv = new Ajv({ allErrors: true });
    addFormats(this.ajv);
    
    // 注册自定义验证规则
    this.registerCustomValidators();
  }

  /**
   * 注册自定义验证规则
   */
  private registerCustomValidators(): void {
    // 验证编程语言
    this.ajv.addKeyword({
      keyword: 'validLanguage',
      type: 'string',
      schemaType: 'boolean',
      compile: (schema: boolean) => {
        return function validate(data: string) {
          if (!schema) return true;
          
          const validLanguages = ['python', 'typescript', 'javascript', 'java', 'go', 'cpp', 'c', 'rust'];
          return validLanguages.includes(data.toLowerCase());
        };
      }
    });

    // 验证框架名称
    this.ajv.addKeyword({
      keyword: 'validFramework',
      type: 'string',
      schemaType: 'boolean',
      compile: (schema: boolean) => {
        return function validate(data: string) {
          if (!schema) return true;
          
          const validFrameworks = [
            'react', 'vue', 'angular', 'express', 'fastapi', 'django', 
            'spring', 'gin', 'fiber', 'nestjs', 'next.js', 'nuxt.js'
          ];
          return validFrameworks.some(fw => data.toLowerCase().includes(fw.toLowerCase()));
        };
      }
    });
  }

  /**
   * 验证搜索代码示例参数
   */
  validateSearchParams(params: SearchCodeExamplesParams): void {
    const schema: JSONSchemaType<SearchCodeExamplesParams> = {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          minLength: 1,
          maxLength: 500
        },
        language: {
          type: 'string',
          enum: ['python', 'typescript', 'javascript', 'java', 'go', 'cpp'],
          nullable: true
        },
        framework: {
          type: 'string',
          minLength: 1,
          maxLength: 50,
          nullable: true
        },
        limit: {
          type: 'number',
          minimum: 1,
          maximum: 50,
          nullable: true
        }
      },
      required: ['query'],
      additionalProperties: false
    };

    const validate = this.ajv.compile(schema);
    
    if (!validate(params)) {
      const errors = validate.errors?.map(err => 
        `${err.instancePath || 'root'}${err.instancePath ? '.' : ''}${err.keyword}: ${err.message}`
      ).join('; ');
      
      throw new Error(`参数验证失败: ${errors}`);
    }

    // 额外的业务逻辑验证
    if (params.query.trim().length === 0) {
      throw new Error('查询不能为空字符串');
    }

    // 检查查询是否包含可能的恶意内容
    this.validateQuery(params.query);
  }

  /**
   * 验证获取设计文档参数
   */
  validateDesignDocsParams(params: GetDesignDocsParams): void {
    const schema: JSONSchemaType<GetDesignDocsParams> = {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          minLength: 1,
          maxLength: 500
        },
        doc_type: {
          type: 'string',
          enum: ['api_design', 'architecture', 'database_design', 'business_logic'],
          nullable: true
        },
        component: {
          type: 'string',
          minLength: 1,
          maxLength: 100,
          nullable: true
        },
        team: {
          type: 'string',
          minLength: 1,
          maxLength: 50,
          nullable: true
        },
        project: {
          type: 'string',
          minLength: 1,
          maxLength: 100,
          nullable: true
        }
      },
      required: ['query'],
      additionalProperties: false
    };

    const validate = this.ajv.compile(schema);
    
    if (!validate(params)) {
      const errors = validate.errors?.map(err => 
        `${err.instancePath || 'root'}${err.instancePath ? '.' : ''}${err.keyword}: ${err.message}`
      ).join('; ');
      
      throw new Error(`参数验证失败: ${errors}`);
    }

    this.validateQuery(params.query);
  }

  /**
   * 验证编码规范参数
   */
  validateCodingStandardsParams(params: GetCodingStandardsParams): void {
    const schema: JSONSchemaType<GetCodingStandardsParams> = {
      type: 'object',
      properties: {
        language: {
          type: 'string',
          enum: ['python', 'typescript', 'javascript', 'java', 'go', 'cpp']
        },
        category: {
          type: 'string',
          enum: ['naming', 'structure', 'testing', 'documentation', 'security'],
          nullable: true
        }
      },
      required: ['language'],
      additionalProperties: false
    };

    const validate = this.ajv.compile(schema);
    
    if (!validate(params)) {
      const errors = validate.errors?.map(err => 
        `${err.instancePath || 'root'}${err.instancePath ? '.' : ''}${err.keyword}: ${err.message}`
      ).join('; ');
      
      throw new Error(`参数验证失败: ${errors}`);
    }
  }

  /**
   * 验证知识图谱查询参数
   */
  validateGraphQueryParams(params: QueryKnowledgeGraphParams): void {
    const schema: JSONSchemaType<QueryKnowledgeGraphParams> = {
      type: 'object',
      properties: {
        entity: {
          type: 'string',
          minLength: 1,
          maxLength: 200
        },
        relation_type: {
          type: 'string',
          enum: ['CALLS', 'INHERITS', 'USES', 'DEPENDS_ON', 'IMPLEMENTS'],
          nullable: true
        },
        depth: {
          type: 'number',
          minimum: 1,
          maximum: 10,
          nullable: true
        }
      },
      required: ['entity'],
      additionalProperties: false
    };

    const validate = this.ajv.compile(schema);
    
    if (!validate(params)) {
      const errors = validate.errors?.map(err => 
        `${err.instancePath || 'root'}${err.instancePath ? '.' : ''}${err.keyword}: ${err.message}`
      ).join('; ');
      
      throw new Error(`参数验证失败: ${errors}`);
    }

    // 验证实体名称格式
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(params.entity)) {
      throw new Error('实体名称格式不正确，只能包含字母、数字和下划线，且不能以数字开头');
    }
  }

  /**
   * 验证查询字符串
   */
  private validateQuery(query: string): void {
    // 检查危险字符
    const dangerousPatterns = [
      /<script/i,
      /javascript:/i,
      /on\w+\s*=/i,
      /eval\s*\(/i,
      /exec\s*\(/i,
      /system\s*\(/i,
      /\|\s*rm\s+/i,
      /;\s*rm\s+/i,
      /&&\s*rm\s+/i
    ];

    for (const pattern of dangerousPatterns) {
      if (pattern.test(query)) {
        throw new Error('查询包含不安全的内容');
      }
    }

    // 检查查询长度和复杂度
    if (query.length > 1000) {
      throw new Error('查询过长，请简化查询内容');
    }

    // 检查是否全是特殊字符
    if (!/[a-zA-Z0-9\u4e00-\u9fff]/.test(query)) {
      throw new Error('查询必须包含有效的字母或数字');
    }
  }

  /**
   * 清理和标准化查询字符串
   */
  sanitizeQuery(query: string): string {
    return query
      .trim()
      .replace(/\s+/g, ' ') // 合并多个空格
      .replace(/[^\w\s\u4e00-\u9fff\-_.]/g, '') // 移除特殊字符，保留中文
      .substring(0, 500); // 限制长度
  }

  /**
   * 验证文件路径
   */
  validateFilePath(filePath: string): boolean {
    // 检查路径遍历攻击
    const dangerousPatterns = [
      /\.\./,
      /\/\.\./,
      /\\\.\./,
      /\0/,
      /\|/,
      /;/,
      /&/
    ];

    return !dangerousPatterns.some(pattern => pattern.test(filePath));
  }

  /**
   * 验证实体名称
   */
  validateEntityName(name: string): boolean {
    // 实体名称只能包含字母、数字、下划线和点
    return /^[a-zA-Z_][a-zA-Z0-9_.]*$/.test(name) && name.length <= 200;
  }

  /**
   * 验证团队名称
   */
  validateTeamName(team: string): boolean {
    // 团队名称格式：字母开头，可包含字母、数字、连字符
    return /^[a-zA-Z][a-zA-Z0-9\-_]*$/.test(team) && team.length <= 50;
  }

  /**
   * 验证项目名称
   */
  validateProjectName(project: string): boolean {
    // 项目名称格式：字母开头，可包含字母、数字、连字符
    return /^[a-zA-Z][a-zA-Z0-9\-_]*$/.test(project) && project.length <= 100;
  }

  /**
   * 获取验证错误的友好消息
   */
  private getFriendlyErrorMessage(error: string): string {
    const errorMap: Record<string, string> = {
      'minLength': '输入内容过短',
      'maxLength': '输入内容过长',
      'minimum': '数值过小',
      'maximum': '数值过大',
      'enum': '值不在允许的选项中',
      'required': '缺少必需的参数',
      'type': '参数类型不正确'
    };

    for (const [key, message] of Object.entries(errorMap)) {
      if (error.includes(key)) {
        return message;
      }
    }

    return error;
  }
}