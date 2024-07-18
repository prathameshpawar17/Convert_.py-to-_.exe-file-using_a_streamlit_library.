import streamlit as st
import pandas as pd
import calendar
import os
import csv

# Initialize data
tasks_file = "tasks.csv"
if os.path.exists(tasks_file):
    tasks = pd.read_csv(tasks_file)["Tasks"].tolist()
else:
    tasks = ["Reception", "Em-M", "Em-Ev", "Em-N", "Mob Medical", "Physio", "Dialysis", "Dental"]
    pd.DataFrame({"Tasks": tasks}).to_csv(tasks_file, index=False)

# Function to get the number of days in a month
def get_days_in_month(month_name):
    month_index = list(calendar.month_name).index(month_name)
    if month_index == 2:  # February
        return 28
    elif month_index in [4, 6, 9, 11]:  # April, June, September, November
        return 30
    else:
        return 31

# Load employees from file
def load_employees():
    if os.path.exists("employees.csv"):
        employees = []
        with open("employees.csv", mode="r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                employees.append({
                    "id": row["id"],
                    "name": row["name"],
                    "positive_tasks": [task.strip() for task in row["positive_tasks"].split(", ") if task.strip()]
                })
        return employees
    else:
        return [{"id": f"E{i}", "name": f"Name {i}", "positive_tasks": []} for i in range(1, 11)]

# Save employees to file
def save_employees(employees):
    with open("employees.csv", mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "name", "positive_tasks"])
        writer.writeheader()
        for employee in employees:
            writer.writerow({
                "id": employee["id"],
                "name": employee["name"],
                "positive_tasks": ", ".join(employee["positive_tasks"])
            })

# Load allocations from file
def load_allocations(month_name):
    file_name = f"allocations_{month_name}.csv"
    if os.path.exists(file_name):
        allocations = pd.read_csv(
            file_name, index_col=0, nrows=get_days_in_month(month_name),
            converters={task: lambda x: eval(x) if isinstance(x, str) else [] for task in tasks}
        )
        # Ensure that the index is integer
        allocations.index = allocations.index.map(int)
        return allocations
    else:
        allocations = pd.DataFrame(index=range(1, get_days_in_month(month_name) + 1), columns=tasks).apply(
            lambda x: [[] for _ in x])
        return allocations

# Save allocations to file
def save_allocations(month_name, allocations):
    filename = f"allocations_{month_name}.csv"
    allocations.to_csv(filename)

# Save tasks to file
def save_tasks():
    pd.DataFrame({"Tasks": tasks}).to_csv(tasks_file, index=False)

# Function to get the day names for each day in the month
def get_day_names(month_name):
    month_index = list(calendar.month_name).index(month_name)
    return list(range(1, get_days_in_month(month_name) + 1))

# Unallocate an employee from a task
def unallocate_employee(day, task, emp_id):
    if emp_id in st.session_state.allocations.at[day, task]:
        st.session_state.allocations.at[day, task].remove(emp_id)
        save_allocations(st.session_state.selected_month, st.session_state.allocations)

# Streamlit application
st.title("3rdEyeAI, a product of CAP CORPORATE AI SOLUTIONS LLP")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Allocation", "Employee and Task Master List"])

