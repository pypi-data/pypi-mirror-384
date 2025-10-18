# Shared Types

```python
from m3ter.types import CurrencyConversion, PricingBand, SetString
```

# Authentication

Types:

```python
from m3ter.types import AuthenticationGetBearerTokenResponse
```

Methods:

- <code title="post /oauth/token">client.authentication.<a href="./src/m3ter/resources/authentication.py">get_bearer_token</a>(\*\*<a href="src/m3ter/types/authentication_get_bearer_token_params.py">params</a>) -> <a href="./src/m3ter/types/authentication_get_bearer_token_response.py">AuthenticationGetBearerTokenResponse</a></code>

# Accounts

Types:

```python
from m3ter.types import (
    AccountResponse,
    Address,
    AccountEndDateBillingEntitiesResponse,
    AccountSearchResponse,
)
```

Methods:

- <code title="post /organizations/{orgId}/accounts">client.accounts.<a href="./src/m3ter/resources/accounts.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/account_create_params.py">params</a>) -> <a href="./src/m3ter/types/account_response.py">AccountResponse</a></code>
- <code title="get /organizations/{orgId}/accounts/{id}">client.accounts.<a href="./src/m3ter/resources/accounts.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/account_response.py">AccountResponse</a></code>
- <code title="put /organizations/{orgId}/accounts/{id}">client.accounts.<a href="./src/m3ter/resources/accounts.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/account_update_params.py">params</a>) -> <a href="./src/m3ter/types/account_response.py">AccountResponse</a></code>
- <code title="get /organizations/{orgId}/accounts">client.accounts.<a href="./src/m3ter/resources/accounts.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/account_list_params.py">params</a>) -> <a href="./src/m3ter/types/account_response.py">SyncCursor[AccountResponse]</a></code>
- <code title="delete /organizations/{orgId}/accounts/{id}">client.accounts.<a href="./src/m3ter/resources/accounts.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/account_response.py">AccountResponse</a></code>
- <code title="put /organizations/{orgId}/accounts/{id}/enddatebillingentities">client.accounts.<a href="./src/m3ter/resources/accounts.py">end_date_billing_entities</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/account_end_date_billing_entities_params.py">params</a>) -> <a href="./src/m3ter/types/account_end_date_billing_entities_response.py">AccountEndDateBillingEntitiesResponse</a></code>
- <code title="get /organizations/{orgId}/accounts/{id}/children">client.accounts.<a href="./src/m3ter/resources/accounts.py">get_children</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/account_get_children_params.py">params</a>) -> <a href="./src/m3ter/types/account_response.py">AccountResponse</a></code>
- <code title="get /organizations/{orgId}/accounts/search">client.accounts.<a href="./src/m3ter/resources/accounts.py">search</a>(\*, org_id, \*\*<a href="src/m3ter/types/account_search_params.py">params</a>) -> <a href="./src/m3ter/types/account_search_response.py">AccountSearchResponse</a></code>

# AccountPlans

Types:

```python
from m3ter.types import AccountPlanResponse
```

Methods:

- <code title="post /organizations/{orgId}/accountplans">client.account_plans.<a href="./src/m3ter/resources/account_plans.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/account_plan_create_params.py">params</a>) -> <a href="./src/m3ter/types/account_plan_response.py">AccountPlanResponse</a></code>
- <code title="get /organizations/{orgId}/accountplans/{id}">client.account_plans.<a href="./src/m3ter/resources/account_plans.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/account_plan_response.py">AccountPlanResponse</a></code>
- <code title="put /organizations/{orgId}/accountplans/{id}">client.account_plans.<a href="./src/m3ter/resources/account_plans.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/account_plan_update_params.py">params</a>) -> <a href="./src/m3ter/types/account_plan_response.py">AccountPlanResponse</a></code>
- <code title="get /organizations/{orgId}/accountplans">client.account_plans.<a href="./src/m3ter/resources/account_plans.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/account_plan_list_params.py">params</a>) -> <a href="./src/m3ter/types/account_plan_response.py">SyncCursor[AccountPlanResponse]</a></code>
- <code title="delete /organizations/{orgId}/accountplans/{id}">client.account_plans.<a href="./src/m3ter/resources/account_plans.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/account_plan_response.py">AccountPlanResponse</a></code>

# Aggregations

Types:

```python
from m3ter.types import AggregationResponse
```

Methods:

- <code title="post /organizations/{orgId}/aggregations">client.aggregations.<a href="./src/m3ter/resources/aggregations.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/aggregation_create_params.py">params</a>) -> <a href="./src/m3ter/types/aggregation_response.py">AggregationResponse</a></code>
- <code title="get /organizations/{orgId}/aggregations/{id}">client.aggregations.<a href="./src/m3ter/resources/aggregations.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/aggregation_response.py">AggregationResponse</a></code>
- <code title="put /organizations/{orgId}/aggregations/{id}">client.aggregations.<a href="./src/m3ter/resources/aggregations.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/aggregation_update_params.py">params</a>) -> <a href="./src/m3ter/types/aggregation_response.py">AggregationResponse</a></code>
- <code title="get /organizations/{orgId}/aggregations">client.aggregations.<a href="./src/m3ter/resources/aggregations.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/aggregation_list_params.py">params</a>) -> <a href="./src/m3ter/types/aggregation_response.py">SyncCursor[AggregationResponse]</a></code>
- <code title="delete /organizations/{orgId}/aggregations/{id}">client.aggregations.<a href="./src/m3ter/resources/aggregations.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/aggregation_response.py">AggregationResponse</a></code>

# Balances

Types:

```python
from m3ter.types import Balance
```

Methods:

- <code title="post /organizations/{orgId}/balances">client.balances.<a href="./src/m3ter/resources/balances/balances.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/balance_create_params.py">params</a>) -> <a href="./src/m3ter/types/balance.py">Balance</a></code>
- <code title="get /organizations/{orgId}/balances/{id}">client.balances.<a href="./src/m3ter/resources/balances/balances.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/balance.py">Balance</a></code>
- <code title="put /organizations/{orgId}/balances/{id}">client.balances.<a href="./src/m3ter/resources/balances/balances.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/balance_update_params.py">params</a>) -> <a href="./src/m3ter/types/balance.py">Balance</a></code>
- <code title="get /organizations/{orgId}/balances">client.balances.<a href="./src/m3ter/resources/balances/balances.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/balance_list_params.py">params</a>) -> <a href="./src/m3ter/types/balance.py">SyncCursor[Balance]</a></code>
- <code title="delete /organizations/{orgId}/balances/{id}">client.balances.<a href="./src/m3ter/resources/balances/balances.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/balance.py">Balance</a></code>

## Transactions

Types:

```python
from m3ter.types.balances import TransactionResponse, TransactionSummaryResponse
```

Methods:

- <code title="post /organizations/{orgId}/balances/{balanceId}/transactions">client.balances.transactions.<a href="./src/m3ter/resources/balances/transactions.py">create</a>(balance_id, \*, org_id, \*\*<a href="src/m3ter/types/balances/transaction_create_params.py">params</a>) -> <a href="./src/m3ter/types/balances/transaction_response.py">TransactionResponse</a></code>
- <code title="get /organizations/{orgId}/balances/{balanceId}/transactions">client.balances.transactions.<a href="./src/m3ter/resources/balances/transactions.py">list</a>(balance_id, \*, org_id, \*\*<a href="src/m3ter/types/balances/transaction_list_params.py">params</a>) -> <a href="./src/m3ter/types/balances/transaction_response.py">SyncCursor[TransactionResponse]</a></code>
- <code title="get /organizations/{orgId}/balances/{balanceId}/transactions/summary">client.balances.transactions.<a href="./src/m3ter/resources/balances/transactions.py">summary</a>(balance_id, \*, org_id) -> <a href="./src/m3ter/types/balances/transaction_summary_response.py">TransactionSummaryResponse</a></code>

# Bills

Types:

```python
from m3ter.types import BillResponse, BillApproveResponse, BillSearchResponse
```

Methods:

- <code title="get /organizations/{orgId}/bills/{id}">client.bills.<a href="./src/m3ter/resources/bills/bills.py">retrieve</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/bill_retrieve_params.py">params</a>) -> <a href="./src/m3ter/types/bill_response.py">BillResponse</a></code>
- <code title="get /organizations/{orgId}/bills">client.bills.<a href="./src/m3ter/resources/bills/bills.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/bill_list_params.py">params</a>) -> <a href="./src/m3ter/types/bill_response.py">SyncCursor[BillResponse]</a></code>
- <code title="delete /organizations/{orgId}/bills/{id}">client.bills.<a href="./src/m3ter/resources/bills/bills.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/bill_response.py">BillResponse</a></code>
- <code title="post /organizations/{orgId}/bills/approve">client.bills.<a href="./src/m3ter/resources/bills/bills.py">approve</a>(\*, org_id, \*\*<a href="src/m3ter/types/bill_approve_params.py">params</a>) -> <a href="./src/m3ter/types/bill_approve_response.py">BillApproveResponse</a></code>
- <code title="get /organizations/{orgId}/bills/latest/{accountId}">client.bills.<a href="./src/m3ter/resources/bills/bills.py">latest_by_account</a>(account_id, \*, org_id, \*\*<a href="src/m3ter/types/bill_latest_by_account_params.py">params</a>) -> <a href="./src/m3ter/types/bill_response.py">BillResponse</a></code>
- <code title="put /organizations/{orgId}/bills/{id}/lock">client.bills.<a href="./src/m3ter/resources/bills/bills.py">lock</a>(id, \*, org_id) -> <a href="./src/m3ter/types/bill_response.py">BillResponse</a></code>
- <code title="get /organizations/{orgId}/bills/search">client.bills.<a href="./src/m3ter/resources/bills/bills.py">search</a>(\*, org_id, \*\*<a href="src/m3ter/types/bill_search_params.py">params</a>) -> <a href="./src/m3ter/types/bill_search_response.py">BillSearchResponse</a></code>
- <code title="put /organizations/{orgId}/bills/{id}/status">client.bills.<a href="./src/m3ter/resources/bills/bills.py">update_status</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/bill_update_status_params.py">params</a>) -> <a href="./src/m3ter/types/bill_response.py">BillResponse</a></code>

