# Focalboard REST API Reference

This document provides a comprehensive guide to the Focalboard REST API, discovered through source code analysis and testing.

## Authentication

### CSRF Protection (CRITICAL)

All API v2 endpoints require CSRF protection. Include this header in **every request**:

```
X-Requested-With: XMLHttpRequest
```

Without this header, all requests will fail with:
```json
{"error": "checkCSRFToken FAILED", "errorCode": 400}
```

### Session Authentication

Focalboard supports multiple authentication methods (in priority order):

1. **Cookie Authentication**
   ```
   Cookie: FOCALBOARDAUTHTOKEN=<token>
   ```

2. **Bearer Token (Header)**
   ```
   Authorization: Bearer <token>
   ```

3. **Token Header**
   ```
   Authorization: token <token>
   ```

4. **Query String** (least secure, for sharing links)
   ```
   ?access_token=<token>
   ```

### Login Endpoint

```bash
# Login to get a session token
curl -s -X POST "http://localhost:8000/api/v2/login" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{"type":"normal","username":"<username>","password":"<password>"}'

# Response:
# {"token": "k77tg84g87pd6tjk7rdho1kqs9h"}
```

**Important:** Use `jq` or proper JSON encoding if password contains special characters:
```bash
jq -n --arg user "username" --arg pass "p@ss!" \
  '{"type":"normal","username":$user,"password":$pass}' | \
  curl -s -X POST "http://localhost:8000/api/v2/login" \
    -H "Content-Type: application/json" \
    -H "X-Requested-With: XMLHttpRequest" \
    -d @-
```

## API Endpoints

### User Endpoints

```bash
# Get current user
GET /api/v2/users/me

# Get user by ID
GET /api/v2/users/{userID}

# Get user preferences
GET /api/v2/users/me/config
```

### Board Endpoints

```bash
# List boards for a team
GET /api/v2/teams/{teamID}/boards

# Get board by ID
GET /api/v2/boards/{boardID}

# Create a new board
POST /api/v2/boards

# Update a board
PATCH /api/v2/boards/{boardID}

# Delete a board
DELETE /api/v2/boards/{boardID}

# Duplicate a board
POST /api/v2/boards/{boardID}/duplicate
```

### Card Endpoints

```bash
# List cards on a board
GET /api/v2/boards/{boardID}/cards

# Create a new card
POST /api/v2/boards/{boardID}/cards

# Get card by ID
GET /api/v2/cards/{cardID}

# Update a card
PATCH /api/v2/cards/{cardID}
```

### Template Endpoints

```bash
# List templates for a team
GET /api/v2/teams/{teamID}/templates
```

## Card Structure

### Card JSON Schema

```json
{
  "title": "Card Title",
  "icon": "🔍",
  "properties": {
    "<property_id>": "<option_id or value>"
  },
  "contentOrder": [],
  "isTemplate": false
}
```

### Property Types

| Type | Value Format | Example |
|------|--------------|---------|
| `select` | Option ID string | `"ayz81h9f3dwp7rzzbdebesc7ute"` |
| `multiSelect` | Array of option IDs | `["id1", "id2"]` |
| `text` | String | `"Some text"` |
| `number` | String (numeric) | `"8"` |
| `date` | JSON object with `from` timestamp | `{"from": 1769814594000}` |
| `person` | User ID string | `"uaf6wzjxcofncxfmojerw3xw51w"` |
| `createdBy` | Auto-populated | - |
| `createdTime` | Auto-populated | - |

**Important:** The `date` type requires a JSON object with a `from` key containing the Unix timestamp in milliseconds.

### Task Naming Convention for Proper Sorting

Focalboard sorts cards alphanumerically. To ensure proper sequential ordering:

```
P00, P01, P02 ... P09, P10, P11, P12  ✓ (zero-padded phases)
T001, T002 ... T009, T010 ... T099, T100  ✓ (three-digit tasks)

1, 2 ... 9, 10, 11  ✗ (10 comes after 1, before 2)
Phase 1, Phase 10, Phase 2  ✗ (wrong order)
```

### Example: Create Card with Properties

```bash
curl -s -X POST "http://localhost:8000/api/v2/boards/bd5mw98s3cjftjnef77q8c4oone/cards" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "Authorization: Bearer k77tg84g87pd6tjk7rdho1kqs9h" \
  -d '{
    "title": "My New Task",
    "icon": "📋",
    "properties": {
      "a972dc7a-5f4c-45d2-8044-8c28c69717f1": "ayz81h9f3dwp7rzzbdebesc7ute",
      "d3d682bf-e074-49d9-8df5-7320921c2d23": "d3bfb50f-f569-4bad-8a3a-dd15c3f60101"
    }
  }'
```

## Board Properties Discovery

To find property IDs and option IDs for a board:

```bash
# Get board details with cardProperties
curl -s -X GET "http://localhost:8000/api/v2/boards/{boardID}" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "Authorization: Bearer {token}" | jq '.cardProperties'
```

Example output:
```json
[
  {
    "id": "a972dc7a-5f4c-45d2-8044-8c28c69717f1",
    "name": "Status",
    "type": "select",
    "options": [
      {"id": "ayz81h9f3dwp7rzzbdebesc7ute", "value": "Not Started", "color": "propColorBlue"},
      {"id": "ar6b8m3jxr3asyxhr8iucdbo6yc", "value": "In Progress", "color": "propColorYellow"},
      {"id": "adeo5xuwne3qjue83fcozekz8ko", "value": "Completed 🙌", "color": "propColorGreen"}
    ]
  }
]
```

## Bulk Operations

### Disable Notifications for Bulk Insert

Add `?disable_notify=true` to prevent notification spam:

```bash
POST /api/v2/boards/{boardID}/cards?disable_notify=true
```

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad Request (CSRF failure, invalid JSON) |
| 401 | Unauthorized (invalid/expired token) |
| 403 | Forbidden (no permission) |
| 404 | Not Found |
| 500 | Internal Server Error |

## Common Issues

### JSON Parsing Errors

If you see `invalid character '!' in string escape code`, ensure proper JSON encoding. Use `jq` for safe construction:

```bash
jq -n --arg title "Task with 'quotes'" '{"title": $title}'
```

### Session Expiry

Sessions may expire. Re-authenticate if you get 401 errors:

```bash
# Check if session is valid
curl -s "http://localhost:8000/api/v2/users/me" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "Authorization: Bearer {token}"
```

## Complete Example: Automation Script

See `/home/bacon/bacon-ai/projects/focalboard/claude-integration/scripts/create_bacon_ai_tasks.sh` for a complete example of:

1. Authentication with Bearer token
2. CSRF protection with X-Requested-With
3. Proper JSON encoding with jq
4. Bulk card creation
5. Property value assignment

---

**Last Updated:** January 2026
**Source:** Focalboard v7.x (mattermost/focalboard)
