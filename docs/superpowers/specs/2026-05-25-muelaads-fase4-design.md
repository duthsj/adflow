# MuelaADS — Fase 4 Design Spec

**Fecha:** 2026-05-25  
**Estado:** Aprobado para implementación  
**Versión objetivo:** v0.4.0

---

## Objetivo

Convertir MuelaADS en un SaaS multi-tenant real: cada agencia tiene su propio workspace, los recursos están aislados por workspace, y hay billing con Stripe para monetizar.

---

## Módulo 1: Workspaces

### Modelos
- `Workspace` — id, name, slug (unique), plan (free/pro/agency), stripe_customer_id, stripe_subscription_id, subscription_status (active/inactive/trialing), created_at
- `WorkspaceMember` — id, workspace_id (FK), user_id (FK), role (owner/editor/viewer), created_at

### Flujo
1. Usuario registra → auto-crea `Workspace` personal + `WorkspaceMember` con role=owner
2. Todos los recursos (clientes, etc.) se crean bajo el workspace del usuario actual
3. `get_current_workspace` dep: busca `WorkspaceMember` del user actual → retorna workspace

### Endpoints
- `GET /workspaces/me` — workspace del usuario actual
- `PUT /workspaces/me` — editar nombre
- `GET /workspaces/me/members` — listar miembros
- `POST /workspaces/me/invite` — crear invite token (expires 48h)
- `POST /workspaces/accept-invite/{token}` — aceptar invitación (no requiere auth previo)

---

## Módulo 2: Client workspace scoping

### Cambio
- Agregar `workspace_id` FK a `Client` model
- Todos los queries de `clients.py` filtran por `workspace_id` del usuario actual
- `projects.py` no cambia directamente (ya filtra por `client_id`)
- `assets.py`, `analytics.py` agregan filtro de workspace via join con clients

### Migración
- Alembic migration para agregar `workspace_id` a tabla `clients`
- Existing clients (si los hay) quedan sin workspace — safe default

---

## Módulo 3: Stripe Billing

### Planes
| Plan | Precio | Límites |
|------|--------|---------|
| free | $0 | 2 clientes, 10 contenidos/mes |
| pro | $29/mes | 20 clientes, ilimitado contenido |
| agency | $99/mes | Ilimitado todo, white label |

### Flujo
1. `POST /billing/checkout` → crea Stripe Customer + Checkout Session → retorna `checkout_url`
2. Usuario paga en Stripe hosted page
3. `POST /billing/webhook` → recibe `customer.subscription.created/updated/deleted` → actualiza `workspace.plan` y `subscription_status`
4. `GET /billing/portal` → crea Stripe Billing Portal session → retorna `portal_url`

### Settings nuevos en config.py
- `stripe_secret_key`
- `stripe_webhook_secret`
- `stripe_pro_price_id`
- `stripe_agency_price_id`

---

## Módulo 4: Frontend

### Página de Onboarding (`/onboarding`)
- Aparece después de register si workspace no tiene nombre configurado
- Form: nombre de la agencia → POST /workspaces/me
- Redirige a /dashboard

### Página de Billing (`/dashboard/billing`)
- Cards de planes: Free / Pro / Agency
- Badge "Plan actual" en plan activo
- Botón "Upgrade" → POST /billing/checkout → redirect a Stripe
- Botón "Manage subscription" → GET /billing/portal → redirect
- Toasts para errores

### Página de Members (`/dashboard/members`)
- Lista de miembros con roles
- Input para invitar por token URL
- Mostrar link de invitación copiable

### Sidebar
- Agregar "Billing" y "Equipo" nav items
- Mostrar badge del plan actual (Free/Pro/Agency) debajo del nombre

---

## Stack Técnico

| Componente | Librería |
|---|---|
| Stripe | stripe==10.x (Python SDK) |
| Alembic | ya instalado (alembic==1.13.3) |
| Frontend | Next.js 15 App Router (existente) |

---

## Tests

- 15+ nuevos tests: workspace CRUD, invite flow, billing endpoints (mock Stripe), client scoping
- Target: 70+ tests passing (de 55 actuales)

---

## Orden de Implementación

1. Workspace + WorkspaceMember models + schemas + endpoints
2. Update auth: register auto-crea workspace, `get_current_workspace` dep
3. Client workspace scoping (add workspace_id FK, update queries)
4. Stripe service + billing endpoints
5. Frontend: Billing page + plan cards
6. Frontend: Members page + invite flow  
7. Frontend: Onboarding + sidebar updates
8. Tests completos + tag v0.4.0
