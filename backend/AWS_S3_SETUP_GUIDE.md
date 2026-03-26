# AWS S3 Integration for QR Codes - Complete Setup Guide

## ✅ IMPLEMENTATION COMPLETE

All code changes have been implemented. Now you need to configure your AWS credentials.

---

## 📋 Quick Setup Checklist

- [ ] Create AWS S3 bucket
- [ ] Create IAM user with S3 access
- [ ] Update `.env` with AWS credentials
- [ ] Enable S3 in `.env`
- [ ] Test SMS with QR code

---

## 🚀 Step-by-Step AWS Setup

### **Step 1: Create S3 Bucket**

1. Go to [AWS Console - S3](https://s3.console.aws.amazon.com/s3/buckets)
2. Click **"Create Bucket"**
3. **Bucket Name**: `digitaldemocracy-qr-codes` (must be globally unique)
4. **Region**: `us-east-1` (or your preferred region)
5. **Block Public Access Settings**:
   - ✓ Uncheck all "Block public access" options
   - Click "I acknowledge that..."
6. Click **"Create Bucket"**

---

### **Step 2: Create Bucket Policy (Allow Public Read)**

1. Go to your new bucket → **"Permissions"** tab
2. Click **"Bucket Policy"**
3. Paste this policy (replace `YOUR-BUCKET-NAME`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
```

4. Click **"Save"**

**Example for your bucket:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::digitaldemocracy-qr-codes/*"
    }
  ]
}
```

---

### **Step 3: Create IAM User**

1. Go to [AWS Console - IAM](https://console.aws.amazon.com/iam/home)
2. Click **"Users"** → **"Create user"**
3. **User Name**: `digital-democracy-app`
4. Click **"Next"**
5. Click **"Attach policies directly"**
6. Search for and select: **`AmazonS3FullAccess`**
7. Click **"Create user"**

---

### **Step 4: Create Access Keys**

1. Click on your new user: `digital-democracy-app`
2. Click **"Security credentials"** tab
3. Click **"Create access key"**
4. Select: **"Application running outside AWS"**
5. Click **"Next"** → **"Create access key"**
6. **IMPORTANT**: Copy and save:
   - ✅ `Access Key ID`
   - ✅ `Secret Access Key`

⚠️ **You can only see the secret key ONCE! Save it securely!**

---

### **Step 5: Update .env with AWS Credentials**

Edit `backend/.env` and update these lines:

```bash
# Change from:
USE_S3_FOR_QR=false
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY
AWS_S3_BUCKET_NAME=digitaldemocracy-qr-codes

# To:
USE_S3_FOR_QR=true
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_S3_BUCKET_NAME=digitaldemocracy-qr-codes
AWS_S3_REGION=us-east-1
AWS_S3_UPLOAD_DIR=qr-codes
```

---

## 🧪 Testing

### **Test 1: Test WITHOUT S3 (Local Storage)**

Keep `USE_S3_FOR_QR=false` and run:

```bash
curl -X POST 'http://127.0.0.1:8000/sms/send-ticket' \
  -H 'Content-Type: application/json' \
  -d '{
    "to": "+918901075231",
    "custom_text": "Your ticket has been created",
    "ticket_id": "TICKET-001",
    "session_id": "session-001",
    "qr_link": "https://track.yourapp.com/ticket/TICKET-001",
    "include_qr_image": false
  }'
```

**Expected Result**: SMS sends successfully ✅

---

### **Test 2: Enable S3 and Test**

1. Update `.env`:

   ```
   USE_S3_FOR_QR=true
   AWS_ACCESS_KEY_ID=YOUR_KEY
   AWS_SECRET_ACCESS_KEY=YOUR_SECRET
   AWS_S3_BUCKET_NAME=digitaldemocracy-qr-codes
   ```

2. Restart backend (changes to .env trigger reload)

3. Send request WITH QR Image:

```bash
curl -X POST 'http://127.0.0.1:8000/sms/send-ticket' \
  -H 'Content-Type: application/json' \
  -d '{
    "to": "+918901075231",
    "custom_text": "Your ticket with QR code",
    "ticket_id": "TICKET-002",
    "session_id": "session-002",
    "qr_link": "https://track.yourapp.com/ticket/TICKET-002",
    "include_qr_image": true
  }'
```

**Expected Response**:

```json
{
  "success": true,
  "to": "+918901075231",
  "ticket_id": "TICKET-002",
  "body": "Your ticket with QR code\nTicket ID: TICKET-002\n...",
  "media_url": "https://s3-api-response.twilio.com/...",
  "status": "queued",
  "sid": "SM..."
}
```

---

## 📂 File Changes Made

| File                         | Change                               |
| ---------------------------- | ------------------------------------ |
| `requirements.txt`           | Added `boto3>=1.26.0`                |
| `app/config.py`              | Added AWS S3 configuration variables |
| `app/services/s3_service.py` | **NEW** - S3 upload/delete functions |
| `app/services/qr_service.py` | Updated to support S3 uploads        |
| `app/routes/sms_routes.py`   | Updated to handle S3 URLs            |
| `.env`                       | Added AWS S3 configuration           |

---

## 🔧 Environment Variables Reference

```bash
# Enable S3 storage (set to true after credentials are added)
USE_S3_FOR_QR=true|false

# AWS Credentials (from IAM user)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# S3 Bucket Details
AWS_S3_BUCKET_NAME=digitaldemocracy-qr-codes
AWS_S3_REGION=us-east-1
AWS_S3_UPLOAD_DIR=qr-codes
```

---

## ✅ Features

- ✅ Automatic S3 upload for QR codes
- ✅ Fallback to local storage if S3 fails
- ✅ Public URL generation for Twilio
- ✅ Timestamped filenames to avoid collisions
- ✅ Configurable S3 prefix/folder
- ✅ Delete functionality available
- ✅ No ngrok URL needed - permanent URLs

---

## 📊 How It Works

```
1. User creates complaint
2. Endpoint generates QR code in memory
3. QR code uploaded to S3 (or saved locally)
4. Public S3 URL generated
5. SMS sent via Twilio with media URL
6. Twilio fetches QR code from S3
7. SMS delivered with QR code attachment
```

---

## 🆘 Troubleshooting

### **S3 Upload Fails**

- Check AWS credentials in `.env`
- Verify bucket exists
- Check bucket policy allows public read
- Check IAM user has S3FullAccess permission

### **SMS Still Shows Error 11200**

- Verify `USE_S3_FOR_QR=true`
- Check S3 bucket name matches in `.env`
- Test S3 URL manually in browser (should show QR image)
- Check AWS_S3_REGION matches bucket region

### **Can't Create IAM User**

- Make sure you're logged into AWS as root or admin
- You need "IAM" permissions

### **Access Key Not Showing**

- You can only see it once!
- If lost, delete the key and create a new one

---

## 💡 Production Tips

1. **Use Regional Bucket**: Choose S3 region closest to your users
2. **Enable Versioning**: In bucket settings for backup
3. **Use CloudFront**: CDN for faster QR code delivery
4. **Set Expiration**: Delete old QR codes after 30 days
5. **Enable Logging**: Track S3 access for debugging

---

## ✅ Status

**Implementation**: Complete ✓
**Code Changes**: Done ✓
**Files Modified**: 6 files ✓
**Ready for Configuration**: Yes ✓

**Next Step**: Add your AWS credentials to `.env` and test!
