/**
 * 分类管理相关接口定义
 */

// 层次化分类结构
export interface HierarchicalClassification {
  teams: TeamInfo[];
  projects: { [teamId: string]: ProjectInfo[] };
  modules: { [projectId: string]: ModuleInfo[] };
  devTypes: DevTypeInfo[];
}

export interface TeamInfo {
  id: string;
  name: string;
  display_name: string;
  description: string;
  tech_stack: string[];
  created_by: string;
  created_at: string;
  member_count: number;
}

export interface ProjectInfo {
  id: string;
  team_id: string;
  name: string;
  display_name: string;
  description: string;
  tech_stack: string[];
  repository_url?: string;
  created_by: string;
  created_at: string;
  module_count: number;
}

export interface ModuleInfo {
  id: string;
  project_id: string;
  name: string;
  display_name: string;
  description: string;
  module_type: string;
  created_by: string;
  created_at: string;
  document_count: number;
}

export interface DevTypeInfo {
  id: string;
  category: 'business_doc' | 'demo_code';
  name: string;
  display_name: string;
  description: string;
  icon: string;
  sort_order: number;
  created_at: string;
}

export interface DocumentClassification {
  team: string;
  project: string;
  module: string;
  dev_type: string;
}

export interface IClassificationService {
  getTeamsByUser(userId: string): Promise<TeamInfo[]>;
  getProjectsByTeam(teamId: string): Promise<ProjectInfo[]>;
  getModulesByProject(projectId: string): Promise<ModuleInfo[]>;
  getDevTypesByCategory(category: 'business_doc' | 'demo_code'): Promise<DevTypeInfo[]>;
  validateClassification(classification: DocumentClassification): Promise<boolean>;
  getAllTeams(): Promise<TeamInfo[]>;
  createTeam(team: Omit<TeamInfo, 'id' | 'created_at' | 'member_count'>): Promise<string>;
  createProject(project: Omit<ProjectInfo, 'id' | 'created_at' | 'module_count'>): Promise<string>;
  createModule(module: Omit<ModuleInfo, 'id' | 'created_at' | 'document_count'>): Promise<string>;
  getClassifications(): Promise<HierarchicalClassification>;
}