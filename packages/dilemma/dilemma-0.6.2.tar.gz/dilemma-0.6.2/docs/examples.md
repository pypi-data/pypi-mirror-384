# Dilemma Expression Examples
This document contains examples of using the Dilemma expression language.


### String
Check if a filename matches a pattern with wildcard

```
'document.pdf' like '*.pdf'
```
`Result: True`

---

Check if two words are equal

```
'hello' is 'hello'
```
`Result: True`

---

Check if two words are not equal

```
'hello' is not 'world'
```
`Result: True`

---

Check if two words are not equal

```
 friend.snores is not 'often'
```
```json
{
  "friend": {
    "name": "Bob",
    "snores": "often"
  }
}
```
`Result: False`

---

Check if a phrase contains a word

```
'world' in 'hello world'
```
`Result: True`

---

Check if two variables are equal

```
var1 is var2
```
```json
{
  "var1": "hello",
  "var2": "hello"
}
```
`Result: True`

---

Check if a string matches a pattern with ? (single character wildcard)

```
'user123' like 'user???'
```
`Result: True`

---

Demonstrate case-insensitive matching with the &#x27;like&#x27; operator

```
'Hello.TXT' like '*.txt'
```
`Result: True`

---

Match a variable against a pattern

```
filename like '*.jpg'
```
```json
{
  "filename": "vacation-photo.JPG"
}
```
`Result: True`

---

Check a variable doen&#x27;t match  a pattern

```
filename not like '*.jpg'
```
```json
{
  "filename": "vacation-photo.JPG"
}
```
`Result: False`

---

Check if two words are equal

```
'hello' == 'hello'
```
`Result: True`

---

Check if two words are not equal

```
'hello' != 'world'
```
`Result: True`

---


### Critical Path
Test lookup of nested attributes by possesive English syntax

```
user's name == 'bob'
```
```json
{
  "user": {
    "name": "bob"
  }
}
```
`Result: True`

---

Test lookup of nested attributes by possesive English syntax

```
'admin' in user's roles
```
```json
{
  "user": {
    "roles": [
      "reader",
      "writer",
      "admin"
    ]
  }
}
```
`Result: True`

---

Test lookup of nested attributes by possesive English syntax

```
 user's roles contains 'reader'
```
```json
{
  "user": {
    "roles": [
      "reader",
      "writer",
      "admin"
    ]
  }
}
```
`Result: True`

---

Is it too late to reach the bar before last orders?

```
bar's closing_time upcoming within (bar.distance / bike.speed)  hours
```
```json
{
  "bar": {
    "closing_time": "__HOUR_FROM_NOW__",
    "distance": 10,
    "units": "miles"
  },
  "bike": {
    "speed": 20,
    "units": "mph"
  }
}
```
`Result: False`

---


### Array Sugar Advanced
Real-world business logic: at least 3 orders over $100

```
at least 3 of orders matches | total > 100 |
```
```json
{
  "orders": [
    {
      "id": "ORD001",
      "total": 150.5,
      "status": "completed"
    },
    {
      "id": "ORD002",
      "total": 89.99,
      "status": "pending"
    },
    {
      "id": "ORD003",
      "total": 200.0,
      "status": "completed"
    },
    {
      "id": "ORD004",
      "total": 125.75,
      "status": "shipped"
    },
    {
      "id": "ORD005",
      "total": 300.0,
      "status": "completed"
    }
  ]
}
```
`Result: True`

---

System monitoring: at most 2 services with errors

```
at most 2 of services matches | error_count > 0 |
```
```json
{
  "services": [
    {
      "name": "auth-service",
      "error_count": 1,
      "status": "degraded"
    },
    {
      "name": "payment-service",
      "error_count": 0,
      "status": "healthy"
    },
    {
      "name": "notification-service",
      "error_count": 3,
      "status": "critical"
    },
    {
      "name": "user-service",
      "error_count": 0,
      "status": "healthy"
    }
  ]
}
```
`Result: True`

---

Team management: exactly 2 senior developers

```
exactly 2 of team_members matches | level == 'senior' and role == 'developer' |
```
```json
{
  "team_members": [
    {
      "name": "Alice",
      "role": "developer",
      "level": "senior",
      "years_experience": 8
    },
    {
      "name": "Bob",
      "role": "developer",
      "level": "junior",
      "years_experience": 2
    },
    {
      "name": "Charlie",
      "role": "developer",
      "level": "senior",
      "years_experience": 12
    },
    {
      "name": "Diana",
      "role": "designer",
      "level": "senior",
      "years_experience": 10
    }
  ]
}
```
`Result: True`

---

Security audit: any server has critical vulnerabilities

```
any of servers matches | vulnerabilities.critical > 0 |
```
```json
{
  "servers": [
    {
      "hostname": "web-01",
      "vulnerabilities": {
        "critical": 0,
        "high": 2,
        "medium": 5
      }
    },
    {
      "hostname": "db-01",
      "vulnerabilities": {
        "critical": 1,
        "high": 0,
        "medium": 3
      }
    },
    {
      "hostname": "cache-01",
      "vulnerabilities": {
        "critical": 0,
        "high": 1,
        "medium": 2
      }
    }
  ]
}
```
`Result: True`

---

Compliance check: all departments meet data retention policies

```
all of departments matches | data_retention_policy.implemented == true and audit_score >= 85 |
```
```json
{
  "departments": [
    {
      "name": "Finance",
      "data_retention_policy": {
        "implemented": true,
        "last_updated": "2024-01-15"
      },
      "audit_score": 92
    },
    {
      "name": "HR",
      "data_retention_policy": {
        "implemented": true,
        "last_updated": "2024-02-10"
      },
      "audit_score": 88
    },
    {
      "name": "Marketing",
      "data_retention_policy": {
        "implemented": false,
        "last_updated": "2023-12-01"
      },
      "audit_score": 78
    }
  ]
}
```
`Result: False`

---

Operations: no critical alerts in the last hour

```
none of alerts matches | severity == 'critical' and age_minutes < 60 |
```
```json
{
  "alerts": [
    {
      "id": "ALT001",
      "severity": "warning",
      "age_minutes": 15,
      "message": "High CPU usage"
    },
    {
      "id": "ALT002",
      "severity": "critical",
      "age_minutes": 45,
      "message": "Database connection failed"
    },
    {
      "id": "ALT003",
      "severity": "info",
      "age_minutes": 120,
      "message": "Scheduled maintenance completed"
    }
  ]
}
```
`Result: False`

---

Inventory: at least 5 items low stock AND exactly 2 items out of stock

```
at least 5 of products matches |stock_level < 10| and exactly 2 of products matches |stock_level == 0|
```
```json
{
  "products": [
    {
      "sku": "PROD001",
      "name": "Widget A",
      "stock_level": 5,
      "reorder_point": 10
    },
    {
      "sku": "PROD002",
      "name": "Widget B",
      "stock_level": 0,
      "reorder_point": 15
    },
    {
      "sku": "PROD003",
      "name": "Widget C",
      "stock_level": 3,
      "reorder_point": 8
    },
    {
      "sku": "PROD004",
      "name": "Widget D",
      "stock_level": 25,
      "reorder_point": 20
    },
    {
      "sku": "PROD005",
      "name": "Widget E",
      "stock_level": 0,
      "reorder_point": 12
    },
    {
      "sku": "PROD006",
      "name": "Widget F",
      "stock_level": 7,
      "reorder_point": 10
    },
    {
      "sku": "PROD007",
      "name": "Widget G",
      "stock_level": 2,
      "reorder_point": 5
    },
    {
      "sku": "PROD008",
      "name": "Widget H",
      "stock_level": 9,
      "reorder_point": 15
    }
  ]
}
```
`Result: True`

