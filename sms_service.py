# sms_service.py
import africastalking

class SMSService:
    def __init__(self, username, api_key):
        africastalking.initialize(username, api_key)
        self.sms = africastalking.SMS

    def send_sms(self, recipients, message):
        try:
            response = self.sms.send(message, recipients)
            return response
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return None

class TransactionNotifier:
    def __init__(self, sms_service):
        self.sms_service = sms_service
    
    def notify_transaction(self, phone_number, amount, transaction_type):
        message = f"Transaction Alert: {transaction_type} of ${amount} completed."
        return self.sms_service.send_sms([phone_number], message)