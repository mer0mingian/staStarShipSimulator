---
name: nodejs-backend-patterns
description: "Build production-ready Node.js backend services with Express/Fastify, implementing middleware patterns, error handling, authentication, database integration, and API design best practices. Use when creating Node.js servers, REST APIs, GraphQL backends, or microservices architectures. Cluster: JavaScript/TypeScript (SPLIT)"
---

# Production Node.js Backend Patterns (Express/Fastify)

Build scalable, secure, and maintainable backend services using modern Node.js patterns.

## When to Use This Skill

- Architecting a new REST or GraphQL API service
- Implementing robust error handling and logging
- Setting up authentication (JWT, OAuth2) and authorization (RBAC)
- Integrating databases (SQL/NoSQL) securely
- Creating reusable middleware patterns
- Optimizing service performance

## Core Concepts

### 1. Frameworks
-   **Express.js**: Mature, flexible, large ecosystem.
-   **Fastify**: High-performance, lower overhead, focused on performance.

### 2. Middleware Architecture (Express Example)
Middleware runs sequentially and can modify the request/response cycle.

| Middleware Type | Purpose | Example |
|-----------------|---------|---------|
| **Logging** | Log request details | Winston, Pino |
| **CORS** | Manage cross-origin requests | `cors` package |
| **Security** | Set headers, prevent XSS/CSRF | Helmet |
| **Authentication** | Validate JWT/session | Passport.js |
| **Validation** | Schema validation (Joi, Zod) | Validator middleware |
| **Error Handling** | Centralized error catcher | Final error middleware |

### 3. API Design Principles
-   **RESTful Design**: Use nouns for resources, proper HTTP verbs (GET, POST, PUT, PATCH, DELETE).
-   **Versioning**: Use `/api/v1/resource`.
-   **HATEOAS**: Hypermedia as the Engine of Application State (optional but good).

## Key Patterns

### Pattern 1: Centralized Error Handling
Use a final error-handling middleware to catch errors thrown by preceding handlers/routes.

```javascript
// app.js (Express)
const express = require('express');
const helmet = require('helmet');
const app = express();

app.use(helmet());
app.use(express.json());

// Routes defined here...
app.get('/protected', isAuthenticated, (req, res) => {
  if (!req.user.admin) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  res.json({ message: 'Admin access granted' });
});

// 404 Handler (must be before the main error handler)
app.use((req, res, next) => {
  res.status(404).json({ error: 'Not Found' });
});

// Main Error Handler (must have 4 arguments)
app.use((err, req, res, next) => {
  console.error(err.stack);
  const statusCode = err.statusCode || 500;
  res.status(statusCode).json({
    status: 'error',
    message: err.isOperational ? err.message : 'Something broke!',
  });
});

module.exports = app;
```

### Pattern 2: Database Integration (ORM/ODM)
-   **SQL (e.g., Sequelize/Prisma):** Use transaction blocks for multiple dependent writes.
-   **NoSQL (e.g., Mongoose):** Use ODM features for schema validation on save.

### Pattern 3: Authentication with JWT
1.  User logs in $\rightarrow$ Server verifies credentials.
2.  Server creates JWT (with user ID, roles, expiry).
3.  Server sends JWT back to client.
4.  Client sends JWT in `Authorization: Bearer <token>` header on subsequent requests.
5.  Middleware extracts token, verifies signature/expiry, attaches user data to request object.

## Best Practices

-   **Operational vs. Programming Errors:** Distinguish between expected errors (4xx) and unexpected bugs (5xx). Log stack traces only for bugs.
-   **Security First:** Use `helmet`, validate all input schemas (`Joi`/`Zod`), sanitize output.
-   **Async/Await:** Use Promises correctly; avoid mixing callback patterns.
-   **Performance:** Use connection pooling for DBs, cache external API results.

## References

-   [Express.js Documentation](references/express-docs.md)
-   [Fastify Documentation](references/fastify-docs.md)
-   [OWASP Top 10 for Node.js](references/owasp-nodejs.md)
-   [Joi/Zod Documentation](references/validation-docs.md)

---

**Remember:** Node.js thrives on non-blocking I/O; ensure all critical paths utilize asynchronous patterns. (Cluster: JavaScript/TypeScript)