---

Performance monitoring: at most 1 service below SLA

```
at most 1 of microservices matches | uptime_percentage < 99.9 |
```
```json
{
  "microservices": [
    {
      "name": "user-api",
      "uptime_percentage": 99.95,
      "response_time_ms": 45
    },
    {
      "name": "payment-api",
      "uptime_percentage": 99.87,
      "response_time_ms": 120
    },
    {
      "name": "inventory-api",
      "uptime_percentage": 99.99,
      "response_time_ms": 32
    },
    {
      "name": "shipping-api",
      "uptime_percentage": 99.92,
      "response_time_ms": 78
    }
  ]
}
```
`Result: True`

---

Analytics: exactly 3 users with high engagement

```
exactly 3 of users matches | session_count > 50 and avg_session_duration > 300 |
```
```json
{
  "users": [
    {
      "user_id": "USR001",
      "session_count": 75,
      "avg_session_duration": 420,
      "last_login": "2024-10-08"
    },
    {
      "user_id": "USR002",
      "session_count": 25,
      "avg_session_duration": 180,
      "last_login": "2024-10-07"
    },
    {
      "user_id": "USR003",
      "session_count": 60,
      "avg_session_duration": 350,
      "last_login": "2024-10-08"
    },
    {
      "user_id": "USR004",
      "session_count": 55,
      "avg_session_duration": 310,
      "last_login": "2024-10-08"
    },
    {
      "user_id": "USR005",
      "session_count": 40,
      "avg_session_duration": 250,
      "last_login": "2024-10-06"
    }
  ]
}
```
`Result: True`

---

Risk management: any portfolio exceeds risk tolerance

```
any of portfolios matches | risk_score > 7.5 and exposure_percentage > 0.15 |
```
```json
{
  "portfolios": [
    {
      "portfolio_id": "PF001",
      "risk_score": 6.2,
      "exposure_percentage": 0.12,
      "total_value": 150000
    },
    {
      "portfolio_id": "PF002",
      "risk_score": 8.1,
      "exposure_percentage": 0.08,
      "total_value": 250000
    },
    {
      "portfolio_id": "PF003",
      "risk_score": 5.9,
      "exposure_percentage": 0.18,
      "total_value": 180000
    },
    {
      "portfolio_id": "PF004",
      "risk_score": 7.3,
      "exposure_percentage": 0.14,
      "total_value": 220000
    }
  ]
}
```
`Result: False`

---

Content moderation: all posts reviewed and none flagged as spam

```
all of posts matches |reviewed == true| and none of posts matches |flags contains 'spam'|
```
```json
{
  "posts": [
    {
      "post_id": "PST001",
      "reviewed": true,
      "flags": [
        "inappropriate"
      ],
      "author": "user123"
    },
    {
      "post_id": "PST002",
      "reviewed": true,
      "flags": [],
      "author": "user456"
    },
    {
      "post_id": "PST003",
      "reviewed": false,
      "flags": [
        "spam"
      ],
      "author": "user789"
    },
    {
      "post_id": "PST004",
      "reviewed": true,
      "flags": [
        "spam",
        "inappropriate"
      ],
      "author": "user101"
    }
  ]
}
```
`Result: False`

---

Auto-scaling: at least 2 nodes with high CPU and exactly 1 with low memory

```
at least 2 of nodes matches |cpu_usage > 85| and exactly 1 of nodes matches |memory_usage < 20|
```
```json
{
  "nodes": [
    {
      "node_id": "NODE001",
      "cpu_usage": 92,
      "memory_usage": 45,
      "disk_usage": 67
    },
    {
      "node_id": "NODE002",
      "cpu_usage": 78,
      "memory_usage": 15,
      "disk_usage": 82
    },
    {
      "node_id": "NODE003",
      "cpu_usage": 89,
      "memory_usage": 56,
      "disk_usage": 34
    },
    {
      "node_id": "NODE004",
      "cpu_usage": 65,
      "memory_usage": 78,
      "disk_usage": 91
    }
  ]
}
```
`Result: True`

---

QA pipeline: none of test suites have failing tests

```
none of test_suites matches | failed_tests > 0 or test_coverage < 80 |
```
```json
{
  "test_suites": [
    {
      "name": "unit_tests",
      "passed_tests": 245,
      "failed_tests": 0,
      "test_coverage": 94.5
    },
    {
      "name": "integration_tests",
      "passed_tests": 78,
      "failed_tests": 0,
      "test_coverage": 87.2
    },
    {
      "name": "e2e_tests",
      "passed_tests": 32,
      "failed_tests": 0,
      "test_coverage": 82.1
    }
  ]
}
```
`Result: True`

---

Customer success: at most 3 customers with low satisfaction

```
at most 3 of customers matches | satisfaction_score < 7 and support_tickets > 5 |
```
```json
{
  "customers": [
    {
      "customer_id": "CUST001",
      "satisfaction_score": 8.5,
      "support_tickets": 2,
      "churn_risk": false
    },
    {
      "customer_id": "CUST002",
      "satisfaction_score": 6.2,
      "support_tickets": 8,
      "churn_risk": true
    },
    {
      "customer_id": "CUST003",
      "satisfaction_score": 9.1,
      "support_tickets": 1,
      "churn_risk": false
    },
    {
      "customer_id": "CUST004",
      "satisfaction_score": 5.8,
      "support_tickets": 12,
      "churn_risk": true
    },
    {
      "customer_id": "CUST005",
      "satisfaction_score": 7.9,
      "support_tickets": 3,
      "churn_risk": false
    }
  ]
}
```
`Result: True`

---

DevOps: all environments healthy and exactly 0 with pending deployments

```
all of environments matches |health_status == 'green'| and exactly 0 of environments matches |pending_deployments > 0|
```
```json
{
  "environments": [
    {
      "name": "development",
      "health_status": "green",
      "pending_deployments": 0,
      "last_deployment": "2024-10-08T10:30:00Z"
    },
    {
      "name": "staging",
      "health_status": "green",
      "pending_deployments": 0,
      "last_deployment": "2024-10-08T09:15:00Z"
    },
    {
      "name": "production",
      "health_status": "green",
      "pending_deployments": 0,
      "last_deployment": "2024-10-07T14:45:00Z"
    }
  ]
}
```
`Result: True`

---


### Array Sugar Combined
Combine array sugar with string pattern matching

```
at least 2 of files matches |name like '*.pdf'| and any of files matches |name like '*.doc'|
```
```json
{
  "files": [
    {
      "name": "report.pdf",
      "size": 1024
    },
    {
      "name": "manual.pdf",
      "size": 2048
    },
    {
      "name": "notes.doc",
      "size": 512
    },
    {
      "name": "image.jpg",
      "size": 256
    }
  ]
}
```
`Result: True`

---

Combine array sugar with date state checking

```
exactly 2 of events matches |date is $past| and none of events matches |date is $future|
```
```json
{
  "events": [
    {
      "name": "Conference",
      "date": "2025-10-14 23:56:44 UTC"
    },
    {
      "name": "Meeting",
      "date": "2025-10-16 23:56:44 UTC"
    },
    {
      "name": "Workshop",
      "date": "2025-10-08 23:56:44 UTC"
    }
  ]
}
```
`Result: False`

---

Array sugar with date time windows

