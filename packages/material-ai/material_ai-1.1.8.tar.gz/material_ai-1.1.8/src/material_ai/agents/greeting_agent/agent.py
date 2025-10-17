from google.adk.agents import Agent
from google.genai.types import Part, Blob
from material_ai.oauth import oauth_user_details_context
import csv
import io


def say_hello():
    return {"description": "Hi, what can I do for you today?"}


def who_am_i():
    user_details = oauth_user_details_context.get()
    return user_details


def create_csv(tool_context=None) -> str:
    """
    Creates sample CSV data and return the file
    """
    if tool_context is None:
        return {
            "status": "error",
            "message": "Tool context is missing, cannot save artifact.",
        }
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header and data rows
    writer.writerow(["ID", "Name", "Role"])
    writer.writerow(["1", "John Doe", "Engineer"])
    writer.writerow(["2", "Jane Smith", "Designer"])

    csv_content = output.getvalue()
    content_bytes = csv_content.encode("utf-8")
    output.close()
    artifact_part = Part(inline_data=Blob(data=content_bytes, mime_type="text/csv"))
    filename = "my-csv.csv"
    version = tool_context.save_artifact(filename=filename, artifact=artifact_part)
    return {
        "status": "success",
        "message": f"File '{filename}' (version {version}) has been created and is now available for download.",
    }


# Define the agent itself, giving it a name and description.
# The agent will automatically use the tools you provide in the list.
root_agent = Agent(
    name="greeting_agent",
    model="gemini-2.0-flash",
    description="An agent that can greet users.",
    instruction="""
    Use 'say_hello' tool to greet user, If user asks about himself use 'who_am_i' tool,
    If the users ask about a csv file use 'create_csv' tool
    """,
    tools=[say_hello, who_am_i, create_csv],
)
