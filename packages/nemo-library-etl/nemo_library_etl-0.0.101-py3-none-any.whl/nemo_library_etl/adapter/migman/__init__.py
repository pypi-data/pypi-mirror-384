"""
MigMan ETL Adapter Package.

This package provides a complete ETL (Extract, Transform, Load) adapter for 
MigMan systems. It is built using the Prefect workflow 
orchestration framework and integrates with the Nemo Library ecosystem.

The adapter includes:
- Extract module for data retrieval from MigMan systems
- Transform module for data processing and business rule application  
- Load module for data insertion into target systems
- Configuration models for pipeline settings and validation
- Main flow orchestration using Prefect workflows

Usage:
    The adapter can be executed as a module or imported for integration
    into larger ETL workflows. Configuration is handled through JSON
    files and Pydantic models for type safety.

Modules:
    extract: Handles data extraction from MigMan systems
    transform: Processes and transforms extracted data
    load: Loads transformed data into target systems
    flow: Orchestrates the complete ETL workflow
    config_models: Defines configuration data models
"""