```
at least 1 of tasks matches | due_date upcoming within 24 hours |
```
```json
{
  "tasks": [
    {
      "title": "Review PR",
      "due_date": "2025-10-15 22:56:44 UTC"
    },
    {
      "title": "Write tests",
      "due_date": "2025-10-16 23:56:44 UTC"
    },
    {
      "title": "Deploy",
      "due_date": "2025-10-08 23:56:44 UTC"
    }
  ]
}
```
`Result: True`

---

Array sugar with nested object string operations

```
any of users matches |profile.email like '*@company.com'| and all of users matches |status != 'inactive'|
```
```json
{
  "users": [
    {
      "name": "Alice",
      "profile": {
        "email": "alice@company.com"
      },
      "status": "active"
    },
    {
      "name": "Bob",
      "profile": {
        "email": "bob@external.org"
      },
      "status": "active"
    },
    {
      "name": "Charlie",
      "profile": {
        "email": "charlie@company.com"
      },
      "status": "pending"
    }
  ]
}
```
`Result: True`

---

Array sugar with possessive syntax

```
exactly 1 of employees matches | manager's department == 'Engineering' |
```
```json
{
  "employees": [
    {
      "name": "Alice",
      "manager": {
        "name": "Sarah",
        "department": "Engineering"
      }
    },
    {
      "name": "Bob",
      "manager": {
        "name": "Mike",
        "department": "Marketing"
      }
    },
    {
      "name": "Charlie",
      "manager": {
        "name": "Lisa",
        "department": "Sales"
      }
    }
  ]
}
```
`Result: True`

---

Complex string conditions in array sugar

```
at most 2 of products matches | name like '*Pro*' and category == 'Software' |
```
```json
{
  "products": [
    {
      "name": "Video Pro",
      "category": "Software",
      "price": 299
    },
    {
      "name": "Audio Pro",
      "category": "Software",
      "price": 199
    },
    {
      "name": "Design Pro",
      "category": "Hardware",
      "price": 399
    },
    {
      "name": "Basic Editor",
      "category": "Software",
      "price": 99
    }
  ]
}
```
`Result: True`

---

Array sugar with date before/after comparisons

```
all of projects matches |start_date before end_date| and at least 1 of projects matches |end_date after '2024-12-01'|
```
```json
{
  "projects": [
    {
      "name": "Project Alpha",
      "start_date": "2024-10-01",
      "end_date": "2024-12-15"
    },
    {
      "name": "Project Beta",
      "start_date": "2024-09-15",
      "end_date": "2024-11-30"
    },
    {
      "name": "Project Gamma",
      "start_date": "2024-11-01",
      "end_date": "2025-01-15"
    }
  ]
}
```
`Result: True`

---

Array sugar with same day date comparisons

```
exactly 2 of meetings matches | start_time same_day_as end_time |
```
```json
{
  "meetings": [
    {
      "title": "Standup",
      "start_time": "2024-10-08T09:00:00Z",
      "end_time": "2024-10-08T09:30:00Z"
    },
    {
      "title": "Planning",
      "start_time": "2024-10-08T14:00:00Z",
      "end_time": "2024-10-09T10:00:00Z"
    },
    {
      "title": "Review",
      "start_time": "2024-10-07T15:00:00Z",
      "end_time": "2024-10-07T16:00:00Z"
    }
  ]
}
```
`Result: True`

---

Array sugar with older than time comparisons

```
none of logs matches | timestamp older than 1 hour |
```
```json
{
  "logs": [
    {
      "message": "System started",
      "timestamp": "2025-10-15 22:56:44 UTC"
    },
    {
      "message": "User login",
      "timestamp": "2025-10-15 23:56:44 UTC"
    },
    {
      "message": "Data processed",
      "timestamp": "2025-10-14 23:56:44 UTC"
    }
  ]
}
```
`Result: False`

---

Combine string contains with date operations

```
any of alerts matches | 'Critical' in message and created_at is $past |
```
```json
{
  "alerts": [
    {
      "id": 1,
      "message": "Critical system failure detected",
      "created_at": "2025-10-14 23:56:44 UTC"
    },
    {
      "id": 2,
      "message": "Warning: high memory usage",
      "created_at": "2025-10-15 23:56:44 UTC"
    },
    {
      "id": 3,
      "message": "Info: backup completed",
      "created_at": "2025-10-16 23:56:44 UTC"
    }
  ]
}
```
`Result: True`

---

Array sugar with negated pattern matching

```
all of documents matches |filename not like '*.tmp'| and at least 3 of documents matches |filename like '*.pdf'|
```
```json
{
  "documents": [
    {
      "filename": "report.pdf",
      "size": 1024
    },
    {
      "filename": "manual.pdf",
      "size": 2048
    },
    {
      "filename": "guide.pdf",
      "size": 1536
    },
    {
      "filename": "notes.txt",
      "size": 256
    },
    {
      "filename": "data.csv",
      "size": 512
    }
  ]
}
```
`Result: True`

---

Array sugar with literal date strings

```
exactly 2 of milestones matches |target_date before '2025-01-01'| and none of milestones matches |target_date before '2024-01-01'|
```
```json
{
  "milestones": [
    {
      "name": "Beta Release",
      "target_date": "2024-11-15"
    },
    {
      "name": "GA Release",
      "target_date": "2025-02-01"
    },
    {
      "name": "Feature Freeze",
      "target_date": "2024-12-01"
    }
  ]
}
```
`Result: True`

---

Complex nested conditions combining multiple features

```
at least 2 of orders matches | customer's profile.tier == 'Premium' and total > 100 and created_date is $past |
```
```json
{
  "orders": [
    {
      "id": "ORD001",
      "total": 150,
      "created_date": "2025-10-14 23:56:44 UTC",
      "customer": {
        "name": "Alice",
        "profile": {
          "tier": "Premium"
        }
      }
    },
    {
      "id": "ORD002",
      "total": 250,
      "created_date": "2025-10-14 23:56:44 UTC",
      "customer": {
        "name": "Bob",
        "profile": {
          "tier": "Premium"
        }
      }
    },
    {
      "id": "ORD003",
      "total": 50,
      "created_date": "2025-10-14 23:56:44 UTC",
      "customer": {
        "name": "Charlie",
        "profile": {
          "tier": "Basic"
        }
      }
    }
  ]
}
```
`Result: True`

---

Mix string equality and pattern matching in array sugar

```
any of files matches |type == 'document' and name like '*.pdf'| and none of files matches |type == 'image' and name like '*.pdf'|
```
```json
{
  "files": [
    {
      "name": "report.pdf",
      "type": "document"
    },
    {
      "name": "photo.jpg",
      "type": "image"
    },
    {
      "name": "manual.pdf",
      "type": "document"
    },
    {
      "name": "chart.png",
      "type": "image"
    }
  ]
}
```
`Result: True`

---

Combine date ranges with string operations

```
all of events matches |start_date before end_date| and exactly 1 of events matches |title like '*Workshop*'|
```
```json
{
  "events": [
    {
      "title": "Team Workshop",
      "start_date": "2024-10-10",
      "end_date": "2024-10-11"
    },
    {
      "title": "Product Launch",
      "start_date": "2024-11-01",
      "end_date": "2024-11-02"
    },
    {
      "title": "Training Session",
      "start_date": "2024-12-01",
      "end_date": "2024-12-03"
    }
  ]
}
```
`Result: True`

---

Combine upcoming within time windows with string matching

