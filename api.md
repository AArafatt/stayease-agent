# StayEase API Contract

Base URL: `http://localhost:8000`

---

## 1. Send a Guest Message

```
POST /api/chat/{conversation_id}/message
```

Sends a guest message to the AI agent and returns the agent's reply along with any structured data (search results, listing details, or booking confirmation).

### Path Parameters

| Parameter         | Type   | Description                          |
| ----------------- | ------ | ------------------------------------ |
| `conversation_id` | string | UUID identifying the conversation    |

### Request Body

```json
{
  "message": "string (required, 1–2000 chars)",
  "guest_name": "string | null",
  "guest_email": "string | null"
}
```

### Response — `200 OK`

```json
{
  "conversation_id": "string",
  "reply": "string",
  "intent": "search | details | book | escalate",
  "data": { } | null
}
```

The `data` field is `null` when the agent's reply is purely conversational. Otherwise it contains one of:

- **Search results** — `{ "properties": [...] }`
- **Booking confirmation** — `{ "booking": { ... } }`

---

### Example — Property Search

**Request**

```bash
curl -X POST http://localhost:8000/api/chat/a1b2c3d4-5678-90ab-cdef-111111111111/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need a room in Cox'\''s Bazar for 2 nights starting December 20 for 2 guests",
    "guest_name": "Rahim Uddin"
  }'
```

**Response**

```json
{
  "conversation_id": "a1b2c3d4-5678-90ab-cdef-111111111111",
  "reply": "Here are available properties in Cox's Bazar for 2 guests (Dec 20–22):\n\n1. **Sea Pearl Beach Resort** — ৳4,500/night (৳9,000 total) ⭐ 4.7\n2. **Ocean Paradise** — ৳3,800/night (৳7,600 total) ⭐ 4.5\n3. **Coral Reef Guest House** — ৳2,200/night (৳4,400 total) ⭐ 4.3\n\nWould you like details on any of these?",
  "intent": "search",
  "data": {
    "properties": [
      {
        "listing_id": 12,
        "title": "Sea Pearl Beach Resort",
        "location": "Cox's Bazar",
        "price_per_night": 4500.00,
        "total_price": 9000.00,
        "max_guests": 4,
        "bedrooms": 2,
        "rating": 4.7,
        "total_reviews": 128
      },
      {
        "listing_id": 7,
        "title": "Ocean Paradise",
        "location": "Cox's Bazar",
        "price_per_night": 3800.00,
        "total_price": 7600.00,
        "max_guests": 3,
        "bedrooms": 1,
        "rating": 4.5,
        "total_reviews": 85
      },
      {
        "listing_id": 23,
        "title": "Coral Reef Guest House",
        "location": "Cox's Bazar",
        "price_per_night": 2200.00,
        "total_price": 4400.00,
        "max_guests": 2,
        "bedrooms": 1,
        "rating": 4.3,
        "total_reviews": 42
      }
    ]
  }
}
```

---

### Example — Create Booking

**Request**

```bash
curl -X POST http://localhost:8000/api/chat/a1b2c3d4-5678-90ab-cdef-111111111111/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Book Sea Pearl Beach Resort for me please",
    "guest_name": "Rahim Uddin",
    "guest_email": "rahim.uddin@gmail.com"
  }'
```

**Response**

```json
{
  "conversation_id": "a1b2c3d4-5678-90ab-cdef-111111111111",
  "reply": "Your booking is confirmed! 🎉\n\n**Sea Pearl Beach Resort**\n📅 Dec 20 – Dec 22 (2 nights)\n👥 2 guests\n💰 Total: ৳9,000\n\nA confirmation has been sent to rahim.uddin@gmail.com. Enjoy your stay in Cox's Bazar!",
  "intent": "book",
  "data": {
    "booking": {
      "booking_id": 45,
      "listing_title": "Sea Pearl Beach Resort",
      "check_in": "2025-12-20",
      "check_out": "2025-12-22",
      "num_guests": 2,
      "total_price": 9000.00,
      "status": "confirmed"
    }
  }
}
```

---

### Error Responses

| Status | Condition                    | Body                                                    |
| ------ | ---------------------------- | ------------------------------------------------------- |
| `422`  | Invalid request body         | `{ "detail": "message: field required" }`               |
| `500`  | Agent or database failure    | `{ "detail": "Internal server error" }`                 |

---

## 2. Get Conversation History

```
GET /api/chat/{conversation_id}/history
```

Returns the full message history for an existing conversation.

### Path Parameters

| Parameter         | Type   | Description                          |
| ----------------- | ------ | ------------------------------------ |
| `conversation_id` | string | UUID identifying the conversation    |

### Response — `200 OK`

```json
{
  "conversation_id": "string",
  "messages": [
    {
      "role": "human | ai",
      "content": "string",
      "timestamp": "ISO 8601 datetime"
    }
  ],
  "intent": "string | null",
  "is_escalated": false
}
```

---

### Example

**Request**

```bash
curl http://localhost:8000/api/chat/a1b2c3d4-5678-90ab-cdef-111111111111/history
```

**Response**

```json
{
  "conversation_id": "a1b2c3d4-5678-90ab-cdef-111111111111",
  "messages": [
    {
      "role": "human",
      "content": "I need a room in Cox's Bazar for 2 nights starting December 20 for 2 guests",
      "timestamp": "2025-12-18T10:30:00Z"
    },
    {
      "role": "ai",
      "content": "Here are available properties in Cox's Bazar for 2 guests (Dec 20–22):\n\n1. **Sea Pearl Beach Resort** — ৳4,500/night (৳9,000 total) ⭐ 4.7\n2. **Ocean Paradise** — ৳3,800/night (৳7,600 total) ⭐ 4.5\n3. **Coral Reef Guest House** — ৳2,200/night (৳4,400 total) ⭐ 4.3\n\nWould you like details on any of these?",
      "timestamp": "2025-12-18T10:30:02Z"
    },
    {
      "role": "human",
      "content": "Book Sea Pearl Beach Resort for me please",
      "timestamp": "2025-12-18T10:31:15Z"
    },
    {
      "role": "ai",
      "content": "Your booking is confirmed! 🎉\n\n**Sea Pearl Beach Resort**\n📅 Dec 20 – Dec 22 (2 nights)\n👥 2 guests\n💰 Total: ৳9,000\n\nA confirmation has been sent to rahim.uddin@gmail.com. Enjoy your stay in Cox's Bazar!",
      "timestamp": "2025-12-18T10:31:18Z"
    }
  ],
  "intent": "book",
  "is_escalated": false
}
```

---

### Error Responses

| Status | Condition               | Body                                       |
| ------ | ----------------------- | ------------------------------------------ |
| `404`  | Conversation not found  | `{ "detail": "Conversation not found." }`  |
| `500`  | Database failure        | `{ "detail": "Internal server error" }`    |
