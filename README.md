Azure Blob storage scanner

Requirements:
  - V2 storage account. If your storage account uses v1, please upgrade.
  - Function App with App service plan. Consumption isn't working well with triggers. Any existing App service plan can also be used. B1 instance can also be used.
- VS Code to upload function to Azure Functions with Azure Extension.

 Installation:
 - Clone repo and open it with VS code (or send a zip to the customer).
 - Modify function.js line 9 "path" option and type in your container
 - Go to the Azure Extension, Login and go to "Application Settings" Add the following settings:
   * PP_TOKEN - token provided by Perception Point
   * PP_ENV - us-east-1 or eu-west-1 depending on where your customer account was originally created
   * AZURE_STORAGE_CONNECTION_STRING - Storage Account access key connection string located in "Access keys" section of your Storage Account settings page.
 - Click "Deploy to Function App..." button