## CreditLineItems

Types:

```python
from m3ter.types.bills import CreditLineItemResponse
```

Methods:

- <code title="post /organizations/{orgId}/bills/{billId}/creditlineitems">client.bills.credit_line_items.<a href="./src/m3ter/resources/bills/credit_line_items.py">create</a>(bill_id, \*, org_id, \*\*<a href="src/m3ter/types/bills/credit_line_item_create_params.py">params</a>) -> <a href="./src/m3ter/types/bills/credit_line_item_response.py">CreditLineItemResponse</a></code>
- <code title="get /organizations/{orgId}/bills/{billId}/creditlineitems/{id}">client.bills.credit_line_items.<a href="./src/m3ter/resources/bills/credit_line_items.py">retrieve</a>(id, \*, org_id, bill_id) -> <a href="./src/m3ter/types/bills/credit_line_item_response.py">CreditLineItemResponse</a></code>
- <code title="put /organizations/{orgId}/bills/{billId}/creditlineitems/{id}">client.bills.credit_line_items.<a href="./src/m3ter/resources/bills/credit_line_items.py">update</a>(id, \*, org_id, bill_id, \*\*<a href="src/m3ter/types/bills/credit_line_item_update_params.py">params</a>) -> <a href="./src/m3ter/types/bills/credit_line_item_response.py">CreditLineItemResponse</a></code>
- <code title="get /organizations/{orgId}/bills/{billId}/creditlineitems">client.bills.credit_line_items.<a href="./src/m3ter/resources/bills/credit_line_items.py">list</a>(bill_id, \*, org_id, \*\*<a href="src/m3ter/types/bills/credit_line_item_list_params.py">params</a>) -> <a href="./src/m3ter/types/bills/credit_line_item_response.py">SyncCursor[CreditLineItemResponse]</a></code>
- <code title="delete /organizations/{orgId}/bills/{billId}/creditlineitems/{id}">client.bills.credit_line_items.<a href="./src/m3ter/resources/bills/credit_line_items.py">delete</a>(id, \*, org_id, bill_id) -> <a href="./src/m3ter/types/bills/credit_line_item_response.py">CreditLineItemResponse</a></code>

## DebitLineItems

Types:

```python
from m3ter.types.bills import DebitLineItemResponse
```

Methods:

- <code title="post /organizations/{orgId}/bills/{billId}/debitlineitems">client.bills.debit_line_items.<a href="./src/m3ter/resources/bills/debit_line_items.py">create</a>(bill_id, \*, org_id, \*\*<a href="src/m3ter/types/bills/debit_line_item_create_params.py">params</a>) -> <a href="./src/m3ter/types/bills/debit_line_item_response.py">DebitLineItemResponse</a></code>
- <code title="get /organizations/{orgId}/bills/{billId}/debitlineitems/{id}">client.bills.debit_line_items.<a href="./src/m3ter/resources/bills/debit_line_items.py">retrieve</a>(id, \*, org_id, bill_id) -> <a href="./src/m3ter/types/bills/debit_line_item_response.py">DebitLineItemResponse</a></code>
- <code title="put /organizations/{orgId}/bills/{billId}/debitlineitems/{id}">client.bills.debit_line_items.<a href="./src/m3ter/resources/bills/debit_line_items.py">update</a>(id, \*, org_id, bill_id, \*\*<a href="src/m3ter/types/bills/debit_line_item_update_params.py">params</a>) -> <a href="./src/m3ter/types/bills/debit_line_item_response.py">DebitLineItemResponse</a></code>
- <code title="get /organizations/{orgId}/bills/{billId}/debitlineitems">client.bills.debit_line_items.<a href="./src/m3ter/resources/bills/debit_line_items.py">list</a>(bill_id, \*, org_id, \*\*<a href="src/m3ter/types/bills/debit_line_item_list_params.py">params</a>) -> <a href="./src/m3ter/types/bills/debit_line_item_response.py">SyncCursor[DebitLineItemResponse]</a></code>
- <code title="delete /organizations/{orgId}/bills/{billId}/debitlineitems/{id}">client.bills.debit_line_items.<a href="./src/m3ter/resources/bills/debit_line_items.py">delete</a>(id, \*, org_id, bill_id) -> <a href="./src/m3ter/types/bills/debit_line_item_response.py">DebitLineItemResponse</a></code>

## LineItems

Types:

```python
from m3ter.types.bills import LineItemResponse
```

Methods:

- <code title="get /organizations/{orgId}/bills/{billId}/lineitems/{id}">client.bills.line_items.<a href="./src/m3ter/resources/bills/line_items.py">retrieve</a>(id, \*, org_id, bill_id, \*\*<a href="src/m3ter/types/bills/line_item_retrieve_params.py">params</a>) -> <a href="./src/m3ter/types/bills/line_item_response.py">LineItemResponse</a></code>
- <code title="get /organizations/{orgId}/bills/{billId}/lineitems">client.bills.line_items.<a href="./src/m3ter/resources/bills/line_items.py">list</a>(bill_id, \*, org_id, \*\*<a href="src/m3ter/types/bills/line_item_list_params.py">params</a>) -> <a href="./src/m3ter/types/bills/line_item_response.py">SyncCursor[LineItemResponse]</a></code>

# BillConfig

Types:

```python
from m3ter.types import BillConfigResponse
```

Methods:

- <code title="get /organizations/{orgId}/billconfig">client.bill_config.<a href="./src/m3ter/resources/bill_config.py">retrieve</a>(\*, org_id) -> <a href="./src/m3ter/types/bill_config_response.py">BillConfigResponse</a></code>
- <code title="put /organizations/{orgId}/billconfig">client.bill_config.<a href="./src/m3ter/resources/bill_config.py">update</a>(\*, org_id, \*\*<a href="src/m3ter/types/bill_config_update_params.py">params</a>) -> <a href="./src/m3ter/types/bill_config_response.py">BillConfigResponse</a></code>

# Commitments

Types:

```python
from m3ter.types import CommitmentFee, CommitmentResponse, CommitmentSearchResponse
```

Methods:

- <code title="post /organizations/{orgId}/commitments">client.commitments.<a href="./src/m3ter/resources/commitments.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/commitment_create_params.py">params</a>) -> <a href="./src/m3ter/types/commitment_response.py">CommitmentResponse</a></code>
- <code title="get /organizations/{orgId}/commitments/{id}">client.commitments.<a href="./src/m3ter/resources/commitments.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/commitment_response.py">CommitmentResponse</a></code>
- <code title="put /organizations/{orgId}/commitments/{id}">client.commitments.<a href="./src/m3ter/resources/commitments.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/commitment_update_params.py">params</a>) -> <a href="./src/m3ter/types/commitment_response.py">CommitmentResponse</a></code>
- <code title="get /organizations/{orgId}/commitments">client.commitments.<a href="./src/m3ter/resources/commitments.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/commitment_list_params.py">params</a>) -> <a href="./src/m3ter/types/commitment_response.py">SyncCursor[CommitmentResponse]</a></code>
- <code title="delete /organizations/{orgId}/commitments/{id}">client.commitments.<a href="./src/m3ter/resources/commitments.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/commitment_response.py">CommitmentResponse</a></code>
- <code title="get /organizations/{orgId}/commitments/search">client.commitments.<a href="./src/m3ter/resources/commitments.py">search</a>(\*, org_id, \*\*<a href="src/m3ter/types/commitment_search_params.py">params</a>) -> <a href="./src/m3ter/types/commitment_search_response.py">CommitmentSearchResponse</a></code>

# BillJobs

Types:

```python
from m3ter.types import BillJobResponse
```

Methods:

- <code title="post /organizations/{orgId}/billjobs">client.bill_jobs.<a href="./src/m3ter/resources/bill_jobs.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/bill_job_create_params.py">params</a>) -> <a href="./src/m3ter/types/bill_job_response.py">BillJobResponse</a></code>
- <code title="get /organizations/{orgId}/billjobs/{id}">client.bill_jobs.<a href="./src/m3ter/resources/bill_jobs.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/bill_job_response.py">BillJobResponse</a></code>
- <code title="get /organizations/{orgId}/billjobs">client.bill_jobs.<a href="./src/m3ter/resources/bill_jobs.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/bill_job_list_params.py">params</a>) -> <a href="./src/m3ter/types/bill_job_response.py">SyncCursor[BillJobResponse]</a></code>
- <code title="post /organizations/{orgId}/billjobs/{id}/cancel">client.bill_jobs.<a href="./src/m3ter/resources/bill_jobs.py">cancel</a>(id, \*, org_id) -> <a href="./src/m3ter/types/bill_job_response.py">BillJobResponse</a></code>
- <code title="post /organizations/{orgId}/billjobs/recalculate">client.bill_jobs.<a href="./src/m3ter/resources/bill_jobs.py">recalculate</a>(\*, org_id, \*\*<a href="src/m3ter/types/bill_job_recalculate_params.py">params</a>) -> <a href="./src/m3ter/types/bill_job_response.py">BillJobResponse</a></code>

# CompoundAggregations

Types:

```python
from m3ter.types import CompoundAggregationResponse
```

