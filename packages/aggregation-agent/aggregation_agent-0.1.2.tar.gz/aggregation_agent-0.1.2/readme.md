
An AI-powered data aggregation tool that intelligently analyzes a dataset and provides smart suggestions for aggregation strategies.

## Description

This agent analyzes a given dataset and its associated metadata (such as domain description, entity descriptions, and column descriptions) to propose intelligent data aggregation strategies. It uses a large language model to:

1.  **Identify** the most relevant columns to group the data by.
2.  **Suggest** appropriate aggregation methods (e.g., `Sum`, `Mean`, `Max`, `Count`) for the remaining columns based on their data types and context.

This is particularly useful for accelerating feature engineering and preparing data for machine learning or advanced analytics tasks.

## Key Features

-   **Intelligent Data Analysis**: Leverages LLMs to understand the semantic context of your data, including domain, entity, and column descriptions.
-   **Automatic Group-By Identification**: Automatically pinpoints the most meaningful categorical or discrete columns for grouping.
-   **Context-Aware Aggregation Suggestions**: Recommends aggregation functions (`SUM`, `AVG`, `COUNT`, etc.) that are appropriate for each column's data type and business meaning.
-   **Accelerates Feature Engineering**: Significantly reduces the manual effort required to explore and create aggregated features from raw data.

## Installation

### Prerequisites

