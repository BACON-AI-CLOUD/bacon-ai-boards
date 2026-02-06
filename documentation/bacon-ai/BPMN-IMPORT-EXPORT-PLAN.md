# BACON-AI-BOARDS: JSON/XML/BPMN Import/Export Implementation Plan

## Session Log
- **Session ID**: velvet-twirling-pie
- **Date**: 2026-02-06
- **Project**: /home/bacon/bacon-ai/projects/focalboard/webapp
- **Status**: PLAN COMPLETE - Ready for implementation
- **Plan saved to**: `/home/bacon/bacon-ai/projects/focalboard/documentation/bacon-ai/BPMN-IMPORT-EXPORT-PLAN.md`

### To Resume This Session
Load this context:
1. Focalboard branding already updated to BACON-AI-BOARDS
2. Plan for JSON/XML/BPMN import/export complete
3. User decisions:
   - Add "Depends On" relation property type for card dependencies
   - Add "Process Flow" as 5th view type (alongside Board/Table/Gallery/Calendar)

---

## Overview

Add comprehensive import/export capabilities to BACON-AI-BOARDS including:
- **JSON/XML formats** for board data interchange
- **BPMN 2.0 format** for business process visualization
- **BPMN Viewer** with token simulation (optional Phase 5)

This enables boards to be visualized as process flow diagrams where cards become tasks and status columns become swimlanes.

---

## Data Mapping Concept

| BACON-AI-BOARDS | BPMN 2.0 |
|-----------------|----------|
| Board | bpmn:process |
| Card | bpmn:userTask |
| Status property options | bpmn:lane (swimlanes) |
| **"Depends On" property** | **bpmn:sequenceFlow** |
| "To Do" cards | Connected from startEvent |
| "Done" cards | Connected to endEvent |
| Card order in column | Fallback sequential flow |

### New "Depends On" Property Type
A new property type `relation` will be added to track card dependencies:
- Cards can reference other cards they depend on
- These dependencies become BPMN sequence flows
- Enables proper process flow visualization
- File: `webapp/src/properties/relation/relation.tsx`

---

## Phase 1: JSON Import/Export (Foundation)

### New Files to Create

#### `webapp/src/exporters/jsonExporter.ts`
```typescript
// Pattern follows: csvExporter.ts and archiver.ts
class JsonExporter {
    static exportBoardJson(board: Board, views: BoardView[], cards: Card[], blocks: Block[]): void
    private static generateBoardData(...): BoardExportData
    private static downloadJson(data: object, filename: string): void
}
```

#### `webapp/src/importers/jsonImporter.ts`
```typescript
class JsonImporter {
    static importBoardJson(onComplete?: (result: ImportResult) => void): void
    private static parseJsonFile(file: File): Promise<BoardExportData>
    private static validateSchema(data: any): BoardExportData
}
```

### Files to Modify

#### `webapp/src/telemetry/telemetryClient.ts`
Add new telemetry actions:
```typescript
ImportJson: 'settings_importJson',
ExportJson: 'settings_exportJson',
```

#### `webapp/src/components/sidebar/sidebarSettingsMenu.tsx`
- Add `Import JSON` to existing Import submenu
- Create new `Export` submenu with:
  - Export archive (existing)
  - Export JSON (new)

#### `webapp/i18n/en.json`
Add i18n strings:
```json
"Sidebar.import-json": "Import JSON",
"Sidebar.export-json": "Export JSON",
"Sidebar.export": "Export"
```

### JSON Schema
```typescript
interface BoardJsonExport {
    version: "1.0";
    format: "bacon-ai-boards-json";
    exportDate: number;
    board: { id, title, description, icon, type, cardProperties[], properties{} };
    views: Array<{ id, title, viewType, groupById, sortOptions, filter, ... }>;
    cards: Array<{ id, title, icon, properties{}, contentOrder[] }>;
    blocks: Array<{ id, parentId, type, title, fields{} }>;
}
```

---

## Phase 2: XML Import/Export

### New Files to Create

#### `webapp/src/exporters/xmlExporter.ts`
```typescript
class XmlExporter {
    static exportBoardXml(board, views, cards, blocks): void
    private static boardToXml(data: BoardExportData): string
    private static escapeXml(text: string): string
}
```

#### `webapp/src/importers/xmlImporter.ts`
```typescript
class XmlImporter {
    static importBoardXml(onComplete?): void
    private static parseXmlFile(file: File): Promise<BoardExportData>
    private static xmlToBoard(xmlDoc: Document): BoardExportData
}
```

### Files to Modify
- `sidebarSettingsMenu.tsx` - Add XML import/export menu items
- `telemetryClient.ts` - Add ImportXml, ExportXml actions
- `en.json` - Add i18n strings

