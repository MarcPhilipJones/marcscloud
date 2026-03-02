# SummariseTranscript Trigger Flow

This Power Automate flow automatically triggers the **SummariseTranscriptonRelatedCase** Logic App when a conversation (msdyn_ocliveworkitem) status changes to Closed, Wrap-up, or Resolved.

## Setup Instructions

### Option 1: Create Manually in Power Automate

1. Go to [Power Automate](https://make.powerautomate.com)
2. Select the **MJCC2024** environment
3. Create a new **Automated cloud flow**
4. Use trigger: **When a row is modified** (Microsoft Dataverse)
   - Table name: **Conversation (msdyn_ocliveworkitem)**
   - Scope: **Organization**
   - Select columns: `statecode,statuscode`
5. Add a **Condition** action:
   - Check if `statecode` equals `1` (Closed) OR `2` (Resolved) OR `statuscode` equals `4` (Closed) OR `5` (Wrap-up) OR `6` (Resolved)
6. If Yes, add an **HTTP** action:
   - Method: `POST`
   - URI: `https://prod-194.westeurope.logic.azure.com:443/workflows/9072abb5ba914f39bf1e65edbdb920b8/triggers/When_a_conversation_ends/paths/invoke?api-version=2018-07-01-preview&sp=%2Ftriggers%2FWhen_a_conversation_ends%2Frun&sv=1.0&sig=ore6ort3nQVFuSR8xfdOPiqx3VhA5YoZJ_XxzZaBO74`
   - Headers: `Content-Type: application/json`
   - Body:
     ```json
     {
       "conversationId": "@{triggerOutputs()?['body/msdyn_ocliveworkitemid']}"
     }
     ```

### Option 2: Import Solution (Coming Soon)

A managed solution will be created for easy import.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Dynamics 365 Omnichannel                                                    │
│  ┌───────────────────────────┐                                              │
│  │ Conversation closes       │                                              │
│  │ (statecode/statuscode     │                                              │
│  │  changes to Closed/       │                                              │
│  │  Wrap-up/Resolved)        │                                              │
│  └───────────┬───────────────┘                                              │
└──────────────┼──────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Power Automate Flow                                                         │
│  ┌───────────────────────────┐                                              │
│  │ When row is modified      │                                              │
│  │ (msdyn_ocliveworkitem)    │                                              │
│  └───────────┬───────────────┘                                              │
│              │                                                              │
│              ▼                                                              │
│  ┌───────────────────────────┐                                              │
│  │ Check if Closed/Wrap-up/  │                                              │
│  │ Resolved                  │                                              │
│  └───────────┬───────────────┘                                              │
│              │ Yes                                                          │
│              ▼                                                              │
│  ┌───────────────────────────┐                                              │
│  │ HTTP POST to Logic App    │                                              │
│  │ with conversationId       │                                              │
│  └───────────┬───────────────┘                                              │
└──────────────┼──────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Azure Logic App: SummariseTranscriptonRelatedCase                          │
│  ┌───────────────────────────┐                                              │
│  │ 1. Validate conversation  │                                              │
│  │    is truly closed        │                                              │
│  ├───────────────────────────┤                                              │
│  │ 2. Extract CaseID from    │                                              │
│  │    regardingobjectid      │                                              │
│  ├───────────────────────────┤                                              │
│  │ 3. Get transcript from    │                                              │
│  │    msdyn_transcripts      │                                              │
│  ├───────────────────────────┤                                              │
│  │ 4. Filter metadata,       │                                              │
│  │    deduplicate,           │                                              │
│  │    format with speaker    │                                              │
│  │    headers                │                                              │
│  ├───────────────────────────┤                                              │
│  │ 5. Update case with       │                                              │
│  │    transcript in          │                                              │
│  │    mj_lasttranscript      │                                              │
│  └───────────────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Related Resources

- Logic App: `SummariseTranscriptonRelatedCase` in `MJ_Resources` resource group
- Environment: MJCC2024
- Dataverse URL: https://org6cb3e9fb.crm4.dynamics.com