if page == "Allocation":
    st.header("Task Allocation - 3rdEyeAI, a product of CAP CORPORATE AI SOLUTIONS LLP")

    # Select month
    month = st.selectbox("Select month", list(calendar.month_name)[1:])

    # Refresh allocations when month changes
    if "selected_month" not in st.session_state:
        st.session_state.selected_month = month
        st.session_state.allocations = load_allocations(month)
    elif st.session_state.selected_month != month:
        st.session_state.selected_month = month
        st.session_state.allocations = load_allocations(month)

    # Ensure tasks are consistent in allocations
    for task in tasks:
        if task not in st.session_state.allocations.columns:
            st.session_state.allocations[task] = [[] for _ in range(get_days_in_month(month))]

    # Handle removal of tasks not in the current task list
    for column in st.session_state.allocations.columns:
        if column not in tasks:
            st.session_state.allocations.drop(columns=[column], inplace=True)

    # Reorder the columns to match the task list
    st.session_state.allocations = st.session_state.allocations[tasks]

    # Save and Upload buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Allocations"):
            save_allocations(month, st.session_state.allocations)
            st.success(f"Allocations saved to 'allocations_{month}.csv'.")

    with col2:
        uploaded_file = st.file_uploader("Upload Allocations CSV", type=["csv"])
        if uploaded_file is not None:
            uploaded_df = pd.read_csv(uploaded_file, index_col=0, converters={task: eval for task in tasks})
            st.session_state.allocations.update(uploaded_df)
            st.success("Allocations loaded from uploaded file.")

    # Select day
    day = st.number_input("Select day to allocate task", min_value=1, max_value=get_days_in_month(month), value=1)

    # Select task
    task = st.selectbox("Select task", tasks)

    def get_employee_lists(day, task):
        allocated_employees = set(
            sum(st.session_state.allocations.loc[day].apply(lambda x: x if isinstance(x, list) else []).values, []))
        available_employees = []
        disallowed_employees = []

        employees = load_employees()

        for e in employees:
            emp_display = f"{e['id']} - {e['name']}"
            if e["id"] in allocated_employees:
                continue
            if task in e["positive_tasks"]:
                available_employees.append(emp_display)
            else:
                disallowed_employees.append(emp_display)

        return available_employees, disallowed_employees

    available_employees, disallowed_employees = get_employee_lists(day, task)

    selected_employee = st.selectbox("Select employee for task", available_employees + disallowed_employees,
                                     format_func=lambda x: x if x in available_employees else f"{x} (disallowed)")

    if st.button("Allocate Task"):
        if selected_employee:
            emp_id = selected_employee.split(" - ")[0]
            if emp_id not in st.session_state.allocations.at[day, task]:
                st.session_state.allocations.at[day, task].append(emp_id)
                st.success(f"Task '{task}' on day {day} allocated to {selected_employee}.")
                available_employees, disallowed_employees = get_employee_lists(day, task)
            else:
                st.warning(f"Task '{task}' on day {day} is already allocated to {selected_employee}.")

    # Reset allocations dropdown and button
    reset_options = ["All"] + [f"Day {i}" for i in range(1, get_days_in_month(month) + 1)]
    reset_choice = st.selectbox("Reset allocations for", reset_options)
    if st.button("Reset Allocations"):
        if reset_choice == "All":
            st.session_state.allocations = pd.DataFrame(index=range(1, get_days_in_month(month) + 1), columns=tasks).apply(
                lambda x: [[] for _ in x])
        else:
            day_to_reset = int(reset_choice.split(" ")[1])
            for task in tasks:
                st.session_state.allocations.at[day_to_reset, task] = []
        st.success(f"Allocations reset for {reset_choice}.")
        available_employees, disallowed_employees = get_employee_lists(day, task)

    # Custom CSS
    st.markdown("""
        <style>
        .employee-bubble {
            display: inline-block;
            background-color: #e0e0e0;
            padding: 2px 6px;
            border-radius: 4px;
            margin: 2px;
            position: relative;
        }
        td {
            white-space: nowrap;
        }
        </style>
    """, unsafe_allow_html=True)

    # Display allocation table with custom styling for disallowed employees
    def style_cell(value, day, task):
        if isinstance(value, list) and value:
            styled_employees = [f'<span class="employee-bubble">{emp_id}</span>' for emp_id in value]
            return "".join(styled_employees)
        return ""

    # Create a copy of the allocations dataframe for styling
    styled_allocations = st.session_state.allocations.copy()

    # Apply the style function to each cell
    for day in range(1, get_days_in_month(month) + 1):
        for task in tasks:
            if task in st.session_state.allocations.columns:
                styled_allocations.at[day, task] = style_cell(st.session_state.allocations.at[day, task], day, task)

    # Add day numbers as the index
    day_numbers = list(range(1, get_days_in_month(month) + 1))
    styled_allocations.index = day_numbers

    # Display styled dataframe
    st.subheader("Current Allocations")
    st.markdown(styled_allocations.to_html(escape=False), unsafe_allow_html=True)