Methods:

- <code title="post /organizations/{orgId}/compoundaggregations">client.compound_aggregations.<a href="./src/m3ter/resources/compound_aggregations.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/compound_aggregation_create_params.py">params</a>) -> <a href="./src/m3ter/types/aggregation_response.py">AggregationResponse</a></code>
- <code title="get /organizations/{orgId}/compoundaggregations/{id}">client.compound_aggregations.<a href="./src/m3ter/resources/compound_aggregations.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/compound_aggregation_response.py">CompoundAggregationResponse</a></code>
- <code title="put /organizations/{orgId}/compoundaggregations/{id}">client.compound_aggregations.<a href="./src/m3ter/resources/compound_aggregations.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/compound_aggregation_update_params.py">params</a>) -> <a href="./src/m3ter/types/aggregation_response.py">AggregationResponse</a></code>
- <code title="get /organizations/{orgId}/compoundaggregations">client.compound_aggregations.<a href="./src/m3ter/resources/compound_aggregations.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/compound_aggregation_list_params.py">params</a>) -> <a href="./src/m3ter/types/compound_aggregation_response.py">SyncCursor[CompoundAggregationResponse]</a></code>
- <code title="delete /organizations/{orgId}/compoundaggregations/{id}">client.compound_aggregations.<a href="./src/m3ter/resources/compound_aggregations.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/compound_aggregation_response.py">CompoundAggregationResponse</a></code>

# Contracts

Types:

```python
from m3ter.types import ContractResponse, ContractEndDateBillingEntitiesResponse
```

Methods:

- <code title="post /organizations/{orgId}/contracts">client.contracts.<a href="./src/m3ter/resources/contracts.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/contract_create_params.py">params</a>) -> <a href="./src/m3ter/types/contract_response.py">ContractResponse</a></code>
- <code title="get /organizations/{orgId}/contracts/{id}">client.contracts.<a href="./src/m3ter/resources/contracts.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/contract_response.py">ContractResponse</a></code>
- <code title="put /organizations/{orgId}/contracts/{id}">client.contracts.<a href="./src/m3ter/resources/contracts.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/contract_update_params.py">params</a>) -> <a href="./src/m3ter/types/contract_response.py">ContractResponse</a></code>
- <code title="get /organizations/{orgId}/contracts">client.contracts.<a href="./src/m3ter/resources/contracts.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/contract_list_params.py">params</a>) -> <a href="./src/m3ter/types/contract_response.py">SyncCursor[ContractResponse]</a></code>
- <code title="delete /organizations/{orgId}/contracts/{id}">client.contracts.<a href="./src/m3ter/resources/contracts.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/contract_response.py">ContractResponse</a></code>
- <code title="put /organizations/{orgId}/contracts/{id}/enddatebillingentities">client.contracts.<a href="./src/m3ter/resources/contracts.py">end_date_billing_entities</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/contract_end_date_billing_entities_params.py">params</a>) -> <a href="./src/m3ter/types/contract_end_date_billing_entities_response.py">ContractEndDateBillingEntitiesResponse</a></code>

# Counters

Types:

```python
from m3ter.types import CounterResponse
```

Methods:

- <code title="post /organizations/{orgId}/counters">client.counters.<a href="./src/m3ter/resources/counters.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/counter_create_params.py">params</a>) -> <a href="./src/m3ter/types/counter_response.py">CounterResponse</a></code>
- <code title="get /organizations/{orgId}/counters/{id}">client.counters.<a href="./src/m3ter/resources/counters.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/counter_response.py">CounterResponse</a></code>
- <code title="put /organizations/{orgId}/counters/{id}">client.counters.<a href="./src/m3ter/resources/counters.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/counter_update_params.py">params</a>) -> <a href="./src/m3ter/types/counter_response.py">CounterResponse</a></code>
- <code title="get /organizations/{orgId}/counters">client.counters.<a href="./src/m3ter/resources/counters.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/counter_list_params.py">params</a>) -> <a href="./src/m3ter/types/counter_response.py">SyncCursor[CounterResponse]</a></code>
- <code title="delete /organizations/{orgId}/counters/{id}">client.counters.<a href="./src/m3ter/resources/counters.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/counter_response.py">CounterResponse</a></code>

# CounterAdjustments

Types:

```python
from m3ter.types import CounterAdjustmentResponse
```

Methods:

- <code title="post /organizations/{orgId}/counteradjustments">client.counter_adjustments.<a href="./src/m3ter/resources/counter_adjustments.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/counter_adjustment_create_params.py">params</a>) -> <a href="./src/m3ter/types/counter_adjustment_response.py">CounterAdjustmentResponse</a></code>
- <code title="get /organizations/{orgId}/counteradjustments/{id}">client.counter_adjustments.<a href="./src/m3ter/resources/counter_adjustments.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/counter_adjustment_response.py">CounterAdjustmentResponse</a></code>
- <code title="put /organizations/{orgId}/counteradjustments/{id}">client.counter_adjustments.<a href="./src/m3ter/resources/counter_adjustments.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/counter_adjustment_update_params.py">params</a>) -> <a href="./src/m3ter/types/counter_adjustment_response.py">CounterAdjustmentResponse</a></code>
- <code title="get /organizations/{orgId}/counteradjustments">client.counter_adjustments.<a href="./src/m3ter/resources/counter_adjustments.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/counter_adjustment_list_params.py">params</a>) -> <a href="./src/m3ter/types/counter_adjustment_response.py">SyncCursor[CounterAdjustmentResponse]</a></code>
- <code title="delete /organizations/{orgId}/counteradjustments/{id}">client.counter_adjustments.<a href="./src/m3ter/resources/counter_adjustments.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/counter_adjustment_response.py">CounterAdjustmentResponse</a></code>

# CounterPricings

Types:

```python
from m3ter.types import CounterPricingResponse
```

Methods:

- <code title="post /organizations/{orgId}/counterpricings">client.counter_pricings.<a href="./src/m3ter/resources/counter_pricings.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/counter_pricing_create_params.py">params</a>) -> <a href="./src/m3ter/types/counter_pricing_response.py">CounterPricingResponse</a></code>
- <code title="get /organizations/{orgId}/counterpricings/{id}">client.counter_pricings.<a href="./src/m3ter/resources/counter_pricings.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/counter_pricing_response.py">CounterPricingResponse</a></code>
- <code title="put /organizations/{orgId}/counterpricings/{id}">client.counter_pricings.<a href="./src/m3ter/resources/counter_pricings.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/counter_pricing_update_params.py">params</a>) -> <a href="./src/m3ter/types/counter_pricing_response.py">CounterPricingResponse</a></code>
- <code title="get /organizations/{orgId}/counterpricings">client.counter_pricings.<a href="./src/m3ter/resources/counter_pricings.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/counter_pricing_list_params.py">params</a>) -> <a href="./src/m3ter/types/counter_pricing_response.py">SyncCursor[CounterPricingResponse]</a></code>
- <code title="delete /organizations/{orgId}/counterpricings/{id}">client.counter_pricings.<a href="./src/m3ter/resources/counter_pricings.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/counter_pricing_response.py">CounterPricingResponse</a></code>

# CreditReasons

Types:

```python
from m3ter.types import CreditReasonResponse
```

Methods:

- <code title="post /organizations/{orgId}/picklists/creditreasons">client.credit_reasons.<a href="./src/m3ter/resources/credit_reasons.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/credit_reason_create_params.py">params</a>) -> <a href="./src/m3ter/types/credit_reason_response.py">CreditReasonResponse</a></code>
- <code title="get /organizations/{orgId}/picklists/creditreasons/{id}">client.credit_reasons.<a href="./src/m3ter/resources/credit_reasons.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/credit_reason_response.py">CreditReasonResponse</a></code>
- <code title="put /organizations/{orgId}/picklists/creditreasons/{id}">client.credit_reasons.<a href="./src/m3ter/resources/credit_reasons.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/credit_reason_update_params.py">params</a>) -> <a href="./src/m3ter/types/credit_reason_response.py">CreditReasonResponse</a></code>
- <code title="get /organizations/{orgId}/picklists/creditreasons">client.credit_reasons.<a href="./src/m3ter/resources/credit_reasons.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/credit_reason_list_params.py">params</a>) -> <a href="./src/m3ter/types/credit_reason_response.py">SyncCursor[CreditReasonResponse]</a></code>
- <code title="delete /organizations/{orgId}/picklists/creditreasons/{id}">client.credit_reasons.<a href="./src/m3ter/resources/credit_reasons.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/credit_reason_response.py">CreditReasonResponse</a></code>

# Currencies

Types:

```python
from m3ter.types import CurrencyResponse
```

Methods:

- <code title="post /organizations/{orgId}/picklists/currency">client.currencies.<a href="./src/m3ter/resources/currencies.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/currency_create_params.py">params</a>) -> <a href="./src/m3ter/types/currency_response.py">CurrencyResponse</a></code>
- <code title="get /organizations/{orgId}/picklists/currency/{id}">client.currencies.<a href="./src/m3ter/resources/currencies.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/currency_response.py">CurrencyResponse</a></code>
- <code title="put /organizations/{orgId}/picklists/currency/{id}">client.currencies.<a href="./src/m3ter/resources/currencies.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/currency_update_params.py">params</a>) -> <a href="./src/m3ter/types/currency_response.py">CurrencyResponse</a></code>
- <code title="get /organizations/{orgId}/picklists/currency">client.currencies.<a href="./src/m3ter/resources/currencies.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/currency_list_params.py">params</a>) -> <a href="./src/m3ter/types/currency_response.py">SyncCursor[CurrencyResponse]</a></code>
- <code title="delete /organizations/{orgId}/picklists/currency/{id}">client.currencies.<a href="./src/m3ter/resources/currencies.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/currency_response.py">CurrencyResponse</a></code>

