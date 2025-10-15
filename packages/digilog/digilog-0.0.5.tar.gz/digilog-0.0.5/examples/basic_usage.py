#!/usr/bin/env python3
"""
Basic usage example for Digilog client.

This example demonstrates the core functionality:
- Initializing a run
- Logging metrics
- Logging configurations
- Finishing a run
"""

import time
import random
import digilog

# Set your authentication token (or use environment variable DIGILOG_API_KEY)
# digilog.set_token("your-token-here")

def main():
    print("Starting Digilog basic usage example...")
    
    # Initialize a new run
    run = digilog.init(
        project="basic-example",
        name="simple-training",
        config={
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 10,
            "model": "simple-nn"
        }
    )
    
    print(f"Started run: {run.id}")
    print(f"Project: {run.project}")
    print(f"Config: {run.config}")
    
    # Simulate training loop
    for epoch in range(10):
        # Simulate training metrics
        loss = 1.0 - (epoch * 0.08) + random.uniform(-0.02, 0.02)
        accuracy = 0.1 + (epoch * 0.08) + random.uniform(-0.02, 0.02)
        
        # Log metrics
        run.log({
            "loss": loss,
            "accuracy": accuracy,
            "epoch": epoch
        })
        
        print(f"Epoch {epoch}: loss={loss:.4f}, accuracy={accuracy:.4f}")
        time.sleep(0.1)  # Simulate training time
    
    # Log final configuration
    run.log_config("final_loss", loss)
    run.log_config("final_accuracy", accuracy)
    
    # Finish the run
    run.finish()
    print("Run finished successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        # Make sure to finish the run even if there's an error
        try:
            digilog.finish()
        except:
            pass 