```
at most 1 of tasks matches | deadline upcoming within 7 days and priority == 'high' |
```
```json
{
  "tasks": [
    {
      "title": "Fix critical bug",
      "deadline": "2025-10-15 22:56:44 UTC",
      "priority": "high"
    },
    {
      "title": "Update documentation",
      "deadline": "2025-10-16 23:56:44 UTC",
      "priority": "medium"
    },
    {
      "title": "Review code",
      "deadline": "2025-10-08 23:56:44 UTC",
      "priority": "low"
    }
  ]
}
```
`Result: True`

---

Combine arithmetic operations with date comparisons in array sugar

```
exactly 2 of products matches | price > 100 and launch_date is $past |
```
```json
{
  "products": [
    {
      "name": "Premium Widget",
      "price": 150,
      "launch_date": "2025-10-14 23:56:44 UTC"
    },
    {
      "name": "Basic Widget",
      "price": 50,
      "launch_date": "2025-10-14 23:56:44 UTC"
    },
    {
      "name": "Pro Widget",
      "price": 200,
      "launch_date": "2025-10-08 23:56:44 UTC"
    },
    {
      "name": "Future Widget",
      "price": 300,
      "launch_date": "2025-10-16 23:56:44 UTC"
    }
  ]
}
```
`Result: True`

---

Multiple different time comparison types in one expression

```
any of events matches |start_time is $today| and all of events matches |end_time after start_time| and none of events matches |duration older than 1 year|
```
```json
{
  "events": [
    {
      "name": "Daily Standup",
      "start_time": "2025-10-15 23:56:44 UTC",
      "end_time": "2025-10-16 23:56:44 UTC",
      "duration": "2025-09-01"
    },
    {
      "name": "Weekly Review",
      "start_time": "2025-10-14 23:56:44 UTC",
      "end_time": "2025-10-16 23:56:44 UTC",
      "duration": "2025-08-01"
    }
  ]
}
```
`Result: True`

---

Case insensitive pattern matching in array sugar

```
at least 2 of files matches |extension like '*.PDF'| and exactly 1 of files matches |name like '*REPORT*'|
```
```json
{
  "files": [
    {
      "name": "annual_report.pdf",
      "extension": ".pdf"
    },
    {
      "name": "monthly_summary.pdf",
      "extension": ".pdf"
    },
    {
      "name": "notes.txt",
      "extension": ".txt"
    },
    {
      "name": "data.csv",
      "extension": ".csv"
    }
  ]
}
```
`Result: True`

---

Complex boolean combinations with array sugar and basic operations

```
(at least 1 of users matches |status == 'active'|) and (none of users matches |last_login older than 30 days|) or (all of users matches |role != 'admin'|)
```
```json
{
  "users": [
    {
      "name": "Alice",
      "status": "active",
      "last_login": "2025-10-14 23:56:44 UTC",
      "role": "user"
    },
    {
      "name": "Bob",
      "status": "inactive",
      "last_login": "2025-10-15 22:56:44 UTC",
      "role": "user"
    },
    {
      "name": "Charlie",
      "status": "active",
      "last_login": "2025-10-15 23:56:44 UTC",
      "role": "moderator"
    }
  ]
}
```
`Result: True`

---


### Property Existence
Check if an object has a specific property using string literal

```
user has 'email'
```
```json
{
  "user": {
    "name": "Alice Smith",
    "email": "alice@example.com",
    "age": 28
  }
}
```
`Result: True`

---

Check for a property that doesn&#x27;t exist

```
user has 'phone'
```
```json
{
  "user": {
    "name": "Bob Jones",
    "email": "bob@example.com"
  }
}
```
`Result: False`

---

Use a variable to specify the property name to check

```
config has required_field
```
```json
{
  "config": {
    "database_url": "postgresql://localhost/myapp",
    "debug_mode": true,
    "secret_key": "my-secret-key"
  },
  "required_field": "database_url"
}
```
`Result: True`

---

Check if a nested object has a property

```
user.profile has 'bio'
```
```json
{
  "user": {
    "name": "Charlie Brown",
    "profile": {
      "bio": "Software developer and coffee enthusiast",
      "location": "San Francisco",
      "website": "https://charlie.dev"
    }
  }
}
```
`Result: True`

---

Check properties in deeply nested structures

```
app.settings.security has 'encryption'
```
```json
{
  "app": {
    "name": "MyApp",
    "settings": {
      "ui": {
        "theme": "dark",
        "language": "en"
      },
      "security": {
        "encryption": "AES-256",
        "two_factor": true
      }
    }
  }
}
```
`Result: True`

---

Check if a list contains an item using &#x27;has&#x27; (similar to &#x27;contains&#x27;)

```
user.roles has 'admin'
```
```json
{
  "user": {
    "username": "adminuser",
    "roles": [
      "user",
      "admin",
      "moderator"
    ]
  }
}
```
`Result: True`

---

Combine &#x27;has&#x27; with logical operators for complex conditions

```
user has 'email' and user has 'verified' and user.verified
```
```json
{
  "user": {
    "name": "Diana Prince",
    "email": "diana@example.com",
    "verified": true,
    "created_at": "2024-01-15"
  }
}
```
`Result: True`

---

Check multiple properties with OR logic

```
contact has 'email' or contact has 'phone'
```
```json
{
  "contact": {
    "name": "Emergency Contact",
    "phone": "+1-555-0123"
  }
}
```
`Result: True`

---

Combine property existence check with value comparison

```
user has 'role' and user.role == 'admin'
```
```json
{
  "user": {
    "username": "superuser",
    "role": "admin",
    "permissions": [
      "read",
      "write",
      "delete"
    ]
  }
}
```
`Result: True`

---

Check for missing property in nested structure

```
product.details has 'warranty'
```
```json
{
  "product": {
    "name": "Laptop",
    "price": 999.99,
    "details": {
      "brand": "TechCorp",
      "model": "Pro 2024",
      "color": "silver"
    }
  }
}
```
`Result: False`

---

Check properties in empty objects

```
empty_config has 'setting'
```
```json
{
  "empty_config": {},
  "non_empty": {
    "setting": "value"
  }
}
```
`Result: False`

---


### Syntax Comparison
Demonstrate improved readability compared to &#x27;in&#x27; operator

```
customer.preferences has 'newsletter' and customer.account has 'premium'
```
```json
{
  "customer": {
    "name": "Jane Customer",
    "preferences": {
      "newsletter": true,
      "marketing": false
    },
    "account": {
      "premium": true,
      "credits": 150
    }
  }
}
```
`Result: True`

---


### Real World Usage
Real-world example: validate required fields in user registration

```
registration has 'username' and registration has 'email' and registration has 'password'
```
```json
{
  "registration": {
    "username": "newuser123",
    "email": "newuser@example.com",
    "password": "secure-password",
    "terms_accepted": true
  }
}
```
`Result: True`

---

Check if specific feature flags exist in configuration

```
features has 'dark_mode' and features has 'notifications'
```
```json
{
  "features": {
    "dark_mode": true,
    "notifications": false,
    "beta_features": true
  }
}
```
`Result: True`

---

Validate API response structure

```
response has 'data' and response has 'status' and response.status == 'success'
```
```json
{
  "response": {
    "status": "success",
    "data": {
      "users": [
        {
          "id": 1,
          "name": "Alice"
        },
        {
          "id": 2,
          "name": "Bob"
        }
      ]
    },
    "meta": {
      "total": 2,
      "page": 1
    }
  }
}
```
`Result: True`

---


### Maths
Multiply two integers

```
8 * 8
```
`Result: 64`

---

Divide two integers

```
64 / 8
```
`Result: 8`

---

Add two integers

```
8 + 8
```
`Result: 16`

