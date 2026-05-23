export type Role = "admin" | "editor" | "designer";
export type ProjectStatus = "pending" | "in_progress" | "review" | "approved" | "delivered";
export type ServiceType = "social_media" | "ads" | "design" | "video" | "seo";
export type ContentStatus = "draft" | "review" | "approved" | "scheduled" | "published";

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
}

export interface BrandGuidelines {
  tone: string;
  colors: string[];
  fonts: string[];
  keywords: string[];
  avoid: string[];
}

export interface SocialAccounts {
  instagram?: string;
  facebook?: string;
  tiktok?: string;
  linkedin?: string;
  twitter?: string;
}

export interface Client {
  id: number;
  name: string;
  industry: string;
  brand_guidelines: BrandGuidelines;
  social_accounts: SocialAccounts;
  active: boolean;
}

export interface Project {
  id: number;
  client_id: number;
  client?: Client;
  title: string;
  service_type: ServiceType;
  status: ProjectStatus;
  deadline: string;
  assigned_to?: number;
}

export interface ContentItem {
  id: number;
  project_id: number;
  type: string;
  body: string;
  status: ContentStatus;
  ai_generated: boolean;
  approved_by?: number;
  created_at: string;
}

export interface ScheduledPost {
  id: number;
  content_id: number;
  content?: ContentItem;
  platform: string;
  scheduled_at: string;
  published_at?: string;
  status: string;
}