---

## Phase 2.5: Add "Depends On" Relation Property Type

### New Files to Create

#### `webapp/src/properties/relation/relation.tsx`
New property type for card-to-card dependencies:
```typescript
// Follows pattern of other properties in webapp/src/properties/
const Relation: PropertyType = {
    Editor: RelationEditor,      // Card picker component
    Display: RelationDisplay,    // Shows linked card titles
    name: 'Relation',
    type: 'relation',
    displayName: 'Relation',
    canFilter: true,
    canGroup: false,
}
```

#### `webapp/src/properties/relation/relationEditor.tsx`
Editor component with card search/picker.

#### `webapp/src/properties/relation/relationDisplay.tsx`
Display component showing linked card titles with click navigation.

### Files to Modify

#### `webapp/src/properties/index.ts`
Register the new relation property type.

#### `webapp/src/blocks/board.ts`
Add 'relation' to PropertyTypeEnum:
```typescript
type PropertyTypeEnum = 'text' | 'number' | 'select' | ... | 'relation';
```

### Relation Property Value Format
```typescript
// Card.properties[dependsOnPropertyId] stores array of card IDs
{
    "depends-on-property-id": ["card-id-1", "card-id-2"]
}
```

---

## Phase 3: BPMN Export (Board to BPMN)

### New Files to Create

#### `webapp/src/types/bpmn.ts`
BPMN 2.0 TypeScript interfaces:
```typescript
interface BpmnDefinitions { id, targetNamespace, process, diagram }
interface BpmnProcess { id, name, laneSets[], startEvents[], endEvents[], tasks[], sequenceFlows[] }
interface BpmnTask { id, name, type, laneRef, incoming[], outgoing[], cardId }
interface BpmnSequenceFlow { id, sourceRef, targetRef }
interface BpmnLane { id, name, flowNodeRefs[], optionId }
interface BpmnDiagram { id, plane: BpmnPlane }
```

#### `webapp/src/exporters/bpmnExporter.ts`
```typescript
interface BpmnMappingConfig {
    statusPropertyId: string;      // Which property = status columns
    startStates: string[];         // Option IDs for "start"
    endStates: string[];           // Option IDs for "end"
    dependencyPropertyId?: string; // Optional dependency property
}

class BpmnExporter {
    static exportBoardBpmn(board, cards, config): void
    private static mapBoardToBpmn(board, cards, config): BpmnDefinitions
    private static generateBpmnXml(definitions): string
    private static calculateDiagramLayout(elements): BpmnDiagram
}
```

#### `webapp/src/components/dialog/bpmnExportDialog.tsx`
Configuration dialog for BPMN export:
- Select status property
- Choose start/end states
- Optional: dependency property

### Mapping Logic
```typescript
function mapCardToTask(card, board, config): BpmnTask {
    return {
        id: `task_${card.id}`,
        name: card.title,
        type: 'userTask',
        laneRef: `lane_${card.properties[config.statusPropertyId]}`,
        cardId: card.id,
    };
}

function determineSequenceFlows(cards, board, config): BpmnSequenceFlow[] {
    // Group cards by status
    // Connect startEvent -> first cards in start states
    // Connect cards in end states -> endEvent
    // Connect cards sequentially within same status
    // Connect last card of one status -> first card of next status
}
```

---

## Phase 4: BPMN Import (BPMN to Board)

### New Files to Create

#### `webapp/src/importers/bpmnImporter.ts`
```typescript
class BpmnImporter {
    static importBpmnFile(teamId, onComplete?): void
    private static parseBpmnFile(file): Promise<BpmnDefinitions>
    private static bpmnToBoard(definitions, teamId): BoardsAndBlocks
    private static mapLanesToStatusProperty(lanes): IPropertyTemplate
    private static mapTaskToCard(task, statusPropertyId): Card
}
```

### Import Mapping
- `bpmn:process` → Board (title from process name)
- `bpmn:lane` → Status property option
- `bpmn:task/userTask` → Card
- Lane assignment → Card status property value
- `bpmn:sequenceFlow` → Card order or dependency property

---

## Phase 5: BPMN Visualization - New "Process Flow" View Type

### Dependencies
```json
"dependencies": {
    "bpmn-js": "^17.0.0",
    "bpmn-js-token-simulation": "^0.32.0"
}
```

### New Files to Create

#### `webapp/src/components/bpmnViewer/bpmnViewer.tsx`
```typescript
import BpmnJS from 'bpmn-js/lib/Viewer';
import tokenSimulation from 'bpmn-js-token-simulation';

const BpmnViewer: React.FC<BpmnViewerProps> = (props) => {
    // Initialize bpmn-js viewer
    // Generate BPMN from board data dynamically
    // Render with token simulation for workflow visualization
    // Handle task click -> navigate to card
    // Sync card status changes to diagram
};
```

