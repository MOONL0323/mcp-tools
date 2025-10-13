-- 开发环境测试数据
-- 此脚本在开发环境中自动执行，用于创建测试数据

-- 插入测试用户
INSERT INTO users (id, username, email, password_hash, full_name, role, teams) VALUES 
(
    '550e8400-e29b-41d4-a716-446655440001',
    'admin',
    'admin@dev.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewZ1eMWkwh9VNbD6', -- password: admin123
    '系统管理员',
    'admin',
    ARRAY['backend_team', 'frontend_team', 'ai_team']
),
(
    '550e8400-e29b-41d4-a716-446655440002',
    'developer1',
    'dev1@dev.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewZ1eMWkwh9VNbD6', -- password: admin123
    '张开发',
    'developer',
    ARRAY['backend_team']
),
(
    '550e8400-e29b-41d4-a716-446655440003',
    'developer2',
    'dev2@dev.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewZ1eMWkwh9VNbD6', -- password: admin123
    '李前端',
    'developer',
    ARRAY['frontend_team']
),
(
    '550e8400-e29b-41d4-a716-446655440004',
    'manager1',
    'manager@dev.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewZ1eMWkwh9VNbD6', -- password: admin123
    '王经理',
    'manager',
    ARRAY['backend_team', 'frontend_team']
);

-- 插入测试团队
INSERT INTO teams (id, name, display_name, description, tech_stack, created_by) VALUES 
(
    '660e8400-e29b-41d4-a716-446655440001',
    'backend_team',
    '后端开发团队',
    '负责后端API开发和数据库设计',
    ARRAY['Python', 'FastAPI', 'PostgreSQL', 'Redis'],
    '550e8400-e29b-41d4-a716-446655440001'
),
(
    '660e8400-e29b-41d4-a716-446655440002',
    'frontend_team',
    '前端开发团队',
    '负责前端界面开发和用户体验设计',
    ARRAY['React', 'TypeScript', 'Ant Design', 'Vite'],
    '550e8400-e29b-41d4-a716-446655440001'
),
(
    '660e8400-e29b-41d4-a716-446655440003',
    'ai_team',
    'AI算法团队',
    '负责AI算法研发和模型训练',
    ARRAY['Python', 'PyTorch', 'Transformers', 'Neo4j'],
    '550e8400-e29b-41d4-a716-446655440001'
);

-- 插入测试项目
INSERT INTO projects (id, team_id, name, display_name, description, tech_stack, created_by) VALUES 
(
    '770e8400-e29b-41d4-a716-446655440001',
    '660e8400-e29b-41d4-a716-446655440001',
    'user_service',
    '用户服务',
    '用户管理相关的后端服务',
    ARRAY['FastAPI', 'SQLAlchemy', 'JWT'],
    '550e8400-e29b-41d4-a716-446655440002'
),
(
    '770e8400-e29b-41d4-a716-446655440002',
    '660e8400-e29b-41d4-a716-446655440001',
    'document_service',
    '文档服务',
    '文档管理和处理的后端服务',
    ARRAY['FastAPI', 'Celery', 'MinIO'],
    '550e8400-e29b-41d4-a716-446655440002'
),
(
    '770e8400-e29b-41d4-a716-446655440003',
    '660e8400-e29b-41d4-a716-446655440002',
    'admin_dashboard',
    '管理后台',
    '系统管理和监控的前端界面',
    ARRAY['React', 'Ant Design Pro', 'Charts'],
    '550e8400-e29b-41d4-a716-446655440003'
),
(
    '770e8400-e29b-41d4-a716-446655440004',
    '660e8400-e29b-41d4-a716-446655440003',
    'rag_engine',
    'RAG检索引擎',
    '基于Graph RAG的智能检索引擎',
    ARRAY['Python', 'ChromaDB', 'Neo4j', 'Transformers'],
    '550e8400-e29b-41d4-a716-446655440001'
);

