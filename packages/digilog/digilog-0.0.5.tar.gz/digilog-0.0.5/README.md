# Digilog Python Client

A Python client for Digilog experiment tracking with a wandb-like interface.

## Installation

```bash
pip install digilog
```

Or install from source:

```bash
git clone https://github.com/digilog/digilog-python.git
cd digilog-python
pip install -e .
```

## Quick Start

```python
import digilog

# Initialize digilog (similar to wandb.init)
run = digilog.init(
    project="my-ml-project",
    name="experiment-1",
    config={
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 100
    }
)

# Log metrics during training
for epoch in range(100):
    loss = train_epoch()
    accuracy = evaluate()
    
    run.log({
        "loss": loss,
        "accuracy": accuracy,
        "epoch": epoch
    })

# Finish the run
run.finish()
```

## API Reference

### digilog.init()

Initialize a new experiment run.

```python
digilog.init(
    project: str,           # Project name
    name: str = None,       # Run name (optional)
    config: dict = None,    # Configuration parameters
    group: str = None,      # Group name for related runs
    tags: list = None,      # Tags for organization
    notes: str = None,      # Description/notes
    **kwargs
) -> Run
```

### run.log()

Log metrics and other data.

```python
run.log(
    data: dict,             # Dictionary of metrics to log
    step: int = None        # Step number (optional)
)
```

### run.config

Access or update configuration parameters.

```python
# Set config values
run.config.update({"new_param": "value"})

# Get config values
learning_rate = run.config.learning_rate
```

### run.finish()

Finish the current run.

```python
run.finish()
```

## Advanced Usage

### Multiple Runs

```python
import digilog

# Create multiple runs
for lr in [0.001, 0.01, 0.1]:
    run = digilog.init(
        project="hyperparameter-tuning",
        name=f"lr-{lr}",
        config={"learning_rate": lr}
    )
    
    # Training loop
    for epoch in range(100):
        loss = train_epoch()
        run.log({"loss": loss, "epoch": epoch})
    
    run.finish()
```

### Custom Step Logging

```python
import digilog

run = digilog.init(project="my-project")

for step in range(1000):
    # Your training code here
    loss = model.train_step()
    
    # Log with custom step
    run.log({
        "loss": loss,
        "learning_rate": scheduler.get_last_lr()[0]
    }, step=step)

run.finish()
```

### Configuration Management

```python
import digilog

# Initialize with config
run = digilog.init(
    project="config-test",
    config={
        "model": "resnet50",
        "optimizer": "adam",
        "learning_rate": 0.001
    }
)

# Update config during run
run.config.update({
    "batch_size": 64,
    "epochs": 200
})

# Access config values
print(f"Learning rate: {run.config.learning_rate}")
```

## Authentication

The client requires authentication via a session token. You can set this in several ways:

1. **Environment variable:**
   ```bash
   export DIGILOG_API_KEY="your-session-token"
   ```

2. **In your code:**
   ```python
   import digilog
   digilog.set_token("your-session-token")
   ```

3. **Login via CLI:**
   ```bash
   digilog login
   ```

## Error Handling

The client handles common errors gracefully:

```python
import digilog

try:
    run = digilog.init(project="my-project")
    run.log({"metric": 0.95})
    run.finish()
except digilog.DigilogError as e:
    print(f"Digilog error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 