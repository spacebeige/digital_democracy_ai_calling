# Schema Change Checklist for NeonDB and Middleware

Use this checklist whenever you add, remove, or rename columns/tables.

## 1. Update SQLAlchemy Models

1. Edit app models in app/models.py.
2. Ensure nullable/default behavior is explicit for new columns.
3. Keep relationship definitions consistent when adding foreign keys.

## 2. Update API Contracts

1. Update request and response models in app/schemas.py.
2. Keep field names aligned with model names.
3. If a field is renamed, support backward compatibility at route level if required.

## 3. Update Route and Service Logic

1. Update all reads and writes using changed columns.
2. Search for old field names across routes and services.
3. Verify create, update, and read paths for affected entities.

## 4. Handle Data Migration

1. Decide migration strategy:
   - simple create_all for additive changes only
   - migration script for rename or type change
2. If using scripts/migrate_sqlite_to_neondb.py, verify source and target columns match.
3. Test migration in staging data before production data.

## 5. Middleware Impact Decision

You usually do not need to change middleware for schema/table updates.

Change middleware only if you are changing session architecture, such as:

1. Multiple database connections or tenant routing.
2. Async SQLAlchemy engine/session adoption.
3. Global transaction policy changes.
4. Retry or circuit-breaker policy changes.

## 6. Verify Runtime Behavior

1. Start API and verify startup logs are clean.
2. Check root health endpoint.
3. Check /db-health endpoint.
4. Run CRUD endpoints that touch changed schema.
5. Confirm no SQLAlchemy errors in logs.

## 7. Update Documentation

1. Update backend/NEON_SETUP.md when migration steps change.
2. Update branch integration README files when schema impacts branch merges.
3. Mention any breaking changes and required env updates.

## 8. Release Safety

1. Back up production data before applying migration.
2. Deploy code and schema changes in a controlled sequence.
3. Keep rollback plan ready:
   - previous image
   - DB snapshot restore point
