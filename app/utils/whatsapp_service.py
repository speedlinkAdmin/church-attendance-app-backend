import requests
import os
import logging

logger = logging.getLogger("whatsapp_service")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("logs/whatsapp.log")
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

class WhatsAppService:
    def __init__(self):
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.token = os.getenv("WHATSAPP_TOKEN")
        self.api_version = os.getenv("WHATSAPP_API_VERSION", "v17.0")

        if not self.phone_number_id or not self.token:
            raise ValueError(
                "WhatsApp configuration missing. "
                "Ensure WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_TOKEN are set."
            )

        self.base_url = (
            f"https://graph.facebook.com/{self.api_version}/"
            f"{self.phone_number_id}/messages"
        )

    def send_message(self, to_phone: str, message: str) -> bool:
        """
        Send WhatsApp text message using Meta WhatsApp Cloud API

        to_phone must be in E.164 format WITHOUT '+'.
        Example: 2348012345678
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=15
            )

            if response.status_code in (200, 201):
                data = response.json()
                message_id = (
                    data.get("messages", [{}])[0].get("id")
                )

                logger.info(
                    f"WhatsApp message sent successfully "
                    f"to={to_phone} message_id={message_id}"
                )
                return True

            logger.error(
                "WhatsApp API error "
                f"status={response.status_code} "
                f"response={response.text}"
            )
            return False

        except requests.RequestException as e:
            logger.error(
                f"WhatsApp request failed to {to_phone}",
                exc_info=True
            )
            return False

    def send_attendance_reminder(self, to_phone: str, name: str, week: int) -> bool:
        message = (
            f"Hello {name},\n\n"
            "📊 *Attendance Reminder*\n\n"
            f"This is a reminder to submit your attendance for *week {week}*.\n\n"
            "Please log in and complete it as soon as possible.\n\n"
            "Thank you."
        )

        return self.send_message(to_phone, message)

whatsapp_service = WhatsAppService()


# import requests
# import os

# class WhatsAppService:
#     def __init__(self):
#         self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '808921198974802')
#         self.token = os.getenv('WHATSAPP_TOKEN', 'EAAZAErWsgvsIBPlmpJAo1tGuVxXaLDcjyPAuNAlQfZBG1w4U337P1etgINLjLlOCLbtWqttnmsIpTXqn9vjKqAajjoUHjTFpUHZC2M1ex62ZBRPLqXuolfzFIyZClYgmurq4fG4kRYrZBrRey2h3QFJvR7ODlHaIB9QBM7t8jU0wpTi0z8QteN64nX4PPNlVf31gZDZD')
#         self.base_url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        
#     def send_message(self, to_phone, message):
#         """
#         Send WhatsApp message to a phone number
#         Phone number should be in format: 1234567890 (without country code prefix)
#         """
#         try:
#             headers = {
#                 'Authorization': f'Bearer {self.token}',
#                 'Content-Type': 'application/json'
#             }
            
#             # Format phone number (add country code if needed)
#             # Assuming Indian numbers - adjust as needed
#             # if to_phone.len(to_phone) == 10:
#             #     to_phone = '91' + to_phone
            
#             payload = {
#                 "messaging_product": "whatsapp",
#                 "to": to_phone,
#                 "type": "text",
#                 "text": {
#                     "body": message
#                 }
#             }
            
#             response = requests.post(self.base_url, json=payload, headers=headers)
            
#             if response.status_code == 200:
#                 print(f"WhatsApp message sent to {to_phone}")
#                 return True
#             else:
#                 print(f"WhatsApp API error: {response.status_code} - {response.text}")
#                 return False
                
#         except Exception as e:
#             print(f"Error sending WhatsApp message: {str(e)}")
#             return False
    
#     def send_attendance_reminder(self, to_phone, name, week):
#         """
#         Send formatted attendance reminder via WhatsApp
#         """
#         message = f"""Hello {name},

# 📊 Attendance Reminder

# This is a friendly reminder to submit your attendance for week {week}.

# Please log in to the system and complete your attendance at your earliest convenience.

# Thank you!"""
        
#         return self.send_message(to_phone, message)

# # Create global instance
# whatsapp_service = WhatsAppService()