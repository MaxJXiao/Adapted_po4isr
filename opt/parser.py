"""
Configuration settings for the project.
Import the 'args' object from this module to use these settings.
"""

class Args:
    reward_func = 'rmse'
    model = 'gpt-4o-mini'
    seed = 42
    candidate_size = 20
    dataset = 'bundle'
    train_num = 50
    batch_size = 16

# Create a single instance that the rest of your project can import and use.
args = Args()