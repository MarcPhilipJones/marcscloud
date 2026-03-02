"""Get available transaction currencies from Dataverse."""
import sys
import os

# Change to the field-service-mikeo directory so .env is found
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, "src")
from field_service_mikeo.dataverse_client import DataverseClient

client = DataverseClient()
result = client.get('transactioncurrencies', {'$select': 'transactioncurrencyid,currencyname,isocurrencycode,currencysymbol'})
for curr in result.get('value', []):
    print(f"{curr['isocurrencycode']}: {curr['currencyname']} ({curr['currencysymbol']}) - {curr['transactioncurrencyid']}")
