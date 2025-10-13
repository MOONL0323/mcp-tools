/**
 * 简单的分类服务实现（用于测试）
 */

import { 
  IClassificationService, 
  TeamInfo, 
  ProjectInfo, 
  ModuleInfo, 
  DevTypeInfo, 
  DocumentClassification,
  HierarchicalClassification 
} from '../interfaces/IClassificationService';

export class SimpleClassificationService implements IClassificationService {
  private teams: TeamInfo[] = [
    {
      id: '1',
      name: 'frontend-team',
      display_name: '前端开发团队',
      description: '负责前端界面开发',
      tech_stack: ['React', 'TypeScript', 'Ant Design'],
      created_by: 'admin',
      created_at: new Date().toISOString(),
      member_count: 5
    },
    {
      id: '2',
      name: 'backend-team',
      display_name: '后端开发团队',
      description: '负责后端API开发',
      tech_stack: ['Python', 'FastAPI', 'PostgreSQL'],
      created_by: 'admin',
      created_at: new Date().toISOString(),
      member_count: 3
    }
  ];

  private projects: ProjectInfo[] = [
    {
      id: '1',
      team_id: '1',
      name: 'ai-context-system',
      display_name: 'AI上下文增强系统',
      description: '基于Graph RAG的AI智能上下文增强系统',
      tech_stack: ['React', 'TypeScript', 'FastAPI'],
      repository_url: 'https://github.com/example/ai-context-system',
      created_by: 'admin',
      created_at: new Date().toISOString(),
      module_count: 4
    }
  ];

  private modules: ModuleInfo[] = [
    {
      id: '1',
      project_id: '1',
      name: 'frontend',
      display_name: '前端模块',
      description: 'React前端界面',
      module_type: 'frontend',
      created_by: 'admin',
      created_at: new Date().toISOString(),
      document_count: 0
    },
    {
      id: '2',
      project_id: '1',
      name: 'backend',
      display_name: '后端模块',
      description: 'FastAPI后端服务',
      module_type: 'backend',
      created_by: 'admin',
      created_at: new Date().toISOString(),
      document_count: 0
    },
    {
      id: '3',
      project_id: '1',
      name: 'knowledge-graph',
      display_name: '知识图谱模块',
      description: '知识图谱处理',
      module_type: 'ai',
      created_by: 'admin',
      created_at: new Date().toISOString(),
      document_count: 0
    }
  ];

  private devTypes: DevTypeInfo[] = [
    {
      id: '1',
      category: 'business_doc',
      name: 'requirement',
      display_name: '需求文档',
      description: '产品需求和功能说明',
      icon: 'file-text',
      sort_order: 1,
      created_at: new Date().toISOString()
    },
    {
      id: '2',
      category: 'business_doc',
      name: 'design',
      display_name: '设计文档',
      description: '系统设计和架构文档',
      icon: 'design',
      sort_order: 2,
      created_at: new Date().toISOString()
    },
    {
      id: '3',
      category: 'demo_code',
      name: 'component',
      display_name: '组件代码',
      description: '可复用组件代码',
      icon: 'code',
      sort_order: 1,
      created_at: new Date().toISOString()
    }
  ];

  async getTeamsByUser(userId: string): Promise<TeamInfo[]> {
    // 简化实现：返回所有团队
    return [...this.teams];
  }

  async getProjectsByTeam(teamId: string): Promise<ProjectInfo[]> {
    return this.projects.filter(project => project.team_id === teamId);
  }

  async getModulesByProject(projectId: string): Promise<ModuleInfo[]> {
    return this.modules.filter(module => module.project_id === projectId);
  }

  async getDevTypesByCategory(category: 'business_doc' | 'demo_code'): Promise<DevTypeInfo[]> {
    return this.devTypes.filter(devType => devType.category === category);
  }

  async validateClassification(classification: DocumentClassification): Promise<boolean> {
    const team = this.teams.find(t => t.name === classification.team);
    if (!team) return false;

    const project = this.projects.find(p => p.name === classification.project && p.team_id === team.id);
    if (!project) return false;

    const module = this.modules.find(m => m.name === classification.module && m.project_id === project.id);
    if (!module) return false;

    return true;
  }

  async getAllTeams(): Promise<TeamInfo[]> {
    return [...this.teams];
  }

  async createTeam(team: Omit<TeamInfo, 'id' | 'created_at' | 'member_count'>): Promise<string> {
    const id = (this.teams.length + 1).toString();
    const newTeam: TeamInfo = {
      ...team,
      id,
      created_at: new Date().toISOString(),
      member_count: 1
    };
    this.teams.push(newTeam);
    return id;
  }

  async createProject(project: Omit<ProjectInfo, 'id' | 'created_at' | 'module_count'>): Promise<string> {
    const id = (this.projects.length + 1).toString();
    const newProject: ProjectInfo = {
      ...project,
      id,
      created_at: new Date().toISOString(),
      module_count: 0
    };
    this.projects.push(newProject);
    return id;
  }

  async createModule(module: Omit<ModuleInfo, 'id' | 'created_at' | 'document_count'>): Promise<string> {
    const id = (this.modules.length + 1).toString();
    const newModule: ModuleInfo = {
      ...module,
      id,
      created_at: new Date().toISOString(),
      document_count: 0
    };
    this.modules.push(newModule);
    return id;
  }

  async getClassifications(): Promise<HierarchicalClassification> {
    // 构建层次化分类结构
    const projectsByTeam: { [teamId: string]: ProjectInfo[] } = {};
    const modulesByProject: { [projectId: string]: ModuleInfo[] } = {};

    // 按团队分组项目
    this.projects.forEach(project => {
      if (!projectsByTeam[project.team_id]) {
        projectsByTeam[project.team_id] = [];
      }
      projectsByTeam[project.team_id].push(project);
    });

    // 按项目分组模块
    this.modules.forEach(module => {
      if (!modulesByProject[module.project_id]) {
        modulesByProject[module.project_id] = [];
      }
      modulesByProject[module.project_id].push(module);
    });

    return {
      teams: this.teams,
      projects: projectsByTeam,
      modules: modulesByProject,
      devTypes: this.devTypes
    };
  }
}