# CustomFields

Types:

```python
from m3ter.types import CustomFieldsResponse
```

Methods:

- <code title="get /organizations/{orgId}/customfields">client.custom_fields.<a href="./src/m3ter/resources/custom_fields.py">retrieve</a>(\*, org_id) -> <a href="./src/m3ter/types/custom_fields_response.py">CustomFieldsResponse</a></code>
- <code title="put /organizations/{orgId}/customfields">client.custom_fields.<a href="./src/m3ter/resources/custom_fields.py">update</a>(\*, org_id, \*\*<a href="src/m3ter/types/custom_field_update_params.py">params</a>) -> <a href="./src/m3ter/types/custom_fields_response.py">CustomFieldsResponse</a></code>

# DataExports

Types:

```python
from m3ter.types import (
    AdHocOperationalDataRequest,
    AdHocResponse,
    AdHocUsageDataRequest,
    DataExplorerAccountGroup,
    DataExplorerDimensionGroup,
    DataExplorerGroup,
    DataExplorerTimeGroup,
)
```

Methods:

- <code title="post /organizations/{orgId}/dataexports/adhoc">client.data_exports.<a href="./src/m3ter/resources/data_exports/data_exports.py">create_adhoc</a>(\*, org_id, \*\*<a href="src/m3ter/types/data_export_create_adhoc_params.py">params</a>) -> <a href="./src/m3ter/types/ad_hoc_response.py">AdHocResponse</a></code>

## Destinations

Types:

```python
from m3ter.types.data_exports import (
    DataExportDestinationGoogleCloudStorageRequest,
    DataExportDestinationResponse,
    DataExportDestinationS3Request,
    DestinationCreateResponse,
    DestinationRetrieveResponse,
    DestinationUpdateResponse,
    DestinationDeleteResponse,
)
```

Methods:

- <code title="post /organizations/{orgId}/dataexports/destinations">client.data_exports.destinations.<a href="./src/m3ter/resources/data_exports/destinations.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/data_exports/destination_create_params.py">params</a>) -> <a href="./src/m3ter/types/data_exports/destination_create_response.py">DestinationCreateResponse</a></code>
- <code title="get /organizations/{orgId}/dataexports/destinations/{id}">client.data_exports.destinations.<a href="./src/m3ter/resources/data_exports/destinations.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/data_exports/destination_retrieve_response.py">DestinationRetrieveResponse</a></code>
- <code title="put /organizations/{orgId}/dataexports/destinations/{id}">client.data_exports.destinations.<a href="./src/m3ter/resources/data_exports/destinations.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/data_exports/destination_update_params.py">params</a>) -> <a href="./src/m3ter/types/data_exports/destination_update_response.py">DestinationUpdateResponse</a></code>
- <code title="get /organizations/{orgId}/dataexports/destinations">client.data_exports.destinations.<a href="./src/m3ter/resources/data_exports/destinations.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/data_exports/destination_list_params.py">params</a>) -> <a href="./src/m3ter/types/data_exports/data_export_destination_response.py">SyncCursor[DataExportDestinationResponse]</a></code>
- <code title="delete /organizations/{orgId}/dataexports/destinations/{id}">client.data_exports.destinations.<a href="./src/m3ter/resources/data_exports/destinations.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/data_exports/destination_delete_response.py">DestinationDeleteResponse</a></code>

## Jobs

Types:

```python
from m3ter.types.data_exports import DataExportJobResponse, JobGetDownloadURLResponse
```

Methods:

- <code title="get /organizations/{orgId}/dataexports/jobs/{id}">client.data_exports.jobs.<a href="./src/m3ter/resources/data_exports/jobs.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/data_exports/data_export_job_response.py">DataExportJobResponse</a></code>
- <code title="get /organizations/{orgId}/dataexports/jobs">client.data_exports.jobs.<a href="./src/m3ter/resources/data_exports/jobs.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/data_exports/job_list_params.py">params</a>) -> <a href="./src/m3ter/types/data_exports/data_export_job_response.py">SyncCursor[DataExportJobResponse]</a></code>
- <code title="get /organizations/{orgId}/dataexports/jobs/{jobId}/getdownloadurl">client.data_exports.jobs.<a href="./src/m3ter/resources/data_exports/jobs.py">get_download_url</a>(job_id, \*, org_id) -> <a href="./src/m3ter/types/data_exports/job_get_download_url_response.py">JobGetDownloadURLResponse</a></code>

## Schedules

Types:

```python
from m3ter.types.data_exports import (
    OperationalDataExportScheduleRequest,
    OperationalDataExportScheduleResponse,
    UsageDataExportScheduleRequest,
    UsageDataExportScheduleResponse,
    ScheduleCreateResponse,
    ScheduleRetrieveResponse,
    ScheduleUpdateResponse,
    ScheduleListResponse,
    ScheduleDeleteResponse,
)
```

Methods:

- <code title="post /organizations/{orgId}/dataexports/schedules">client.data_exports.schedules.<a href="./src/m3ter/resources/data_exports/schedules.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/data_exports/schedule_create_params.py">params</a>) -> <a href="./src/m3ter/types/data_exports/schedule_create_response.py">ScheduleCreateResponse</a></code>
- <code title="get /organizations/{orgId}/dataexports/schedules/{id}">client.data_exports.schedules.<a href="./src/m3ter/resources/data_exports/schedules.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/data_exports/schedule_retrieve_response.py">ScheduleRetrieveResponse</a></code>
- <code title="put /organizations/{orgId}/dataexports/schedules/{id}">client.data_exports.schedules.<a href="./src/m3ter/resources/data_exports/schedules.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/data_exports/schedule_update_params.py">params</a>) -> <a href="./src/m3ter/types/data_exports/schedule_update_response.py">ScheduleUpdateResponse</a></code>
- <code title="get /organizations/{orgId}/dataexports/schedules">client.data_exports.schedules.<a href="./src/m3ter/resources/data_exports/schedules.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/data_exports/schedule_list_params.py">params</a>) -> <a href="./src/m3ter/types/data_exports/schedule_list_response.py">SyncCursor[ScheduleListResponse]</a></code>
- <code title="delete /organizations/{orgId}/dataexports/schedules/{id}">client.data_exports.schedules.<a href="./src/m3ter/resources/data_exports/schedules.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/data_exports/schedule_delete_response.py">ScheduleDeleteResponse</a></code>

# DebitReasons

Types:

```python
from m3ter.types import DebitReasonResponse
```

Methods:

- <code title="post /organizations/{orgId}/picklists/debitreasons">client.debit_reasons.<a href="./src/m3ter/resources/debit_reasons.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/debit_reason_create_params.py">params</a>) -> <a href="./src/m3ter/types/debit_reason_response.py">DebitReasonResponse</a></code>
- <code title="get /organizations/{orgId}/picklists/debitreasons/{id}">client.debit_reasons.<a href="./src/m3ter/resources/debit_reasons.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/debit_reason_response.py">DebitReasonResponse</a></code>
- <code title="put /organizations/{orgId}/picklists/debitreasons/{id}">client.debit_reasons.<a href="./src/m3ter/resources/debit_reasons.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/debit_reason_update_params.py">params</a>) -> <a href="./src/m3ter/types/debit_reason_response.py">DebitReasonResponse</a></code>
- <code title="get /organizations/{orgId}/picklists/debitreasons">client.debit_reasons.<a href="./src/m3ter/resources/debit_reasons.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/debit_reason_list_params.py">params</a>) -> <a href="./src/m3ter/types/debit_reason_response.py">SyncCursor[DebitReasonResponse]</a></code>
- <code title="delete /organizations/{orgId}/picklists/debitreasons/{id}">client.debit_reasons.<a href="./src/m3ter/resources/debit_reasons.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/debit_reason_response.py">DebitReasonResponse</a></code>

# Events

Types:

```python
from m3ter.types import EventResponse, EventGetFieldsResponse, EventGetTypesResponse
```

Methods:

- <code title="get /organizations/{orgId}/events/{id}">client.events.<a href="./src/m3ter/resources/events.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/event_response.py">EventResponse</a></code>
- <code title="get /organizations/{orgId}/events">client.events.<a href="./src/m3ter/resources/events.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/event_list_params.py">params</a>) -> <a href="./src/m3ter/types/event_response.py">SyncCursor[EventResponse]</a></code>
- <code title="get /organizations/{orgId}/events/fields">client.events.<a href="./src/m3ter/resources/events.py">get_fields</a>(\*, org_id, \*\*<a href="src/m3ter/types/event_get_fields_params.py">params</a>) -> <a href="./src/m3ter/types/event_get_fields_response.py">EventGetFieldsResponse</a></code>
- <code title="get /organizations/{orgId}/events/types">client.events.<a href="./src/m3ter/resources/events.py">get_types</a>(\*, org_id) -> <a href="./src/m3ter/types/event_get_types_response.py">EventGetTypesResponse</a></code>

# ExternalMappings

Types:

```python
from m3ter.types import ExternalMappingResponse
```

Methods:

- <code title="post /organizations/{orgId}/externalmappings">client.external_mappings.<a href="./src/m3ter/resources/external_mappings.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/external_mapping_create_params.py">params</a>) -> <a href="./src/m3ter/types/external_mapping_response.py">ExternalMappingResponse</a></code>
- <code title="get /organizations/{orgId}/externalmappings/{id}">client.external_mappings.<a href="./src/m3ter/resources/external_mappings.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/external_mapping_response.py">ExternalMappingResponse</a></code>
- <code title="put /organizations/{orgId}/externalmappings/{id}">client.external_mappings.<a href="./src/m3ter/resources/external_mappings.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/external_mapping_update_params.py">params</a>) -> <a href="./src/m3ter/types/external_mapping_response.py">ExternalMappingResponse</a></code>
- <code title="get /organizations/{orgId}/externalmappings">client.external_mappings.<a href="./src/m3ter/resources/external_mappings.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/external_mapping_list_params.py">params</a>) -> <a href="./src/m3ter/types/external_mapping_response.py">SyncCursor[ExternalMappingResponse]</a></code>
- <code title="delete /organizations/{orgId}/externalmappings/{id}">client.external_mappings.<a href="./src/m3ter/resources/external_mappings.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/external_mapping_response.py">ExternalMappingResponse</a></code>
- <code title="get /organizations/{orgId}/externalmappings/externalid/{system}/{externalTable}/{externalId}">client.external_mappings.<a href="./src/m3ter/resources/external_mappings.py">list_by_external_entity</a>(external_id, \*, org_id, system, external_table, \*\*<a href="src/m3ter/types/external_mapping_list_by_external_entity_params.py">params</a>) -> <a href="./src/m3ter/types/external_mapping_response.py">SyncCursor[ExternalMappingResponse]</a></code>
- <code title="get /organizations/{orgId}/externalmappings/external/{entity}/{m3terId}">client.external_mappings.<a href="./src/m3ter/resources/external_mappings.py">list_by_m3ter_entity</a>(m3ter_id, \*, org_id, entity, \*\*<a href="src/m3ter/types/external_mapping_list_by_m3ter_entity_params.py">params</a>) -> <a href="./src/m3ter/types/external_mapping_response.py">SyncCursor[ExternalMappingResponse]</a></code>

# IntegrationConfigurations

Types:

```python
from m3ter.types import (
    IntegrationConfigurationResponse,
    IntegrationConfigurationCreateResponse,
    IntegrationConfigurationUpdateResponse,
    IntegrationConfigurationListResponse,
    IntegrationConfigurationDeleteResponse,
    IntegrationConfigurationEnableResponse,
)
```

Methods:

- <code title="post /organizations/{orgId}/integrationconfigs">client.integration_configurations.<a href="./src/m3ter/resources/integration_configurations.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/integration_configuration_create_params.py">params</a>) -> <a href="./src/m3ter/types/integration_configuration_create_response.py">IntegrationConfigurationCreateResponse</a></code>
- <code title="get /organizations/{orgId}/integrationconfigs/{id}">client.integration_configurations.<a href="./src/m3ter/resources/integration_configurations.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/integration_configuration_response.py">IntegrationConfigurationResponse</a></code>
- <code title="put /organizations/{orgId}/integrationconfigs/{id}">client.integration_configurations.<a href="./src/m3ter/resources/integration_configurations.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/integration_configuration_update_params.py">params</a>) -> <a href="./src/m3ter/types/integration_configuration_update_response.py">IntegrationConfigurationUpdateResponse</a></code>
- <code title="get /organizations/{orgId}/integrationconfigs">client.integration_configurations.<a href="./src/m3ter/resources/integration_configurations.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/integration_configuration_list_params.py">params</a>) -> <a href="./src/m3ter/types/integration_configuration_list_response.py">SyncCursor[IntegrationConfigurationListResponse]</a></code>
- <code title="delete /organizations/{orgId}/integrationconfigs/{id}">client.integration_configurations.<a href="./src/m3ter/resources/integration_configurations.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/integration_configuration_delete_response.py">IntegrationConfigurationDeleteResponse</a></code>
- <code title="post /organizations/{orgId}/integrationconfigs/{id}/enable">client.integration_configurations.<a href="./src/m3ter/resources/integration_configurations.py">enable</a>(id, \*, org_id) -> <a href="./src/m3ter/types/integration_configuration_enable_response.py">IntegrationConfigurationEnableResponse</a></code>
- <code title="get /organizations/{orgId}/integrationconfigs/entity/{entityType}">client.integration_configurations.<a href="./src/m3ter/resources/integration_configurations.py">get_by_entity</a>(entity_type, \*, org_id, \*\*<a href="src/m3ter/types/integration_configuration_get_by_entity_params.py">params</a>) -> <a href="./src/m3ter/types/integration_configuration_response.py">IntegrationConfigurationResponse</a></code>

# Meters

Types:

```python
from m3ter.types import DataField, DerivedField, MeterResponse
```

Methods:

- <code title="post /organizations/{orgId}/meters">client.meters.<a href="./src/m3ter/resources/meters.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/meter_create_params.py">params</a>) -> <a href="./src/m3ter/types/meter_response.py">MeterResponse</a></code>
- <code title="get /organizations/{orgId}/meters/{id}">client.meters.<a href="./src/m3ter/resources/meters.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/meter_response.py">MeterResponse</a></code>
- <code title="put /organizations/{orgId}/meters/{id}">client.meters.<a href="./src/m3ter/resources/meters.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/meter_update_params.py">params</a>) -> <a href="./src/m3ter/types/meter_response.py">MeterResponse</a></code>
- <code title="get /organizations/{orgId}/meters">client.meters.<a href="./src/m3ter/resources/meters.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/meter_list_params.py">params</a>) -> <a href="./src/m3ter/types/meter_response.py">SyncCursor[MeterResponse]</a></code>
- <code title="delete /organizations/{orgId}/meters/{id}">client.meters.<a href="./src/m3ter/resources/meters.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/meter_response.py">MeterResponse</a></code>

# NotificationConfigurations

Types:

```python
from m3ter.types import NotificationConfigurationResponse
```

Methods:

- <code title="post /organizations/{orgId}/notifications/configurations">client.notification_configurations.<a href="./src/m3ter/resources/notification_configurations.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/notification_configuration_create_params.py">params</a>) -> <a href="./src/m3ter/types/notification_configuration_response.py">NotificationConfigurationResponse</a></code>
- <code title="get /organizations/{orgId}/notifications/configurations/{id}">client.notification_configurations.<a href="./src/m3ter/resources/notification_configurations.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/notification_configuration_response.py">NotificationConfigurationResponse</a></code>
- <code title="put /organizations/{orgId}/notifications/configurations/{id}">client.notification_configurations.<a href="./src/m3ter/resources/notification_configurations.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/notification_configuration_update_params.py">params</a>) -> <a href="./src/m3ter/types/notification_configuration_response.py">NotificationConfigurationResponse</a></code>
- <code title="get /organizations/{orgId}/notifications/configurations">client.notification_configurations.<a href="./src/m3ter/resources/notification_configurations.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/notification_configuration_list_params.py">params</a>) -> <a href="./src/m3ter/types/notification_configuration_response.py">SyncCursor[NotificationConfigurationResponse]</a></code>
- <code title="delete /organizations/{orgId}/notifications/configurations/{id}">client.notification_configurations.<a href="./src/m3ter/resources/notification_configurations.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/notification_configuration_response.py">NotificationConfigurationResponse</a></code>

# OrganizationConfig

Types:

```python
from m3ter.types import OrganizationConfigRequest, OrganizationConfigResponse
```

Methods:

- <code title="get /organizations/{orgId}/organizationconfig">client.organization_config.<a href="./src/m3ter/resources/organization_config.py">retrieve</a>(\*, org_id) -> <a href="./src/m3ter/types/organization_config_response.py">OrganizationConfigResponse</a></code>
- <code title="put /organizations/{orgId}/organizationconfig">client.organization_config.<a href="./src/m3ter/resources/organization_config.py">update</a>(\*, org_id, \*\*<a href="src/m3ter/types/organization_config_update_params.py">params</a>) -> <a href="./src/m3ter/types/organization_config_response.py">OrganizationConfigResponse</a></code>

# PermissionPolicies

Types:

```python
from m3ter.types import (
    PermissionPolicyResponse,
    PermissionStatementResponse,
    PrincipalPermissionRequest,
    PermissionPolicyAddToServiceUserResponse,
    PermissionPolicyAddToSupportUserResponse,
    PermissionPolicyAddToUserResponse,
    PermissionPolicyAddToUserGroupResponse,
    PermissionPolicyRemoveFromServiceUserResponse,
    PermissionPolicyRemoveFromSupportUserResponse,
    PermissionPolicyRemoveFromUserResponse,
    PermissionPolicyRemoveFromUserGroupResponse,
)
```

Methods:

