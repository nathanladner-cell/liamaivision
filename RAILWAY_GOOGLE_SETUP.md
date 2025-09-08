# Railway Google Cloud Setup Instructions

## Setting up Google Cloud Vision for Hybrid Scanner

To enable the hybrid Google Vision + OpenAI scanner on Railway, you need to set up the Google Cloud credentials as an environment variable.

### Steps:

1. **Go to your Railway project dashboard**
   - Navigate to: https://railway.app/dashboard
   - Select your project: `upbeat-gratitude`

2. **Go to Variables tab**
   - Click on the "Variables" tab in your project

3. **Add Google Cloud Credentials**
   - Click "New Variable"
   - **Variable Name**: `GOOGLE_CLOUD_CREDENTIALS_JSON`
   - **Variable Value**: Copy the ENTIRE contents of `crucial-bloom-413616-9b1e75106f6e.json` (the JSON should be on one line)

### JSON Content to Copy:

**Copy the ENTIRE contents of your local `crucial-bloom-413616-9b1e75106f6e.json` file**

The JSON should be formatted as a single line (no line breaks) and contain all the service account information including:
- type
- project_id  
- private_key_id
- private_key
- client_email
- client_id
- auth_uri
- token_uri
- etc.

**Important**: Make sure to copy it exactly as one continuous JSON string.

4. **Save the variable**
   - Click "Add" to save the environment variable

5. **Redeploy**
   - The app should automatically redeploy with the new environment variable
   - If not, trigger a manual redeploy

### Verification:

After deployment, visit your app and check:
- The header should show "🔍 Google Vision + 🧠 OpenAI = Maximum Accuracy"
- The status endpoint should show `hybrid_ready: true`
- Analysis should show "hybrid" method and OCR character counts

### Security Note:

This approach keeps the credentials secure in Railway's environment variables instead of committing them to your Git repository, which is the recommended security practice.
