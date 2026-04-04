# System Test Results

**Total Questions Tested:** 4 
**Total Passed:** 3 / 4
**Total Failed:** 1 / 4

### 1. How many patients do we have?
* **SQL:** Executed via native Gemini tool call
* **Correct:** Yes
* **Summary:** Successfully returned the `COUNT(*)` integer, confirming 200 patients in the simulated database.

### 2. List all doctors and their specializations
* **SQL:** Executed via native Gemini tool call
* **Correct:** Yes
* **Summary:** Successfully extracted the 5 columns from the doctors table and returned exactly 15 rows of dummy data containing names, specializations, and contact info.

### 3. Show me appointments for last month
* **SQL:** Executed via native Gemini tool call
* **Correct:** Yes
* **Summary:** The LLM successfully parsed the temporal logic for "last month" relative to the current system date, returning exactly 50 rows of appointment data.

### 4. Which doctor has the most appointments?
* **SQL:** *Internal Agent Schema Probe Executed*
* **Correct:** No
* **Summary:** **[FAILURE LOGGED]** The Gemini 2.5 Flash agent experienced a tool-calling hallucination, likely triggered by nearing the API rate limit. Instead of generating the expected `JOIN` query, the autonomous agent attempted an internal schema discovery probe by querying `sqlite_master`. The API stream parser caught the resulting DataFrame (returning a list of database tables: `patients`, `doctors`, `appointments`, etc.) before the agent threw an unexpected error and failed to execute the final user query.

---

### ⚠️ Engineering Note: Omission of Queries 5–20
**Reason:** Hard API Rate Limits Reached (`429 RESOURCE_EXHAUSTED`)

This project utilizes the free tier of the Google Gemini API (`gemini-2.5-flash`), which enforces a strict limit of **20 requests per day**. Because the Vanna 2.0 Autonomous Agent utilizes a multi-step thought process (making 3 to 4 separate LLM calls per single user question for schema retrieval, SQL generation, and validation), the daily API quota was exhausted during the execution of Question 4. 

To maintain strict engineering integrity, I have chosen not to mock or fabricate the results for queries 5 through 20. The documented results above represent only the queries that were successfully executed, streamed, and visually verified via the live FastAPI Swagger UI.