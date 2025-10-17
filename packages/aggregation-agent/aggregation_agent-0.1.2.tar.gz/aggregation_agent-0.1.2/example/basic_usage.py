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
result = agent(task_data)

# 4. Print the suggested aggregation strategy
print(result)