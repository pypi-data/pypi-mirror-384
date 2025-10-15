# Nedo Vision Training Service

A distributed AI model training service for the Nedo Vision platform. This service manages training workflows, monitoring, and lifecycle management for computer vision models using RF-DETR architecture.

## Features

- **Configurable Training Service**: Automated training with customizable intervals and parameters
- **gRPC Communication**: Reliable communication with the vision manager and other services
- **Distributed Training**: Support for multi-GPU and distributed training scenarios
- **Real-time Monitoring**: System resource monitoring and training progress tracking
- **Cloud Integration**: AWS S3 integration for model storage and dataset management
- **Message Queue Support**: RabbitMQ integration for task queue management

## Installation

Install the package from PyPI:

```bash
pip install nedo-vision-training
```

For GPU support with CUDA 12.1:

```bash
pip install nedo-vision-training[gpu] --extra-index-url https://download.pytorch.org/whl/cu121
```

For development with all tools:

```bash
pip install nedo-vision-training[dev]
```

## Quick Start

### Using the CLI

After installation, you can use the training service CLI:

```bash
# Show CLI help
nedo-training --help

# Check system dependencies and requirements
nedo-training doctor

# Start training service with authentication token
nedo-training run --token YOUR_TOKEN

# Start with custom server configuration
nedo-training run --token YOUR_TOKEN --server-host custom.server.com --server-port 60000

# Start with custom REST API port
nedo-training run --token YOUR_TOKEN --rest-api-port 8081

# Start with custom intervals
nedo-training run --token YOUR_TOKEN --system-usage-interval 30 --latency-check-interval 15

# Start with all custom configurations
nedo-training run --token YOUR_TOKEN \
  --server-host custom.server.com \
  --server-port 60000 \
  --rest-api-port 8081 \
  --system-usage-interval 30 \
  --latency-check-interval 15
```

### Configuration Options

The service supports various configuration options:

#### Available Commands

- `doctor`: Check system dependencies and requirements (CUDA, NVIDIA drivers, etc.)
- `run`: Start the training service

#### Run Command Options

- `--token`: Authentication token for secure communication (required)
- `--server-host`: gRPC server host (default: localhost)
- `--server-port`: gRPC server port (default: 50051)
- `--rest-api-port`: Manager REST API port (default: 8081)
- `--system-usage-interval`: System usage reporting interval in seconds (default: 30)
- `--latency-check-interval`: Latency monitoring interval in seconds (default: 10)

## Architecture

### Core Components

- **TrainingService**: Main service orchestrator for training workflows
- **RFDETRTrainer**: RF-DETR algorithm implementation with PyTorch backend
- **TrainerLogger**: Real-time training progress logging via gRPC
- **ResourceMonitor**: System resource monitoring (GPU, CPU, memory)

### Dependencies

The service relies on several key technologies:

- **PyTorch**: Deep learning framework with CUDA support
- **RF-DETR**: Roboflow's Real-time Detection Transformer
- **gRPC**: High-performance RPC framework
- **RabbitMQ**: Message queue for distributed task management
- **AWS SDK**: Cloud storage integration
- **NVIDIA ML**: GPU monitoring and management

## Development Setup

## Troubleshooting

### Common Issues

1. **gRPC Connection Timeouts**: Ensure the server host and port are correctly configured
2. **CUDA Out of Memory**: Reduce batch size or use gradient accumulation
3. **Missing Dependencies**: Reinstall with `pip install --upgrade nedo-vision-training`

### Support

For issues and questions:

- Check the logs for detailed error information
- Ensure your token is valid and not expired
- Verify network connectivity to the training manager

## License

This project is part of the Nedo Vision platform. Please refer to the main project license for usage terms.