-- 插入测试模块
INSERT INTO modules (id, project_id, name, display_name, description, module_type, created_by) VALUES 
(
    '880e8400-e29b-41d4-a716-446655440001',
    '770e8400-e29b-41d4-a716-446655440001',
    'authentication',
    '用户认证',
    '用户登录、注册、JWT token管理',
    'api',
    '550e8400-e29b-41d4-a716-446655440002'
),
(
    '880e8400-e29b-41d4-a716-446655440002',
    '770e8400-e29b-41d4-a716-446655440001',
    'user_management',
    '用户管理',
    '用户信息CRUD操作',
    'api',
    '550e8400-e29b-41d4-a716-446655440002'
),
(
    '880e8400-e29b-41d4-a716-446655440003',
    '770e8400-e29b-41d4-a716-446655440002',
    'file_upload',
    '文件上传',
    '文档文件上传和存储管理',
    'api',
    '550e8400-e29b-41d4-a716-446655440002'
),
(
    '880e8400-e29b-41d4-a716-446655440004',
    '770e8400-e29b-41d4-a716-446655440002',
    'document_processing',
    '文档处理',
    '文档解析、分块、向量化处理',
    'service',
    '550e8400-e29b-41d4-a716-446655440002'
),
(
    '880e8400-e29b-41d4-a716-446655440005',
    '770e8400-e29b-41d4-a716-446655440003',
    'document_manager',
    '文档管理组件',
    '文档列表、上传、查看等前端组件',
    'component',
    '550e8400-e29b-41d4-a716-446655440003'
),
(
    '880e8400-e29b-41d4-a716-446655440006',
    '770e8400-e29b-41d4-a716-446655440004',
    'graph_builder',
    '图谱构建器',
    '从文档中提取实体和关系构建知识图谱',
    'algorithm',
    '550e8400-e29b-41d4-a716-446655440001'
);

-- 插入开发类型
INSERT INTO dev_types (id, category, name, display_name, description, icon, sort_order) VALUES 
-- 业务文档类型
(
    '990e8400-e29b-41d4-a716-446655440001',
    'business_doc',
    'overview_design',
    '概要设计文档',
    '系统整体架构和设计方案',
    '📋',
    1
),
(
    '990e8400-e29b-41d4-a716-446655440002',
    'business_doc',
    'detailed_design',
    '详细设计文档',
    '具体功能模块的详细设计',
    '📝',
    2
),
(
    '990e8400-e29b-41d4-a716-446655440003',
    'business_doc',
    'api_doc',
    'API接口文档',
    'API接口定义和使用说明',
    '🔌',
    3
),
(
    '990e8400-e29b-41d4-a716-446655440004',
    'business_doc',
    'database_design',
    '数据库设计文档',
    '数据库表结构和关系设计',
    '🗄️',
    4
),
(
    '990e8400-e29b-41d4-a716-446655440005',
    'business_doc',
    'architecture_doc',
    '架构设计文档',
    '系统架构和技术选型说明',
    '🏗️',
    5
),

-- Demo代码类型
(
    '990e8400-e29b-41d4-a716-446655440006',
    'demo_code',
    'api_module',
    'API模块代码',
    'API接口实现和路由代码',
    '🔗',
    1
),
(
    '990e8400-e29b-41d4-a716-446655440007',
    'demo_code',
    'business_logic',
    '业务逻辑代码',
    '核心业务逻辑实现代码',
    '⚙️',
    2
),
(
    '990e8400-e29b-41d4-a716-446655440008',
    'demo_code',
    'database_operation',
    '数据库操作代码',
    '数据库CRUD操作和ORM代码',
    '💾',
    3
),
(
    '990e8400-e29b-41d4-a716-446655440009',
    'demo_code',
    'unit_test',
    '单元测试代码',
    '单元测试和集成测试代码',
    '🧪',
    4
),
(
    '990e8400-e29b-41d4-a716-446655440010',
    'demo_code',
    'utility_class',
    '工具类代码',
    '通用工具函数和辅助类',
    '🔧',
    5
);