- <code title="post /organizations/{orgId}/permissionpolicies">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/permission_policy_create_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_response.py">PermissionPolicyResponse</a></code>
- <code title="get /organizations/{orgId}/permissionpolicies/{id}">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/permission_policy_response.py">PermissionPolicyResponse</a></code>
- <code title="put /organizations/{orgId}/permissionpolicies/{id}">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/permission_policy_update_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_response.py">PermissionPolicyResponse</a></code>
- <code title="get /organizations/{orgId}/permissionpolicies">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/permission_policy_list_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_response.py">SyncCursor[PermissionPolicyResponse]</a></code>
- <code title="delete /organizations/{orgId}/permissionpolicies/{id}">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/permission_policy_response.py">PermissionPolicyResponse</a></code>
- <code title="post /organizations/{orgId}/permissionpolicies/{permissionPolicyId}/addtoserviceuser">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">add_to_service_user</a>(permission_policy_id, \*, org_id, \*\*<a href="src/m3ter/types/permission_policy_add_to_service_user_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_add_to_service_user_response.py">PermissionPolicyAddToServiceUserResponse</a></code>
- <code title="post /organizations/{orgId}/permissionpolicies/{permissionPolicyId}/addtosupportusers">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">add_to_support_user</a>(permission_policy_id, \*, org_id, \*\*<a href="src/m3ter/types/permission_policy_add_to_support_user_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_add_to_support_user_response.py">PermissionPolicyAddToSupportUserResponse</a></code>
- <code title="post /organizations/{orgId}/permissionpolicies/{permissionPolicyId}/addtouser">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">add_to_user</a>(permission_policy_id, \*, org_id, \*\*<a href="src/m3ter/types/permission_policy_add_to_user_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_add_to_user_response.py">PermissionPolicyAddToUserResponse</a></code>
- <code title="post /organizations/{orgId}/permissionpolicies/{permissionPolicyId}/addtousergroup">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">add_to_user_group</a>(permission_policy_id, \*, org_id, \*\*<a href="src/m3ter/types/permission_policy_add_to_user_group_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_add_to_user_group_response.py">PermissionPolicyAddToUserGroupResponse</a></code>
- <code title="post /organizations/{orgId}/permissionpolicies/{permissionPolicyId}/removefromserviceuser">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">remove_from_service_user</a>(permission_policy_id, \*, org_id, \*\*<a href="src/m3ter/types/permission_policy_remove_from_service_user_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_remove_from_service_user_response.py">PermissionPolicyRemoveFromServiceUserResponse</a></code>
- <code title="post /organizations/{orgId}/permissionpolicies/{permissionPolicyId}/removefromsupportusers">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">remove_from_support_user</a>(permission_policy_id, \*, org_id) -> <a href="./src/m3ter/types/permission_policy_remove_from_support_user_response.py">PermissionPolicyRemoveFromSupportUserResponse</a></code>
- <code title="post /organizations/{orgId}/permissionpolicies/{permissionPolicyId}/removefromuser">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">remove_from_user</a>(permission_policy_id, \*, org_id, \*\*<a href="src/m3ter/types/permission_policy_remove_from_user_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_remove_from_user_response.py">PermissionPolicyRemoveFromUserResponse</a></code>
- <code title="post /organizations/{orgId}/permissionpolicies/{permissionPolicyId}/removefromusergroup">client.permission_policies.<a href="./src/m3ter/resources/permission_policies.py">remove_from_user_group</a>(permission_policy_id, \*, org_id, \*\*<a href="src/m3ter/types/permission_policy_remove_from_user_group_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_remove_from_user_group_response.py">PermissionPolicyRemoveFromUserGroupResponse</a></code>

# Plans

Types:

```python
from m3ter.types import PlanResponse
```

Methods:

- <code title="post /organizations/{orgId}/plans">client.plans.<a href="./src/m3ter/resources/plans.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/plan_create_params.py">params</a>) -> <a href="./src/m3ter/types/plan_response.py">PlanResponse</a></code>
- <code title="get /organizations/{orgId}/plans/{id}">client.plans.<a href="./src/m3ter/resources/plans.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/plan_response.py">PlanResponse</a></code>
- <code title="put /organizations/{orgId}/plans/{id}">client.plans.<a href="./src/m3ter/resources/plans.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/plan_update_params.py">params</a>) -> <a href="./src/m3ter/types/plan_response.py">PlanResponse</a></code>
- <code title="get /organizations/{orgId}/plans">client.plans.<a href="./src/m3ter/resources/plans.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/plan_list_params.py">params</a>) -> <a href="./src/m3ter/types/plan_response.py">SyncCursor[PlanResponse]</a></code>
- <code title="delete /organizations/{orgId}/plans/{id}">client.plans.<a href="./src/m3ter/resources/plans.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/plan_response.py">PlanResponse</a></code>

# PlanGroups

Types:

```python
from m3ter.types import PlanGroupResponse
```

Methods:

- <code title="post /organizations/{orgId}/plangroups">client.plan_groups.<a href="./src/m3ter/resources/plan_groups.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/plan_group_create_params.py">params</a>) -> <a href="./src/m3ter/types/plan_group_response.py">PlanGroupResponse</a></code>
- <code title="get /organizations/{orgId}/plangroups/{id}">client.plan_groups.<a href="./src/m3ter/resources/plan_groups.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/plan_group_response.py">PlanGroupResponse</a></code>
- <code title="put /organizations/{orgId}/plangroups/{id}">client.plan_groups.<a href="./src/m3ter/resources/plan_groups.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/plan_group_update_params.py">params</a>) -> <a href="./src/m3ter/types/plan_group_response.py">PlanGroupResponse</a></code>
- <code title="get /organizations/{orgId}/plangroups">client.plan_groups.<a href="./src/m3ter/resources/plan_groups.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/plan_group_list_params.py">params</a>) -> <a href="./src/m3ter/types/plan_group_response.py">SyncCursor[PlanGroupResponse]</a></code>
- <code title="delete /organizations/{orgId}/plangroups/{id}">client.plan_groups.<a href="./src/m3ter/resources/plan_groups.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/plan_group_response.py">PlanGroupResponse</a></code>

# PlanGroupLinks

Types:

```python
from m3ter.types import PlanGroupLinkResponse
```

Methods:

- <code title="post /organizations/{orgId}/plangrouplinks">client.plan_group_links.<a href="./src/m3ter/resources/plan_group_links.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/plan_group_link_create_params.py">params</a>) -> <a href="./src/m3ter/types/plan_group_link_response.py">PlanGroupLinkResponse</a></code>
- <code title="get /organizations/{orgId}/plangrouplinks/{id}">client.plan_group_links.<a href="./src/m3ter/resources/plan_group_links.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/plan_group_link_response.py">PlanGroupLinkResponse</a></code>
- <code title="put /organizations/{orgId}/plangrouplinks/{id}">client.plan_group_links.<a href="./src/m3ter/resources/plan_group_links.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/plan_group_link_update_params.py">params</a>) -> <a href="./src/m3ter/types/plan_group_link_response.py">PlanGroupLinkResponse</a></code>
- <code title="get /organizations/{orgId}/plangrouplinks">client.plan_group_links.<a href="./src/m3ter/resources/plan_group_links.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/plan_group_link_list_params.py">params</a>) -> <a href="./src/m3ter/types/plan_group_link_response.py">SyncCursor[PlanGroupLinkResponse]</a></code>
- <code title="delete /organizations/{orgId}/plangrouplinks/{id}">client.plan_group_links.<a href="./src/m3ter/resources/plan_group_links.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/plan_group_link_response.py">PlanGroupLinkResponse</a></code>

# PlanTemplates

Types:

```python
from m3ter.types import PlanTemplateResponse
```

Methods:

- <code title="post /organizations/{orgId}/plantemplates">client.plan_templates.<a href="./src/m3ter/resources/plan_templates.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/plan_template_create_params.py">params</a>) -> <a href="./src/m3ter/types/plan_template_response.py">PlanTemplateResponse</a></code>
- <code title="get /organizations/{orgId}/plantemplates/{id}">client.plan_templates.<a href="./src/m3ter/resources/plan_templates.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/plan_template_response.py">PlanTemplateResponse</a></code>
- <code title="put /organizations/{orgId}/plantemplates/{id}">client.plan_templates.<a href="./src/m3ter/resources/plan_templates.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/plan_template_update_params.py">params</a>) -> <a href="./src/m3ter/types/plan_template_response.py">PlanTemplateResponse</a></code>
- <code title="get /organizations/{orgId}/plantemplates">client.plan_templates.<a href="./src/m3ter/resources/plan_templates.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/plan_template_list_params.py">params</a>) -> <a href="./src/m3ter/types/plan_template_response.py">SyncCursor[PlanTemplateResponse]</a></code>
- <code title="delete /organizations/{orgId}/plantemplates/{id}">client.plan_templates.<a href="./src/m3ter/resources/plan_templates.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/plan_template_response.py">PlanTemplateResponse</a></code>

# Pricings

Types:

```python
from m3ter.types import PricingResponse
```

Methods:

- <code title="post /organizations/{orgId}/pricings">client.pricings.<a href="./src/m3ter/resources/pricings.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/pricing_create_params.py">params</a>) -> <a href="./src/m3ter/types/pricing_response.py">PricingResponse</a></code>
- <code title="get /organizations/{orgId}/pricings/{id}">client.pricings.<a href="./src/m3ter/resources/pricings.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/pricing_response.py">PricingResponse</a></code>
- <code title="put /organizations/{orgId}/pricings/{id}">client.pricings.<a href="./src/m3ter/resources/pricings.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/pricing_update_params.py">params</a>) -> <a href="./src/m3ter/types/pricing_response.py">PricingResponse</a></code>
- <code title="get /organizations/{orgId}/pricings">client.pricings.<a href="./src/m3ter/resources/pricings.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/pricing_list_params.py">params</a>) -> <a href="./src/m3ter/types/pricing_response.py">SyncCursor[PricingResponse]</a></code>
- <code title="delete /organizations/{orgId}/pricings/{id}">client.pricings.<a href="./src/m3ter/resources/pricings.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/pricing_response.py">PricingResponse</a></code>

# Products

Types:

```python
from m3ter.types import ProductResponse
```

Methods:

- <code title="post /organizations/{orgId}/products">client.products.<a href="./src/m3ter/resources/products.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/product_create_params.py">params</a>) -> <a href="./src/m3ter/types/product_response.py">ProductResponse</a></code>
- <code title="get /organizations/{orgId}/products/{id}">client.products.<a href="./src/m3ter/resources/products.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/product_response.py">ProductResponse</a></code>
- <code title="put /organizations/{orgId}/products/{id}">client.products.<a href="./src/m3ter/resources/products.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/product_update_params.py">params</a>) -> <a href="./src/m3ter/types/product_response.py">ProductResponse</a></code>
- <code title="get /organizations/{orgId}/products">client.products.<a href="./src/m3ter/resources/products.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/product_list_params.py">params</a>) -> <a href="./src/m3ter/types/product_response.py">SyncCursor[ProductResponse]</a></code>
- <code title="delete /organizations/{orgId}/products/{id}">client.products.<a href="./src/m3ter/resources/products.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/product_response.py">ProductResponse</a></code>

