Setup:

- Start meiliearch container:

```bash
docker run -it --rm -p 7700:7700 \
  --network host \
  -e MEILI_MASTER_KEY=test \
  -e MEILI_TASK_WEBHOOK_URL=http://localhost:8069/meilisearch/task-webhook/ \
  getmeili/meilisearch:latest
```

Configuration:

- Open the user group "Index Manager"
- Add your user to the group

Index Lifecycle:

- Open Meilisearch Index "Countries"
- Enable the index
- Click "Check API Key" and ensure it works
- Click on "Create Index" and "Update Index"
- Click "View Documents"
- Mark all records and run "Update Documents"
- Mark all records again and run "Check Documents"
- Open record "Schweiz" and check if documents match
- Click "Open Document" and append "X" to name
- Return to Document and click "Check Documents"
- Ensure indexed name is "SchweizX"

Cron job:

- Install the job_portal_meilisearch module
- For each Meilisearch index run create and update index
- Then update all documents for each index
- Set database for "Countries" to "odoo" and for "Job Offer" to current database name
- Open the scheduled actions and run "Meilisearch: Check all documents"
- Open the index list and check if the colument "Filtered" matches "Indexed"

Garbage collection:

- Open Meilisearch Index "Countries"
- Click "View Documents"
- Mark all records and run "Update Documents"
- Then "Delete Documents"
- Open Meilisearch Tasks
- Check if new tasks are created
- Open scheduled actions and run "Base: Auto-vacuum internal data"
- Open Meilisearch Tasks
- Check if only the deletion tasks are present

Disable task creation:

- Open Meilisearch Index "Countries"
- Disable Option "Create Tasks"
- Click "View Documents"
- Mark all records and run "Update Documents"
- Return to Index and click "View Tasks"
- Check that no tasks have been created
