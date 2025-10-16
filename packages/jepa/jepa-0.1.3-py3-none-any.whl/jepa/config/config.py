"""
Configuration management for JEPA training and evaluation.
"""

import yaml
import argparse
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class ModelConfig:
    """Model configuration parameters."""
    encoder_type: str = "transformer"
    encoder_dim: int = 512
    predictor_type: str = "mlp"
    predictor_hidden_dim: int = 1024
    predictor_output_dim: int = 512
    dropout: float = 0.1


@dataclass
class TrainingConfig:
    """Training configuration parameters."""
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    num_epochs: int = 100
    warmup_epochs: int = 10
    gradient_clip_norm: Optional[float] = 1.0
    save_every: int = 10
    early_stopping_patience: Optional[int] = 20
    log_interval: int = 100


@dataclass
class DataConfig:
    """Data configuration parameters."""
    train_data_path: str = ""
    val_data_path: str = ""
    test_data_path: str = ""
    num_workers: int = 4
    pin_memory: bool = True
    sequence_length: int = 10
    input_dim: int = 784


@dataclass
class WandbConfig:
    """Weights & Biases logging configuration."""
    enabled: bool = False
    project: str = "jepa"
    entity: Optional[str] = None
    name: Optional[str] = None
    tags: Optional[list] = None
    notes: Optional[str] = None
    log_model: bool = True
    log_gradients: bool = False
    log_freq: int = 100
    watch_model: bool = True


@dataclass
class TensorBoardConfig:
    """TensorBoard logging configuration."""
    enabled: bool = False
    log_dir: str = "./tensorboard_logs"
    comment: str = ""


@dataclass
class ConsoleConfig:
    """Console logging configuration."""
    enabled: bool = True
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: bool = False
    file_level: str = "DEBUG"
    log_dir: str = "./logs"


@dataclass
class LoggingConfig:
    """Comprehensive logging configuration."""
    wandb: WandbConfig
    tensorboard: TensorBoardConfig
    console: ConsoleConfig


@dataclass
class JEPAConfig:
    """Main JEPA configuration."""
    model: ModelConfig
    training: TrainingConfig
    data: DataConfig
    logging: LoggingConfig
    device: str = "auto"
    seed: int = 42
    output_dir: str = "./outputs"
    checkpoint_dir: str = "./checkpoints"
    experiment_name: str = "jepa_experiment"


def load_config(config_path: str) -> JEPAConfig:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        JEPAConfig instance
    """
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    return JEPAConfig(
        model=ModelConfig(**config_dict.get('model', {})),
        training=TrainingConfig(**config_dict.get('training', {})),
        data=DataConfig(**config_dict.get('data', {})),
        logging=LoggingConfig(
            wandb=WandbConfig(**config_dict.get('logging', {}).get('wandb', {})),
            tensorboard=TensorBoardConfig(**config_dict.get('logging', {}).get('tensorboard', {})),
            console=ConsoleConfig(**config_dict.get('logging', {}).get('console', {}))
        ),
        device=config_dict.get('device', 'auto'),
        seed=config_dict.get('seed', 42),
        output_dir=config_dict.get('output_dir', './outputs'),
        checkpoint_dir=config_dict.get('checkpoint_dir', './checkpoints'),
        experiment_name=config_dict.get('experiment_name', 'jepa_experiment')
    )


def save_config(config: JEPAConfig, save_path: str):
    """
    Save configuration to YAML file.
    
    Args:
        config: JEPAConfig instance
        save_path: Path to save the configuration
    """
    config_dict = asdict(config)
    with open(save_path, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False, indent=2)


def create_default_config() -> JEPAConfig:
    """Create a default configuration."""
    return JEPAConfig(
        model=ModelConfig(),
        training=TrainingConfig(),
        data=DataConfig(),
        logging=LoggingConfig(
            wandb=WandbConfig(),
            tensorboard=TensorBoardConfig(),
            console=ConsoleConfig()
        )
    )


def override_config_with_args(config: JEPAConfig, args: argparse.Namespace) -> JEPAConfig:
    """
    Override configuration with command line arguments.
    
    Args:
        config: Base configuration
        args: Command line arguments
        
    Returns:
        Updated configuration
    """
    # Override training parameters if provided
    if hasattr(args, 'batch_size') and args.batch_size:
        config.training.batch_size = args.batch_size
    if hasattr(args, 'learning_rate') and args.learning_rate:
        config.training.learning_rate = args.learning_rate
    if hasattr(args, 'num_epochs') and args.num_epochs:
        config.training.num_epochs = args.num_epochs
    if hasattr(args, 'device') and args.device:
        config.device = args.device
    
    # Override data paths if provided
    if hasattr(args, 'train_data') and args.train_data:
        config.data.train_data_path = args.train_data
    if hasattr(args, 'val_data') and args.val_data:
        config.data.val_data_path = args.val_data
    if hasattr(args, 'test_data') and args.test_data:
        config.data.test_data_path = args.test_data
    
    # Override output directories if provided
    if hasattr(args, 'output_dir') and args.output_dir:
        config.output_dir = args.output_dir
    if hasattr(args, 'checkpoint_dir') and args.checkpoint_dir:
        config.checkpoint_dir = args.checkpoint_dir
    
    # Override wandb settings if provided
    if hasattr(args, 'wandb') and args.wandb:
        config.logging.wandb.enabled = True
    if hasattr(args, 'wandb_project') and args.wandb_project:
        config.logging.wandb.project = args.wandb_project
    if hasattr(args, 'wandb_entity') and args.wandb_entity:
        config.logging.wandb.entity = args.wandb_entity
    if hasattr(args, 'wandb_name') and args.wandb_name:
        config.logging.wandb.name = args.wandb_name
    if hasattr(args, 'wandb_tags') and args.wandb_tags:
        config.logging.wandb.tags = args.wandb_tags
    
    return config
