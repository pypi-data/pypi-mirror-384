import aiohttp
from fastapi import HTTPException
from token_service_toolkit import TokenService  

class EmailService:
    """
    Async email service to send emails via Microsoft Graph API.
    """

    def __init__(self, token_service: TokenService, sender_email: str, graph_base_url: str):
        """
        :param token_service: Instance of TokenService for fetching Graph API tokens.
        :param sender_email: Email address to send from.
        :param graph_base_url: Base URL for Microsoft Graph API.
        """
        if not isinstance(token_service, TokenService):
            raise ValueError("token_service must be an instance of TokenService")
        
        self.token_service = token_service
        self.sender_email = sender_email
        self.graph_base_url = graph_base_url

    async def send_email(
        self,
        to_emails: list[str],
        subject: str,
        html_body: str,
        cc_emails: list[str] = None,
        bcc_emails: list[str] = None,
        attachments: list[dict] = None,
        timeout_seconds: int = 15
    ):
        if not to_emails:
            return {"status": "failed", "reason": "No recipients"}

        message = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [{"emailAddress": {"address": e}} for e in to_emails],
        }

        if cc_emails:
            message["ccRecipients"] = [{"emailAddress": {"address": e}} for e in cc_emails]
        if bcc_emails:
            message["bccRecipients"] = [{"emailAddress": {"address": e}} for e in bcc_emails]
        if attachments:
            message["attachments"] = attachments

        payload = {"message": message, "saveToSentItems": True}

        try:
            # Use the TokenService instance to fetch the access token
            token = await self.token_service.get_access_token()
            url = f"{self.graph_base_url}/users/{self.sender_email}/sendMail"
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                ) as response:
                    if response.status == 202:
                        return {"status": "success"}
                    text = await response.text()
                    return {
                        "status": "failed",
                        "response_code": response.status,
                        "response_text": text
                    }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
