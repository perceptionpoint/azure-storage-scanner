Azure Blob storage scanner

Requirements:
- Function App with App service plan. Consumption isn't working well with triggers. Any existing App service plan can also be used B1 instance can also be used.
- VS Code to upload function to Azure Functions with Azure Extension.

Installation:
- Clone repo and open it with VS code (or send a zip to the customer).
- Modify function.json line 9 "path" option and type your Container name (bucket)
- Switch to the Azure extension in VS Code, Login and find your Function App. Click on "Application Settings". Add the following settings:
  * PP_TOKEN - token provided by Perception Point
  * PP_ENV - us-east-1 or eu-west-1 depending on where your customer account was originally created
  * AZURE_STORAGE_CONNECTION_STRING - Storage Account connection string located in "Access keys" section of your Storage Account settings page.
- Right-Click on your Function App and click on "Deploy to Function App..."