elif page == "Employee and Task Master List":
    st.header("Employee and Task Master List - 3rdEyeAI, a product of CAP CORPORATE AI SOLUTIONS LLP")

    # Load employees into session state
    if "employees" not in st.session_state:
        st.session_state.employees = load_employees()

    # Divide the page into two columns
    col1, col2 = st.columns(2)

    # Employee master list
    with col1:
        st.subheader("Employee Master List")

        # Display employee table
        df_employees = pd.DataFrame(st.session_state.employees)
        df_employees["positive_tasks"] = df_employees["positive_tasks"].apply(", ".join)
        st.dataframe(df_employees)

        # Add new employee
        st.subheader("Add New Employee")
        new_employee_name = st.text_input("Employee Name")
        if st.button("Add Employee"):
            if new_employee_name:
                new_employee_id = f"E{len(st.session_state.employees) + 1}"
                st.session_state.employees.append(
                    {"id": new_employee_id, "name": new_employee_name, "positive_tasks": []})
                save_employees(st.session_state.employees)
                st.success(f"Employee '{new_employee_name}' added with ID '{new_employee_id}'.")
                st.experimental_rerun()
            else:
                st.warning("Employee name cannot be empty.")

        # Edit employee
        st.subheader("Edit Employee")
        selected_employee = st.selectbox("Select Employee to Edit",
                                         [f"{emp['id']} - {emp['name']}" for emp in st.session_state.employees])
        emp_id = selected_employee.split(" - ")[0]
        emp = next(emp for emp in st.session_state.employees if emp["id"] == emp_id)
        new_employee_name = st.text_input("New Employee Name", value=emp["name"])
        new_positive_tasks = st.multiselect("Positive Task List", tasks,
                                            default=[task for task in emp["positive_tasks"] if task in tasks])

        if st.button("Save Changes"):
            if new_employee_name:
                emp["name"] = new_employee_name
                emp["positive_tasks"] = new_positive_tasks
                save_employees(st.session_state.employees)
                st.success(f"Employee '{emp_id}' updated.")
                st.experimental_rerun()
            else:
                st.warning("Employee name cannot be empty.")

    # Task management
    with col2:
        st.subheader("Task Management")

        # Display task table
        task_df = pd.DataFrame({"Tasks": tasks})
        st.dataframe(task_df)

        # Add new task
        st.subheader("Add New Task")
        new_task_name = st.text_input("Task Name")
        if st.button("Add Task"):
            if new_task_name and new_task_name not in tasks:
                tasks.append(new_task_name)
                save_tasks()
                # Add new task as a column in the allocations DataFrame
                st.session_state.allocations[new_task_name] = [[] for _ in range(get_days_in_month(st.session_state.selected_month))]
                save_allocations(st.session_state.selected_month, st.session_state.allocations)
                st.success(f"Task '{new_task_name}' added.")
                st.experimental_rerun()
            else:
                st.warning("Task name cannot be empty or duplicate.")

        # Edit or delete existing task
        st.subheader("Edit/Delete Task")
        selected_task = st.selectbox("Select Task to Edit/Delete", tasks)
        new_task_name = st.text_input("New Task Name", value=selected_task)
        if st.button("Update Task"):
            if new_task_name and new_task_name != selected_task and new_task_name not in tasks:
                # Update task name in the tasks list
                tasks[tasks.index(selected_task)] = new_task_name
                save_tasks()

                # Update task name in the allocations DataFrame
                st.session_state.allocations.rename(columns={selected_task: new_task_name}, inplace=True)
                save_allocations(st.session_state.selected_month, st.session_state.allocations)

                st.success(f"Task '{selected_task}' updated to '{new_task_name}'.")
                st.experimental_rerun()
            else:
                st.warning("New task name cannot be empty, duplicate, or the same as the old name.")
        if st.button("Delete Task"):
            if selected_task in tasks:
                tasks.remove(selected_task)
                save_tasks()

                # Remove task from the allocations DataFrame
                st.session_state.allocations.drop(columns=[selected_task], inplace=True)
                save_allocations(st.session_state.selected_month, st.session_state.allocations)

                st.success(f"Task '{selected_task}' deleted.")
                st.experimental_rerun()
            else:
                st.warning("Task not found.")
