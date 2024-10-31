import logging

def setup_logging():
    """
    Configures logging settings for the application.
    """
    logging.basicConfig(
        level=logging.INFO,  # Set the minimum log level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
        handlers=[
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    logger = logging.getLogger(__name__)

    return(logger)