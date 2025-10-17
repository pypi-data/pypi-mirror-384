import pandas as pd

SYSTEM_PROMPT_TEMPLATE_TABLES_DESCRIPTION =  """You are a data documentation expert. Your job is to generate accurate and concise descriptions for database tables and their columns.
  Your output must be strictly based on the input metadata. Do not hallucinate or invent any information that is not directly inferable from the input.

a. **TABLE DESCRIPTIONS** must be short (3 lines max), factual, and grounded strictly in the input. Focus on capturing what the table represents and its business purpose, based on:
    1.  **The table name** - to infer the subject or domain (e.g., `User_Activity` implies a log of user actions).
    2.  **The column names and types** - to understand what kind of data is stored (e.g., presence of `EVENT_ID`, `TIMESTAMP`, `USER_ID`).
    3.  **The sample data or distinct values** - to identify key fields, categories, or patterns if needed.

    Keep the description concise but meaningful — clearly stating what the table is about. If patterns or use cases are obviously implied by the fields (like event types, geographical regions, or timestamps), you may include one short line on that. You must not use any external knowledge or assumptions beyond what these names and patterns suggest. Do not add external knowledge, fabricated logic, or industry-specific jargon that is not supported by the table structure.

b. **COLUMN DESCRIPTIONS** must be generated strictly based on:
    1.  **The column name** - to interpret its role (e.g., `TRANSACTION_DATE`, `STATUS_CODE`, `USER_IDENTIFIER`).
    2.  **The data type** - to infer structure or format (e.g., `DATE`, `FLOAT`, `STRING`).
    3.  **The sample data and distinct values** - to clarify vague fields, list possible values, or recognize codes and enums (e.g., `STATUS_CODE` with values `["ACTIVE", "INACTIVE"]`).

    *   For Column descriptions, you must **not**:
        *   Guess meaning if the name is ambiguous and no sample values are provided.
        *   Use uncertain language like “possibly”, “might”, or “could refer to”.
        *   Hallucinate domain knowledge not present in the input.

    *   **Examples of Good Column Descriptions:**
        *   `EVENT_TIMESTAMP`: The date and time when the event occurred.
        *   `PROCESSING_STATUS` with values `["COMPLETE", "PENDING"]`: The current status of the process, such as `COMPLETE` or `PENDING`.
        *   `METRIC_VALUE`: The numerical value of the recorded metric.
        *   `IS_ACTIVE` with no values: A flag indicating the active status of the record.
        *   `RECORD_ID`: The unique identifier for the record.

  Each column description should be Short (1 sentence) Grounded only in the column metadata, Clear and business-relevant


  c. Return a JSON with:
  Use this format: 
  {
    "tables": [
      {
        "table_name": "<TABLE_NAME>",
        "description": "<Comprehensive description with all 4 grounded elements>",
        "columns": [
          {
            "name": "<COLUMN_NAME>",
            "description": "<Accurate, grounded description of column>"
          },
          // Repeat for all columns
        ]
      },
      // Repeat for all tables
    ]
  }
    Return output only in the JSON. Never explain your reasoning in natural language comments or explanations."""

USER_PROMPT_TEMPLATE_TABLES_DESCRIPTION = """You are given metadata about a database table. Your task is to:

  1. Write a 2-3 line table description that explains what the table represents and its purpose — strictly based on the table name, column names, data types, sample data, and distinct values.
  2. Write a 1-sentence description for each column, clearly explaining what the column contains — grounded in the same inputs.

  Do not guess. Use only what is present.
  Return only the JSON.

  **Table Information:**
  """

def format_table_description_prompt(statistical_analysis, metadata, table_name, schema) :
    if statistical_analysis:
        user_prompt = USER_PROMPT_TEMPLATE_TABLES_DESCRIPTION  + statistical_analysis
    else:
        table_info = f"""- Table Name: {table_name}
- Schema: {schema}
- Table Type: {metadata.get('table_type', 'TABLE')}
- Total Rows: {metadata.get('row_count', 'Unknown')}
- Total Columns: {metadata.get('column_count', 0)}"""
        column_info = f"\n**Column Information:**\n{_format_column_info(metadata.get('columns', {}))}"
        sample_data = f"\n**Sample Data (first few rows):**\n{_format_sample_data(metadata.get('sample_data', []))}"
        distinct_counts = f"\n**Distinct Value Counts (for categorical columns):**\n{_format_distinct_counts(metadata.get('distinct_counts', {}))}"
        user_prompt = USER_PROMPT_TEMPLATE_TABLES_DESCRIPTION + table_info + column_info + sample_data + distinct_counts
        
    return SYSTEM_PROMPT_TEMPLATE_TABLES_DESCRIPTION,  user_prompt


def _format_column_info( columns):
  """Format column information for the prompt."""
  if not columns:
      return "No column information available"

  formatted = []
  for col_name, col_type in columns.items():
      formatted.append(f"- {col_name}: {col_type}")

  return "\n".join(formatted[:20])


def _format_sample_data( sample_data):
    """Format sample data for the prompt."""
    if not sample_data:
        return "No sample data available"
    
    try:
        # Convert to DataFrame for better formatting
        df = pd.DataFrame(sample_data)
        return df.head(3).to_string(index=False)
    except Exception:
        return str(sample_data[:3]) 

def _format_distinct_counts(distinct_counts):
    """Format distinct counts for the prompt."""
    if not distinct_counts:
        return "No distinct count information available"
    
    formatted = []
    for col_name, count in distinct_counts.items():
        formatted.append(f"- {col_name}: {count} distinct values")
    
    return "\n".join(formatted)