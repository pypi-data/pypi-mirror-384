#!/usr/bin/env python3
"""
Advanced usage example for Digilog client.

This example demonstrates advanced features:
- Context manager usage
- Multiple runs with different configurations
- Hyperparameter tuning simulation
- Error handling
"""

import time
import random
import digilog

# Set your authentication token (or use environment variable DIGILOG_API_KEY)
# digilog.set_token("your-token-here")

def train_model(learning_rate, batch_size, epochs=5):
    """Simulate training a model with given parameters."""
    # Simulate training metrics
    for epoch in range(epochs):
        loss = 1.0 - (epoch * 0.15) + random.uniform(-0.05, 0.05)
        accuracy = 0.1 + (epoch * 0.15) + random.uniform(-0.05, 0.05)
        
        digilog.log({
            "loss": loss,
            "accuracy": accuracy,
            "epoch": epoch
        })
        
        time.sleep(0.1)  # Simulate training time
    
    return loss, accuracy

def hyperparameter_tuning():
    """Demonstrate hyperparameter tuning with multiple runs."""
    print("Starting hyperparameter tuning...")
    
    # Define hyperparameter combinations
    learning_rates = [0.001, 0.01, 0.1]
    batch_sizes = [16, 32, 64]
    
    best_accuracy = 0
    best_config = None
    
    for lr in learning_rates:
        for bs in batch_sizes:
            # Use context manager for automatic run management
            with digilog.init(
                project="hyperparameter-tuning",
                name=f"lr-{lr}-bs-{bs}",
                config={
                    "learning_rate": lr,
                    "batch_size": bs,
                    "optimizer": "adam"
                },
                group="tuning-experiment"
            ) as run:
                print(f"Training with lr={lr}, batch_size={bs}")
                
                # Train the model
                final_loss, final_accuracy = train_model(lr, bs)
                
                # Log final results
                run.log_config("final_loss", final_loss)
                run.log_config("final_accuracy", final_accuracy)
                
                # Track best configuration
                if final_accuracy > best_accuracy:
                    best_accuracy = final_accuracy
                    best_config = {"lr": lr, "batch_size": bs}
    
    print(f"Best configuration: {best_config} with accuracy: {best_accuracy:.4f}")

def error_handling_example():
    """Demonstrate error handling and automatic run cleanup."""
    print("Demonstrating error handling...")
    
    try:
        with digilog.init(
            project="error-handling-demo",
            name="error-test",
            config={"test_param": "value"}
        ) as run:
            print("Starting run that will encounter an error...")
            
            # Log some initial data
            run.log({"step": 0, "value": 1.0})
            
            # Simulate an error
            raise ValueError("Simulated training error!")
            
    except Exception as e:
        print(f"Caught error: {e}")
        print("Run was automatically finished with FAILED status")

def main():
    print("Starting Digilog advanced usage examples...")
    
    # Example 1: Hyperparameter tuning
    hyperparameter_tuning()
    
    # Example 2: Error handling
    error_handling_example()
    
    print("All examples completed!")

if __name__ == "__main__":
    main() 