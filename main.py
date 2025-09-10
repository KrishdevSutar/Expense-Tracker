import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os



st.set_page_config(page_title="Expense Tracker App", page_icon="$", layout="wide")

category_file = "categories.json"

if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": []
    }
if os.path.exists(category_file):
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)

def save_categories():
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)

def categorize_transactions(df):
    df["Category"] = "Uncategorized"
    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue
        lowered_keywords = [keyword.lower().strip() for keyword in keywords]
        for idx, row in df.iterrows():
            details = row["Details"].lower().strip()
            if details in lowered_keywords:
                df.at[idx, "Category"] = category
    return df

def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    return False

def load_transaction(file):
    try:
        column_names = ['Date','Details','Credit','Debit','Balance']
        df = pd.read_csv(file, names=column_names, header=None)
        df.columns = [col.strip() for col in df.columns]
        #df["Credit"] = df["Credit"].str.replace(",","").astype(float)
        df["Date"] = pd.to_datetime(df["Date"], format='%m/%d/%Y')
        df["Amount"] = df['Credit'].fillna(df['Debit'])
        column_order = ['Date','Details','Amount','Credit','Debit','Balance']
        df = df[column_order]
        #nan_value = float("NaN")
        #df.replace("", nan_value, inplace=True)
        #df.dropna(how='all', axis=1, inplace=True)
        #Sst.write(df)
        
        return categorize_transactions(df)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None


def main():
    st.title("Expense Tracker Dashboard")
    uploaded_file = st.file_uploader("Upload your transaction Bank CSV File", type=["csv"])
    if uploaded_file is not None:
        df = load_transaction(uploaded_file)
        if df is not None:
            nan_value = float("NaN")
            debits_df = df.drop('Credit', axis=1).dropna(subset=['Debit']).copy()
            credits_df = df.drop('Debit', axis=1).dropna(subset=['Credit']).copy()

            st.session_state.credits_df = credits_df.copy()

            tab1, tab2 = st.tabs(["Expenses (Credits)", "Payments (Debits)"])
            
            with tab1:
                new_category = st.text_input("New Category Name")
                add_button = st.button("Add Category")
                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        #st.success(f"New Category was added: {new_category}")
                        st.rerun()
                
                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.credits_df[["Date", "Details","Amount","Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="MM/DD/YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f CAD"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"
                )

                save_button = st.button("Apply Changes", type="primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]
                        if new_category == st.session_state.credits_df.at[idx, "Category"]:
                            continue
                        details = row["Details"]
                        st.session_state.credits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details)
                        
                st.subheader('Expense Summary')
                category_totals = st.session_state.credits_df.groupby("Category")["Amount"].sum().reset_index()
                category_totals = category_totals.sort_values("Amount", ascending=False)

                st.dataframe(
                    category_totals,
                    column_config={
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f CAD"),
                    },
                    hide_index=True,
                    use_container_width=True
                )

                fig = px.pie(
                    category_totals,
                    values="Amount",
                    names="Category",
                    title="Expenses by Category"
                )
                st.plotly_chart(fig, use_container_width=True)

                #st.write(debits_df)
               
            with tab2:
                st.subheader("Payment Summary")
                total_payments = debits_df["Amount"].sum()
                st.metric('Total Payments', f"{total_payments:.2f} CAD")
                st.write(debits_df)
            

main()