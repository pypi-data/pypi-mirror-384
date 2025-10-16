# Shared Types

```python
from distillery.types import (
    Account,
    Customer,
    Experiment,
    Rule,
    Section,
    SeoExperimentResult,
    Step,
    Value,
)
```

# Customers

Methods:

- <code title="get /api/external/v1/customers/{customer_slug}/">client.customers.<a href="./src/distillery/resources/customers.py">retrieve</a>(customer_slug) -> <a href="./src/distillery/types/shared/customer.py">Customer</a></code>
- <code title="get /api/external/v1/customers/">client.customers.<a href="./src/distillery/resources/customers.py">list</a>(\*\*<a href="src/distillery/types/customer_list_params.py">params</a>) -> <a href="./src/distillery/types/shared/customer.py">SyncCursorURLPage[Customer]</a></code>

# Accounts

Methods:

- <code title="get /api/external/v1/accounts/{account_slug}/">client.accounts.<a href="./src/distillery/resources/accounts.py">retrieve</a>(account_slug) -> <a href="./src/distillery/types/shared/account.py">Account</a></code>
- <code title="get /api/external/v1/accounts/">client.accounts.<a href="./src/distillery/resources/accounts.py">list</a>(\*\*<a href="src/distillery/types/account_list_params.py">params</a>) -> <a href="./src/distillery/types/shared/account.py">SyncCursorURLPage[Account]</a></code>

# Sections

Methods:

- <code title="get /api/external/v1/sections/{account_slug}/{section_slug}/">client.sections.<a href="./src/distillery/resources/sections.py">retrieve</a>(section_slug, \*, account_slug) -> <a href="./src/distillery/types/shared/section.py">Section</a></code>
- <code title="get /api/external/v1/sections/">client.sections.<a href="./src/distillery/resources/sections.py">list</a>(\*\*<a href="src/distillery/types/section_list_params.py">params</a>) -> <a href="./src/distillery/types/shared/section.py">SyncCursorURLPage[Section]</a></code>

# Rules

Methods:

- <code title="get /api/external/v1/rules/{rule_id}/">client.rules.<a href="./src/distillery/resources/rules.py">retrieve</a>(rule_id) -> <a href="./src/distillery/types/shared/rule.py">Rule</a></code>
- <code title="get /api/external/v1/rules/">client.rules.<a href="./src/distillery/resources/rules.py">list</a>(\*\*<a href="src/distillery/types/rule_list_params.py">params</a>) -> <a href="./src/distillery/types/shared/rule.py">SyncCursorURLPage[Rule]</a></code>

# Steps

Methods:

- <code title="get /api/external/v1/steps/{step_id}/">client.steps.<a href="./src/distillery/resources/steps.py">retrieve</a>(step_id) -> <a href="./src/distillery/types/shared/step.py">Step</a></code>
- <code title="get /api/external/v1/steps/">client.steps.<a href="./src/distillery/resources/steps.py">list</a>(\*\*<a href="src/distillery/types/step_list_params.py">params</a>) -> <a href="./src/distillery/types/shared/step.py">SyncCursorURLPage[Step]</a></code>

# Values

Methods:

- <code title="get /api/external/v1/values/{value_id}/">client.values.<a href="./src/distillery/resources/values.py">retrieve</a>(value_id) -> <a href="./src/distillery/types/shared/value.py">Value</a></code>
- <code title="get /api/external/v1/values/">client.values.<a href="./src/distillery/resources/values.py">list</a>(\*\*<a href="src/distillery/types/value_list_params.py">params</a>) -> <a href="./src/distillery/types/shared/value.py">SyncCursorURLPage[Value]</a></code>

# Experiments

Methods:

- <code title="get /api/external/v1/experiments/{experiment_id}/">client.experiments.<a href="./src/distillery/resources/experiments.py">retrieve</a>(experiment_id) -> <a href="./src/distillery/types/shared/experiment.py">Experiment</a></code>
- <code title="get /api/external/v1/experiments/">client.experiments.<a href="./src/distillery/resources/experiments.py">list</a>(\*\*<a href="src/distillery/types/experiment_list_params.py">params</a>) -> <a href="./src/distillery/types/shared/experiment.py">SyncCursorURLPage[Experiment]</a></code>

# SeoExperimentResults

Methods:

- <code title="get /api/external/v1/seo_experiment_results/{seo_experiment_result_id}/">client.seo_experiment_results.<a href="./src/distillery/resources/seo_experiment_results.py">retrieve</a>(seo_experiment_result_id) -> <a href="./src/distillery/types/shared/seo_experiment_result.py">SeoExperimentResult</a></code>
- <code title="get /api/external/v1/seo_experiment_results/">client.seo_experiment_results.<a href="./src/distillery/resources/seo_experiment_results.py">list</a>(\*\*<a href="src/distillery/types/seo_experiment_result_list_params.py">params</a>) -> <a href="./src/distillery/types/shared/seo_experiment_result.py">SyncCursorURLPage[SeoExperimentResult]</a></code>