---

Subtract two integers

```
8 - 8
```
`Result: 0`

---

Multiply two floating point numbers

```
0.5 * 8.0
```
`Result: 4.0`

---

Use variables in expressions

```
banana.price * order.quantity
```
```json
{
  "banana": {
    "price": 2
  },
  "order": {
    "quantity": 8
  }
}
```
`Result: 16`

---


### Date State
Verify a date in the past

```
past_date is $past
```
```json
{
  "past_date": "2025-10-14 23:56:44 UTC"
}
```
`Result: True`

---

Verify a date in the future

```
future_date is $future
```
```json
{
  "future_date": "2025-10-16 23:56:44 UTC"
}
```
`Result: True`

---

Verify a date is $today

```
today_date is $today
```
```json
{
  "today_date": "2025-10-15 23:56:44 UTC"
}
```
`Result: True`

---


### Time Window
Check event upcoming within recent hours

```
recent_event upcoming within 12 hours
```
```json
{
  "recent_event": "2025-10-15 22:56:44 UTC"
}
```
`Result: True`

---

Check event older than a week

```
old_event older than 1 week
```
```json
{
  "old_event": "2025-10-08 23:56:44 UTC"
}
```
`Result: True`

---


### Date Comparison
Compare two dates with before

```
start_date before end_date
```
```json
{
  "start_date": "2025-10-14 23:56:44 UTC",
  "end_date": "2025-10-16 23:56:44 UTC"
}
```
`Result: True`

---

Compare two dates with after

```
end_date after start_date
```
```json
{
  "start_date": "2025-10-14 23:56:44 UTC",
  "end_date": "2025-10-16 23:56:44 UTC"
}
```
`Result: True`

---

Check same day (should be true)

```
same_day_morning same_day_as same_day_evening
```
```json
{
  "same_day_morning": "2023-05-10T08:00:00Z",
  "same_day_evening": "2023-05-10T20:00:00Z"
}
```
`Result: True`

---

Check same day (should be false)

```
different_days same_day_as other_day
```
```json
{
  "different_days": "2023-05-10T08:00:00Z",
  "other_day": "2023-05-11T08:00:00Z"
}
```
`Result: False`

---


### Complex
Check if project is currently active

```
project_start is $past and project_end is $future
```
```json
{
  "project_start": "2025-10-14 23:56:44 UTC",
  "project_end": "2025-10-16 23:56:44 UTC"
}
```
`Result: True`

---

Recent login but account not new

```
last_login upcoming within 4 hours and signup_date older than 1 day
```
```json
{
  "last_login": "2025-10-15 22:56:44 UTC",
  "signup_date": "2025-10-14 23:56:44 UTC"
}
```
`Result: True`

---


### String Dates
Compare ISO formatted date string

```
iso_date before '2030-01-01'
```
```json
{
  "iso_date": "2023-05-10T00:00:00Z"
}
```
`Result: True`

---

Check literal date is $past

```
'2020-01-01' is $past
```
`Result: True`

---

Check literal date older than period

```
'2020-01-01' older than 1 year
```
`Result: True`

---


### Time Units
Use hours time unit

```
hour_ago upcoming within 2 hours
```
```json
{
  "hour_ago": "2025-10-15 22:56:44 UTC"
}
```
`Result: True`

---

Use minutes time unit

```
hour_ago upcoming within 120 minutes
```
```json
{
  "hour_ago": "2025-10-15 22:56:44 UTC"
}
```
`Result: True`

---

Use days time unit

```
week_ago older than 6 days
```
```json
{
  "week_ago": "2025-10-08 23:56:44 UTC"
}
```
`Result: True`

---


### List Operations
Check if an element exists in a list using &#x27;in&#x27;

```
'admin' in user.roles
```
```json
{
  "user": {
    "roles": [
      "user",
      "admin",
      "editor"
    ],
    "name": "John Doe"
  }
}
```
`Result: True`

---

Use a variable as the item to check in a list

```
requested_role in available_roles
```
```json
{
  "requested_role": "manager",
  "available_roles": [
    "user",
    "admin",
    "manager",
    "guest"
  ]
}
```
`Result: True`

---

Alternative contains syntax for list membership

```
permissions contains 'delete'
```
```json
{
  "permissions": [
    "read",
    "write",
    "delete",
    "share"
  ]
}
```
`Result: True`

---

Check behavior when element is not in list

```
'superadmin' in user.roles
```
```json
{
  "user": {
    "roles": [
      "user",
      "admin",
      "editor"
    ]
  }
}
```
`Result: False`

---


### Object Operations
Check if a key exists in a dictionary

```
'address' in user.profile
```
```json
{
  "user": {
    "profile": {
      "name": "Jane Smith",
      "email": "jane@example.com",
      "address": "123 Main St",
      "phone": "555-1234"
    }
  }
}
```
`Result: True`

---

Use a variable to check dictionary key membership

```
required_field in form_data
```
```json
{
  "required_field": "tax_id",
  "form_data": {
    "name": "Company Inc",
    "email": "info@company.com",
    "address": "456 Business Ave"
  }
}
```
`Result: False`

---

Use contains operator with dictionary

```
config contains 'debug_mode'
```
```json
{
  "config": {
    "app_name": "MyApp",
    "version": "1.2.3",
    "debug_mode": true,
    "theme": "dark"
  }
}
```
`Result: True`

---


### Mixed Collections
Check membership in a list nested upcoming within a dictionary

```
'python' in user.skills.programming
```
```json
{
  "user": {
    "name": "Alex Developer",
    "skills": {
      "programming": [
        "javascript",
        "python",
        "go"
      ],
      "languages": [
        "english",
        "spanish"
      ]
    }
  }
}
```
`Result: True`

---

Combine collection operators with other logical operators

```
'admin' in user.roles and user.settings contains 'notifications' and user.settings.notifications
```
```json
{
  "user": {
    "roles": [
      "user",
      "admin"
    ],
    "settings": {
      "theme": "light",
      "notifications": true,
      "privacy": "high"
    }
  }
}
```
`Result: True`

---


### Collection Equality
Compare two lists for equality

```
user.permissions == required_permissions
```
```json
{
  "user": {
    "permissions": [
      "read",
      "write",
      "delete"
    ]
  },
  "required_permissions": [
    "read",
    "write",
    "delete"
  ]
}
```
`Result: True`

---

Compare two dictionaries for equality

```
user.preferences == default_preferences
```
```json
{
  "user": {
    "preferences": {
      "theme": "dark",
      "font_size": "medium"
    }
  },
  "default_preferences": {
    "theme": "light",
    "font_size": "medium"
  }
}
```
`Result: False`

---


### Complex Scenarios
Use membership test with a composite condition

```
(user.role in admin_roles) or (user.domain in approved_domains and user.verified)
```
```json
{
  "user": {
    "role": "manager",
    "email": "user@company.com",
    "domain": "company.com",
    "verified": true
  },
  "admin_roles": [
    "admin",
    "superadmin"
  ],
  "approved_domains": [
    "company.com",
    "partner.org"
  ]
}
```
`Result: True`

---


### Path Syntax
Look up elements in arrays using indexing

```
teams[0].name == 'Frontend'
```
```json
{
  "teams": [
    {
      "name": "Frontend",
      "members": [
        "Alice",
        "Bob"
      ]
    },
    {
      "name": "Backend",
      "members": [
        "Charlie",
        "Dave"
      ]
    }
  ]
}
```
`Result: True`

---

Use nested array indexing in paths