-- 插入测试文档
INSERT INTO documents (
    id, title, description, type, 
    team_id, project_id, module_id, dev_type_id,
    file_name, file_path, file_size, mime_type, file_hash,
    access_level, status, tags,
    uploaded_by, version
) VALUES 
(
    'aa0e8400-e29b-41d4-a716-446655440001',
    '用户认证API设计文档',
    '详细描述用户登录、注册、JWT token管理等API接口的设计和实现',
    'business_doc',
    '660e8400-e29b-41d4-a716-446655440001', -- backend_team
    '770e8400-e29b-41d4-a716-446655440001', -- user_service
    '880e8400-e29b-41d4-a716-446655440001', -- authentication
    '990e8400-e29b-41d4-a716-446655440003', -- api_doc
    'user_auth_api.md',
    '/documents/backend_team/user_service/auth/user_auth_api.md',
    15360, -- 15KB
    'text/markdown',
    'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
    'team',
    'completed',
    ARRAY['authentication', 'jwt', 'api', 'security'],
    '550e8400-e29b-41d4-a716-446655440002', -- developer1
    '1.0'
),
(
    'aa0e8400-e29b-41d4-a716-446655440002',
    '文档管理前端组件实现',
    'React + TypeScript实现的文档管理界面组件，包含上传、列表、搜索等功能',
    'demo_code',
    '660e8400-e29b-41d4-a716-446655440002', -- frontend_team
    '770e8400-e29b-41d4-a716-446655440003', -- admin_dashboard
    '880e8400-e29b-41d4-a716-446655440005', -- document_manager
    '990e8400-e29b-41d4-a716-446655440006', -- api_module
    'DocumentManager.tsx',
    '/documents/frontend_team/admin_dashboard/DocumentManager.tsx',
    28672, -- 28KB
    'text/typescript',
    'b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456a1',
    'team',
    'completed',
    ARRAY['react', 'typescript', 'component', 'document-management'],
    '550e8400-e29b-41d4-a716-446655440003', -- developer2
    '1.0'
),
(
    'aa0e8400-e29b-41d4-a716-446655440003',
    'Graph RAG算法实现指南',
    '基于Neo4j和ChromaDB的Graph RAG算法实现，包含实体提取、关系构建、向量检索等',
    'business_doc',
    '660e8400-e29b-41d4-a716-446655440003', -- ai_team
    '770e8400-e29b-41d4-a716-446655440004', -- rag_engine
    '880e8400-e29b-41d4-a716-446655440006', -- graph_builder
    '990e8400-e29b-41d4-a716-446655440001', -- overview_design
    'graph_rag_design.md',
    '/documents/ai_team/rag_engine/graph_rag_design.md',
    45120, -- 44KB
    'text/markdown',
    'c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456a1b2',
    'public',
    'completed',
    ARRAY['graph-rag', 'neo4j', 'chromadb', 'algorithm', 'ai'],
    '550e8400-e29b-41d4-a716-446655440001', -- admin
    '1.2'
);

-- 更新文档统计信息
UPDATE documents SET 
    chunk_count = 12,
    entity_count = 25,
    processed_at = CURRENT_TIMESTAMP,
    view_count = 5,
    download_count = 2
WHERE id = 'aa0e8400-e29b-41d4-a716-446655440001';

UPDATE documents SET 
    chunk_count = 18,
    entity_count = 35,
    processed_at = CURRENT_TIMESTAMP,
    view_count = 8,
    download_count = 3
WHERE id = 'aa0e8400-e29b-41d4-a716-446655440002';

UPDATE documents SET 
    chunk_count = 24,
    entity_count = 42,
    processed_at = CURRENT_TIMESTAMP,
    view_count = 15,
    download_count = 7
WHERE id = 'aa0e8400-e29b-41d4-a716-446655440003';

-- 插入测试文档块
INSERT INTO document_chunks (
    id, document_id, content, title, summary, keywords, content_type, 
    chunk_index, start_position, end_position
) VALUES 
(
    'bb0e8400-e29b-41d4-a716-446655440001',
    'aa0e8400-e29b-41d4-a716-446655440001',
    '## 用户登录API\n\n### 接口地址\nPOST /api/auth/login\n\n### 请求参数\n- username: 用户名\n- password: 密码\n\n### 响应格式\n```json\n{\n  "access_token": "jwt_token",\n  "refresh_token": "refresh_token",\n  "user": {\n    "id": "user_id",\n    "username": "username",\n    "role": "developer"\n  }\n}\n```',
    '用户登录API',
    '用户登录接口，返回JWT token和用户信息',
    ARRAY['login', 'authentication', 'jwt', 'api'],
    'api_interface',
    1, 0, 300
),
(
    'bb0e8400-e29b-41d4-a716-446655440002',
    'aa0e8400-e29b-41d4-a716-446655440002',
    'export const DocumentManager: React.FC = () => {\n  const { user, hasPermission } = useAuth();\n  const [documents, setDocuments] = useState<DocumentItem[]>([]);\n  const [loading, setLoading] = useState(false);\n\n  const documentService = useService<IDocumentService>(''IDocumentService'');\n\n  const loadDocuments = async () => {\n    try {\n      setLoading(true);\n      const docs = await documentService.getDocuments();\n      setDocuments(docs);\n    } catch (error) {\n      message.error(''加载文档失败'');\n    } finally {\n      setLoading(false);\n    }\n  };',
    'DocumentManager组件主体',
    'React文档管理组件的主要实现，包含状态管理和数据加载',
    ARRAY['react', 'component', 'state-management', 'document'],
    'code_example',
    1, 0, 500
);

