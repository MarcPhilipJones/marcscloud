# Knowledge Article Creation Prompt

Use this prompt template with GitHub Copilot to create fully-formatted knowledge articles in Dataverse.

## Quick Start

Copy and customize this prompt:

```
Create a complete knowledge article in Dataverse with the following specifications:

**Article Details:**
- Title: [YOUR TITLE HERE]
- Description: [SHORT SUMMARY FOR SEARCH RESULTS - 1-2 sentences]
- Keywords: [COMMA-SEPARATED KEYWORDS]
- Content: [DESCRIBE THE CONTENT YOU WANT]

**Requirements:**
1. Generate the article content using INLINE STYLES on every HTML element (Dataverse strips <style> blocks)
2. Use these style constants for consistent formatting:
   - Headings: font-family: Segoe UI, sans-serif; color: #2c3e50
   - Body text: font-family: Segoe UI, sans-serif; font-size: 12pt; line-height: 1.6
   - Lists: margin and padding for proper spacing
3. Create the article as Draft initially
4. After creation, publish ONLY the latest version (check islatestversion=true)
5. Verify the published state before completing

**Publishing Method:**
- Use direct PATCH to knowledgearticles({id}) with statecode=3, statuscode=7
- Do NOT use PublishKnowledgeArticle action (it doesn't exist)

**Version Handling:**
- If updating an existing article, query for islatestversion=true
- Publish only that version, not the root article

**Validation:**
- After publishing, query the article to confirm statecode=3 (Published)
- Show the Article Public Number and version in the output

**Output:**
- Show the created article ID and public number
- Confirm the published state
- Provide a URL to view in Dynamics 365
```

---

## Example: Printer Troubleshooting Article

```
Create a complete knowledge article in Dataverse with the following specifications:

**Article Details:**
- Title: Troubleshooting Printer Connectivity Issues
- Description: Step-by-step guide for resolving common network printer connection problems
- Keywords: printer, network, connectivity, troubleshooting, offline, driver
- Content: 
  - Introduction explaining common causes
  - Section 1: Check physical connections
  - Section 2: Verify network settings (IP, subnet)
  - Section 3: Reinstall/update drivers
  - Section 4: Test print and escalation path
  - Include a troubleshooting flowchart description

**Requirements:**
1. Generate the article content using INLINE STYLES on every HTML element
2. Create as Draft, then publish the latest version
3. Verify published state before completing

**Validation:**
- Confirm statecode=3 after publishing
- Show Article Public Number
```

---

## Technical Reference

### Knowledge Article Status Values

| statecode | State | statuscode | Status Reason |
|-----------|-------|------------|---------------|
| 0 | Draft | 1 | Proposed |
| 0 | Draft | 2 | Draft |
| 0 | Draft | 8 | Needs Review |
| 1 | Approved | 5 | Approved |
| 2 | Scheduled | 6 | Scheduled |
| 3 | Published | 7 | Published |
| 4 | Expired | 10 | Expired |
| 5 | Archived | 12 | Archived |
| 6 | Discarded | 11 | Discarded |

### HTML Formatting - CRITICAL

**Dataverse sanitizes `<style>` blocks** - they are completely stripped from Knowledge Article content.

❌ **Does NOT work:**
```html
<style>body { font-family: Arial; }</style>
<p>Content here</p>
```

✅ **Works - use inline styles on EVERY element:**
```html
<p style="font-family: Segoe UI, sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 15px;">Content here</p>
```

### Recommended Style Constants (Python)

```python
H1_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 18pt; color: #2c3e50; margin-bottom: 15px;"'
H2_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 14pt; color: #2c3e50; margin-top: 20px; margin-bottom: 10px;"'
P_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 15px;"'
LI_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; margin-bottom: 8px;"'
UL_STYLE = 'style="margin: 0 0 15px 20px; padding: 0;"'
```

### Version Handling

When you create a new version in Dynamics 365, it creates a **separate record**:
- **Root article** (`isrootarticle=True`): The original article
- **Revision** (`isrootarticle=False`): New version(s) created via "Update" in the UI

**Always publish the LATEST version**, not the root. Use this query:

```python
params = {
    "$filter": "contains(title, 'Article Name') and islatestversion eq true",
    "$select": "knowledgearticleid,title,statecode,majorversionnumber,minorversionnumber"
}
```

### Publishing via API

```python
# Publish by updating statecode and statuscode
client.patch(f"knowledgearticles({article_id})", {
    "statecode": 3,
    "statuscode": 7
})
```

**Note**: There is no `PublishKnowledgeArticle` unbound action. Direct PATCH is the official method.

### Viewing in Dynamics 365

After creation, the article can be viewed at:
```
https://{org}.crm4.dynamics.com/main.aspx?etn=knowledgearticle&id={knowledgearticleid}&pagetype=entityrecord
```

---

## Environment Details

- **Tenant**: D365DemoTSCE63319057.onmicrosoft.com
- **Environment**: MJCC2024
- **API Base**: https://org6cb3e9fb.crm4.dynamics.com/api/data/v9.2/

---

*Last updated: February 2026*