```
departments[0].teams[1].name == 'Backend'
```
```json
{
  "departments": [
    {
      "name": "Engineering",
      "teams": [
        {
          "name": "Frontend",
          "members": [
            "Alice",
            "Bob"
          ]
        },
        {
          "name": "Backend",
          "members": [
            "Charlie",
            "Dave"
          ]
        }
      ]
    },
    {
      "name": "Marketing",
      "teams": [
        {
          "name": "Digital",
          "members": [
            "Eve",
            "Frank"
          ]
        }
      ]
    }
  ]
}
```
`Result: True`

---

Test property of an element accessed through indexing

```
users[1].role == 'admin' and users[1].verified
```
```json
{
  "users": [
    {
      "username": "johndoe",
      "role": "user",
      "verified": false
    },
    {
      "username": "janedoe",
      "role": "admin",
      "verified": true
    }
  ]
}
```
`Result: True`

---

Combine array indexing with membership test

```
'testing' in projects[0].tags and projects[1].status == 'completed'
```
```json
{
  "projects": [
    {
      "name": "Feature A",
      "tags": [
        "important",
        "testing",
        "frontend"
      ],
      "status": "in_progress"
    },
    {
      "name": "Feature B",
      "tags": [
        "backend",
        "documentation"
      ],
      "status": "completed"
    }
  ]
}
```
`Result: True`

---


### Complex Path Operations
Complex expression combining array lookups with object properties

```
organization.departments[0].teams[0].members[1] == 'Bob' and organization.departments[1].teams[0].members[0] == 'Eve'
```
```json
{
  "organization": {
    "name": "Acme Corp",
    "departments": [
      {
        "name": "Engineering",
        "teams": [
          {
            "name": "Frontend",
            "members": [
              "Alice",
              "Bob"
            ]
          },
          {
            "name": "Backend",
            "members": [
              "Charlie",
              "Dave"
            ]
          }
        ]
      },
      {
        "name": "Marketing",
        "teams": [
          {
            "name": "Digital",
            "members": [
              "Eve",
              "Frank"
            ]
          }
        ]
      }
    ]
  }
}
```
`Result: True`

---


### Container Operations
Check if containers are empty using &#x27;is $empty&#x27;

```
ghost_crew is $empty and deserted_mansion is $empty and (treasure_chest is $empty) == false
```
```json
{
  "ghost_crew": [],
  "treasure_chest": [
    "ancient coin",
    "golden chalice",
    "ruby necklace"
  ],
  "deserted_mansion": {},
  "dragon_hoard": {
    "golden_crown": 1500,
    "enchanted_sword": 3000,
    "crystal_orb": 750
  }
}
```
`Result: True`

---


### Nested Objects
Check if user is eligible for premium features

```
user.account.is_active and (user.subscription.level == 'premium' or user.account.credits > 100)
```
```json
{
  "user": {
    "account": {
      "is_active": true,
      "credits": 150,
      "created_at": "2025-10-08 23:56:44 UTC"
    },
    "subscription": {
      "level": "basic",
      "renewal_date": "2025-11-14 23:56:44 UTC"
    }
  }
}
```
`Result: True`

---

Evaluate complex project status conditions

```
project.status == 'in_progress'
and (
  project.metrics.completion > 50
  or (project.team.size >= 3 and project.priority == 'high')
)

```
```json
{
  "project": {
    "status": "in_progress",
    "start_date": "2025-10-08 23:56:44 UTC",
    "deadline": "2025-11-14 23:56:44 UTC",
    "metrics": {
      "completion": 45,
      "quality": 98
    },
    "team": {
      "size": 5,
      "lead": "Alice"
    },
    "priority": "high"
  }
}
```
`Result: True`

---


### Mixed Date Logic
Check if order is eligible for express shipping

```
order.status == 'confirmed'
and order.created_at upcoming within 24 hours
and (
  order.items.count < 5
  or (order.customer.tier == 'gold' and order.total_value > 100)
)

```
```json
{
  "order": {
    "status": "confirmed",
    "created_at": "2025-10-15 22:56:44 UTC",
    "items": {
      "count": 7,
      "categories": [
        "electronics",
        "books"
      ]
    },
    "customer": {
      "tier": "gold",
      "since": "2025-10-08 23:56:44 UTC"
    },
    "total_value": 250
  }
}
```
`Result: True`

---

Multiple date conditions with nested properties

```
(user.last_login upcoming within 7 days or user.auto_login)
and (
  user.account.trial_ends is $future
  or
  user.account.subscription.status == 'active'
)

```
```json
{
  "user": {
    "last_login": "2025-10-08 23:56:44 UTC",
    "auto_login": true,
    "registration_date": "2023-01-15",
    "account": {
      "trial_ends": "2025-10-14 23:56:44 UTC",
      "subscription": {
        "status": "active",
        "plan": "premium",
        "next_payment": "2025-11-14 23:56:44 UTC"
      }
    }
  }
}
```
`Result: True`

---


### Complex Precedence
Test operator precedence with mixed conditions

```
user.settings.notifications.enabled
and (user.last_seen older than 1 day or user.preferences.urgent_only)
and ('admin' in user.roles or user.tasks.pending > 0)

```
```json
{
  "user": {
    "settings": {
      "notifications": {
        "enabled": true,
        "channels": [
          "email",
          "push"
        ]
      },
      "theme": "dark"
    },
    "last_seen": "2025-10-08 23:56:44 UTC",
    "preferences": {
      "urgent_only": false,
      "language": "en"
    },
    "roles": "user, admin",
    "tasks": {
      "pending": 3,
      "completed": 27
    }
  }
}
```
`Result: True`

---


### Jq Basics
Basic JQ expression to access a nested property

```
`.user.profile.name` == 'Alice'
```
```json
{
  "user": {
    "profile": {
      "name": "Alice",
      "age": 32
    },
    "settings": {
      "notifications": true
    }
  }
}
```
`Result: True`

---


### Jq Arrays
Access elements in an array using JQ indexing

```
`.team[1].role` == 'developer'
```
```json
{
  "team": [
    {
      "name": "Bob",
      "role": "manager"
    },
    {
      "name": "Charlie",
      "role": "developer"
    },
    {
      "name": "Diana",
      "role": "designer"
    }
  ]
}
```
`Result: True`

---

Check array length using JQ pipe function

```
`.products | length` > 2
```
```json
{
  "products": [
    {
      "id": 101,
      "name": "Laptop"
    },
    {
      "id": 102,
      "name": "Phone"
    },
    {
      "id": 103,
      "name": "Tablet"
    }
  ]
}
```
`Result: True`

---

Check if any array element matches a condition

```
`.users[] | select(.role == "admin") | .name` == 'Eva'
```
```json
{
  "users": [
    {
      "name": "Dave",
      "role": "user"
    },
    {
      "name": "Eva",
      "role": "admin"
    },
    {
      "name": "Frank",
      "role": "user"
    }
  ]
}
```
`Result: True`

---


### Jq Filtering
Filter array elements based on a condition

```
`.orders[] | select(.status == "completed") | .id` == 1003
```
```json
{
  "orders": [
    {
      "id": 1001,
      "status": "pending"
    },
    {
      "id": 1002,
      "status": "processing"
    },
    {
      "id": 1003,
      "status": "completed"
    }
  ]
}
```
`Result: True`

---


### Jq Mixed
Combine JQ with regular Dilemma expressions

```
`.user.membership.level` == 'gold' and user.account.active == true
```
```json
{
  "user": {
    "membership": {
      "level": "gold",
      "since": "2025-10-08 23:56:44 UTC"
    },
    "account": {
      "active": true,
      "credits": 500
    }
  }
}
```
`Result: True`