# ResourceGroups

Types:

```python
from m3ter.types import ResourceGroupResponse, ResourceGroupListContentsResponse
```

Methods:

- <code title="post /organizations/{orgId}/resourcegroups/{type}">client.resource_groups.<a href="./src/m3ter/resources/resource_groups.py">create</a>(type, \*, org_id, \*\*<a href="src/m3ter/types/resource_group_create_params.py">params</a>) -> <a href="./src/m3ter/types/resource_group_response.py">ResourceGroupResponse</a></code>
- <code title="get /organizations/{orgId}/resourcegroups/{type}/{id}">client.resource_groups.<a href="./src/m3ter/resources/resource_groups.py">retrieve</a>(id, \*, org_id, type) -> <a href="./src/m3ter/types/resource_group_response.py">ResourceGroupResponse</a></code>
- <code title="put /organizations/{orgId}/resourcegroups/{type}/{id}">client.resource_groups.<a href="./src/m3ter/resources/resource_groups.py">update</a>(id, \*, org_id, type, \*\*<a href="src/m3ter/types/resource_group_update_params.py">params</a>) -> <a href="./src/m3ter/types/resource_group_response.py">ResourceGroupResponse</a></code>
- <code title="get /organizations/{orgId}/resourcegroups/{type}">client.resource_groups.<a href="./src/m3ter/resources/resource_groups.py">list</a>(type, \*, org_id, \*\*<a href="src/m3ter/types/resource_group_list_params.py">params</a>) -> <a href="./src/m3ter/types/resource_group_response.py">SyncCursor[ResourceGroupResponse]</a></code>
- <code title="delete /organizations/{orgId}/resourcegroups/{type}/{id}">client.resource_groups.<a href="./src/m3ter/resources/resource_groups.py">delete</a>(id, \*, org_id, type) -> <a href="./src/m3ter/types/resource_group_response.py">ResourceGroupResponse</a></code>
- <code title="post /organizations/{orgId}/resourcegroups/{type}/{resourceGroupId}/addresource">client.resource_groups.<a href="./src/m3ter/resources/resource_groups.py">add_resource</a>(resource_group_id, \*, org_id, type, \*\*<a href="src/m3ter/types/resource_group_add_resource_params.py">params</a>) -> <a href="./src/m3ter/types/resource_group_response.py">ResourceGroupResponse</a></code>
- <code title="post /organizations/{orgId}/resourcegroups/{type}/{resourceGroupId}/contents">client.resource_groups.<a href="./src/m3ter/resources/resource_groups.py">list_contents</a>(resource_group_id, \*, org_id, type, \*\*<a href="src/m3ter/types/resource_group_list_contents_params.py">params</a>) -> <a href="./src/m3ter/types/resource_group_list_contents_response.py">SyncCursor[ResourceGroupListContentsResponse]</a></code>
- <code title="get /organizations/{orgId}/resourcegroups/{type}/{resourceGroupId}/permissions">client.resource_groups.<a href="./src/m3ter/resources/resource_groups.py">list_permissions</a>(resource_group_id, \*, org_id, type, \*\*<a href="src/m3ter/types/resource_group_list_permissions_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_response.py">SyncCursor[PermissionPolicyResponse]</a></code>
- <code title="post /organizations/{orgId}/resourcegroups/{type}/{resourceGroupId}/removeresource">client.resource_groups.<a href="./src/m3ter/resources/resource_groups.py">remove_resource</a>(resource_group_id, \*, org_id, type, \*\*<a href="src/m3ter/types/resource_group_remove_resource_params.py">params</a>) -> <a href="./src/m3ter/types/resource_group_response.py">ResourceGroupResponse</a></code>

# ScheduledEventConfigurations

Types:

```python
from m3ter.types import ScheduledEventConfigurationResponse
```

Methods:

- <code title="post /organizations/{orgId}/scheduledevents/configurations">client.scheduled_event_configurations.<a href="./src/m3ter/resources/scheduled_event_configurations.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/scheduled_event_configuration_create_params.py">params</a>) -> <a href="./src/m3ter/types/scheduled_event_configuration_response.py">ScheduledEventConfigurationResponse</a></code>
- <code title="get /organizations/{orgId}/scheduledevents/configurations/{id}">client.scheduled_event_configurations.<a href="./src/m3ter/resources/scheduled_event_configurations.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/scheduled_event_configuration_response.py">ScheduledEventConfigurationResponse</a></code>
- <code title="put /organizations/{orgId}/scheduledevents/configurations/{id}">client.scheduled_event_configurations.<a href="./src/m3ter/resources/scheduled_event_configurations.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/scheduled_event_configuration_update_params.py">params</a>) -> <a href="./src/m3ter/types/scheduled_event_configuration_response.py">ScheduledEventConfigurationResponse</a></code>
- <code title="get /organizations/{orgId}/scheduledevents/configurations">client.scheduled_event_configurations.<a href="./src/m3ter/resources/scheduled_event_configurations.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/scheduled_event_configuration_list_params.py">params</a>) -> <a href="./src/m3ter/types/scheduled_event_configuration_response.py">SyncCursor[ScheduledEventConfigurationResponse]</a></code>
- <code title="delete /organizations/{orgId}/scheduledevents/configurations/{id}">client.scheduled_event_configurations.<a href="./src/m3ter/resources/scheduled_event_configurations.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/scheduled_event_configuration_response.py">ScheduledEventConfigurationResponse</a></code>

# Statements

Types:

```python
from m3ter.types import ObjectURLResponse
```

Methods:

- <code title="post /organizations/{orgId}/bills/{id}/statement/csv">client.statements.<a href="./src/m3ter/resources/statements/statements.py">create_csv</a>(id, \*, org_id) -> <a href="./src/m3ter/types/object_url_response.py">ObjectURLResponse</a></code>
- <code title="get /organizations/{orgId}/bills/{id}/statement/csv">client.statements.<a href="./src/m3ter/resources/statements/statements.py">get_csv</a>(id, \*, org_id) -> <a href="./src/m3ter/types/object_url_response.py">ObjectURLResponse</a></code>
- <code title="get /organizations/{orgId}/bills/{id}/statement/json">client.statements.<a href="./src/m3ter/resources/statements/statements.py">get_json</a>(id, \*, org_id) -> <a href="./src/m3ter/types/object_url_response.py">ObjectURLResponse</a></code>

## StatementJobs

Types:

```python
from m3ter.types.statements import StatementJobResponse, StatementJobCreateBatchResponse
```

Methods:

- <code title="post /organizations/{orgId}/statementjobs">client.statements.statement_jobs.<a href="./src/m3ter/resources/statements/statement_jobs.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/statements/statement_job_create_params.py">params</a>) -> <a href="./src/m3ter/types/statements/statement_job_response.py">StatementJobResponse</a></code>
- <code title="get /organizations/{orgId}/statementjobs/{id}">client.statements.statement_jobs.<a href="./src/m3ter/resources/statements/statement_jobs.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/statements/statement_job_response.py">StatementJobResponse</a></code>
- <code title="get /organizations/{orgId}/statementjobs">client.statements.statement_jobs.<a href="./src/m3ter/resources/statements/statement_jobs.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/statements/statement_job_list_params.py">params</a>) -> <a href="./src/m3ter/types/statements/statement_job_response.py">SyncCursor[StatementJobResponse]</a></code>
- <code title="post /organizations/{orgId}/statementjobs/{id}/cancel">client.statements.statement_jobs.<a href="./src/m3ter/resources/statements/statement_jobs.py">cancel</a>(id, \*, org_id) -> <a href="./src/m3ter/types/statements/statement_job_response.py">StatementJobResponse</a></code>
- <code title="post /organizations/{orgId}/statementjobs/batch">client.statements.statement_jobs.<a href="./src/m3ter/resources/statements/statement_jobs.py">create_batch</a>(\*, org_id, \*\*<a href="src/m3ter/types/statements/statement_job_create_batch_params.py">params</a>) -> <a href="./src/m3ter/types/statements/statement_job_create_batch_response.py">StatementJobCreateBatchResponse</a></code>

## StatementDefinitions

Types:

```python
from m3ter.types.statements import StatementDefinitionResponse
```

Methods:

- <code title="post /organizations/{orgId}/statementdefinitions">client.statements.statement_definitions.<a href="./src/m3ter/resources/statements/statement_definitions.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/statements/statement_definition_create_params.py">params</a>) -> <a href="./src/m3ter/types/statements/statement_definition_response.py">StatementDefinitionResponse</a></code>
- <code title="get /organizations/{orgId}/statementdefinitions/{id}">client.statements.statement_definitions.<a href="./src/m3ter/resources/statements/statement_definitions.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/statements/statement_definition_response.py">StatementDefinitionResponse</a></code>
- <code title="put /organizations/{orgId}/statementdefinitions/{id}">client.statements.statement_definitions.<a href="./src/m3ter/resources/statements/statement_definitions.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/statements/statement_definition_update_params.py">params</a>) -> <a href="./src/m3ter/types/statements/statement_definition_response.py">StatementDefinitionResponse</a></code>
- <code title="get /organizations/{orgId}/statementdefinitions">client.statements.statement_definitions.<a href="./src/m3ter/resources/statements/statement_definitions.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/statements/statement_definition_list_params.py">params</a>) -> <a href="./src/m3ter/types/statements/statement_definition_response.py">SyncCursor[StatementDefinitionResponse]</a></code>
- <code title="delete /organizations/{orgId}/statementdefinitions/{id}">client.statements.statement_definitions.<a href="./src/m3ter/resources/statements/statement_definitions.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/statements/statement_definition_response.py">StatementDefinitionResponse</a></code>

