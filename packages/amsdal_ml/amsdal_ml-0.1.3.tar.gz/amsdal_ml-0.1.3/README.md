# amsdal-ml

This plugin extends the AMSDAL Framework with machine learning utilities, 
including custom models for embeddings, properties for ML metadata, and 
hooks for working with vector search and AI-driven features.

## Plugin Structure

- `src/models/` - Contains model definitions in Python format
- `src/transactions/` - Contains transaction definitions
- `pyproject.toml` - Plugin configuration file
- `config.yml` - Configuration for connections

## Installing this Plugin

To use this plugin in an AMSDAL application:

1. Copy the plugin directory to your AMSDAL application
2. Import the models and transactions as needed
3. Register the plugin in your application configuration

## Development

This plugin uses sync mode.

### Adding Models

```bash
amsdal generate model ModelName --format py
```

### Adding Properties

```bash
amsdal generate property --model ModelName property_name
```

### Adding Transactions

```bash
amsdal generate transaction TransactionName
```

### Adding Hooks

```bash
amsdal generate hook --model ModelName on_create
```

## Testing

Test your plugin by integrating it with an AMSDAL application and running the application's test suite.