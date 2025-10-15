class TemplateService:
    """
    Service to fetch and format email templates from blob storage or JSON config.
    """

    def __init__(self, blob_config_service, config_blob_name="subject.json"):
        self.blob_config_service = blob_config_service
        self.config = self.blob_config_service.get_json(config_blob_name)

    async def get_email_template(self, key: str, **kwargs):
        if key not in self.config:
            raise ValueError(f"Email template '{key}' not found")

        subject = self.config[key].get("subject", "").format(**kwargs)
        body = self.config[key].get("body", "").format(**kwargs)
        return subject, body

    def _create_failure_details_html(self, failures: list[dict]):
        if not failures:
            return ""
        rows = "".join(
            f"<tr><td>{f.get('name')}</td><td>{f.get('reason')}</td></tr>" for f in failures
        )
        return f"<table border='1'>{rows}</table>"
