import argparse
import sys
import signal
import traceback
import time
from .training_service import TrainingService
from .doctor import run_doctor
from .logger.Logger import Logger


def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    print("\n🛑 Received interrupt signal. Shutting down gracefully...")
    sys.exit(0)


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Nedo Vision Training Service Library CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check system dependencies and requirements
  nedo-training doctor

  # Start training service with token
  nedo-training run --token YOUR_TOKEN

  # Start with custom server configuration
  nedo-training run --token YOUR_TOKEN --server-host custom.server.com --server-port 60000

  # Start with custom REST API port
  nedo-training run --token YOUR_TOKEN --rest-api-port 8081

  # Start with custom intervals
  nedo-training run --token YOUR_TOKEN --system-usage-interval 30 --latency-check-interval 15
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="nedo-vision-training 1.2.0"
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(
        dest='command', 
        help='Available commands',
        required=True
    )
    
    # Doctor command
    subparsers.add_parser(
        'doctor', 
        help='Check system dependencies and requirements',
        description='Run diagnostic checks for CUDA, NVIDIA drivers, and other dependencies'
    )
    
    # Run command
    run_parser = subparsers.add_parser(
        'run',
        help='Start the training service',
        description='Start the Nedo Vision Training Service'
    )
    
    run_parser.add_argument(
        "--token", 
        required=True,
        help="Authentication token provided by the manager"
    )
    
    run_parser.add_argument(
        "--server-host",
        default="localhost",
        help="Server hostname for communication (default: localhost)"
    )
    
    run_parser.add_argument(
        "--server-port",
        type=int,
        default=50051,
        help="Server port for communication (default: 50051)"
    )
    
    run_parser.add_argument(
        "--rest-api-port",
        type=int,
        default=8081,
        help="Manager REST API port (default: 8081)"
    )
    
    run_parser.add_argument(
        "--system-usage-interval",
        type=int,
        default=30,
        help="System usage reporting interval in seconds (default: 30)"
    )
    
    run_parser.add_argument(
        "--latency-check-interval",
        type=int,
        default=10,
        help="Latency monitoring interval in seconds (default: 10)"
    )
    
    return parser


def run_training_service(args):
    """Run the training service with the provided arguments."""
    logger = Logger()
    
    try:
        # Create and configure the training service
        service = TrainingService(
            token=args.token,
            server_host=args.server_host,
            server_port=args.server_port,
            rest_api_port=args.rest_api_port,
            system_usage_interval=args.system_usage_interval,
            latency_check_interval=args.latency_check_interval
        )
        
        # Log startup information
        logger.info("🚀 Starting Nedo Vision Training Service...")
        logger.info(f"🌐 Server: {args.server_host}:{args.server_port}")
        logger.info(f"⏱️ System Usage Interval: {args.system_usage_interval}s")
        logger.info(f"📊 Latency Check Interval: {args.latency_check_interval}s")
        
        # Start the service
        service.run()
        
        # Keep the service running
        try:
            while getattr(service, 'running', False):
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown requested...")
        finally:
            service.stop()
            logger.info("✅ Service stopped successfully")
            
    except Exception as e:
        logger.error(f"❌ Error starting service: {e}")
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Execute the requested command
    if args.command == 'doctor':
        sys.exit(run_doctor())
    elif args.command == 'run':
        run_training_service(args)


if __name__ == "__main__":
    main()