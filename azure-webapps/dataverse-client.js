/**
 * Dataverse client using MSAL client-credentials flow.
 * Token is cached in-memory and refreshed 5 minutes before expiry.
 */
const { ConfidentialClientApplication } = require("@azure/msal-node");

class DataverseClient {
  constructor({ baseUrl, tenantId, clientId, clientSecret }) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiUrl = `${this.baseUrl}/api/data/v9.2`;
    this.tokenCache = null;
    this.tokenExpiry = null;
    this.msalClient = new ConfidentialClientApplication({
      auth: {
        clientId,
        authority: `https://login.microsoftonline.com/${tenantId}`,
        clientSecret,
      },
    });
  }

  async getToken() {
    if (
      this.tokenCache &&
      this.tokenExpiry &&
      Date.now() < this.tokenExpiry - 300_000
    ) {
      return this.tokenCache;
    }
    const result = await this.msalClient.acquireTokenByClientCredential({
      scopes: [`${this.baseUrl}/.default`],
    });
    this.tokenCache = result.accessToken;
    this.tokenExpiry = result.expiresOn
      ? result.expiresOn.getTime()
      : Date.now() + 3_600_000;
    return this.tokenCache;
  }

  async fetch(endpoint, options = {}) {
    const token = await this.getToken();
    const url = endpoint.startsWith("http")
      ? endpoint
      : `${this.apiUrl}/${endpoint}`;
    const response = await globalThis.fetch(url, {
      ...options,
      headers: {
        Authorization: `Bearer ${token}`,
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        Accept: "application/json",
        "Content-Type": "application/json",
        Prefer:
          'odata.include-annotations="OData.Community.Display.V1.FormattedValue"',
        ...options.headers,
      },
    });
    if (!response.ok) {
      const body = await response.text();
      const err = new Error(`Dataverse ${response.status}: ${body}`);
      err.status = response.status;
      throw err;
    }
    if (response.status === 204) return null;
    return response.json();
  }

  async get(entity, query = "") {
    return this.fetch(`${entity}${query ? "?" + query : ""}`);
  }

  async getById(entity, id, query = "") {
    return this.fetch(`${entity}(${id})${query ? "?" + query : ""}`);
  }
}

module.exports = { DataverseClient };
