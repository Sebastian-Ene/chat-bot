Just a POC. Did not consider making the ai logging necessary work for another dev or other ai tools than Claude.

Diagram:

Nginx/AWS load balancer ->((server docker): uvicorn -> fastapi app )-> ( (db docker) vector db)

Use uvicorn + fastapi for speed (async)