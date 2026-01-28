/**
 * Contractor Portal for Dynamics 365 Field Service
 * 
 * This server acts as an API proxy between the front-end and Dataverse,
 * handling OAuth client credentials authentication.
 * 
 * SCHEMA MAP - Adjust these if your Field Service environment uses different field names
 */

require('dotenv').config();
const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

// =============================================================================
// SCHEMA MAP - Edit these values if your environment uses different field names
// =============================================================================
const SCHEMA = {
    // Entity logical names
    entities: {
        workOrder: 'msdyn_workorder',
        booking: 'bookableresourcebooking',
        bookableResource: 'bookableresource',
        account: 'account',
        annotation: 'annotation'
    },

    // Work Order fields
    workOrder: {
        id: 'msdyn_workorderid',
        name: 'msdyn_name',                           // Work Order Number
        systemStatus: 'msdyn_systemstatus',           // System Status (picklist)
        summary: 'msdyn_workordersummary',            // "Summary" field - EDITABLE
        instructions: 'msdyn_instructions',           // Instructions on Work Order
        serviceAccount: 'msdyn_serviceaccount',       // Service Account lookup
        primaryIncidentType: 'msdyn_primaryincidenttype',
        primaryIncidentDescription: 'msdyn_primaryincidentdescription',
        address: 'msdyn_address1',                    // Service address if available
        priority: 'msdyn_priority',
        createdOn: 'createdon',
        modifiedOn: 'modifiedon'
    },

    // Account fields (Service Account)
    account: {
        id: 'accountid',
        name: 'name',
        workOrderInstructions: 'msdyn_workorderinstructions'  // "Account Instructions" - EDITABLE
    },

    // Booking fields
    booking: {
        id: 'bookableresourcebookingid',
        name: 'name',
        startTime: 'starttime',
        endTime: 'endtime',
        duration: 'duration',
        resource: 'resource',                         // Bookable Resource lookup
        workOrder: 'msdyn_workorder',                 // Work Order lookup
        bookingStatus: 'bookingstatus'                // Booking Status lookup
    },

    // System Status values (from msdyn_systemstatus optionset)
    // These match your environment's actual values
    systemStatusOptions: [
        { value: 690970000, label: 'Unscheduled' },
        { value: 690970001, label: 'Scheduled' },
        { value: 690970002, label: 'In Progress' },
        { value: 690970003, label: 'Completed' },
        { value: 690970004, label: 'Posted' },
        { value: 690970005, label: 'Canceled' }
    ]
};

// =============================================================================
// CONFIGURATION
// =============================================================================
const config = {
    dataverseUrl: process.env.DATAVERSE_BASE_URL,
    tenantId: process.env.TENANT_ID,
    clientId: process.env.CLIENT_ID,
    clientSecret: process.env.CLIENT_SECRET,
    contractorResourceId: process.env.CONTRACTOR_RESOURCE_ID,
    port: process.env.PORT || 3000,
    apiVersion: 'v9.2'
};

// Validate configuration
const requiredEnvVars = ['DATAVERSE_BASE_URL', 'TENANT_ID', 'CLIENT_ID', 'CLIENT_SECRET', 'CONTRACTOR_RESOURCE_ID'];
for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
        console.error(`ERROR: Missing required environment variable: ${envVar}`);
        process.exit(1);
    }
}

// =============================================================================
// TOKEN MANAGEMENT
// =============================================================================
let cachedToken = null;
let tokenExpiry = null;

async function getAccessToken() {
    // Return cached token if still valid (with 5 minute buffer)
    if (cachedToken && tokenExpiry && Date.now() < tokenExpiry - 300000) {
        return cachedToken;
    }

    const tokenUrl = `https://login.microsoftonline.com/${config.tenantId}/oauth2/v2.0/token`;
    
    const body = new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: config.clientId,
        client_secret: config.clientSecret,
        scope: `${config.dataverseUrl}/.default`
    });

    try {
        const response = await fetch(tokenUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: body.toString()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(`Token error: ${error.error_description || error.error}`);
        }

        const data = await response.json();
        cachedToken = data.access_token;
        tokenExpiry = Date.now() + (data.expires_in * 1000);
        
        console.log('Access token acquired, expires in', data.expires_in, 'seconds');
        return cachedToken;
    } catch (error) {
        console.error('Failed to get access token:', error.message);
        throw error;
    }
}

