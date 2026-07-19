import os
import time
import asyncio
from typing import Optional
from twilio.rest import Client
from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.db.models import Alert
from app.services.risk_scorer import RiskAssessment

# In-memory rate limiting dict: { job_id: last_alert_timestamp }
rate_limit_store = {}

class AlertService:
    def __init__(self):
        # Initialize Twilio client
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            print("Twilio client configured successfully.")
        else:
            self.client = None
            
        self.include_media = os.getenv("INCLUDE_MEDIA", "False").lower() in ("true", "1", "yes")

    def trigger_voice_call(self, assessment: RiskAssessment, location: str) -> Optional[str]:
        if not self.client:
            print("Twilio client not configured. Skipping voice call.")
            return None
            
        factor = assessment.contributing_factors[0] if assessment.contributing_factors else "Multiple high-risk factors."
        
        twiml = f"""
        <Response>
            <Say voice="Polly.Aditi">
                FALCON AI Alert. Severity: {assessment.severity}. Location: {location}.
                Estimated crowd density and convergence pattern indicate: {factor}.
                Please check the dashboard immediately.
            </Say>
        </Response>
        """
        
        try:
            call = self.client.calls.create(
                twiml=twiml,
                to=settings.MY_PHONE_NUMBER,
                from_=settings.TWILIO_PHONE_NUMBER
            )
            return call.sid
        except Exception as e:
            print(f"Error triggering voice call: {e}")
            return None

    def trigger_whatsapp_alert(self, assessment: RiskAssessment, location: str, snapshot_url: str, dashboard_url: str) -> Optional[str]:
        if not self.client:
            print("Twilio client not configured. Skipping WhatsApp alert.")
            return None
            
        factors_str = "\n- ".join(assessment.contributing_factors) if assessment.contributing_factors else "Elevated risk"
        
        message_body = (
            f"🚨 *FALCON AI - CRITICAL CROWD ALERT* 🚨\n\n"
            f"*Severity*: {assessment.severity}\n"
            f"*Location*: {location}\n"
            f"*Time*: Frame {assessment.frame_index}\n\n"
            f"*Factors*:\n- {factors_str}\n\n"
            f"Please check dashboard immediately:\n{dashboard_url}"
        )
        
        try:
            kwargs = {
                "body": message_body,
                "from_": f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                "to": f"whatsapp:{settings.MY_PHONE_NUMBER}"
            }
            if self.include_media and snapshot_url:
                kwargs["media_url"] = [snapshot_url]
                
            msg = self.client.messages.create(**kwargs)
            return msg.sid
        except Exception as e:
            print(f"Error triggering WhatsApp: {e}")
            return None

    async def _log_alert(self, incident_id: str, channel: str, sid: Optional[str]):
        async with AsyncSessionLocal() as session:
            new_alert = Alert(
                incident_id=incident_id,
                channel=channel,
                status="SENT" if sid else "FAILED",
                external_sid=sid or ""
            )
            session.add(new_alert)
            await session.commit()

    def trigger_all(self, job_id: str, assessment: RiskAssessment, location: str, snapshot_url: str, dashboard_url: str):
        # Rate limiting: 60 seconds per job_id
        now = time.time()
        last_time = rate_limit_store.get(job_id, 0.0)
        if now - last_time < 60.0:
            print(f"Alert suppressed for {job_id} due to rate limiting (last alert {int(now - last_time)}s ago).")
            return
            
        rate_limit_store[job_id] = now
        
        print(f"Triggering alerts for job {job_id}...")
        
        call_sid = self.trigger_voice_call(assessment, location)
        msg_sid = self.trigger_whatsapp_alert(assessment, location, snapshot_url, dashboard_url)
        
        # Log to DB
        try:
            asyncio.run(self._log_alert(job_id, "VOICE", call_sid))
            asyncio.run(self._log_alert(job_id, "WHATSAPP", msg_sid))
        except RuntimeError:
            asyncio.ensure_future(self._log_alert(job_id, "VOICE", call_sid))
            asyncio.ensure_future(self._log_alert(job_id, "WHATSAPP", msg_sid))

    def trigger_alert(
        self,
        event_type: str,
        confidence: float,
        message: str,
        metadata: Optional[dict] = None
    ):
        metadata = metadata or {}
        job_id = metadata.get("job_id", "unknown_job")
        location = metadata.get("location", "Unknown Location")
        dashboard_url = metadata.get("dashboard_url", "")
        snapshot_url = metadata.get("snapshot_url", "")

        now = time.time()
        last_time = rate_limit_store.get(job_id, 0.0)
        if now - last_time < 60.0:
            print(f"Alert suppressed for {job_id} due to rate limiting.")
            return

        rate_limit_store[job_id] = now
        print(f"Triggering {event_type} alerts for job {job_id}...")

        # 1. Voice Call
        call_sid = None
        if self.client:
            twiml = f"""
            <Response>
                <Say voice="Polly.Aditi">
                    FALCON AI Alert. CRITICAL {event_type.upper()} DETECTED.
                    Confidence is {confidence * 100:.1f} percent.
                    {message}
                </Say>
            </Response>
            """
            try:
                call = self.client.calls.create(
                    twiml=twiml,
                    to=settings.MY_PHONE_NUMBER,
                    from_=settings.TWILIO_PHONE_NUMBER
                )
                call_sid = call.sid
            except Exception as e:
                print(f"Error triggering voice call: {e}")

        # 2. WhatsApp Message
        msg_sid = None
        if self.client:
            message_body = (
                f"🚨 *FALCON AI - CRITICAL {event_type.upper()} ALERT* 🚨\n\n"
                f"*Confidence*: {confidence * 100:.1f}%\n"
                f"*Location*: {location}\n\n"
                f"*Message*:\n{message}\n\n"
            )
            if dashboard_url:
                message_body += f"Please check dashboard immediately:\n{dashboard_url}"

            try:
                kwargs = {
                    "body": message_body,
                    "from_": f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                    "to": f"whatsapp:{settings.MY_PHONE_NUMBER}"
                }
                if self.include_media and snapshot_url:
                    kwargs["media_url"] = [snapshot_url]
                    
                msg = self.client.messages.create(**kwargs)
                msg_sid = msg.sid
            except Exception as e:
                print(f"Error triggering WhatsApp: {e}")

        # 3. Log to DB
        try:
            asyncio.run(self._log_alert(job_id, "VOICE", call_sid))
            asyncio.run(self._log_alert(job_id, "WHATSAPP", msg_sid))
        except RuntimeError:
            asyncio.ensure_future(self._log_alert(job_id, "VOICE", call_sid))
            asyncio.ensure_future(self._log_alert(job_id, "WHATSAPP", msg_sid))
