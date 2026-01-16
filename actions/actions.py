#actions.yml
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.forms import FormValidationAction


class ValidateReclamationForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_reclamation_form"

    async def validate_email(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate email slot."""
        if not slot_value or not str(slot_value).strip():
            return {"email": None}

        email = str(slot_value).strip()

        if '@' not in email or '.' not in email:
            dispatcher.utter_message(
                text="Please provide a valid email address (e.g., name@example.com)."
            )
            return {"email": None}

        return {"email": email}

    async def validate_phone(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate phone slot."""
        if not slot_value or not str(slot_value).strip():
            return {"phone": None}

        phone = str(slot_value).strip()

        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) < 5:
            dispatcher.utter_message(
                text="Please provide a valid phone number with at least 5 digits."
            )
            return {"phone": None}

        return {"phone": phone}

    async def validate_username(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate username slot."""
        if not slot_value or len(str(slot_value).strip()) < 2:
            dispatcher.utter_message(text="Please provide a valid username (at least 2 characters).")
            return {"username": None}

        username = str(slot_value).strip()

        if username.isdigit():
            dispatcher.utter_message(
                text="That looks like a reclamation ID. Please provide your username instead."
            )
            return {"username": None}

        return {"username": username}

    async def validate_reclamation_message(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate reclamation message slot."""
        if not slot_value or len(str(slot_value).strip()) < 10:
            dispatcher.utter_message(
                text="Please provide more details about your issue (at least 10 characters)."
            )
            return {"reclamation_message": None}

        return {"reclamation_message": str(slot_value).strip()}


class ActionSubmitReclamation(Action):
    def name(self) -> Text:
        return "action_submit_reclamation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get all slots
        username = tracker.get_slot("username")
        reclamation_message = tracker.get_slot("reclamation_message")
        email = tracker.get_slot("email")
        phone = tracker.get_slot("phone")

        # Build data for Django
        data = {
            "username": username if username else "Anonymous",
            "message": reclamation_message if reclamation_message else "",
            "category": "Rasa Bot",
            "location": "Rasa Chat Interface"
        }

        # Add email if available
        if email and str(email).strip():
            data["email"] = str(email).strip()

        # Add phone if available
        if phone and str(phone).strip():
            data["phone"] = str(phone).strip()

        try:
            import requests

            response = requests.post(
                "http://localhost:8000/api/reclamations/add/",
                json=data,
                timeout=10
            )

            if response.status_code == 201:
                response_data = response.json()
                reclamation_id = response_data.get("id", "Unknown")

                # Get analysis results
                priority = response_data.get("priority", "normal").upper()
                sentiment = response_data.get("sentiment", "neutral").capitalize()

                # Build contact info for display
                contact_info = ""
                if email and str(email).strip():
                    contact_info += f"\n📧 Email: {email}"
                if phone and str(phone).strip():
                    contact_info += f"\n📞 Phone: {phone}"

                # Build success message
                success_message = (
                    f"✅ Reclamation submitted successfully!{contact_info}\n\n"
                    f" **Reclamation ID:** #{reclamation_id}\n"
                    f" **Username:** {username}\n"
                    f" **Issue:** {reclamation_message[:100]}...\n"
                    f" **Priority:** {priority}\n"
                    f" **Sentiment:** {sentiment}\n\n"
                    f"We will review your issue and contact you soon."
                )

                dispatcher.utter_message(text=success_message)
                return [SlotSet("reclamation_id", str(reclamation_id))]

            else:
                dispatcher.utter_message(
                    text=f"❌ Error submitting reclamation. Please try again."
                )

        except Exception:
            dispatcher.utter_message(
                text="❌ Could not connect to server. Please try again later."
            )

        return []




