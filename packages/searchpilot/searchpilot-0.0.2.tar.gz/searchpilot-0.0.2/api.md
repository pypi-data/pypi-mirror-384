# External

## V1

### Accounts

Types:

```python
from searchpilot.types.external.v1 import Account, AccountListResponse
```

Methods:

- <code title="get /api/external/v1/accounts/{account_slug}/">client.external.v1.accounts.<a href="./src/searchpilot/resources/external/v1/accounts.py">retrieve</a>(account_slug) -> <a href="./src/searchpilot/types/external/v1/account.py">Account</a></code>
- <code title="get /api/external/v1/accounts/">client.external.v1.accounts.<a href="./src/searchpilot/resources/external/v1/accounts.py">list</a>(\*\*<a href="src/searchpilot/types/external/v1/account_list_params.py">params</a>) -> <a href="./src/searchpilot/types/external/v1/account_list_response.py">AccountListResponse</a></code>

### Customers

Types:

```python
from searchpilot.types.external.v1 import Customer, CustomerListResponse
```

Methods:

- <code title="get /api/external/v1/customers/{customer_slug}/">client.external.v1.customers.<a href="./src/searchpilot/resources/external/v1/customers.py">retrieve</a>(customer_slug) -> <a href="./src/searchpilot/types/external/v1/customer.py">Customer</a></code>
- <code title="get /api/external/v1/customers/">client.external.v1.customers.<a href="./src/searchpilot/resources/external/v1/customers.py">list</a>(\*\*<a href="src/searchpilot/types/external/v1/customer_list_params.py">params</a>) -> <a href="./src/searchpilot/types/external/v1/customer_list_response.py">CustomerListResponse</a></code>

### Experiments

Types:

```python
from searchpilot.types.external.v1 import Experiment, HasherEnum, NullEnum, ExperimentListResponse
```

Methods:

- <code title="get /api/external/v1/experiments/{experiment_id}/">client.external.v1.experiments.<a href="./src/searchpilot/resources/external/v1/experiments.py">retrieve</a>(experiment_id) -> <a href="./src/searchpilot/types/external/v1/experiment.py">Experiment</a></code>
- <code title="get /api/external/v1/experiments/">client.external.v1.experiments.<a href="./src/searchpilot/resources/external/v1/experiments.py">list</a>(\*\*<a href="src/searchpilot/types/external/v1/experiment_list_params.py">params</a>) -> <a href="./src/searchpilot/types/external/v1/experiment_list_response.py">ExperimentListResponse</a></code>

### Rules

Types:

```python
from searchpilot.types.external.v1 import Rule, RuleListResponse
```

Methods:

- <code title="get /api/external/v1/rules/{rule_id}/">client.external.v1.rules.<a href="./src/searchpilot/resources/external/v1/rules.py">retrieve</a>(rule_id) -> <a href="./src/searchpilot/types/external/v1/rule.py">Rule</a></code>
- <code title="get /api/external/v1/rules/">client.external.v1.rules.<a href="./src/searchpilot/resources/external/v1/rules.py">list</a>(\*\*<a href="src/searchpilot/types/external/v1/rule_list_params.py">params</a>) -> <a href="./src/searchpilot/types/external/v1/rule_list_response.py">RuleListResponse</a></code>

### Sections

Types:

```python
from searchpilot.types.external.v1 import Section, SectionListResponse
```

Methods:

- <code title="get /api/external/v1/sections/{account_slug}/{section_slug}/">client.external.v1.sections.<a href="./src/searchpilot/resources/external/v1/sections.py">retrieve</a>(section_slug, \*, account_slug) -> <a href="./src/searchpilot/types/external/v1/section.py">Section</a></code>
- <code title="get /api/external/v1/sections/">client.external.v1.sections.<a href="./src/searchpilot/resources/external/v1/sections.py">list</a>(\*\*<a href="src/searchpilot/types/external/v1/section_list_params.py">params</a>) -> <a href="./src/searchpilot/types/external/v1/section_list_response.py">SectionListResponse</a></code>

### SeoExperimentResults

Types:

```python
from searchpilot.types.external.v1 import SeoExperimentResult, SeoExperimentResultListResponse
```

Methods:

- <code title="get /api/external/v1/seo_experiment_results/{seo_experiment_result_id}/">client.external.v1.seo_experiment_results.<a href="./src/searchpilot/resources/external/v1/seo_experiment_results.py">retrieve</a>(seo_experiment_result_id) -> <a href="./src/searchpilot/types/external/v1/seo_experiment_result.py">SeoExperimentResult</a></code>
- <code title="get /api/external/v1/seo_experiment_results/">client.external.v1.seo_experiment_results.<a href="./src/searchpilot/resources/external/v1/seo_experiment_results.py">list</a>(\*\*<a href="src/searchpilot/types/external/v1/seo_experiment_result_list_params.py">params</a>) -> <a href="./src/searchpilot/types/external/v1/seo_experiment_result_list_response.py">SeoExperimentResultListResponse</a></code>

### Steps

Types:

```python
from searchpilot.types.external.v1 import Step, StepListResponse
```

Methods:

- <code title="get /api/external/v1/steps/{step_id}/">client.external.v1.steps.<a href="./src/searchpilot/resources/external/v1/steps.py">retrieve</a>(step_id) -> <a href="./src/searchpilot/types/external/v1/step.py">Step</a></code>
- <code title="get /api/external/v1/steps/">client.external.v1.steps.<a href="./src/searchpilot/resources/external/v1/steps.py">list</a>(\*\*<a href="src/searchpilot/types/external/v1/step_list_params.py">params</a>) -> <a href="./src/searchpilot/types/external/v1/step_list_response.py">StepListResponse</a></code>

### Values

Types:

```python
from searchpilot.types.external.v1 import Value, ValueListResponse
```

Methods:

- <code title="get /api/external/v1/values/{value_id}/">client.external.v1.values.<a href="./src/searchpilot/resources/external/v1/values.py">retrieve</a>(value_id) -> <a href="./src/searchpilot/types/external/v1/value.py">Value</a></code>
- <code title="get /api/external/v1/values/">client.external.v1.values.<a href="./src/searchpilot/resources/external/v1/values.py">list</a>(\*\*<a href="src/searchpilot/types/external/v1/value_list_params.py">params</a>) -> <a href="./src/searchpilot/types/external/v1/value_list_response.py">ValueListResponse</a></code>
