# Configuration Migration: From Multiple URLs to argo_base_url

## Overview

This document describes the configuration refactoring that replaces multiple individual URL fields with a single `argo_base_url` field, providing better maintainability and backward compatibility.

## Changes Made

### Before (Legacy Format)

```yaml
host: "0.0.0.0"
port: 44497
user: "username"
argo_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
argo_stream_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/streamchat/"
argo_embedding_url: "https://apps.inside.anl.gov/argoapi/api/v1/resource/embed/"
verbose: true
```

### After (New Format)

```yaml
host: "0.0.0.0"
port: 44497
user: "username"
argo_base_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/"
verbose: true
```

## Key Benefits

1. **Single Source of Truth**: Only one URL to maintain for the base API endpoint
2. **Environment Switching**: Easy to switch between dev/staging/production environments
3. **Reduced Configuration**: Fewer fields to configure and maintain
4. **Automatic URL Construction**: All specific URLs are built dynamically from the base URL

## Backward Compatibility

The system provides **full backward compatibility**:

- ✅ Existing configurations with legacy URLs continue to work
- ✅ Automatic migration happens silently on first load
- ✅ Migrated configurations are saved in the new format
- ✅ No manual intervention required

## Migration Process

When the system detects a legacy configuration:

1. **Detection**: Checks if legacy URL fields exist without `argo_base_url`
2. **Extraction**: Extracts the base URL from any of the legacy URL fields
3. **Migration**: Sets the `argo_base_url` and constructs all specific URLs
4. **Persistence**: Saves the migrated configuration in the new format
5. **Logging**: Informs the user about the successful migration

## URL Construction

From the base URL, the system automatically constructs:

```python
base = "https://apps-dev.inside.anl.gov/argoapi/api/v1/"

# Constructed URLs:
argo_url = f"{base}resource/chat/"
argo_stream_url = f"{base}resource/streamchat/"
argo_embedding_url = f"{base}resource/embed/"
argo_model_url = f"{base}models/"
```

## Code Changes

### Modified Files

1. **`src/argoproxy/config.py`**:

   - Updated `ArgoConfig` dataclass with new `argo_base_url` field
   - Added migration logic in `__post_init__()`, `_migrate_legacy_config()`, and `_extract_base_url_from_legacy()`
   - Updated `save_config()` to exclude legacy fields from saved configuration
   - Modified `validate_config()` to handle automatic migration
   - Updated `REQUIRED_KEYS` to use `argo_base_url` instead of individual URLs

2. **`config.sample.yaml`**:
   - Updated sample configuration to use new `argo_base_url` format

### New Features

- **Automatic Migration**: Legacy configurations are automatically migrated on load
- **URL Construction**: Dynamic URL building from base URL
- **Migration Detection**: System can detect if migration is needed
- **Clean Persistence**: Only new format fields are saved to configuration files

## Testing

The migration functionality has been thoroughly tested:

- **Legacy Migration Test**: Verifies automatic migration from old to new format
- **New Format Test**: Ensures new configurations work correctly
- **URL Construction Test**: Validates that all URLs are built correctly
- **Persistence Test**: Confirms that saved configurations use the new format

Run tests with:

```bash
python dev_scripts/test_migration.py
```

## Usage Examples

### For New Users

Simply use the new format in your `config.yaml`:

```yaml
argo_base_url: "https://your-argo-instance.com/api/v1/"
```

### For Existing Users

No action required! Your existing configuration will be automatically migrated when you next start the application.

## Migration Log Messages

When migration occurs, you'll see:

```
INFO - Migrated from legacy configuration to new argo_base_url format
INFO - Configuration successfully migrated and saved to: /path/to/config.yaml
```

## Environment Switching

With the new format, switching environments is much easier:

```yaml
# Development
argo_base_url: "https://apps-dev.inside.anl.gov/argoapi/api/v1/"

# Production
argo_base_url: "https://apps.inside.anl.gov/argoapi/api/v1/"
```

## Troubleshooting

If you encounter issues:

1. **Check logs**: Migration status is logged during startup
2. **Verify base URL**: Ensure the `argo_base_url` ends with `/`
3. **Test connectivity**: The system will validate URL connectivity
4. **Manual migration**: Delete old URL fields and add `argo_base_url` if needed

## Future Considerations

This refactoring provides a foundation for:

- Easy addition of new API endpoints
- Environment-specific configuration management
- Simplified deployment across different environments
- Better configuration validation and error handling
