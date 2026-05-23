# MuelaADS — Diseño del Sistema Interno

**Fecha:** 2026-05-23  
**Estado:** Aprobado para implementación

---

## Resumen

MuelaADS es una plataforma interna para operar una agencia de marketing impulsada por AI. Cubre todos los servicios: redes sociales, publicidad paga, diseño gráfico, video, y SEO. El sistema combina automatización AI con supervisión humana según el tipo de servicio.

---

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14 App Router + Tailwind CSS + shadcn/ui |
| Backend | FastAPI + SQLAlchemy + PostgreSQL |
| AI Agents | Claude Sonnet 4.6 (Anthropic API) |
| Storage | Cloudflare R2 |
| Social Publishing | Blotato API |
| Auth | JWT + roles |
| Deploy | PM2 + Nginx |

---

## Estructura de Carpetas

```
muelaads/
├── frontend/
│   ├── app/
│   │   ├── (auth)/
│   │   ├── dashboard/
│   │   ├── clients/
│   │   ├── projects/
│   │   ├── agents/
│   │   ├── calendar/
│   │   ├── assets/
│   │   └── analytics/
│   └── components/
├── backend/
│   ├── api/
│   │   ├── auth.py
│   │   ├── clients.py
│   │   ├── projects.py
│   │   ├── agents.py
│   │   └── content.py
│   ├── models/
│   ├── services/
│   └── agents/
│       ├── social_agent.py
│       ├── ads_agent.py
│       ├── design_agent.py
│       ├── video_agent.py
│       ├── seo_agent.py
│       └── orchestrator.py
└── docs/
```

---

## Módulos del Sistema

### 1. CRM (Clientes)
- Alta, edición y archivo de clientes
- Brand guidelines por cliente (colores, fuentes, tono de voz, logo)
- Cuentas sociales vinculadas (IG, FB, TikTok, LinkedIn, Google)
- Historial de proyectos y entregables

### 2. Gestión de Proyectos
- Proyectos por cliente, tipo de servicio y estado
- Kanban: Pendiente → En progreso → Revisión → Aprobado → Entregado
- Asignación a agente AI o miembro del equipo
- Fechas límite y alertas

### 3. Agentes AI

| Agente | Automatización | Responsabilidad |
|--------|---------------|-----------------|
| Social Media Agent | Full-auto | Genera copy posts/stories/reels, programa y publica vía Blotato |
| Ads Agent | Semi-auto | Copy para Meta/Google Ads, variantes A/B, sugerencias de targeting |
| Design Agent | Asistida | Genera prompts para Midjourney/DALL-E, brief para diseñador humano |
| Video Agent | Asistida | Scripts, storyboards, captions, guiones para reels |
| SEO Agent | Semi-auto | Artículos de blog, keyword clusters, meta tags, internal linking |
| Orchestrator | Sistema | Recibe proyecto, asigna agente correcto, coordina flujo |

Cada agente recibe: brand guidelines del cliente + brief del proyecto + historial previo.

### 4. Calendario de Contenido
- Vista mensual/semanal de contenido programado por cliente
- Drag & drop para reprogramar
- Estado visual: borrador / revisión / programado / publicado
- Integración directa con Blotato para scheduling

### 5. Gestor de Assets
- Upload a Cloudflare R2
- Organización por cliente y tipo (logo, foto, video, template)
- Búsqueda por tags
- Preview inline

### 6. Analytics
- Métricas por cliente y plataforma
- Reach, engagement, clicks, conversiones
- Comparativa periódica (semana/mes)
- Exportable a PDF/CSV

### 7. Portal de Aprobaciones
- Cliente recibe link para revisar contenido pendiente
- Puede aprobar, rechazar o comentar
- Sin necesidad de cuenta — token de acceso temporal

---

## Base de Datos

```sql
users          (id, email, password_hash, role, name, created_at)
clients        (id, name, industry, brand_guidelines JSONB, social_accounts JSONB, active)
projects       (id, client_id, service_type, title, status, deadline, assigned_to, created_at)
tasks          (id, project_id, agent_type, description, status, assigned_to, due_date)
content_items  (id, project_id, type, body TEXT, status, ai_generated BOOL, approved_by, created_at)
scheduled_posts(id, content_id, platform, scheduled_at, published_at, blotato_id, status)
assets         (id, client_id, type, r2_key, filename, size, tags JSONB, uploaded_by)
analytics      (id, client_id, platform, metric_type, value DECIMAL, recorded_at)
```

---

## Roles y Permisos

| Rol | Acceso |
|-----|--------|
| admin | Todo — configuración, usuarios, facturación |
| editor | Proyectos, contenido, calendario, assets |
| diseñador | Proyectos asignados, assets, design agent |
| cliente | Solo portal de aprobaciones (token temporal) |

---

## Flujo Principal

```
1. Cliente nuevo → creado en CRM con brand guidelines
2. Proyecto creado → tipo de servicio seleccionado
3. Orchestrator determina agente(s) a usar
4. Agente genera contenido con contexto del cliente
5. Si semi-auto/asistida → editor/diseñador revisa
6. Contenido aprobado → entra al Calendario
7. Blotato publica en fecha/hora programada
8. Analytics captura métricas post-publicación
```

---

## Integraciones Externas

- **Blotato API** — publicación multi-plataforma (IG, FB, TikTok, LinkedIn, X)
- **Anthropic Claude API** — todos los agentes AI (Sonnet 4.6)
- **Cloudflare R2** — storage de assets
- **Google Analytics API** — métricas web (opcional fase 2)

---

## Fases de Build

### Fase 1 — Core (MVP interno)
- Auth + roles
- CRM clientes
- Gestión proyectos básica
- Social Media Agent (full-auto)
- Calendario + Blotato

### Fase 2 — Agentes completos
- Ads Agent, SEO Agent, Design Agent, Video Agent
- Orchestrator inteligente
- Portal de aprobaciones cliente

### Fase 3 — Analytics + Optimización
- Dashboard analytics
- Reportes automatizados
- Refinamiento de prompts por agente

### Fase 4 — SaaS
- Multi-tenant
- Billing (Stripe)
- Onboarding self-service

---

## Referencias

- [agency-agents](https://github.com/msitarzewski/agency-agents) — referencia de agentes especializados
- [vintasoftware/nextjs-fastapi-template](https://github.com/vintasoftware/nextjs-fastapi-template) — base stack
- [Blotato](https://www.blotato.com/) — API publicación social
- [ai-marketing-skills](https://github.com/ericosiu/ai-marketing-skills) — skills de referencia