---


### Jq Advanced
Complex data transformation with JQ

```
`.departments[] | select(.name == "Engineering").employees | map(.salary) | add / length` > 75000
```
```json
{
  "departments": [
    {
      "name": "Marketing",
      "employees": [
        {
          "name": "Grace",
          "salary": 65000
        },
        {
          "name": "Henry",
          "salary": 68000
        }
      ]
    },
    {
      "name": "Engineering",
      "employees": [
        {
          "name": "Isla",
          "salary": 78000
        },
        {
          "name": "Jack",
          "salary": 82000
        },
        {
          "name": "Kate",
          "salary": 80000
        }
      ]
    }
  ]
}
```
`Result: True`

---

Check if an array contains a specific value

```
`.user.permissions | contains(["edit"])`
```
```json
{
  "user": {
    "id": 1234,
    "name": "Lucy",
    "permissions": [
      "read",
      "edit",
      "share"
    ]
  }
}
```
`Result: True`

---

Use JQ to conditionally create and check an object

```
`if .user.premium then {access: "full"} else {access: "limited"} end | .access` == 'full'
```
```json
{
  "user": {
    "premium": true,
    "account_type": "business"
  }
}
```
`Result: True`

---

Complex JQ expression with deeply nested parentheses and operations

```
`.employees | map( ((.performance.rating * 0.5) + ((.projects | map(select(.status == "completed") | .difficulty) | add // 0) * 0.3) + (if (.years_experience > 5) then ((.leadership_score // 0) * 0.2) else ((.learning_speed // 0) * 0.2) end) ) * (if .department == "Engineering" then 1.1 else 1 end) ) | add / length` > 75
```
```json
{
  "employees": [
    {
      "name": "Alice",
      "department": "Engineering",
      "performance": {
        "rating": 98
      },
      "projects": [
        {
          "name": "Project A",
          "status": "completed",
          "difficulty": 9
        },
        {
          "name": "Project B",
          "status": "completed",
          "difficulty": 10
        }
      ],
      "years_experience": 7,
      "leadership_score": 95
    },
    {
      "name": "Bob",
      "department": "Engineering",
      "performance": {
        "rating": 95
      },
      "projects": [
        {
          "name": "Project C",
          "status": "completed",
          "difficulty": 8
        },
        {
          "name": "Project D",
          "status": "in_progress",
          "difficulty": 10
        }
      ],
      "years_experience": 4,
      "learning_speed": 98
    },
    {
      "name": "Charlie",
      "department": "Marketing",
      "performance": {
        "rating": 98
      },
      "projects": [
        {
          "name": "Project E",
          "status": "completed",
          "difficulty": 10
        },
        {
          "name": "Project F",
          "status": "completed",
          "difficulty": 8
        }
      ],
      "years_experience": 6,
      "leadership_score": 90
    }
  ]
}
```
`Result: True`

---


### Jq With Dates
Use JQ to extract a date for comparison

```
`.project.milestones[] | select(.name == "beta").date` is $past
```
```json
{
  "project": {
    "name": "Product Launch",
    "milestones": [
      {
        "name": "alpha",
        "date": "2025-11-14 23:56:44 UTC"
      },
      {
        "name": "beta",
        "date": "2025-10-14 23:56:44 UTC"
      },
      {
        "name": "release",
        "date": "2025-10-16 01:56:44 UTC"
      }
    ]
  }
}
```
`Result: True`

---


### Jq Parsing
Simple JQ expression nested inside multiple levels of Dilemma parentheses

```
(5 + ((`.users | length` * 2) - 1)) > 5
```
```json
{
  "users": [
    {
      "id": 1,
      "name": "Alice"
    },
    {
      "id": 2,
      "name": "Bob"
    },
    {
      "id": 3,
      "name": "Charlie"
    }
  ]
}
```
`Result: True`

---


### Errors
Test division by zero error

```
12 / 0
```
**Expected Error:**
```
It is not possible to divide by zero (12 / 0 ).
You can guard against this error by checking that
the value of the right-hand side is not zero.
```

---

Error message for an unknown variable name

```
bob
```
**Expected Error:**
```
The word &#x27;bob&#x27; is not recognised.
Unquoted words should refer names of data items in the context.
Possibly a spelling mistake?
If you intended this word to be used for a comparison put it in quotation marks.
```

---

Error message for an unknown variable path

```
bob's age
```
**Expected Error:**
```
Lookup for a value matching &#x27;bob&#x27;s age&#x27; failed.
The first part of this phrase is expected to be the name of an item in the context,
subsequent parts are the names of nested items
Possibly a spelling mistake? Please check the context.
If you intended this word to be used for a comparison put it in quotation marks.
```

---


### Function Operations
Count members in a list that match a condition

```
count_of(roles, `'write' in permissions`) == 3
```
```json
{
  "roles": [
    {
      "name": "user",
      "permissions": [
        "read",
        "write"
      ]
    },
    {
      "name": "admin",
      "permissions": [
        "read",
        "write",
        "delete"
      ]
    },
    {
      "name": "manager",
      "permissions": [
        "read",
        "write",
        "approve"
      ]
    },
    {
      "name": "guest",
      "permissions": [
        "read"
      ]
    }
  ]
}
```
`Result: True`

---

Count all members in a list (no condition)

```
count_of(roles) == 4
```
```json
{
  "roles": [
    {
      "name": "user",
      "permissions": [
        "read",
        "write"
      ]
    },
    {
      "name": "admin",
      "permissions": [
        "read",
        "write",
        "delete"
      ]
    },
    {
      "name": "manager",
      "permissions": [
        "read",
        "write",
        "approve"
      ]
    },
    {
      "name": "guest",
      "permissions": [
        "read"
      ]
    }
  ]
}
```
`Result: True`

---

Count items that match a numeric condition

```
count_of(scores, `score > 80`) == 2
```
```json
{
  "scores": [
    {
      "name": "Alice",
      "score": 95
    },
    {
      "name": "Bob",
      "score": 72
    },
    {
      "name": "Charlie",
      "score": 88
    },
    {
      "name": "David",
      "score": 65
    }
  ]
}
```
`Result: True`

---

Check if any item matches a condition

```
any_of(users, `age >= 18`)
```
```json
{
  "users": [
    {
      "name": "Alice",
      "age": 25
    },
    {
      "name": "Bob",
      "age": 16
    },
    {
      "name": "Charlie",
      "age": 30
    }
  ]
}
```
`Result: True`

---

Check if any item is truthy

```
any_of(flags)
```
```json
{
  "flags": [
    false,
    true,
    false
  ]
}
```
`Result: True`

---

Check if any item matches condition (false case)

```
any_of(users, `age > 100`)
```
```json
{
  "users": [
    {
      "name": "Alice",
      "age": 25
    },
    {
      "name": "Bob",
      "age": 16
    }
  ]
}
```
`Result: False`

---

Check if all items match a condition (true case)

```
all_of(products, `price > 0`)
```
```json
{
  "products": [
    {
      "name": "Widget A",
      "price": 10.5
    },
    {
      "name": "Widget B",
      "price": 25.0
    },
    {
      "name": "Widget C",
      "price": 5.99
    }
  ]
}
```
`Result: True`

---

Check if all items match a condition (false case)

```
all_of(products, `price > 20`)
```
```json
{
  "products": [
    {
      "name": "Widget A",
      "price": 10.5
    },
    {
      "name": "Widget B",
      "price": 25.0
    },
    {
      "name": "Widget C",
      "price": 5.99
    }
  ]
}
```
`Result: False`

---

Check if all items are truthy

```
all_of(flags)
```
```json
{
  "flags": [
    true,
    false,
    true
  ]
}
```
`Result: False`

---

Check if no items match a condition (true case)

```
none_of(users, `age > 100`)
```
```json
{
  "users": [
    {
      "name": "Alice",
      "age": 25
    },
    {
      "name": "Bob",
      "age": 16
    }
  ]
}
```
`Result: True`

---

Check if no items match a condition (false case)

```
none_of(users, `age >= 18`)
```
```json
{
  "users": [
    {
      "name": "Alice",
      "age": 25
    },
    {
      "name": "Bob",
      "age": 16
    }
  ]
}
```
`Result: False`

---

Check if no items are truthy

```
none_of(flags)
```
```json
{
  "flags": [
    false,
    false,
    false
  ]
}
```
`Result: True`

---

Count items matching a string condition

```
count_of(employees, `department == 'Engineering'`) == 2
```
```json
{
  "employees": [
    {
      "name": "Alice",
      "department": "Engineering"
    },
    {
      "name": "Bob",
      "department": "Marketing"
    },
    {
      "name": "Charlie",
      "department": "Engineering"
    },
    {
      "name": "David",
      "department": "Sales"
    }
  ]
}
```
`Result: True`

---

Check if any employee has &#x27;manager&#x27; in their title

```
any_of(employees, `'Manager' in title`)
```
```json
{
  "employees": [
    {
      "name": "Alice",
      "title": "Senior Engineer"
    },
    {
      "name": "Bob",
      "title": "Project Manager"
    },
    {
      "name": "Charlie",
      "title": "Developer"
    }
  ]
}
```
`Result: True`

---

Test functions with empty list

```
count_of(empty_list) == 0 and any_of(empty_list) == false and all_of(empty_list) == true and none_of(empty_list) == true
```
```json
{
  "empty_list": []
}
```
`Result: True`

---


### Array Sugar
Test &#x27;at least N of X has predicate&#x27; natural language sugar

```
at least 2 of users matches | age >= 25 |
```
```json
{
  "users": [
    {
      "name": "Alice",
      "age": 25
    },
    {
      "name": "Bob",
      "age": 30
    },
    {
      "name": "Charlie",
      "age": 20
    }
  ]
}
```
`Result: True`

---

Test &#x27;at most N of X has predicate&#x27; natural language sugar

```
at most 1 of products matches | price > 100 |
```
```json
{
  "products": [
    {
      "name": "Widget A",
      "price": 50
    },
    {
      "name": "Widget B",
      "price": 150
    },
    {
      "name": "Widget C",
      "price": 75
    }
  ]
}
```
`Result: True`

---

Test &#x27;exactly N of X has predicate&#x27; natural language sugar

```
exactly 2 of employees matches | department == 'Engineering' |
```
```json
{
  "employees": [
    {
      "name": "Alice",
      "department": "Engineering"
    },
    {
      "name": "Bob",
      "department": "Marketing"
    },
    {
      "name": "Charlie",
      "department": "Engineering"
    }
  ]
}
```
`Result: True`

---

Test &#x27;any of X has predicate&#x27; natural language sugar

```
any of tasks matches | status == 'urgent' |
```
```json
{
  "tasks": [
    {
      "id": 1,
      "status": "normal"
    },
    {
      "id": 2,
      "status": "urgent"
    },
    {
      "id": 3,
      "status": "low"
    }
  ]
}
```
`Result: True`

---

Test &#x27;all of X has predicate&#x27; natural language sugar

```
all of orders matches | paid == true |
```
```json
{
  "orders": [
    {
      "id": 1,
      "paid": true
    },
    {
      "id": 2,
      "paid": false
    },
    {
      "id": 3,
      "paid": true
    }
  ]
}
```
`Result: False`

---

Test &#x27;none of X has predicate&#x27; natural language sugar

```
none of items matches | defective == true |
```
```json
{
  "items": [
    {
      "id": 1,
      "defective": false
    },
    {
      "id": 2,
      "defective": false
    },
    {
      "id": 3,
      "defective": false
    }
  ]
}
```
`Result: True`

---

Test sugar with complex boolean predicates

```
at least 1 of users matches | age > 21 and active == true |
```
```json
{
  "users": [
    {
      "name": "Alice",
      "age": 25,
      "active": true
    },
    {
      "name": "Bob",
      "age": 18,
      "active": true
    },
    {
      "name": "Charlie",
      "age": 30,
      "active": false
    }
  ]
}
```
`Result: True`

---

Test sugar combined with logical operators

```
exactly 2 of team matches |role == 'developer'| and any of team matches |role == 'lead'|
```
```json
{
  "team": [
    {
      "name": "Alice",
      "role": "lead"
    },
    {
      "name": "Bob",
      "role": "developer"
    },
    {
      "name": "Charlie",
      "role": "developer"
    },
    {
      "name": "David",
      "role": "designer"
    }
  ]
}
```
`Result: True`

---

Test sugar with string pattern matching

```
at least 2 of files matches | name like '*.txt' |
```
```json
{
  "files": [
    {
      "name": "document.txt",
      "size": 1024
    },
    {
      "name": "readme.txt",
      "size": 512
    },
    {
      "name": "image.jpg",
      "size": 2048
    }
  ]
}
```
`Result: True`

---

Test sugar with nested object property access

```
exactly 1 of projects matches | team.size > 5 |
```
```json
{
  "projects": [
    {
      "name": "Project A",
      "team": {
        "size": 3,
        "lead": "Alice"
      }
    },
    {
      "name": "Project B",
      "team": {
        "size": 7,
        "lead": "Bob"
      }
    },
    {
      "name": "Project C",
      "team": {
        "size": 4,
        "lead": "Charlie"
      }
    }
  ]
}
```
`Result: True`

---

Test sugar expressions that should count zero

```
exactly 0 of users matches |age > 100| and none of users matches |name == 'Nobody'|
```
```json
{
  "users": [
    {
      "name": "Alice",
      "age": 25
    },
    {
      "name": "Bob",
      "age": 30
    }
  ]
}
```
`Result: True`

---

Test sugar with empty collections

```
exactly 0 of empty_list matches |value > 0| and all of empty_list matches |value < 1000|
```
```json
{
  "empty_list": []
}
```
`Result: True`

---

Test using sugar result in comparisons

```
exactly 3 of scores matches | points > 80 | == true
```
```json
{
  "scores": [
    {
      "player": "Alice",
      "points": 95
    },
    {
      "player": "Bob",
      "points": 72
    },
    {
      "player": "Charlie",
      "points": 88
    },
    {
      "player": "David",
      "points": 91
    }
  ]
}
```
`Result: True`

---

Test sugar in arithmetic context (boolean to number conversion)

```
at least 1 of items matches | value > 5 | + 2
```
```json
{
  "items": [
    {
      "value": 10
    },
    {
      "value": 2
    },
    {
      "value": 8
    }
  ]
}
```
`Result: 3`

---

Test multiple sugar conditions in one expression

```
at least 2 of users matches |active == true| and at most 1 of users matches |role == 'admin'|
```
```json
{
  "users": [
    {
      "name": "Alice",
      "active": true,
      "role": "user"
    },
    {
      "name": "Bob",
      "active": true,
      "role": "admin"
    },
    {
      "name": "Charlie",
      "active": false,
      "role": "user"
    }
  ]
}
```
`Result: True`

---