#### `webapp/src/components/bpmnViewer/bpmnViewer.scss`
Styling for BPMN canvas and controls.

### New View Type: "Process Flow"
Add 'process' to `IViewType` in `boardView.ts`:
```typescript
type IViewType = 'board' | 'table' | 'gallery' | 'calendar' | 'process';
```

Users can switch between views:
- **Board** (Kanban) - Traditional column view
- **Table** - Spreadsheet view
- **Gallery** - Card grid view
- **Calendar** - Date-based view
- **Process Flow** - BPMN diagram with token simulation

The Process Flow view will:
- Render cards as BPMN tasks in swimlanes (by status)
- Show dependencies as connecting arrows
- Allow token simulation to visualize workflow progression
- Click on task → open card detail
- Real-time sync when cards are updated

---

## Critical Files Reference

| File | Purpose |
|------|---------|
| `webapp/src/archiver.ts` | Pattern for file download/upload (lines 21-47, 64-82) |
| `webapp/src/csvExporter.ts` | Pattern for exporter class (lines 16-49) |
| `webapp/src/components/sidebar/sidebarSettingsMenu.tsx` | Menu location for import/export |
| `webapp/src/blocks/board.ts` | Board and IPropertyTemplate interfaces |
| `webapp/src/blocks/card.ts` | Card interface |
| `webapp/src/telemetry/telemetryClient.ts` | Telemetry actions enum |
| `webapp/src/mutator.ts` | API calls for import/export |

---

## Implementation Order

1. **Sprint 1 (Phase 1)**: JSON Export/Import - Validates architecture
2. **Sprint 2 (Phase 2)**: XML Export/Import - Alternative format
3. **Sprint 3 (Phase 2.5)**: Add "Depends On" relation property type
4. **Sprint 4 (Phase 3)**: BPMN Export - Core BPMN mapping with dependencies
5. **Sprint 5 (Phase 4)**: BPMN Import - Reverse mapping
6. **Sprint 6 (Phase 5)**: Process Flow View - Interactive BPMN visualization

---

## Verification Plan

### Unit Tests
- `jsonExporter.test.ts` - JSON generation
- `jsonImporter.test.ts` - JSON parsing and validation
- `bpmnExporter.test.ts` - BPMN mapping logic

### Integration Tests
- Round-trip: Export → Import → Verify equality
- BPMN export validation with external tools (Camunda Modeler, bpmn.io)

### Manual Testing
1. Export a board with multiple views and cards to JSON
2. Import the JSON into a new team
3. Verify all cards, properties, and views match
4. Export to BPMN and open in https://demo.bpmn.io/
5. Verify tasks match cards and lanes match status columns
6. Test BPMN viewer with token simulation

---

## Generated BPMN Example

```xml
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
    <bpmn:process id="Process_board_xyz" name="My Project">
        <bpmn:laneSet>
            <bpmn:lane id="Lane_todo" name="To Do">
                <bpmn:flowNodeRef>task_card1</bpmn:flowNodeRef>
            </bpmn:lane>
            <bpmn:lane id="Lane_done" name="Done">
                <bpmn:flowNodeRef>task_card2</bpmn:flowNodeRef>
            </bpmn:lane>
        </bpmn:laneSet>
        <bpmn:startEvent id="StartEvent_1"/>
        <bpmn:userTask id="task_card1" name="Design Feature"/>
        <bpmn:userTask id="task_card2" name="Review Feature"/>
        <bpmn:endEvent id="EndEvent_1"/>
        <bpmn:sequenceFlow sourceRef="StartEvent_1" targetRef="task_card1"/>
        <bpmn:sequenceFlow sourceRef="task_card1" targetRef="task_card2"/>
        <bpmn:sequenceFlow sourceRef="task_card2" targetRef="EndEvent_1"/>
    </bpmn:process>
</bpmn:definitions>
```

---

## i18n Strings

```json
{
    "Sidebar.import-json": "Import JSON",
    "Sidebar.export-json": "Export JSON",
    "Sidebar.import-xml": "Import XML",
    "Sidebar.export-xml": "Export XML",
    "Sidebar.import-bpmn": "Import BPMN",
    "Sidebar.export-bpmn": "Export BPMN",
    "Sidebar.export": "Export",
    "BpmnExport.title": "Export as BPMN",
    "BpmnExport.statusProperty": "Status Property",
    "BpmnExport.startStates": "Start States",
    "BpmnExport.endStates": "End States",
    "BpmnViewer.simulate": "Simulate Workflow",
    "BpmnViewer.title": "BPMN Process View"
}
```