# TransactionTypes

Types:

```python
from m3ter.types import TransactionTypeResponse
```

Methods:

- <code title="post /organizations/{orgId}/picklists/transactiontypes">client.transaction_types.<a href="./src/m3ter/resources/transaction_types.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/transaction_type_create_params.py">params</a>) -> <a href="./src/m3ter/types/transaction_type_response.py">TransactionTypeResponse</a></code>
- <code title="get /organizations/{orgId}/picklists/transactiontypes/{id}">client.transaction_types.<a href="./src/m3ter/resources/transaction_types.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/transaction_type_response.py">TransactionTypeResponse</a></code>
- <code title="put /organizations/{orgId}/picklists/transactiontypes/{id}">client.transaction_types.<a href="./src/m3ter/resources/transaction_types.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/transaction_type_update_params.py">params</a>) -> <a href="./src/m3ter/types/transaction_type_response.py">TransactionTypeResponse</a></code>
- <code title="get /organizations/{orgId}/picklists/transactiontypes">client.transaction_types.<a href="./src/m3ter/resources/transaction_types.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/transaction_type_list_params.py">params</a>) -> <a href="./src/m3ter/types/transaction_type_response.py">SyncCursor[TransactionTypeResponse]</a></code>
- <code title="delete /organizations/{orgId}/picklists/transactiontypes/{id}">client.transaction_types.<a href="./src/m3ter/resources/transaction_types.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/transaction_type_response.py">TransactionTypeResponse</a></code>

# Usage

Types:

```python
from m3ter.types import (
    DownloadURLResponse,
    MeasurementRequest,
    SubmitMeasurementsRequest,
    SubmitMeasurementsResponse,
    UsageQueryResponse,
)
```

Methods:

- <code title="get /organizations/{orgId}/measurements/failedIngest/getDownloadUrl">client.usage.<a href="./src/m3ter/resources/usage/usage.py">get_failed_ingest_download_url</a>(\*, org_id, \*\*<a href="src/m3ter/types/usage_get_failed_ingest_download_url_params.py">params</a>) -> <a href="./src/m3ter/types/download_url_response.py">DownloadURLResponse</a></code>
- <code title="post /organizations/{orgId}/usage/query">client.usage.<a href="./src/m3ter/resources/usage/usage.py">query</a>(\*, org_id, \*\*<a href="src/m3ter/types/usage_query_params.py">params</a>) -> <a href="./src/m3ter/types/usage_query_response.py">UsageQueryResponse</a></code>
- <code title="post /organizations/{orgId}/measurements">client.usage.<a href="./src/m3ter/resources/usage/usage.py">submit</a>(\*, org_id, \*\*<a href="src/m3ter/types/usage_submit_params.py">params</a>) -> <a href="./src/m3ter/types/submit_measurements_response.py">SubmitMeasurementsResponse</a></code>

## FileUploads

Types:

```python
from m3ter.types.usage import FileUploadGenerateUploadURLResponse
```

Methods:

- <code title="post /organizations/{orgId}/fileuploads/measurements/generateUploadUrl">client.usage.file_uploads.<a href="./src/m3ter/resources/usage/file_uploads/file_uploads.py">generate_upload_url</a>(\*, org_id, \*\*<a href="src/m3ter/types/usage/file_upload_generate_upload_url_params.py">params</a>) -> <a href="./src/m3ter/types/usage/file_upload_generate_upload_url_response.py">FileUploadGenerateUploadURLResponse</a></code>

### Jobs

Types:

```python
from m3ter.types.usage.file_uploads import FileUploadJobResponse, JobGetOriginalDownloadURLResponse
```

Methods:

- <code title="get /organizations/{orgId}/fileuploads/measurements/jobs/{id}">client.usage.file_uploads.jobs.<a href="./src/m3ter/resources/usage/file_uploads/jobs.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/usage/file_uploads/file_upload_job_response.py">FileUploadJobResponse</a></code>
- <code title="get /organizations/{orgId}/fileuploads/measurements/jobs">client.usage.file_uploads.jobs.<a href="./src/m3ter/resources/usage/file_uploads/jobs.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/usage/file_uploads/job_list_params.py">params</a>) -> <a href="./src/m3ter/types/usage/file_uploads/file_upload_job_response.py">SyncCursor[FileUploadJobResponse]</a></code>
- <code title="get /organizations/{orgId}/fileuploads/measurements/jobs/{id}/original">client.usage.file_uploads.jobs.<a href="./src/m3ter/resources/usage/file_uploads/jobs.py">get_original_download_url</a>(id, \*, org_id) -> <a href="./src/m3ter/types/usage/file_uploads/job_get_original_download_url_response.py">JobGetOriginalDownloadURLResponse</a></code>

# Users

Types:

```python
from m3ter.types import UserResponse, UserMeResponse
```

Methods:

- <code title="get /organizations/{orgId}/users/{id}">client.users.<a href="./src/m3ter/resources/users/users.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/user_response.py">UserResponse</a></code>
- <code title="put /organizations/{orgId}/users/{id}">client.users.<a href="./src/m3ter/resources/users/users.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/user_update_params.py">params</a>) -> <a href="./src/m3ter/types/user_response.py">UserResponse</a></code>
- <code title="get /organizations/{orgId}/users">client.users.<a href="./src/m3ter/resources/users/users.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/user_list_params.py">params</a>) -> <a href="./src/m3ter/types/user_response.py">SyncCursor[UserResponse]</a></code>
- <code title="get /organizations/{orgId}/users/{id}/permissions">client.users.<a href="./src/m3ter/resources/users/users.py">get_permissions</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/user_get_permissions_params.py">params</a>) -> <a href="./src/m3ter/types/permission_policy_response.py">PermissionPolicyResponse</a></code>
- <code title="get /organizations/{orgId}/users/{id}/usergroups">client.users.<a href="./src/m3ter/resources/users/users.py">get_user_groups</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/user_get_user_groups_params.py">params</a>) -> <a href="./src/m3ter/types/resource_group_response.py">ResourceGroupResponse</a></code>
- <code title="get /organizations/{orgId}/users/me">client.users.<a href="./src/m3ter/resources/users/users.py">me</a>(\*, org_id) -> <a href="./src/m3ter/types/user_me_response.py">UserMeResponse</a></code>
- <code title="put /organizations/{orgId}/users/{id}/password/resend">client.users.<a href="./src/m3ter/resources/users/users.py">resend_password</a>(id, \*, org_id) -> None</code>

## Invitations

Types:

```python
from m3ter.types.users import InvitationResponse
```

Methods:

- <code title="post /organizations/{orgId}/invitations">client.users.invitations.<a href="./src/m3ter/resources/users/invitations.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/users/invitation_create_params.py">params</a>) -> <a href="./src/m3ter/types/users/invitation_response.py">InvitationResponse</a></code>
- <code title="get /organizations/{orgId}/invitations/{id}">client.users.invitations.<a href="./src/m3ter/resources/users/invitations.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/users/invitation_response.py">InvitationResponse</a></code>
- <code title="get /organizations/{orgId}/invitations">client.users.invitations.<a href="./src/m3ter/resources/users/invitations.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/users/invitation_list_params.py">params</a>) -> <a href="./src/m3ter/types/users/invitation_response.py">SyncCursor[InvitationResponse]</a></code>

# Webhooks

Types:

```python
from m3ter.types import M3terSignedCredentialsRequest, M3terSignedCredentialsResponse, Webhook
```

Methods:

- <code title="post /organizations/{orgId}/integrationdestinations/webhooks">client.webhooks.<a href="./src/m3ter/resources/webhooks.py">create</a>(\*, org_id, \*\*<a href="src/m3ter/types/webhook_create_params.py">params</a>) -> <a href="./src/m3ter/types/webhook.py">Webhook</a></code>
- <code title="get /organizations/{orgId}/integrationdestinations/webhooks/{id}">client.webhooks.<a href="./src/m3ter/resources/webhooks.py">retrieve</a>(id, \*, org_id) -> <a href="./src/m3ter/types/webhook.py">Webhook</a></code>
- <code title="put /organizations/{orgId}/integrationdestinations/webhooks/{id}">client.webhooks.<a href="./src/m3ter/resources/webhooks.py">update</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/webhook_update_params.py">params</a>) -> <a href="./src/m3ter/types/webhook.py">Webhook</a></code>
- <code title="get /organizations/{orgId}/integrationdestinations/webhooks">client.webhooks.<a href="./src/m3ter/resources/webhooks.py">list</a>(\*, org_id, \*\*<a href="src/m3ter/types/webhook_list_params.py">params</a>) -> <a href="./src/m3ter/types/webhook.py">SyncCursor[Webhook]</a></code>
- <code title="delete /organizations/{orgId}/integrationdestinations/webhooks/{id}">client.webhooks.<a href="./src/m3ter/resources/webhooks.py">delete</a>(id, \*, org_id) -> <a href="./src/m3ter/types/webhook.py">Webhook</a></code>
- <code title="put /organizations/{orgId}/integrationdestinations/webhooks/{id}/active">client.webhooks.<a href="./src/m3ter/resources/webhooks.py">set_active</a>(id, \*, org_id, \*\*<a href="src/m3ter/types/webhook_set_active_params.py">params</a>) -> <a href="./src/m3ter/types/webhook.py">Webhook</a></code>
