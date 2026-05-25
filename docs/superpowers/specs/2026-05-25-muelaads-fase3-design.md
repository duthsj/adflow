# MuelaADS — Fase 3 Design Spec

**Fecha:** 2026-05-25  
**Estado:** Aprobado para implementación  
**Versión objetivo:** v0.3.0

---

## Contexto

MuelaADS v0.2.0 tiene 5 agentes AI, portal de aprobaciones, CRM y calendario. La investigación competitiva contra ContentStudio, Hootsuite, Buffer y plataformas SaaS 2026 identifica 4 gaps críticos que bloquean el valor real para clientes:

1. Sin analytics — no hay datos de performance
2. Sin media library — assets desorganizados
3. Sin publicación real — Blotato mock solamente
4. Sin reportes — accountability manual

---

## Objetivos Fase 3

Superar ContentStudio en 3 áreas donde nuestros agentes AI dan ventaja diferencial:
- **Reportes AI** — generados automáticamente con insights de Claude, no solo métricas brutas
- **Media Library** — búsqueda semántica por contenido (no solo tags)
- **Analytics predictivos** — mejor hora para publicar por cliente y plataforma, calculado con AI

---

## Módulo 1: Analytics Dashboard

### Backend
- Modelo `Analytics` ya en schema de diseño original
- Endpoint `GET /analytics/summary?client_id=&period=week|month` — agrega métricas
- Endpoint `GET /analytics/clients/{id}` — breakdown por plataforma
- Endpoint `POST /analytics/ingest` — recibe webhooks de Blotato post-publicación
- Datos simulados iniciales si Blotato no tiene webhooks reales aún

### Frontend
- Página `/dashboard/analytics` con:
  - KPI cards: total posts, reach promedio, engagement rate, aprobaciones pendientes
  - Line chart: posts publicados vs semana anterior (recharts o chart.js)
  - Bar chart: breakdown por plataforma (IG, FB, TikTok, LinkedIn)
  - Table: top contenido por engagement
  - Filtro por cliente y período

### AI Insights
- Endpoint `POST /analytics/insights` — llama Claude con métricas del período
- Claude retorna 3 bullets: qué funcionó, qué no, recomendación siguiente semana
- Frontend muestra insights debajo del dashboard principal

---

## Módulo 2: Media Library

### Backend
- Modelo `Asset` nuevo: `id, client_id, filename, r2_key, type, size, tags[], semantic_tags[], uploaded_by, created_at`
- Cloudflare R2 integration via boto3 (S3-compatible): upload, get_presigned_url, delete
- Endpoint `POST /assets/upload` — multipart form, sube a R2, guarda metadata en DB
- Endpoint `GET /assets?client_id=&type=&search=` — filtro + búsqueda por tags
- Endpoint `DELETE /assets/{id}` — elimina R2 + DB
- Claude genera `semantic_tags` automáticos al subir (describe imagen/doc con AI)

### Frontend
- Página `/dashboard/assets` con:
  - Grid de miniaturas (imágenes) o iconos (docs/videos)
  - Upload drag-and-drop
  - Filtros: por cliente, tipo (image/video/doc/template), búsqueda libre
  - Preview modal con metadata + tags
  - Copy link presigned para usar en content generator

---

## Módulo 3: Blotato Publishing Real

### Backend
- `BlogatoService` actualizado: `schedule_post(platform, content, scheduled_at, media_urls[])` real
- Manejo de errores: retry 3x con backoff, estado `failed` si persiste
- Endpoint `GET /posts/{blotato_id}/status` — polling de estado real
- Webhook endpoint `POST /webhooks/blotato` — recibe status updates

### Frontend
- ContentGenerator actualizado: tras aprobar, muestra form de scheduling real
- Calendar muestra estado real: draft / scheduled / published / failed
- Badge color por estado en todas las vistas de contenido

---

## Módulo 4: PDF Reports

### Backend
- `reportlab` o `weasyprint` para generación PDF
- Endpoint `POST /reports/generate` con `client_id, period, include_insights: bool`
- Reporte incluye: logo cliente, KPIs período, charts (como PNG embebidos), AI insights
- Endpoint `GET /reports/{id}/download` — sirve PDF

### Frontend
- Botón "Generar Reporte" en página Analytics por cliente
- Modal: seleccionar período + toggle incluir AI insights
- Descarga directa del PDF generado

---

## Módulo 5: UX Polish

### Toast Notifications
- Librería `react-hot-toast` o `sonner`
- Todos los actions actuales (create, approve, reject, generate) muestran toast
- Errores API muestran toast de error con mensaje

### Loading States
- Skeletons en listas (clientes, proyectos, contenido)
- Spinner en generación AI con mensaje "Generando con Claude..."
- Optimistic updates en aprobaciones del portal

### Empty States
- Ilustraciones o mensajes útiles cuando no hay datos
- CTAs claros: "Crear primer cliente", "Generar primer contenido"

---

## Stack Técnico Fase 3

| Componente | Librería |
|---|---|
| Charts | recharts (ya en ecosistema React) |
| PDF | weasyprint (Python, HTML→PDF) |
| R2/S3 | boto3 + python-multipart |
| Toasts | sonner (shadcn compatible) |
| AI tags | Claude claude-sonnet-4-6 |

---

## Tests

- 15+ nuevos tests: analytics endpoints, asset upload mock, report generation, Blotato real mock
- Target: 60+ tests passing (de 42 actuales)

---

## Orden de Implementación

1. Analytics Backend (modelo + endpoints + datos mock)
2. Analytics Frontend (dashboard + charts)
3. AI Insights endpoint
4. Media Library Backend (R2 + asset model)
5. Media Library Frontend (grid + upload)
6. Blotato real (actualizar service + webhooks)
7. PDF Reports (backend + frontend)
8. UX Polish (toasts + loading + empty states)
9. Tests completos

---

## Referencias

- [ContentStudio features](https://contentstudio.io/) — competidor principal analizado
- [langchain-ai/social-media-agent](https://github.com/langchain-ai/social-media-agent) — patrón human-in-loop
- [recharts](https://recharts.org/) — charts React
- [Cloudflare R2 boto3](https://developers.cloudflare.com/r2/api/s3/api/) — S3-compatible API