-- 插入测试实体
INSERT INTO entities (
    id, name, type, description, document_id, properties
) VALUES 
(
    'cc0e8400-e29b-41d4-a716-446655440001',
    'LoginAPI',
    'API',
    '用户登录API接口',
    'aa0e8400-e29b-41d4-a716-446655440001',
    '{"method": "POST", "path": "/api/auth/login", "parameters": ["username", "password"]}'::jsonb
),
(
    'cc0e8400-e29b-41d4-a716-446655440002',
    'User',
    'Model',
    '用户数据模型',
    'aa0e8400-e29b-41d4-a716-446655440001',
    '{"fields": ["id", "username", "role"], "type": "entity"}'::jsonb
),
(
    'cc0e8400-e29b-41d4-a716-446655440003',
    'DocumentManager',
    'Component',
    'React文档管理组件',
    'aa0e8400-e29b-41d4-a716-446655440002',
    '{"framework": "React", "language": "TypeScript", "props": ["user", "hasPermission"]}'::jsonb
),
(
    'cc0e8400-e29b-41d4-a716-446655440004',
    'useAuth',
    'Hook',
    'React认证Hook',
    'aa0e8400-e29b-41d4-a716-446655440002',
    '{"type": "custom-hook", "returns": ["user", "hasPermission", "login", "logout"]}'::jsonb
);

-- 插入测试关系
INSERT INTO relations (
    id, source_entity_id, target_entity_id, relation_type, description, confidence
) VALUES 
(
    'dd0e8400-e29b-41d4-a716-446655440001',
    'cc0e8400-e29b-41d4-a716-446655440001', -- LoginAPI
    'cc0e8400-e29b-41d4-a716-446655440002', -- User
    'RETURNS',
    '登录API返回用户信息',
    0.95
),
(
    'dd0e8400-e29b-41d4-a716-446655440002',
    'cc0e8400-e29b-41d4-a716-446655440003', -- DocumentManager
    'cc0e8400-e29b-41d4-a716-446655440004', -- useAuth
    'USES',
    'DocumentManager组件使用useAuth Hook',
    0.98
);

-- 插入测试访问记录
INSERT INTO document_access_logs (document_id, user_id, action, ip_address) VALUES 
('aa0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', 'view', '127.0.0.1'),
('aa0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440003', 'view', '127.0.0.1'),
('aa0e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'download', '127.0.0.1'),
('aa0e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440002', 'view', '127.0.0.1');

-- 创建测试视图，方便查询
CREATE VIEW v_document_details AS
SELECT 
    d.id,
    d.title,
    d.description,
    d.type,
    t.display_name as team_name,
    p.display_name as project_name,
    m.display_name as module_name,
    dt.display_name as dev_type_name,
    d.file_name,
    d.file_size,
    d.access_level,
    d.status,
    d.chunk_count,
    d.entity_count,
    d.tags,
    d.view_count,
    d.download_count,
    u.full_name as uploader_name,
    u.username as uploader_username,
    d.created_at,
    d.updated_at
FROM documents d
LEFT JOIN teams t ON d.team_id = t.id
LEFT JOIN projects p ON d.project_id = p.id
LEFT JOIN modules m ON d.module_id = m.id
LEFT JOIN dev_types dt ON d.dev_type_id = dt.id
LEFT JOIN users u ON d.uploaded_by = u.id;

-- 创建文档统计视图
CREATE VIEW v_document_stats AS
SELECT 
    t.display_name as team_name,
    COUNT(*) as total_documents,
    COUNT(CASE WHEN d.type = 'business_doc' THEN 1 END) as business_docs,
    COUNT(CASE WHEN d.type = 'demo_code' THEN 1 END) as demo_codes,
    COUNT(CASE WHEN d.status = 'completed' THEN 1 END) as completed_docs,
    SUM(d.file_size) as total_file_size,
    SUM(d.view_count) as total_views,
    SUM(d.download_count) as total_downloads
FROM documents d
JOIN teams t ON d.team_id = t.id
GROUP BY t.id, t.display_name;

COMMIT;