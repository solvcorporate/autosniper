"""
Stripe webhook handler for processing subscription events.
"""
import os
import logging
import json
from flask import Flask, request, jsonify
from subscription import get_subscription_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("webhook")

# Create Flask app for webhook handling
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events."""
    payload = request.data.decode('utf-8')
    sig_header = request.headers.get('Stripe-Signature')
    
    logger.info("Received webhook from Stripe")
    
    if not sig_header:
        logger.error("No Stripe-Signature header found")
        return jsonify({'error': 'No Stripe-Signature header'}), 400
    
    # Process the webhook event
    subscription_manager = get_subscription_manager()
    
    try:
        # Handle the webhook event
        success = subscription_manager.handle_webhook_event(payload, sig_header)
        
        if success:
            logger.info("Successfully processed webhook event")
            return jsonify({'status': 'success'}), 200
        else:
            logger.error("Failed to process webhook event")
            return jsonify({'error': 'Failed to process event'}), 400
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
