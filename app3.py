import streamlit as st
import openai

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'income' not in st.session_state:
    st.session_state.income = 0
if 'expenses' not in st.session_state:
    st.session_state.expenses = {}
if 'suggested_budget' not in st.session_state:
    st.session_state.suggested_budget = {}

# Function to greet the user
def greet_user():
    st.write("Hello! I'm your budget planning chatbot. Let's get started with your budget planning.")

# Function to get the user's income
def get_income():
    income = st.number_input("Please enter your monthly income in rupees:", min_value=0.0, step=0.01)
    if st.button("Submit Income"):
        if income > 0:
            st.session_state.income = income
            st.session_state.step = 1
            st.session_state.suggested_budget = calculate_budget(income)
        else:
            st.write("Income must be a positive number. Please try again.")

# Function to calculate the suggested budget and store it in session state
def calculate_budget(income):
    suggested_budget = {
        "Rent": int(income * 0.30),          # 30% for rent
        "Food": int(income * 0.20),          # 20% for food
        "Savings": int(income * 0.20),       # 20% for savings
        "Utilities": int(income * 0.10),     # 10% for utilities
        "Entertainment": int(income * 0.10)  # 10% for entertainment
    }
    st.session_state.suggested_budget = suggested_budget  # Store in session state
    return suggested_budget

# Function to display the suggested budget plan (from session state)
def display_suggested_budget():
    st.write("Suggested budget plan based on your income:")
    for category, amount in st.session_state.suggested_budget.items():
        st.write(f"- {category}: ₹{amount:.2f}")

# Function to allow editing or removing categories in the suggested budget
def edit_or_remove_suggested_budget():
    suggested_budget = st.session_state.suggested_budget

    category_to_edit = st.selectbox("Select a suggested budget category to edit or remove:", 
                                    options=[""] + list(suggested_budget.keys()))

    if category_to_edit:
        action = st.radio("Choose action:", ["Edit", "Remove"])

        if action == "Edit":
            new_amount = st.number_input(f"New amount for {category_to_edit}:", min_value=0.0, step=0.01)

            if st.button(f"Update {category_to_edit}"):
                old_amount = suggested_budget[category_to_edit]
                amount_diff = new_amount - old_amount  # Find the change

                # Calculate remaining income before updating the category
                remaining_income = st.session_state.income - sum(suggested_budget.values()) + suggested_budget["Savings"]

                if remaining_income >= amount_diff:
                    # Only update Rent if there is enough income to adjust Savings
                    suggested_budget[category_to_edit] = new_amount  # Update the category

                    # Adjust Savings based on remaining income after other expenses
                    remaining_income_after_expense = st.session_state.income - sum(suggested_budget.values()) + suggested_budget["Savings"]
                    
                    if remaining_income_after_expense >= 0:
                        suggested_budget["Savings"] = remaining_income_after_expense  # Update Savings based on available remaining income
                    else:
                        st.write(f"Not enough funds to update {category_to_edit} to ₹{new_amount:.2f}. Savings cannot be updated as there is not enough income.")
                        return  # Prevent further updates if there are insufficient funds

                    st.session_state.suggested_budget = suggested_budget  # Store update
                    st.write(f"Updated {category_to_edit}: ₹{new_amount:.2f}")
                    st.write(f"New Savings: ₹{suggested_budget['Savings']:.2f}")
                else:
                    st.write(f"Insufficient funds! Can't update {category_to_edit} to ₹{new_amount:.2f}. Please adjust your expenses.")
                    return  # Prevent updating Rent if not enough money
                

        elif action == "Remove":
            if category_to_edit in suggested_budget:
                removed_amount = suggested_budget[category_to_edit]
                
                del suggested_budget[category_to_edit]  # Remove category
                
                # Add removed amount back to Savings
                if "Savings" in suggested_budget:
                    suggested_budget["Savings"] += removed_amount

                st.session_state.suggested_budget = suggested_budget  # Store update
                st.write(f"Removed {category_to_edit}. Added ₹{removed_amount:.2f} to Savings.")

# Function to calculate the actual budget plan
def calculate_actual_budget(income, expenses):
    total_expenses = sum(expenses.values())
    remaining_income = income - total_expenses
    return total_expenses, remaining_income

# Function to update the suggested budget based on remaining income after expenses
def update_suggested_budget_based_on_remaining_income(income, expenses):
    total_expenses = sum(expenses.values())
    remaining_income = income - total_expenses
    if remaining_income > 0:
        st.session_state.suggested_budget = calculate_budget(remaining_income)