-   [**uv**](https://docs.astral.sh/uv/getting-started/installation/) – A fast Python package and environment manager.
    -   For a quick setup on macOS/Linux, you can use:
        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```
-   [**Git**](https://git-scm.com/)

### Steps

1.  **Clone the `aggregation_agent` repository:**
    ```bash
    git clone https://github.com/stepfnAI/aggregation_agent.git
    cd aggregation_agent
    git switch dev
    ```

2.  **Create a virtual environment and install dependencies:**
    This command creates a `.venv` folder in the current directory and installs all required packages.
    ```bash
    uv sync --extra dev
    source .venv/bin/activate
    ```

3.  **Clone and install the `sfn_blueprint` dependency:**
    The agent requires the `sfn_blueprint` library. The following commands clone it into a sibling directory and install it in editable mode.
    ```bash
    cd ../
    git clone https://github.com/stepfnAI/sfn_blueprint.git
    cd sfn_blueprint
    git switch dev
    uv pip install -e .
    cd ../aggregation_agent
    ```


## Configuration

You can configure the agent in two ways: using a `.env` file for project-specific settings or by exporting environment variables for more dynamic, shell-level control. Settings loaded via `export` will take precedence over those in a `.env` file.

### Available Settings

The following table details the configuration options available:

| Environment Variable        | Description                                  | Default      |
| --------------------------- | -------------------------------------------- | ------------ |
| `OPENAI_API_KEY`            | **(Required)** Your OpenAI API key.          | *None*       |
| `AGGREGATION_AI_PROVIDER`   | AI provider for aggregation suggestions.     | `openai`     |
| `AGGREGATION_MODEL`         | AI model for aggregation suggestions.        | `gpt-4o`     |
| `TEMPERATURE`               | AI model temperature (e.g., `0.0` to `2.0`). | `0.3`        |
| `MAX_TOKENS`                | Maximum tokens for the AI response.          | `4000`       |
| `GROUP_BY_AI_PROVIDER`      | AI provider for group-by column mapping.     | `openai`     |
| `GROUP_BY_MODEL`            | AI model for group-by column mapping.        | `gpt-4o`     |

---

### Method 1: Using a `.env` File (Recommended)

For consistent configuration within your project, create a file named `.env` in the root directory and add your settings. This method is ideal for storing API keys and project-wide defaults.

1.  Create a file named `.env` in the root of your project.
2.  Add the key-value pairs for the settings you wish to override.

#### Example `.env` file:

```dotenv
# .env

# --- Required Settings ---
ANTHROPIC_API_KEY="sk-your-api-key-here"

# --- Optional Overrides ---
# Use a different model for aggregation
AGGREGATION_AI_PROVIDER="anthropic"
AGGREGATION_MODEL="claude-3-sonnet-20240229"

# Use a higher temperature for more creative responses
TEMPERATURE=0.7
```

---

### Method 2: Using `export` Commands

For temporary settings or use in CI/CD environments, you can `export` variables directly in your terminal shell. These variables are set for the current session and will override any values defined in your `.env` file.

1.  Open your terminal.
2.  Use the `export` command to set a variable before running your application.

#### Example `export` commands:

This example sets a different model and token limit for a single run of your script.

```bash
# Set the environment variables for the current terminal session
export OPENAI_API_KEY="sk-your-api-key-here"
export AGGREGATION_MODEL="gpt-4o-mini"
export MAX_TOKENS=6000
```

**Note:** The variable names are identical for both the `.env` file and the `export` command. The application will automatically detect and use them based on this hierarchy.
## Testing

To run the test suite, use the following command from the root of the `aggregation_agent` directory:

```bash
pytest
```

## Usage

### Running the Example Script

To see a quick demonstration, run the provided example script from the root of the project directory. This will execute the agent with pre-defined metadata and print the resulting aggregation suggestions to the console.

```bash
python example/basic_usage.py
```

### Using as a Library

You can also integrate the `AggregationAgent` directly into your Python applications. The following example demonstrates how to define your data's context and get intelligent aggregation suggestions.
```python
from aggregation_agent import AggregationAgent

# 1. Define the domain and data context
domain_name = "Mortgage Servicing"

domain_description = """Business Purpose:
- Manage mortgage loans post-origination through payoff or foreclosure, including international loans, accommodating cross-border legal and regulatory requirements.
- Ensure timely payment collection and regulatory compliance, both domestically and internationally.
- Support borrowers with escrow management, loan modifications, and navigating the complexities of international property ownership.

Core Business Activities:
- Process mortgage payments (principal, interest, taxes, insurance) for both domestic and international properties.
- Manage escrow disbursements for taxes and insurance, adapting to the requirements of different countries.
- Track delinquencies, defaults, and foreclosures, with a specialized focus on international loan agreements.
- Handle borrower communications and support, providing guidance on international mortgage servicing practices.
- Process loan modifications, forbearance, and payoffs, including those involving foreign currency transactions.

Key Stakeholders:
- Borrower: Responsible for making mortgage payments, including international clients.
- Servicer: Manages loan servicing for lender/investor, with expertise in both domestic and international mortgages.
- Investor: Owns the mortgage asset, which may include international properties.
- Regulator: Ensures compliance with servicing standards, including international regulations.
- Insurer: Provides mortgage insurance, adapting policies to cover international properties.
- Tax Authorities: Receive property tax payments from escrow, including those from abroad.

Typical Information Systems:
- Loan servicing platforms (e.g., MSP by Black Knight, Sagent) equipped to handle international transactions.
- Escrow management systems that accommodate multiple currencies and international tax and insurance payments.
- Customer support and ticketing tools with multilingual and multicurrency capabilities.
- Compliance and regulatory reporting systems, designed for both domestic and international standards.

Data Sensitivities:
- Borrower PII and financial data, including that of international clients.
- Loan payment histories, encompassing both domestic and international loans.
- Data subject to CFPB, privacy regulations, and international data protection laws.

Potential Use Cases:
- Predict delinquencies using payment history and credit scores, including for international borrowers.
- Forecast escrow adjustments based on tax and insurance changes, with considerations for international market fluctuations.
- Detect payment anomalies and potential fraud in both domestic and international transactions.
- Predict early payoff or refinance likelihood, including the impact of currency exchange rates on international loans.
- Optimize customer support using risk-based prioritization, factoring in the complexities of international mortgage management."""

table_category = "Customer Data"
entity_description = {"Borrower Profile": "Contains personal and financial details of borrowers applying for or servicing mortgage loans."}

column_description = {
  "Address": "Residential address of the borrower",
  "BorrowerId": "Unique identifier for the borrower",
  "ContactNumber": "Primary phone number",
  "CreditScore": "Borrower's credit score from credit bureau sources",
  "DateOfBirth": "Borrower's date of birth",
  "Email": "Email address for communication",
  "EmploymentStatus": "Current employment status (e.g., employed, self-employed, unemployed)",
  "FirstName": "Borrower's first name",
  "LastName": "Borrower's last name",
  "SocialSecurityNumber": "Government issued identification number"
}

semantic_to_column = {
    "Borrower Address": "Address",
    "Borrower Identifier": "BorrowerId",
    "Phone Number": "ContactNumber",
    "Credit Score": "CreditScore",
    "Date of Birth": "DateOfBirth",
    "Email Address": "Email",
    "Employment Status": "EmploymentStatus",
    "First Name": "FirstName",
    "Last Name": "LastName",
    "Government ID Number": "SocialSecurityNumber"
}

# 2. Prepare the task data payload
task_data = {
    "file": "example/Borrower_Profile.csv",
    "domain_name": domain_name,
    "domain_description": domain_description,
    "column_description" : column_description,
    "entity_description": entity_description,
    "mappings": semantic_to_column,
    "table_category": table_category
}

# 3. Initialize and execute the agent
agent = AggregationAgent()
result = agent.execute_task(task_data)

# 4. Print the suggested aggregation strategy
print(result)

```

### Example Output

The agent will return a JSON object containing the suggested columns to group by and the recommended aggregation functions for other relevant columns.

*(Note: The actual output may vary slightly based on the LLM's response.)*

```json
{
  "success": true,
  "result": {
    "aggregation_suggestions": {
      "Address": [
        {
          "method": "Unique Count",
          "explanation": "Counts distinct addresses to identify unique residences."
        },
        {
          "method": "Mode",
          "explanation": "Finds the most common address, indicating popular locations."
        }
      ],
      "ContactNumber": [
        {
          "method": "Unique Count",
          "explanation": "Counts distinct contact numbers to identify unique phone numbers."
        },
        {
          "method": "Last Value",
          "explanation": "Captures the most recent contact number for up-to-date communication."
        }
      ],
      "CreditScore": [
        {
          "method": "Mean",
          "explanation": "Calculates the average credit score to assess overall creditworthiness."
        },
        {
          "method": "Median",
          "explanation": "Finds the middle credit score, useful when data is skewed."
        }
      ],
      "DateOfBirth": [
        {
          "method": "Unique Count",
          "explanation": "Counts distinct birth dates to identify unique individuals."
        }
      ],
      "Email": [
        {
          "method": "Unique Count",
          "explanation": "Counts distinct emails to identify unique communication addresses."
        },
        {
          "method": "Last Value",
          "explanation": "Captures the most recent email for current contact information."
        }
      ],
      "EmploymentStatus": [
        {
          "method": "Mode",
          "explanation": "Identifies the most common employment status among borrowers."
        },
        {
          "method": "Unique Count",
          "explanation": "Counts distinct employment statuses to understand diversity in employment."
        }
      ],
      "FirstName": [
        {
          "method": "Unique Count",
          "explanation": "Counts distinct first names to identify unique individuals."
        },
        {
          "method": "Mode",
          "explanation": "Finds the most common first name, indicating popular names."
        }
      ],
      "LastName": [
        {
          "method": "Unique Count",
          "explanation": "Counts distinct last names to identify unique family names."
        },
        {
          "method": "Mode",
          "explanation": "Finds the most common last name, indicating popular surnames."
        }
      ],
      "SocialSecurityNumber": [
        {
          "method": "Unique Count",
          "explanation": "Counts distinct social security numbers to identify unique individuals."
        }
      ]
    },
    "groupby_columns": [
      "BorrowerId"
    ],
    "message": "Aggregation methods suggested and validated successfully."
  },
  "agent": "AggregationAgent"
}
```