// =============================================================================
// DATAVERSE API HELPER
// =============================================================================
async function dataverseRequest(method, endpoint, body = null) {
    const token = await getAccessToken();
    const url = `${config.dataverseUrl}/api/data/${config.apiVersion}/${endpoint}`;
    
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
        'OData-Version': '4.0',
        'OData-MaxVersion': '4.0',
        'Prefer': 'odata.include-annotations="*"'
    };

    if (body) {
        headers['Content-Type'] = 'application/json; charset=utf-8';
    }

    const options = {
        method,
        headers
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    console.log(`Dataverse ${method}: ${endpoint}`);

    const response = await fetch(url, options);
    
    // Handle different response types
    if (response.status === 204) {
        return { success: true };
    }

    const contentType = response.headers.get('content-type');
    
    if (!response.ok) {
        let errorMessage = `Dataverse error: ${response.status} ${response.statusText}`;
        if (contentType && contentType.includes('application/json')) {
            const errorData = await response.json();
            errorMessage = errorData.error?.message || errorMessage;
        }
        throw new Error(errorMessage);
    }

    if (contentType && contentType.includes('application/json')) {
        return await response.json();
    }

    return { success: true };
}

// Handle paging for large result sets
async function dataverseRequestWithPaging(endpoint) {
    let allResults = [];
    let nextLink = endpoint;
    let pageCount = 0;
    const maxPages = 10; // Safety limit

    while (nextLink && pageCount < maxPages) {
        const result = await dataverseRequest('GET', nextLink);
        
        if (result.value) {
            allResults = allResults.concat(result.value);
        }

        // Check for next page
        nextLink = result['@odata.nextLink'];
        if (nextLink) {
            // Extract just the relative path for subsequent requests
            nextLink = nextLink.replace(`${config.dataverseUrl}/api/data/${config.apiVersion}/`, '');
        }
        pageCount++;
    }

    return allResults;
}

// =============================================================================
// EXPRESS APP SETUP
// =============================================================================
const app = express();
app.use(express.json());

// Serve static files from /public
app.use(express.static(path.join(__dirname, 'public')));

// Configure multer for file uploads (10MB limit, single file)
const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
    fileFilter: (req, file, cb) => {
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
        if (allowedTypes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error('Only JPG, JPEG, and PNG files are allowed'));
        }
    }
});

// =============================================================================
// API ENDPOINTS
// =============================================================================

