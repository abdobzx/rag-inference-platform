# Database Migrations

This directory contains database migration scripts for the SothemaAI authentication service using Alembic.

## Overview

Database migrations ensure that:
- Schema changes are version-controlled
- Multiple environments stay synchronized
- Rollbacks are possible
- Database evolution is safe and predictable

## Directory Structure

```
alembic/
├── versions/           # Migration scripts
├── env.py             # Alembic environment configuration
├── script.py.mako     # Migration script template
└── README             # Alembic-generated documentation

migrate.py             # Migration management script
setup_db.py           # Database setup script
```

## Usage

### Initial Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up the database:**
   ```bash
   python setup_db.py
   ```

### Running Migrations

Use the migration script for all migration operations:

```bash
# Check current migration status
python migrate.py current

# View migration history
python migrate.py history

# Upgrade to latest migration
python migrate.py upgrade

# Upgrade to specific revision
python migrate.py upgrade <revision_id>

# Downgrade to specific revision
python migrate.py downgrade <revision_id>

# Create new migration (auto-generated)
python migrate.py revision -m "Add new feature"
```

### Manual Alembic Commands

You can also use alembic directly:

```bash
# Check status
alembic current

# View history
alembic history

# Upgrade
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"
```

## Migration Best Practices

### 1. **Always Test Migrations**
- Test upgrades and downgrades on a copy of production data
- Verify data integrity after migrations
- Test with different database engines (SQLite for dev, PostgreSQL for prod)

### 2. **Use Descriptive Messages**
```bash
# Good
python migrate.py revision -m "Add user preferences table"

# Bad
python migrate.py revision -m "changes"
```

### 3. **Review Auto-generated Migrations**
- Alembic auto-generates migrations but they should be reviewed
- Ensure column types, constraints, and indexes are correct
- Test the migration on different environments

### 4. **Backup Before Migration**
- Always backup production databases before running migrations
- Test migrations on staging environments first

## Environment Configuration

### Development (SQLite)
- Default configuration uses SQLite
- Database file: `sql_app.db`
- No additional setup required

### Production (PostgreSQL)
Set the `DATABASE_URL` environment variable:
```bash
export DATABASE_URL="postgresql://user:password@localhost/dbname"
```

## Troubleshooting

### Migration Fails
1. Check database connectivity
2. Verify environment variables
3. Review migration script for errors
4. Check database permissions

### Auto-generation Issues
1. Ensure models are properly imported in `env.py`
2. Check that `target_metadata` is correctly set
3. Verify model definitions are valid

### Rollback Issues
1. Some operations cannot be rolled back (data loss)
2. Test rollbacks in development first
3. Have backup strategies for production

## Migration History

### Completed Migrations

1. **934bfc2a0292** - Create users and api_keys tables
   - Initial schema creation
   - Users table with authentication fields
   - API keys table with foreign key relationship

2. **eea056c9e987** - Add user preferences column
   - Added JSON preferences column to users table
   - Supports user customization settings

3. **b00265253864** - Add production constraints and optimizations
   - Check constraints for data validation
   - Performance indexes for query optimization
   - Production-ready database constraints

### Current Status

- **Head Revision**: b00265253864
- **Status**: All migrations applied successfully
- **Tested**: Upgrade/downgrade cycles verified

## Schema Overview

### Users Table

- Stores user account information
- Includes authentication and verification data
- Related to API keys

### API Keys Table

- Stores API key information for inference access
- Linked to users with foreign key relationship
- Includes security and usage tracking fields

## Contributing

When making schema changes:

1. Modify the SQLAlchemy models in `src/models/`
2. Create a migration: `python migrate.py revision -m "Description"`
3. Review and test the generated migration
4. Commit both model changes and migration script
