import asyncio
from universal_mcp.agentr import AgentrIntegration
from universal_mcp.applications.outlook import OutlookApp

async def main():
    """
    Lists attachments for a specific email and reads the content of the first attachment.
    """
    integration = AgentrIntegration(name="outlook")
    outlook_app = OutlookApp(integration=integration)
    
    message_id = "AQMkADA0ZTgyZDFjLWM1ODUtNGRiNy1hOWUzLTJhZTNmYTlhYzY4ZQBGAAAD6L6bViLO4U2MOssjvBYsMwcAdjsC31mYRU2oinxOMukhHgAAAgEMAAAAdjsC31mYRU2oinxOMukhHgAAAgVYAAAA"

    try:
        print(f"Listing attachments for message ID: {message_id}...")
        attachments_response = outlook_app.list_email_attachments(message_id=message_id)
        attachments = attachments_response.get("value", [])

        if not attachments:
            print("No attachments found for this email.")
            return

        print(f"Found {len(attachments)} attachment(s):")
        for i, attachment in enumerate(attachments):
            print(f"  {i+1}. Name: {attachment.get('name')}")
            print(f"     ID: {attachment.get('id')}")
            print(f"     Content Type: {attachment.get('contentType')}")
            print(f"     Size: {attachment.get('size')} bytes")

        # Get content of the first attachment
        first_attachment_id = attachments[0].get("id")
        if first_attachment_id:
            print(f"\nReading content of the first attachment (ID: {first_attachment_id})...")
            attachment_details = outlook_app.get_attachment(
                message_id=message_id,
                attachment_id=first_attachment_id
            )
            
            print("Successfully retrieved attachment content in Gemini format:")
            print(f"  Type: {attachment_details.get('type')}")
            print(f"  File Name: {attachment_details.get('file_name')}")
            print(f"  MIME Type: {attachment_details.get('mime_type')}")
            
            content_bytes_b64 = attachment_details.get("data")
            if content_bytes_b64:
                print(f"  Data (first 60 chars of base64): {content_bytes_b64[:60]}...")
            else:
                print("  Attachment data was not found in the response.")
        else:
            print("Could not get ID of the first attachment.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
