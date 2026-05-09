# Generate Project Diagrams

Generate comprehensive project documentation diagrams including data flow diagrams, ER diagrams, functional module diagrams, and use case diagrams.

## Usage

```
/generate-diagrams [options]
```

## Options

- `--output-dir <path>`: Output directory for generated diagrams (default: `$HOME/Desktop/项目图表`)
- `--type <types>`: Comma-separated diagram types to generate:
  - `dataflow`: Data flow diagram
  - `er`: Database ER diagram
  - `module`: Functional module diagram
  - `usecase`: Use case diagram
  - `all`: Generate all diagram types (default)
- `--style <style>`: Diagram style:
  - `detailed`: More detailed diagrams with more information
  - `simple`: Simplified diagrams focusing on key elements (default for ER)
- `--lang <language>`: Language for diagram content (default: `zh` for Chinese)

## Examples

```bash
# Generate all diagrams to default location
/generate-diagrams

# Generate only ER diagram and data flow diagram
/generate-diagrams --type er,dataflow

# Generate detailed data flow diagram
/generate-diagrams --type dataflow --style detailed

# Output to custom directory
/generate-diagrams --output-dir ./docs/diagrams
```

## What This Skill Does

1. **Analyzes Project Structure**
   - Scans Django models (`models.py` files)
   - Analyzes views and business logic
   - Identifies user and admin functionalities
   - Maps relationships between entities

2. **Generates Diagrams**

   ### Data Flow Diagram
   - Level 0: System context diagram
   - Level 1: Detailed process flow
   - Core business data flow

   ### Database ER Diagram
   - Full entity-relationship diagram with all fields
   - Simplified core relationship diagram
   - Entity descriptions

   ### Functional Module Diagram
   - User-side modules (authentication, shopping, orders)
   - Admin-side modules (management, analytics)
   - System architecture diagram

   ### Use Case Diagram
   - User use cases with relationships
   - Admin use cases with relationships
   - Use case specification tables

3. **Output Format**
   - Markdown files with Mermaid diagrams
   - Compatible with Mermaid renderers
   - Organized structure with table of contents

## Implementation Instructions

When this skill is invoked:

1. **Project Analysis Phase**
   ```
   - Read all models.py files to understand data structures
   - Read all views.py files to understand business logic
   - Read urls.py to understand routing
   - Identify user roles (user, admin, guest)
   - Map all CRUD operations and workflows
   ```

2. **Diagram Generation Phase**
   ```
   - Create output directory if not exists
   - Generate each requested diagram type
   - Use Mermaid syntax for all diagrams
   - Include both detailed and simplified versions where applicable
   - Add explanatory text in Chinese (or specified language)
   ```

3. **Output Structure**
   ```
   输出目录/
   ├── 数据流图.md
   ├── 数据库ER图.md
   ├── 功能模块图.md
   └── 用例图.md
   ```

## Diagram Design Guidelines

### Data Flow Diagrams
- Use `flowchart TB` or `flowchart LR` for Mermaid
- Level 0: Show external entities and main system
- Level 1: Show processes, data stores, and data flows
- Include Session/Cache as data stores if used
- Show bidirectional data flows where applicable

### ER Diagrams
- Use `erDiagram` for Mermaid
- Show primary keys (PK) and foreign keys (FK)
- Include field types and constraints
- Use cardinality notation (||--o{, }o--||, etc.)
- Group related entities logically

### Functional Module Diagrams
- Use `mindmap` for hierarchical structure
- Separate user and admin modules
- Include up to 3 levels of nesting
- Use clear, action-oriented labels
- Show system architecture separately

### Use Case Diagrams
- Use `flowchart TB` for Mermaid (closest to UML use case)
- Define actors (user, admin) as rounded nodes
- Group use cases by functional area
- Show include/extend relationships with dotted lines
- Include a specification table for key use cases

## Template Variables

The skill can use these template variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{project_name}}` | Project name | "电商系统" |
| `{{entities}}` | List of database entities | User, Product, Order |
| `{{user_features}}` | User-side features | 注册、登录、购物 |
| `{{admin_features}}` | Admin-side features | 商品管理、订单管理 |
| `{{output_dir}}` | Output directory path | /Users/xxx/Desktop/项目图表 |

## Notes

- Requires Mermaid-compatible Markdown viewer for rendering
- Diagrams are generated based on current code state
- Re-run after significant code changes to update diagrams
- Can be customized by modifying templates in this file
