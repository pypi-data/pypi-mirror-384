# Defend

Types:

```python
from deeprails.types import DefendResponse, WorkflowEventResponse
```

Methods:

- <code title="post /defend">client.defend.<a href="./src/deeprails/resources/defend.py">create_workflow</a>(\*\*<a href="src/deeprails/types/defend_create_workflow_params.py">params</a>) -> <a href="./src/deeprails/types/defend_response.py">DefendResponse</a></code>
- <code title="get /defend/{workflow_id}/events/{event_id}">client.defend.<a href="./src/deeprails/resources/defend.py">retrieve_event</a>(event_id, \*, workflow_id) -> <a href="./src/deeprails/types/workflow_event_response.py">WorkflowEventResponse</a></code>
- <code title="get /defend/{workflow_id}">client.defend.<a href="./src/deeprails/resources/defend.py">retrieve_workflow</a>(workflow_id) -> <a href="./src/deeprails/types/defend_response.py">DefendResponse</a></code>
- <code title="post /defend/{workflow_id}/events">client.defend.<a href="./src/deeprails/resources/defend.py">submit_event</a>(workflow_id, \*\*<a href="src/deeprails/types/defend_submit_event_params.py">params</a>) -> <a href="./src/deeprails/types/workflow_event_response.py">WorkflowEventResponse</a></code>
- <code title="put /defend/{workflow_id}">client.defend.<a href="./src/deeprails/resources/defend.py">update_workflow</a>(workflow_id, \*\*<a href="src/deeprails/types/defend_update_workflow_params.py">params</a>) -> <a href="./src/deeprails/types/defend_response.py">DefendResponse</a></code>

# Monitor

Types:

```python
from deeprails.types import APIResponse, MonitorRetrieveResponse, MonitorSubmitEventResponse
```

Methods:

- <code title="post /monitor">client.monitor.<a href="./src/deeprails/resources/monitor.py">create</a>(\*\*<a href="src/deeprails/types/monitor_create_params.py">params</a>) -> <a href="./src/deeprails/types/api_response.py">APIResponse</a></code>
- <code title="get /monitor/{monitor_id}">client.monitor.<a href="./src/deeprails/resources/monitor.py">retrieve</a>(monitor_id, \*\*<a href="src/deeprails/types/monitor_retrieve_params.py">params</a>) -> <a href="./src/deeprails/types/monitor_retrieve_response.py">MonitorRetrieveResponse</a></code>
- <code title="put /monitor/{monitor_id}">client.monitor.<a href="./src/deeprails/resources/monitor.py">update</a>(monitor_id, \*\*<a href="src/deeprails/types/monitor_update_params.py">params</a>) -> <a href="./src/deeprails/types/api_response.py">APIResponse</a></code>
- <code title="post /monitor/{monitor_id}/events">client.monitor.<a href="./src/deeprails/resources/monitor.py">submit_event</a>(monitor_id, \*\*<a href="src/deeprails/types/monitor_submit_event_params.py">params</a>) -> <a href="./src/deeprails/types/monitor_submit_event_response.py">MonitorSubmitEventResponse</a></code>

# Evaluate

Types:

```python
from deeprails.types import Evaluation
```

Methods:

- <code title="post /evaluate">client.evaluate.<a href="./src/deeprails/resources/evaluate.py">create</a>(\*\*<a href="src/deeprails/types/evaluate_create_params.py">params</a>) -> <a href="./src/deeprails/types/evaluation.py">Evaluation</a></code>
- <code title="get /evaluate/{eval_id}">client.evaluate.<a href="./src/deeprails/resources/evaluate.py">retrieve</a>(eval_id) -> <a href="./src/deeprails/types/evaluation.py">Evaluation</a></code>
