# SPEC-011: Configuration Import/Export

## Overview
Complete system for backing up and restoring RabbitMQ topology configurations using RabbitMQ's definitions.json format with safe merge and destructive overwrite options.

## Components

### Export Functionality
- **Topology Export**: Export complete RabbitMQ topology to definitions.json
- **Selective Export**: Export specific vhosts, queues, exchanges, or bindings
- **Metadata Export**: Include user permissions, policies, and configurations
- **Format Validation**: Ensure exported definitions are valid RabbitMQ format

### Import Functionality
- **Full Import**: Import complete topology from definitions.json
- **Selective Import**: Import specific components (queues, exchanges, bindings)
- **Merge Mode**: Safe merge with existing topology (preserve users/vhosts)
- **Overwrite Mode**: Destructive import with complete topology replacement

### Backup and Restore
- **Automated Backups**: Scheduled topology backups
- **Backup Retention**: Configurable backup retention policies
- **Restore Validation**: Validate topology before restore operations
- **Rollback Support**: Ability to rollback failed imports

### Configuration Management
- **Version Control**: Track topology changes and versions
- **Diff Analysis**: Compare current vs imported topology
- **Conflict Resolution**: Handle conflicts during merge operations
- **Validation**: Comprehensive validation of imported configurations

### Internal Operations (Auto-generated from OpenAPI)
**OpenAPI-Driven**: These operations are derived from RabbitMQ Management API definitions endpoints.

- `definitions.export`: GET /api/definitions - Export topology to definitions.json (from OpenAPI)
- `definitions.import`: POST /api/definitions - Import topology from definitions.json (from OpenAPI)
- `config.backup-topology`: Create topology backup (custom wrapper around definitions.export)
- `config.restore-topology`: Restore topology from backup (custom wrapper around definitions.import)
- `config.validate-topology`: Validate topology configuration (local validation logic)

**Note**: Base operations auto-generated from OpenAPI `paths` with tag "Definitions"

## Technical Requirements

### Export Features
- Support for RabbitMQ definitions.json format
- Export of queues, exchanges, bindings, users, vhosts, policies
- Metadata preservation (permissions, configurations)
- Selective export by component type or vhost

### Import Features
- Full and selective import capabilities
- Safe merge mode (preserve existing users/vhosts)
- Destructive overwrite mode (complete replacement)
- Conflict detection and resolution

### Backup System
- Automated daily backups (configurable schedule)
- Backup retention (30 days default, configurable)
- Backup compression and encryption
- Backup integrity verification

### Validation
- Pre-import topology validation
- Conflict detection and reporting
- Rollback capability for failed imports
- Comprehensive error reporting

### Performance
- Export operations complete within 30 seconds
- Import operations complete within 60 seconds
- Support for topologies with 1000+ components
- Efficient diff analysis and conflict detection

## Acceptance Criteria

### Functional Requirements
- [ ] Export complete topology to definitions.json
- [ ] Import topology with merge and overwrite modes
- [ ] Selective export/import by component type works
- [ ] Automated backup system functions correctly
- [ ] Topology validation prevents invalid imports
- [ ] Rollback capability works for failed imports

### Performance Requirements
- [ ] Export operations complete within 30 seconds
- [ ] Import operations complete within 60 seconds
- [ ] Supports topologies with 1000+ components
- [ ] Diff analysis is efficient and accurate

### Safety Requirements
- [ ] Safe merge mode preserves existing configurations
- [ ] Conflict detection prevents data loss
- [ ] Rollback capability restores previous state
- [ ] Backup integrity is verified

### Quality Requirements
- [ ] Exported definitions are valid RabbitMQ format
- [ ] Import validation catches configuration errors
- [ ] Error messages are clear and actionable
- [ ] Backup and restore procedures are reliable

## Dependencies
- RabbitMQ Management API for topology operations
- JSON schema validation for definitions format
- asyncio for concurrent backup operations

## Implementation Notes
- Use RabbitMQ Management API for topology export/import
- Implement proper conflict detection algorithms
- Use JSON schema validation for definitions format
- Implement efficient diff analysis for large topologies
- Set up automated backup scheduling
- Create comprehensive validation rules
- Implement rollback mechanisms for failed operations
- Set up backup integrity verification
