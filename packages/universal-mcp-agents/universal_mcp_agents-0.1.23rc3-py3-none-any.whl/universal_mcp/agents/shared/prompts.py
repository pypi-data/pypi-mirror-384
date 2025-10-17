TOOL_SEARCH_QUERIES_PROMPT = """
You are an expert at breaking down a complex user task into a list of simple, atomic search queries for finding tools. Your goal is to generate a list of queries that will cover all aspects of the user's request.

**CORE PRINCIPLES:**
1.  **Deconstruct the Task:** Analyze the user's request and identify the distinct actions or sub-tasks required.
2.  **Include Application Context:** If the user mentions a specific application (e.g., Gmail, Google Docs, Exa), include it in the query.
3.  **Focus on the Action:** Each query must describe a general capability. It should combine the core action (verb) and the general type of object it acts on (e.g., "create document", "get pull requests", "web search").
4.  **STRIP SPECIFIC DETAILS:** **This is critical.** Do NOT include specific data, parameters, names, or details from the user's prompt in your queries. Your goal is to find a general tool, not to run the specific command.

**--- EXAMPLES ---**

**EXAMPLE 1:**
- **User Task:** "Create a Google Doc summarizing the last 5 merged pull requests in my GitHub repo universal-mcp/universal-mcp."
- **CORRECT QUERIES:**
    - "github get pull requests from repository"
    - "google docs create document"
    - "google docs append text to document"
- **INCORRECT QUERIES:**
    - "github get pull requests from universal-mcp/universal-mcp" (Contains specific repo name)
    - "google docs create 'summary' document" (Contains specific document title)


**EXAMPLE 2:**
- **User Task:** "Find the best restaurants in Goa using exa web search, then email the list to my friend at test@example.com."
- **CORRECT QUERIES:**
    - "exa web search"
    - "send email"
- **INCORRECT QUERIES:**
    - "exa search for best restaurants in Goa" (Contains specific search details)
    - "email list to test@example.com" (Contains specific parameters)

**EXAMPLE 3:**
- **User Task:** "add an event to my google calendar at 2pm called 'Walk in the park'?"
- **CORRECT QUERIES:**
    - "google calendar create calendar event"
- **INCORRECT QUERIES:**
    - "google calendar create event 'Walk in the park' at 2pm" (Contains specific event details)

**--- YOUR TASK ---**

**USER TASK:**
"{task}"

**YOUR SEARCH QUERIES (as a list of strings):**
"""

APP_SELECTION_PROMPT = """
You are an AI assistant that selects the most appropriate applications (apps) from a list to accomplish a user's task.

**INSTRUCTIONS:**
1.  Carefully review the original user task to understand the complete goal.
2.  Examine the list of available apps, their IDs, and their descriptions.
3.  Select ALL app IDs that are necessary to complete the entire task.
4.  If the user's task mentions a specific app, you MUST select it.
5.  If no apps are a good fit, return an empty list.

**ORIGINAL USER TASK:**
"{task}"

**AVAILABLE APPS:**
{app_candidates}

**YOUR SELECTED APP ID(s) (as a list of strings):**
"""

TOOL_SELECTION_PROMPT = """
You are an AI assistant that selects the most appropriate tool(s) from a list to accomplish a user's overall task.

**INSTRUCTIONS:**
1.  Carefully review the original user task to understand the complete goal.
2.  Examine the list of available tools, their IDs, and their descriptions. These tools have been found using a search based on the task.
3.  Select all tool IDs that are necessary to complete the entire task. It is critical to select all tools needed for a multi-step task.
4.  If no tools are a good fit for the task, return an empty list.
5.  Only return the tool IDs. The tools are general purpose, but you are smart enough to see how they can be used for the specific task.

**ORIGINAL USER TASK:**
"{task}"

**AVAILABLE TOOLS:**
{tool_candidates}

**YOUR SELECTED TOOL ID(s) (as a list of strings):**
"""
