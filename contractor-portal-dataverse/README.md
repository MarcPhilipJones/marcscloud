# Contractor Portal for Dynamics 365 Field Service

A local web-based contractor portal that connects to Dynamics 365 Field Service (Dataverse) via OAuth client credentials. Shows bookings and linked work orders for a specific contractor (Bookable Resource), with the ability to:

- View all bookings (past, upcoming, or all)
- View work order details
- **Edit** Work Order System Status
- **Edit** Work Order Summary
- **Edit** Account Instructions (on the Service Account)
- Upload photos to Work Orders (as Note attachments)

## Prerequisites

- **Node.js 18+** (for native `fetch` support)
- **Azure AD App Registration** with:
  - Client credentials (client secret)
  - API permissions for Dynamics 365 CRM (`user_impersonation` or application permissions)
- **Dynamics 365 Field Service** environment

## Quick Start

### 1. Clone/Download the project

```bash
cd contractor-portal-dataverse
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment

Copy the example environment file and edit with your values:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit `.env` with your Dataverse credentials:

```env
DATAVERSE_BASE_URL=https://yourorg.crm.dynamics.com
TENANT_ID=your-tenant-id
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
CONTRACTOR_RESOURCE_ID=your-bookable-resource-guid
PORT=3000
```

### 4. Start the server

```bash
npm start
# or
npm run dev
```

### 5. Open in browser

Navigate to: **http://localhost:3000**

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATAVERSE_BASE_URL` | Your Dataverse environment URL (no trailing slash) | `https://org6cb3e9fb.crm4.dynamics.com` |
| `TENANT_ID` | Azure AD tenant ID | `996f568a-cc69-450a-b684-ae784069e679` |
| `CLIENT_ID` | App registration client ID | `beb6cb7d-3328-4c2f-be9a-aab746be614a` |
| `CLIENT_SECRET` | App registration client secret | `mVc8Q~...` |
| `CONTRACTOR_RESOURCE_ID` | The Bookable Resource GUID for the contractor | `303c022d-6cfb-f011-8406-7ced8d4279eb` |
| `PORT` | Server port (optional, default 3000) | `3000` |

### Changing the Contractor

To change which contractor's bookings are displayed, update the `CONTRACTOR_RESOURCE_ID` in your `.env` file with the GUID of a different Bookable Resource.

To find the GUID:
1. Open Dynamics 365 Field Service
2. Navigate to Resources → Bookable Resources
3. Open the contractor record
4. Copy the GUID from the URL

### Schema Map

If your Field Service environment uses different field names, you can adjust the schema mapping at the top of `server.js`:

```javascript
const SCHEMA = {
    workOrder: {
        summary: 'msdyn_workordersummary',        // Change if different
        instructions: 'msdyn_instructions',       // Change if different
        // ... other fields
    },
    account: {
        workOrderInstructions: 'msdyn_workorderinstructions'  // Change if different
    },
    // ... other entities
};
```

## Project Structure

```
contractor-portal-dataverse/
├── server.js           # Express server with Dataverse proxy
├── package.json        # Dependencies and scripts
├── .env                # Your environment configuration (gitignored)
├── .env.example        # Template for environment configuration
├── .gitignore          # Git ignore rules
├── README.md           # This file
└── public/             # Static front-end files
    ├── index.html      # Main HTML page
    ├── styles.css      # CSS styles (Contoso branding)
    └── app.js          # Front-end JavaScript
```

## API Endpoints

The server exposes these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/contractor` | Get contractor info |
| `GET` | `/api/bookings?view=all\|upcoming\|past` | Get bookings for contractor |
| `GET` | `/api/workorders/:id` | Get work order details |
| `PATCH` | `/api/workorders/:id/status` | Update system status |
| `PATCH` | `/api/workorders/:id/summary` | Update summary field |
| `PATCH` | `/api/accounts/:id/instructions` | Update account instructions |
| `POST` | `/api/workorders/:id/photos` | Upload photo attachment |
| `GET` | `/api/annotations/:id/content` | Get photo content |
| `GET` | `/api/metadata/systemstatus` | Get system status options |

## Features

### Bookings List (Left Panel)
- Shows all bookings for the contractor
- Filter by: All / Upcoming / Past
- Displays: Date, time, booking status, work order number, service account, address

### Work Order Detail (Right Panel)
- Read-only fields: Service Account, Address, Incident Type, Created Date, Instructions
- **Editable: System Status** - Dropdown with all status options
- **Editable: Summary** - Multi-line text field
- **Editable: Account Instructions** - Multi-line text (saved to the Service Account record)
- **Photo Upload** - Upload JPG/PNG photos (max 10MB), stored as annotations

## Troubleshooting

### "Failed to get access token"
- Verify your `CLIENT_ID`, `CLIENT_SECRET`, and `TENANT_ID` are correct
- Ensure the app registration has the correct API permissions
- Check that the client secret hasn't expired

### "No bookings found"
- Verify the `CONTRACTOR_RESOURCE_ID` is correct
- Check that the bookable resource has bookings assigned in Field Service
- Try a different contractor resource ID

### "Cannot update field"
- Ensure the app registration has write permissions
- Verify the field names in the schema map match your environment

## Hosting Options

### Local Development (Recommended)
The server runs locally and serves both the API and static files. This is the simplest setup for demos.

### Separate Hosting
If you need to host the front-end separately (e.g., GitHub Pages):
1. Update `public/app.js` to point to your hosted API URL
2. Enable CORS in `server.js`
3. Host the API proxy on a server that can store secrets securely

**Note:** Never expose client secrets in front-end code.

## License

MIT License

## Support

This is a demo application for presales purposes. For production use, consider:
- Adding proper authentication for the front-end
- Implementing rate limiting
- Adding logging and monitoring
- Using Azure Key Vault for secrets