// Health check
app.get('/api/health', async (req, res) => {
    try {
        // Test Dataverse connection
        await getAccessToken();
        res.json({
            status: 'healthy',
            dataverseUrl: config.dataverseUrl,
            contractorResourceId: config.contractorResourceId,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.status(500).json({
            status: 'unhealthy',
            error: error.message
        });
    }
});

// Get contractor info
app.get('/api/contractor', async (req, res) => {
    try {
        const endpoint = `bookableresources(${config.contractorResourceId})?$select=name,bookableresourceid,resourcetype`;
        const result = await dataverseRequest('GET', endpoint);
        
        res.json({
            id: result.bookableresourceid,
            name: result.name,
            resourceType: result.resourcetype,
            resourceTypeName: result['resourcetype@OData.Community.Display.V1.FormattedValue'] || getResourceTypeName(result.resourcetype)
        });
    } catch (error) {
        console.error('Error fetching contractor:', error);
        res.status(500).json({ error: error.message });
    }
});

function getResourceTypeName(type) {
    const types = { 1: 'Generic', 2: 'Contact', 3: 'User', 4: 'Equipment', 5: 'Account', 6: 'Crew', 7: 'Facility', 8: 'Pool' };
    return types[type] || 'Unknown';
}

// Get bookings for the contractor
app.get('/api/bookings', async (req, res) => {
    try {
        const view = req.query.view || 'all'; // all, upcoming, past
        const now = new Date().toISOString();

        // Build filter for contractor's bookings
        let filter = `_resource_value eq '${config.contractorResourceId}'`;
        
        if (view === 'upcoming') {
            filter += ` and ${SCHEMA.booking.startTime} ge ${now}`;
        } else if (view === 'past') {
            filter += ` and ${SCHEMA.booking.endTime} lt ${now}`;
        }

        // Build the query with work order and service account expansion
        const selectFields = [
            SCHEMA.booking.id,
            SCHEMA.booking.name,
            SCHEMA.booking.startTime,
            SCHEMA.booking.endTime,
            SCHEMA.booking.duration,
            `_${SCHEMA.booking.workOrder}_value`,
            `_${SCHEMA.booking.bookingStatus}_value`
        ].join(',');

        // Expand to work order with service account
        const workOrderSelect = [
            SCHEMA.workOrder.id,
            SCHEMA.workOrder.name,
            SCHEMA.workOrder.systemStatus,
            SCHEMA.workOrder.summary,
            SCHEMA.workOrder.address,
            SCHEMA.workOrder.priority
        ].join(',');

        const accountSelect = [
            SCHEMA.account.id,
            SCHEMA.account.name
        ].join(',');

        const expand = `${SCHEMA.booking.workOrder}($select=${workOrderSelect};$expand=${SCHEMA.workOrder.serviceAccount}($select=${accountSelect}))`;
        
        const endpoint = `bookableresourcebookings?$filter=${encodeURIComponent(filter)}&$select=${selectFields}&$expand=${expand}&$orderby=${SCHEMA.booking.startTime} desc`;
        
        const bookings = await dataverseRequestWithPaging(endpoint);

        // Transform results for front-end
        const transformed = bookings.map(booking => {
            const wo = booking[SCHEMA.booking.workOrder] || {};
            const sa = wo[SCHEMA.workOrder.serviceAccount] || {};
            
            return {
                id: booking[SCHEMA.booking.id],
                name: booking[SCHEMA.booking.name],
                startTime: booking[SCHEMA.booking.startTime],
                endTime: booking[SCHEMA.booking.endTime],
                duration: booking[SCHEMA.booking.duration],
                bookingStatus: booking[`_${SCHEMA.booking.bookingStatus}_value@OData.Community.Display.V1.FormattedValue`] || 'Unknown',
                bookingStatusId: booking[`_${SCHEMA.booking.bookingStatus}_value`],
                workOrder: wo[SCHEMA.workOrder.id] ? {
                    id: wo[SCHEMA.workOrder.id],
                    name: wo[SCHEMA.workOrder.name],
                    systemStatus: wo[SCHEMA.workOrder.systemStatus],
                    systemStatusName: wo[`${SCHEMA.workOrder.systemStatus}@OData.Community.Display.V1.FormattedValue`] || getSystemStatusName(wo[SCHEMA.workOrder.systemStatus]),
                    summary: wo[SCHEMA.workOrder.summary] || '',
                    address: wo[SCHEMA.workOrder.address] || '',
                    priority: wo[`${SCHEMA.workOrder.priority}@OData.Community.Display.V1.FormattedValue`] || ''
                } : null,
                serviceAccount: sa[SCHEMA.account.id] ? {
                    id: sa[SCHEMA.account.id],
                    name: sa[SCHEMA.account.name]
                } : null
            };
        });

        res.json({
            count: transformed.length,
            bookings: transformed
        });
    } catch (error) {
        console.error('Error fetching bookings:', error);
        res.status(500).json({ error: error.message });
    }
});

function getSystemStatusName(value) {
    const status = SCHEMA.systemStatusOptions.find(s => s.value === value);
    return status ? status.label : 'Unknown';
}

// Get work order details
app.get('/api/workorders/:workOrderId', async (req, res) => {
    try {
        const { workOrderId } = req.params;

        // Build comprehensive select for work order
        const selectFields = [
            SCHEMA.workOrder.id,
            SCHEMA.workOrder.name,
            SCHEMA.workOrder.systemStatus,
            SCHEMA.workOrder.summary,
            SCHEMA.workOrder.instructions,
            SCHEMA.workOrder.address,
            SCHEMA.workOrder.priority,
            SCHEMA.workOrder.primaryIncidentDescription,
            SCHEMA.workOrder.createdOn,
            SCHEMA.workOrder.modifiedOn,
            `_${SCHEMA.workOrder.serviceAccount}_value`,
            `_${SCHEMA.workOrder.primaryIncidentType}_value`
        ].join(',');

        // Expand service account with work order instructions
        const accountSelect = [
            SCHEMA.account.id,
            SCHEMA.account.name,
            SCHEMA.account.workOrderInstructions
        ].join(',');

        const expand = `${SCHEMA.workOrder.serviceAccount}($select=${accountSelect})`;

        const endpoint = `msdyn_workorders(${workOrderId})?$select=${selectFields}&$expand=${expand}`;
        const wo = await dataverseRequest('GET', endpoint);

        const sa = wo[SCHEMA.workOrder.serviceAccount] || {};

        // Get related bookings for this work order
        const bookingsEndpoint = `bookableresourcebookings?$filter=_${SCHEMA.booking.workOrder}_value eq '${workOrderId}'&$select=${SCHEMA.booking.id},${SCHEMA.booking.name},${SCHEMA.booking.startTime},${SCHEMA.booking.endTime},_${SCHEMA.booking.bookingStatus}_value,_${SCHEMA.booking.resource}_value&$orderby=${SCHEMA.booking.startTime} desc`;
        const bookings = await dataverseRequest('GET', bookingsEndpoint);

        // Get annotations (photos) for this work order
        const annotationsEndpoint = `annotations?$filter=_objectid_value eq '${workOrderId}' and isdocument eq true&$select=annotationid,filename,mimetype,filesize,subject,notetext,createdon&$orderby=createdon desc`;
        let annotations = [];
        try {
            const annotationsResult = await dataverseRequest('GET', annotationsEndpoint);
            annotations = annotationsResult.value || [];
        } catch (e) {
            console.log('No annotations found or error:', e.message);
        }

        const result = {
            id: wo[SCHEMA.workOrder.id],
            name: wo[SCHEMA.workOrder.name],
            systemStatus: wo[SCHEMA.workOrder.systemStatus],
            systemStatusName: wo[`${SCHEMA.workOrder.systemStatus}@OData.Community.Display.V1.FormattedValue`] || getSystemStatusName(wo[SCHEMA.workOrder.systemStatus]),
            summary: wo[SCHEMA.workOrder.summary] || '',
            instructions: wo[SCHEMA.workOrder.instructions] || '',
            address: wo[SCHEMA.workOrder.address] || '',
            priority: wo[`${SCHEMA.workOrder.priority}@OData.Community.Display.V1.FormattedValue`] || '',
            primaryIncidentType: wo[`_${SCHEMA.workOrder.primaryIncidentType}_value@OData.Community.Display.V1.FormattedValue`] || '',
            primaryIncidentDescription: wo[SCHEMA.workOrder.primaryIncidentDescription] || '',
            createdOn: wo[SCHEMA.workOrder.createdOn],
            modifiedOn: wo[SCHEMA.workOrder.modifiedOn],
            serviceAccount: sa[SCHEMA.account.id] ? {
                id: sa[SCHEMA.account.id],
                name: sa[SCHEMA.account.name],
                workOrderInstructions: sa[SCHEMA.account.workOrderInstructions] || ''
            } : null,
            bookings: (bookings.value || []).map(b => ({
                id: b[SCHEMA.booking.id],
                name: b[SCHEMA.booking.name],
                startTime: b[SCHEMA.booking.startTime],
                endTime: b[SCHEMA.booking.endTime],
                bookingStatus: b[`_${SCHEMA.booking.bookingStatus}_value@OData.Community.Display.V1.FormattedValue`] || 'Unknown',
                resource: b[`_${SCHEMA.booking.resource}_value@OData.Community.Display.V1.FormattedValue`] || ''
            })),
            photos: annotations.map(a => ({
                id: a.annotationid,
                filename: a.filename,
                mimetype: a.mimetype,
                filesize: a.filesize,
                subject: a.subject,
                notetext: a.notetext,
                createdOn: a.createdon
            })),
            systemStatusOptions: SCHEMA.systemStatusOptions
        };

        res.json(result);
    } catch (error) {
        console.error('Error fetching work order:', error);
        res.status(500).json({ error: error.message });
    }
});

// Update work order system status
app.patch('/api/workorders/:workOrderId/status', async (req, res) => {
    try {
        const { workOrderId } = req.params;
        const { systemStatus } = req.body;

        if (systemStatus === undefined || systemStatus === null) {
            return res.status(400).json({ error: 'systemStatus is required' });
        }

        // Validate status value
        const validStatus = SCHEMA.systemStatusOptions.find(s => s.value === systemStatus);
        if (!validStatus) {
            return res.status(400).json({ 
                error: 'Invalid systemStatus value',
                validOptions: SCHEMA.systemStatusOptions
            });
        }

        const endpoint = `msdyn_workorders(${workOrderId})`;
        const body = {
            [SCHEMA.workOrder.systemStatus]: systemStatus
        };

        await dataverseRequest('PATCH', endpoint, body);

        res.json({
            success: true,
            message: `System status updated to "${validStatus.label}"`,
            newStatus: validStatus
        });
    } catch (error) {
        console.error('Error updating system status:', error);
        res.status(500).json({ error: error.message });
    }
});

// Update work order summary
app.patch('/api/workorders/:workOrderId/summary', async (req, res) => {
    try {
        const { workOrderId } = req.params;
        const { summary } = req.body;

        if (summary === undefined) {
            return res.status(400).json({ error: 'summary is required' });
        }

        const endpoint = `msdyn_workorders(${workOrderId})`;
        const body = {
            [SCHEMA.workOrder.summary]: summary
        };

        await dataverseRequest('PATCH', endpoint, body);

        res.json({
            success: true,
            message: 'Work Order Summary updated successfully'
        });
    } catch (error) {
        console.error('Error updating summary:', error);
        res.status(500).json({ error: error.message });
    }
});

// Update service account work order instructions (Account Instructions)
app.patch('/api/accounts/:accountId/instructions', async (req, res) => {
    try {
        const { accountId } = req.params;
        const { instructions } = req.body;

        if (instructions === undefined) {
            return res.status(400).json({ error: 'instructions is required' });
        }

        const endpoint = `accounts(${accountId})`;
        const body = {
            [SCHEMA.account.workOrderInstructions]: instructions
        };

        await dataverseRequest('PATCH', endpoint, body);

        res.json({
            success: true,
            message: 'Account Instructions updated successfully'
        });
    } catch (error) {
        console.error('Error updating account instructions:', error);
        res.status(500).json({ error: error.message });
    }
});

// Upload photo to work order as annotation
app.post('/api/workorders/:workOrderId/photos', upload.single('photo'), async (req, res) => {
    try {
        const { workOrderId } = req.params;
        const file = req.file;

        if (!file) {
            return res.status(400).json({ error: 'No photo file provided' });
        }

        // Convert file to base64
        const documentBody = file.buffer.toString('base64');

        // Create annotation record
        const annotation = {
            subject: req.body.subject || 'Photo Upload',
            notetext: req.body.description || '',
            filename: file.originalname,
            mimetype: file.mimetype,
            documentbody: documentBody,
            isdocument: true,
            'objectid_msdyn_workorder@odata.bind': `/msdyn_workorders(${workOrderId})`
        };

        const result = await dataverseRequest('POST', 'annotations', annotation);

        res.json({
            success: true,
            message: 'Photo uploaded successfully',
            annotationId: result.annotationid,
            filename: file.originalname
        });
    } catch (error) {
        console.error('Error uploading photo:', error);
        res.status(500).json({ error: error.message });
    }
});

// Get photo content (for display)
app.get('/api/annotations/:annotationId/content', async (req, res) => {
    try {
        const { annotationId } = req.params;
        
        const endpoint = `annotations(${annotationId})?$select=documentbody,mimetype,filename`;
        const annotation = await dataverseRequest('GET', endpoint);

        if (!annotation.documentbody) {
            return res.status(404).json({ error: 'No document content found' });
        }

        // Convert base64 to buffer and send
        const buffer = Buffer.from(annotation.documentbody, 'base64');
        res.set({
            'Content-Type': annotation.mimetype,
            'Content-Disposition': `inline; filename="${annotation.filename}"`
        });
        res.send(buffer);
    } catch (error) {
        console.error('Error fetching annotation content:', error);
        res.status(500).json({ error: error.message });
    }
});

// Get system status options
app.get('/api/metadata/systemstatus', (req, res) => {
    res.json(SCHEMA.systemStatusOptions);
});

// Catch-all: serve index.html for SPA
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    
    if (err instanceof multer.MulterError) {
        if (err.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ error: 'File too large. Maximum size is 10MB.' });
        }
    }
    
    res.status(500).json({ error: err.message || 'Internal server error' });
});

// =============================================================================
// START SERVER
// =============================================================================
app.listen(config.port, () => {
    console.log('');
    console.log('╔════════════════════════════════════════════════════════════════╗');
    console.log('║           Contractor Portal for Dynamics 365 Field Service     ║');
    console.log('╠════════════════════════════════════════════════════════════════╣');
    console.log(`║  Server running at:  http://localhost:${config.port}                    ║`);
    console.log(`║  Dataverse URL:      ${config.dataverseUrl.substring(0, 40).padEnd(40)} ║`);
    console.log(`║  Contractor ID:      ${config.contractorResourceId}   ║`);
    console.log('╚════════════════════════════════════════════════════════════════╝');
    console.log('');
});