# Function to display the actual budget plan (including extra expenses)
def display_actual_budget_plan(income, expenses, total_expenses, remaining_income):
    st.write(f"### Your Monthly Income: ₹{income:.2f}")
    
    st.write("#### Suggested Budget Plan:")
    for category, amount in st.session_state.suggested_budget.items():  # Fetching from session state
        st.write(f"- {category}: ₹{amount:.2f}")

    st.write("#### Extra Expenses You Added:")
    if expenses:
        for category, amount in expenses.items():
            st.write(f"- {category}: ₹{amount:.2f}")
    else:
        st.write("No additional expenses recorded.")

    st.write(f"### Total Expenses: ₹{total_expenses:.2f}")
    st.write(f"### Remaining Income: ₹{remaining_income:.2f}")

def check_budget_exceedance(expenses, suggested_budget):
    for category, amount in expenses.items():
        if category in suggested_budget and amount > suggested_budget[category]:
            st.warning(f"Warning: You have exceeded the budget for {category}! Suggested: ₹{suggested_budget[category]}, Actual: ₹{amount}")

# Function to get GPT recommendations securely
def get_gpt_recommendations(income, expenses, remaining_income):
    # Securely fetch API key from Streamlit secrets
    openai.api_key = st.secrets["openai"]["api_key"]

    prompt = (f"User's income is ₹{income}, current expenses: {expenses}, remaining income: ₹{remaining_income}. "
              "Provide personalized budgeting advice, suggest adjustments for saving, and reducing unnecessary expenses.")

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()

    except Exception as e:
        st.error("Error fetching GPT recommendations. Please try again later.")
        return str(e)

# Function to get expenses
def get_expenses():
    expenses = st.session_state.expenses  # Retrieve stored expenses

    # Display all added expenses dynamically
    if expenses:
        st.write("### Your Current Expenses:")
        for category, amount in expenses.items():
            st.write(f"- {category}: ₹{amount:.2f}")

    category = st.text_input("Enter an expense category (or type 'done' to finish):")

    if category:
        if category.lower() == 'done':
            if expenses:
                st.session_state.step = 2  # Move to the next step if expenses exist
            else:
                st.write("No extra expenses added.")
            return  # Exit function to prevent further execution
        
        amount = st.number_input(f"Enter the amount for {category} (in rupees):", min_value=0.0, step=0.01)

        if category in expenses:
            action = st.radio(f"'{category}' already exists. Choose an action:", ["Update amount", "Add to existing amount", "Remove Expense"])

            if action == "Update amount":
                if st.button(f"Update {category}"):
                    if amount > 0:
                        expenses[category] = amount  # Replace with new amount
                        st.session_state.expenses = expenses

            elif action == "Add to existing amount":
                if st.button(f"Add {amount} to {category}"):
                    expenses[category] += amount  # Add new amount to existing
                    st.session_state.expenses = expenses

            elif action == "Remove Expense":
                if st.button(f"Remove {category}"):
                    del expenses[category]  # Remove the expense
                    st.session_state.expenses = expenses

        else:
            if st.button("Add Expense"):
                if amount <= 0:
                    st.warning("Expense amount must be greater than zero.")
                else:
                    expenses[category] = amount
                    st.session_state.expenses = expenses

    # Recalculate and update budget after modifications
    total_expenses, remaining_income = calculate_actual_budget(st.session_state.income, expenses)
    display_actual_budget_plan(st.session_state.income, expenses, total_expenses, remaining_income)
    update_suggested_budget_based_on_remaining_income(st.session_state.income, expenses)
    display_suggested_budget()

    # Check for exceedance in the budget
    check_budget_exceedance(expenses, st.session_state.suggested_budget)

# Main function to run the app
def main():
    st.title("Budget Planner Chatbot")
    greet_user()

    if st.session_state.step == 0:
        get_income()
    elif st.session_state.step == 1:
        st.write("Suggested budget based on your income:")
        display_suggested_budget()
        get_expenses()
        edit_or_remove_suggested_budget()  # Allow editing/removal of suggested budget

        if st.button("View Updated Budget"):
            income = st.session_state.income
            expenses = st.session_state.expenses
            total_expenses, remaining_income = calculate_actual_budget(income, expenses)

    elif st.session_state.step == 2:
        income = st.session_state.income
        expenses = st.session_state.expenses
        total_expenses, remaining_income = calculate_actual_budget(income, expenses)
        display_actual_budget_plan(income, expenses, total_expenses, remaining_income)

        gpt_advice = get_gpt_recommendations(income, expenses, remaining_income)
        st.write("GPT Budgeting Advice: ", gpt_advice)

        if st.button("Update Expenses"):
            st.session_state.step = 1

if __name__ == "__main__":
    main()
