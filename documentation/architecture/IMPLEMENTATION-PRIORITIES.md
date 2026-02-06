# BACON-AI Template & Documentation System - Implementation Priorities

## Quick Reference: Recommended Next Steps

### Immediate Actions (This Week)

1. **Create Template Directory Structure**
   ```bash
   mkdir -p /home/bacon/bacon-ai/templates/{framework,domain}
   mkdir -p ~/.bacon-ai/library/{patterns,lessons,methodologies,templates}
   ```

2. **Export Current BACON-AI Board as Template**
   - Use existing board `bd5mw98s3cjftjnef77q8c4oone` as baseline
   - Extract phases, tasks, properties, and checklist structures
   - Save as `bacon-ai-12-phase/template.json`

3. **Add Document Properties to Focalboard Board**
   - Add `doc_links` (text/url) property to track documents
   - Add `prompt_archive` and `result_archive` properties
   - Update SKILL.md with new property IDs

### MCP Server Extensions (Priority Order)

| Priority | Tool | Effort | Value |
|----------|------|--------|-------|
| **P0** | `focalboard_instantiate_template` | Medium | Enables automated board creation |
| **P0** | `focalboard_store_document` | Low | Captures deliverables |
| **P1** | `focalboard_link_document_to_task` | Low | Creates traceability |
| **P1** | `focalboard_list_templates` | Low | Discovery for orchestrator |
| **P2** | `focalboard_search_library` | Medium | Knowledge reuse |
| **P2** | `focalboard_archive_prompt_result` | Medium | Full audit trail |
| **P3** | `focalboard_suggest_template` | High | AI-assisted selection |

### UI Views (Focalboard Customization)

| View | Purpose | Implementation |
|------|---------|----------------|
| **Documentation View** | Browse all project documents by phase | Gallery view with doc_links filter |
| **Template View** | Show board origin and deviation | Table view with template metadata |

## Architecture Decisions Made

### 1. Two-Tier Library (Recommended)
- **Global**: `~/.bacon-ai/library/` - Cross-project knowledge
- **Project**: `{project}/docs/bacon-ai/` - Project-specific deliverables

### 2. Template Hierarchy
```
Framework Templates → Domain Templates → Project Instances
(BACON-AI-12)       (Feature-Dev)       (Project-Alpha Board)
```

### 3. Document-Task Linking
- Card properties store document IDs
- Documents contain task metadata
- Bidirectional traceability

### 4. Prompt/Result Archival
- Every agent execution archived
- Linked to task card
- Enables learning and debugging

## Key Metrics to Track

| Metric | Target | Measurement |
|--------|--------|-------------|
| Template reuse rate | > 80% new projects | Projects created from templates |
| Document coverage | 100% P0 tasks | Tasks with linked deliverables |
| Library growth | +5 patterns/month | Global library entries |
| Search effectiveness | < 3 queries to find | User search behavior |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Template bloat | Version control + deprecation policy |
| Document sprawl | Strict naming conventions + auto-cleanup |
| Search noise | Quality scoring + manual curation |
| Adoption friction | Value-first onboarding + gradual rollout |

---

**Next Action**: Implement `focalboard_instantiate_template` tool to enable board creation from templates.
