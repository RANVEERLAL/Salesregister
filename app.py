import streamlit as st
import pandas as pd
import plotly.express as px
import warnings

# Suppress warnings related to Plotly versions or similar minor issues
warnings.filterwarnings('ignore')

# Set Streamlit page configuration
st.set_page_config(layout="wide", page_title="Sales Performance Dashboard", page_icon="📈")

# --- Data Loading and Preprocessing ---
@st.cache_data # Cache data to avoid reloading every time the app interacts
def load_data():
    """
    Loads the sales data from a CSV file named 'EA.csv'.
    Performs initial data cleaning and feature engineering.
    """
    try:
        # Read the CSV file directly from the same directory
        df = pd.read_csv('EA.csv')

        # Standardize column names by stripping whitespace and making them lowercase
        df.columns = df.columns.str.strip()

        # Rename columns for easier access and cleaner visualization labels
        df = df.rename(columns={
            'Final Line Amount (A-B+C)': 'Final_Line_Amount',
            'Posting Date': 'Posting_Date',
            'Sell to State': 'Region',
            'Product Group': 'Product_Group',
            'Customer Name': 'Customer_Name',
            'MRP Category': 'MRP_Category',
            'Gender': 'Gender',
            'Brands': 'Brand',
            'Channel': 'Sales_Channel',
            'Item Description': 'Item_Description',
            'Sales Article': 'Sales_Article',
            'Quantity': 'Quantity',
            'Unit Price': 'Unit_Price',
            'GL Account Code': 'GL_Account_Code',
            'Account Name': 'Account_Name',
            'ASM Name': 'ASM_Name',
            'Item Category': 'Item_Category',
            'Product Type': 'Product_Type',
            'Online Store': 'Online_Store',
            'Company Name': 'Company_Name'
        })

        # Convert 'Posting_Date' to datetime objects, handling various formats
        # Using dayfirst=True to correctly parse 'DD-MM-YY' or 'DD-MM-YYYY'
        df['Posting_Date'] = pd.to_datetime(df['Posting_Date'], errors='coerce', dayfirst=True)

        # Drop rows where 'Posting_Date' is NaT (Not a Time) after conversion issues
        df.dropna(subset=['Posting_Date'], inplace=True)

        # Create 'Sale_Over_1000' column based on 'Final_Line_Amount'
        df['Sale_Over_1000'] = df['Final_Line_Amount'] > 1000

        # Extract Year, Month, Day for time-based analysis
        df['Year'] = df['Posting_Date'].dt.year
        df['Month'] = df['Posting_Date'].dt.month_name()
        df['Day_of_Week'] = df['Posting_Date'].dt.day_name()
        df['Quarter'] = df['Posting_Date'].dt.quarter.apply(lambda x: f'Q{x}')

        # Ensure numeric types for calculations
        # List all columns that should be numeric and handle non-numeric values
        numeric_cols = [
            'Quantity', 'Unit_Price', 'Line Discount', 'Line Amount (Qty * Unit Unit_Price) -A',
            'Invoice Discount Amount-B', 'Final_Line_Amount', 'GST Base Amount',
            'GST Percentage', 'Total GST Amount', 'IGST Amount', 'IGST Per',
            'SGST Amount', 'SGST Per', 'CGST Amount', 'CGST Per', 'TDS Amount'
        ]
        for col in numeric_cols:
            # Check if column exists before processing
            if col in df.columns:
                # Handle commas as thousand separators and convert to numeric
                df[col] = df[col].astype(str).str.replace(',', '').str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Fill NaN in numeric columns with 0 after conversion, as NaNs can break aggregations
        df[numeric_cols] = df[numeric_cols].fillna(0)

        return df
    except FileNotFoundError:
        st.error("Error: 'EA.csv' not found. Please make sure the CSV file is in the same directory as 'app.py'.")
        st.stop() # Stop the app execution if the file is not found
    except Exception as e:
        st.error(f"Error loading or processing data: {e}")
        st.stop() # Stop the app for other data loading/processing errors

# Load data at the beginning of the script
df = load_data()

# Sidebar Filters
st.sidebar.header("Filter Options")

# Check if DataFrame is empty after loading (e.g., if CSV was not found or was empty)
if not df.empty:
    min_date = df['Posting_Date'].min().to_pydatetime()
    max_date = df['Posting_Date'].max().to_pydatetime()

    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Apply date filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = df[(df['Posting_Date'] >= pd.to_datetime(start_date)) & (df['Posting_Date'] <= pd.to_datetime(end_date))]
    else:
        filtered_df = df.copy() # If date range is not fully selected, use full data initially

    # Other filters (ensure they are only created if filtered_df is not empty)
    if not filtered_df.empty:
        all_regions = ['All'] + sorted(filtered_df['Region'].dropna().unique().tolist())
        selected_regions = st.sidebar.multiselect("Select Region(s)", all_regions, default='All')
        if 'All' not in selected_regions:
            filtered_df = filtered_df[filtered_df['Region'].isin(selected_regions)]

        all_product_groups = ['All'] + sorted(filtered_df['Product_Group'].dropna().unique().tolist())
        selected_product_groups = st.sidebar.multiselect("Select Product Group(s)", all_product_groups, default='All')
        if 'All' not in selected_product_groups:
            filtered_df = filtered_df[filtered_df['Product_Group'].isin(selected_product_groups)]

        all_sales_channels = ['All'] + sorted(filtered_df['Sales_Channel'].dropna().unique().tolist())
        selected_sales_channels = st.sidebar.multiselect("Select Sales Channel(s)", all_sales_channels, default='All')
        if 'All' not in selected_sales_channels:
            filtered_df = filtered_df[filtered_df['Sales_Channel'].isin(selected_sales_channels)]

        # Dynamic slider for Final Line Amount (A-B+C)
        # Check if 'Final_Line_Amount' is present and not all NaN before creating slider
        if 'Final_Line_Amount' in filtered_df.columns and not filtered_df['Final_Line_Amount'].empty:
            min_amount = float(filtered_df['Final_Line_Amount'].min())
            max_amount = float(filtered_df['Final_Line_Amount'].max())
            amount_range = st.sidebar.slider(
                "Filter by Final Line Amount",
                min_value=min_amount,
                max_value=max_amount,
                value=(min_amount, max_amount)
            )
            filtered_df = filtered_df[(filtered_df['Final_Line_Amount'] >= amount_range[0]) & (filtered_df['Final_Line_Amount'] <= amount_range[1])]
        else:
            st.sidebar.warning("Final Line Amount data not available for filtering.")

else:
    st.info("No data loaded or available for filtering. Please check 'EA.csv'.")
    filtered_df = pd.DataFrame() # Ensure filtered_df is an empty DataFrame if initial load failed

# --- Dashboard Content ---
st.title("Sales Performance Dashboard 📈")
st.markdown("This dashboard provides a comprehensive view of sales data, offering micro and macro insights for HR and stakeholders.")

if filtered_df.empty:
    st.info("No data available based on current filters. Please adjust your selections or check the 'EA.csv' file.")
else:
    # --- Tabs for navigation ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Overview", "Sales Analysis", "Amount > 1000 Analysis", "Trend Analysis", "Customer & Product Insights", "Detailed Data"])

    with tab1:
        st.header("Overview: Key Sales Metrics")

        # Row 1: Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("### Total Sales Revenue")
            total_sales = filtered_df['Final_Line_Amount'].sum()
            st.metric(label="Total Sales", value=f"${total_sales:,.2f}")
            st.markdown("This metric represents the sum of all final line amounts, giving a grand total of sales revenue generated within the selected filters.")
        with col2:
            st.markdown("### Total Transactions")
            # Using 'Document No.' assuming it's the unique identifier for a transaction
            total_transactions = filtered_df['Document No.'].nunique()
            st.metric(label="Total Transactions", value=f"{total_transactions:,}")
            st.markdown("This shows the total count of unique sales documents, indicating the volume of sales activities.")
        with col3:
            st.markdown("### Sales Above $1000")
            sales_over_1000 = filtered_df[filtered_df['Sale_Over_1000']].shape[0]
            st.metric(label="Transactions > $1000", value=f"{sales_over_1000:,}")
            st.markdown("This highlights the number of individual sales transactions where the final amount exceeded $1000, identifying high-value deals.")
        with col4:
            st.markdown("### % Sales Above $1000")
            percentage_over_1000 = (sales_over_1000 / total_transactions * 100) if total_transactions > 0 else 0
            st.metric(label="% of Transactions > $1000", value=f"{percentage_over_1000:,.2f}%")
            st.markdown("This percentage indicates the proportion of high-value sales relative to all transactions, useful for understanding sales quality.")

        st.markdown("---")

        # Chart 1: Sales Distribution by Product Group (Top 10)
        st.markdown("### Sales Distribution by Product Group")
        st.markdown("This bar chart illustrates the total sales revenue generated by each product group. It helps in identifying which product categories are the most profitable.")
        product_sales = filtered_df.groupby('Product_Group')['Final_Line_Amount'].sum().nlargest(10).reset_index()
        if not product_sales.empty:
            fig1 = px.bar(product_sales, x='Product_Group', y='Final_Line_Amount',
                          title='Top 10 Product Group Sales',
                          labels={'Product_Group': 'Product Group', 'Final_Line_Amount': 'Total Sales Amount'},
                          color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Plasma)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No data for Product Group Sales.")

        # Chart 2: Sales Distribution by Region
        st.markdown("### Sales Distribution by Region")
        st.markdown("This pie chart visualizes the proportion of total sales contributed by each geographical region. It helps in understanding regional sales performance at a glance.")
        region_sales = filtered_df.groupby('Region')['Final_Line_Amount'].sum().reset_index()
        if not region_sales.empty:
            fig2 = px.pie(region_sales, values='Final_Line_Amount', names='Region',
                          title='Sales Distribution by Region',
                          hole=0.3,
                          labels={'Final_Line_Amount': 'Total Sales Amount'})
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No data for Sales Distribution by Region.")


    with tab2:
        st.header("Sales Analysis: Deep Dive")

        # Chart 3: Sales by Sales Channel
        st.markdown("### Sales by Sales Channel")
        st.markdown("This bar chart breaks down sales by the channel through which they were made (e.g., Distributor, Online). It helps in assessing the effectiveness of different sales strategies.")
        channel_sales = filtered_df.groupby('Sales_Channel')['Final_Line_Amount'].sum().reset_index()
        if not channel_sales.empty:
            fig3 = px.bar(channel_sales, x='Sales_Channel', y='Final_Line_Amount',
                          title='Sales by Sales Channel',
                          labels={'Sales_Channel': 'Sales Channel', 'Final_Line_Amount': 'Total Sales Amount'},
                          color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Viridis)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No data for Sales by Sales Channel.")

        # Chart 4: Sales by Customer Name (Top N)
        st.markdown("### Top 15 Customers by Sales Amount")
        st.markdown("This chart identifies the top customers based on their total purchase amounts. It's crucial for understanding key accounts and customer loyalty.")
        top_customers = filtered_df.groupby('Customer_Name')['Final_Line_Amount'].sum().nlargest(15).reset_index()
        if not top_customers.empty:
            fig4 = px.bar(top_customers, x='Customer_Name', y='Final_Line_Amount',
                          title='Top 15 Customers by Sales Amount',
                          labels={'Customer_Name': 'Customer Name', 'Final_Line_Amount': 'Total Sales Amount'},
                          color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Mint)
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No data for Top Customers by Sales Amount.")

        # Chart 5: Sales by MRP Category
        st.markdown("### Sales by MRP Category")
        st.markdown("This visualization categorizes sales by their MRP (Maximum Retail Price) groups, offering insights into which price segments perform best.")
        mrp_sales = filtered_df.groupby('MRP_Category')['Final_Line_Amount'].sum().reset_index()
        if not mrp_sales.empty:
            fig5 = px.bar(mrp_sales, x='MRP_Category', y='Final_Line_Amount',
                          title='Sales by MRP Category',
                          labels={'MRP_Category': 'MRP Category', 'Final_Line_Amount': 'Total Sales Amount'},
                          color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Sunset)
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No data for Sales by MRP Category.")

        # Chart 6: Quantity Sold by Product Group
        st.markdown("### Quantity Sold by Product Group")
        st.markdown("This bar chart shows the total quantity of items sold within each product group, complementing the sales revenue data for a complete picture of performance.")
        qty_product_sales = filtered_df.groupby('Product_Group')['Quantity'].sum().nlargest(10).reset_index()
        if not qty_product_sales.empty:
            fig6 = px.bar(qty_product_sales, x='Product_Group', y='Quantity',
                          title='Top 10 Product Group by Quantity Sold',
                          labels={'Product_Group': 'Product Group', 'Quantity': 'Total Quantity Sold'},
                          color='Quantity', color_continuous_scale=px.colors.sequential.Plasma)
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("No data for Quantity Sold by Product Group.")
        
        # Chart 7: Average Unit Price by Product Group
        st.markdown("### Average Unit Price by Product Group")
        st.markdown("This chart shows the average unit price for items in each product group, which can indicate pricing strategies or product value.")
        avg_price_product = filtered_df.groupby('Product_Group')['Unit_Price'].mean().reset_index()
        if not avg_price_product.empty:
            fig7 = px.bar(avg_price_product, x='Product_Group', y='Unit_Price',
                          title='Average Unit Price by Product Group',
                          labels={'Product_Group': 'Product Group', 'Unit_Price': 'Average Unit Price'},
                          color='Unit_Price', color_continuous_scale=px.colors.sequential.Greens)
            st.plotly_chart(fig7, use_container_width=True)
        else:
            st.info("No data for Average Unit Price by Product Group.")

    with tab3:
        st.header("Amount > $1000 Analysis")

        # Chart 8: Sales Above/Below $1000 Distribution
        st.markdown("### Distribution of Sales by Amount Threshold ($1000)")
        st.markdown("This pie chart illustrates the proportion of transactions that are above or below the $1000 threshold. It helps HR and stakeholders understand the volume of high-value versus regular transactions.")
        amount_category_counts = filtered_df['Sale_Over_1000'].value_counts().reset_index()
        amount_category_counts.columns = ['Category', 'Count']
        amount_category_counts['Category'] = amount_category_counts['Category'].map({True: 'Sales > $1000', False: 'Sales <= $1000'})
        if not amount_category_counts.empty:
            fig8 = px.pie(amount_category_counts, values='Count', names='Category',
                          title='Number of Sales Transactions Above/Below $1000',
                          hole=0.3,
                          labels={'Count': 'Number of Transactions'})
            st.plotly_chart(fig8, use_container_width=True)
        else:
            st.info("No data for Sales Above/Below $1000 Distribution.")

        # Chart 9: Total Revenue from Sales Above/Below $1000
        st.markdown("### Revenue Contribution by Sales Amount Threshold ($1000)")
        st.markdown("This bar chart shows the total revenue generated from sales above $1000 compared to sales below or equal to $1000. It highlights the significant financial impact of high-value sales.")
        revenue_by_category = filtered_df.groupby('Sale_Over_1000')['Final_Line_Amount'].sum().reset_index()
        revenue_by_category['Sale_Over_1000'] = revenue_by_category['Sale_Over_1000'].map({True: 'Revenue from Sales > $1000', False: 'Revenue from Sales <= $1000'})
        if not revenue_by_category.empty:
            fig9 = px.bar(revenue_by_category, x='Sale_Over_1000', y='Final_Line_Amount',
                          title='Total Revenue from Sales Above/Below $1000',
                          labels={'Sale_Over_1000': 'Sale Category', 'Final_Line_Amount': 'Total Revenue'},
                          color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Blues)
            st.plotly_chart(fig9, use_container_width=True)
        else:
            st.info("No data for Revenue Contribution by Sales Amount Threshold.")
        
        # Chart 10: Sales > $1000 by Region
        st.markdown("### High-Value Sales (> $1000) by Region")
        st.markdown("This chart focuses specifically on high-value transactions and breaks them down by region. This helps identify regions that are strong contributors to premium sales.")
        high_value_region_sales = filtered_df[filtered_df['Sale_Over_1000']].groupby('Region')['Final_Line_Amount'].sum().reset_index()
        if not high_value_region_sales.empty:
            fig10 = px.bar(high_value_region_sales, x='Region', y='Final_Line_Amount',
                           title='High-Value Sales (> $1000) by Region',
                           labels={'Region': 'Region', 'Final_Line_Amount': 'Total High-Value Sales'},
                           color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Oranges)
            st.plotly_chart(fig10, use_container_width=True)
        else:
            st.info("No data for High-Value Sales by Region.")

        # Chart 11: Sales > $1000 by Product Group
        st.markdown("### High-Value Sales (> $1000) by Product Group")
        st.markdown("This chart shows which product groups are driving the most high-value sales. This information is critical for product development and marketing strategies.")
        high_value_product_sales = filtered_df[filtered_df['Sale_Over_1000']].groupby('Product_Group')['Final_Line_Amount'].sum().nlargest(10).reset_index()
        if not high_value_product_sales.empty:
            fig11 = px.bar(high_value_product_sales, x='Product_Group', y='Final_Line_Amount',
                           title='Top 10 Product Group High-Value Sales (> $1000)',
                           labels={'Product_Group': 'Product Group', 'Final_Line_Amount': 'Total High-Value Sales'},
                           color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Greys)
            st.plotly_chart(fig11, use_container_width=True)
        else:
            st.info("No data for High-Value Sales by Product Group.")

    with tab4:
        st.header("Trend Analysis")

        # Chart 12: Monthly Sales Trend
        st.markdown("### Monthly Sales Trend")
        st.markdown("This line chart visualizes the total sales amount over months. It helps identify seasonal patterns or overall growth/decline trends in sales performance.")
        # Ensure 'Posting_Date' is a datetime index for resampling
        monthly_sales = filtered_df.set_index('Posting_Date').resample('M')['Final_Line_Amount'].sum().reset_index()
        if not monthly_sales.empty:
            fig12 = px.line(monthly_sales, x='Posting_Date', y='Final_Line_Amount',
                            title='Monthly Sales Trend',
                            labels={'Posting_Date': 'Date', 'Final_Line_Amount': 'Total Sales Amount'})
            st.plotly_chart(fig12, use_container_width=True)
        else:
            st.info("No data for Monthly Sales Trend.")

        # Chart 13: Quarterly Sales Trend
        st.markdown("### Quarterly Sales Trend")
        st.markdown("This bar chart displays sales aggregated by quarter. It provides a broader view of sales cycles, which is useful for long-term planning and resource allocation.")
        quarterly_sales = filtered_df.groupby('Quarter')['Final_Line_Amount'].sum().reset_index()
        # Ensure correct order for quarters if needed, e.g., using a categorical type
        quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
        quarterly_sales['Quarter'] = pd.Categorical(quarterly_sales['Quarter'], categories=quarter_order, ordered=True)
        quarterly_sales = quarterly_sales.sort_values('Quarter')
        
        if not quarterly_sales.empty:
            fig13 = px.bar(quarterly_sales, x='Quarter', y='Final_Line_Amount',
                           title='Quarterly Sales Trend',
                           labels={'Quarter': 'Quarter', 'Final_Line_Amount': 'Total Sales Amount'},
                           color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Teal)
            st.plotly_chart(fig13, use_container_width=True)
        else:
            st.info("No data for Quarterly Sales Trend.")

        # Chart 14: Sales by Day of Week
        st.markdown("### Sales by Day of Week")
        st.markdown("This chart reveals sales performance across different days of the week, indicating peak selling days or periods of lower activity for operational adjustments.")
        day_of_week_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_sales = filtered_df.groupby('Day_of_Week')['Final_Line_Amount'].sum().reindex(day_of_week_order).reset_index()
        if not daily_sales.empty:
            fig14 = px.bar(daily_sales, x='Day_of_Week', y='Final_Line_Amount',
                           title='Sales by Day of Week',
                           labels={'Day_of_Week': 'Day of Week', 'Final_Line_Amount': 'Total Sales Amount'},
                           color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Magenta)
            st.plotly_chart(fig14, use_container_width=True)
        else:
            st.info("No data for Sales by Day of Week.")

        # Chart 15: Monthly Quantity Sold Trend
        st.markdown("### Monthly Quantity Sold Trend")
        st.markdown("Similar to the monthly sales trend, this graph tracks the quantity of items sold each month, helping to understand inventory movement and demand fluctuations.")
        monthly_qty = filtered_df.set_index('Posting_Date').resample('M')['Quantity'].sum().reset_index()
        if not monthly_qty.empty:
            fig15 = px.line(monthly_qty, x='Posting_Date', y='Quantity',
                            title='Monthly Quantity Sold Trend',
                            labels={'Posting_Date': 'Date', 'Quantity': 'Total Quantity Sold'})
            st.plotly_chart(fig15, use_container_width=True)
        else:
            st.info("No data for Monthly Quantity Sold Trend.")

    with tab5:
        st.header("Customer & Product Insights")

        # Chart 16: Sales by Gender
        st.markdown("### Sales by Gender")
        st.markdown("This chart breaks down sales figures based on customer gender, which can inform targeted marketing campaigns and product development.")
        gender_sales = filtered_df.groupby('Gender')['Final_Line_Amount'].sum().reset_index()
        if not gender_sales.empty:
            fig16 = px.bar(gender_sales, x='Gender', y='Final_Line_Amount',
                           title='Sales by Gender',
                           labels={'Gender': 'Gender', 'Final_Line_Amount': 'Total Sales Amount'},
                           color='Gender', color_continuous_scale=px.colors.sequential.Portland)
            st.plotly_chart(fig16, use_container_width=True)
        else:
            st.info("No data for Sales by Gender.")

        # Chart 17: Sales by Brand (Top 10)
        st.markdown("### Top 10 Brands by Sales")
        st.markdown("This bar chart highlights the brands that contribute the most to total sales revenue, identifying top-performing brands in the portfolio.")
        brand_sales = filtered_df.groupby('Brand')['Final_Line_Amount'].sum().nlargest(10).reset_index()
        if not brand_sales.empty:
            fig17 = px.bar(brand_sales, x='Brand', y='Final_Line_Amount',
                           title='Top 10 Brands by Sales',
                           labels={'Brand': 'Brand', 'Final_Line_Amount': 'Total Sales Amount'},
                           color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Rainbow)
            st.plotly_chart(fig17, use_container_width=True)
        else:
            st.info("No data for Top 10 Brands by Sales.")
        
        # Chart 18: Sales by ASM Name (Top 10 Sales Representatives)
        st.markdown("### Sales Performance by Sales Area Manager (ASM)")
        st.markdown("This chart displays the sales contribution of each ASM (Area Sales Manager). It's useful for evaluating individual performance and identifying top sales personnel.")
        asm_sales = filtered_df.groupby('ASM_Name')['Final_Line_Amount'].sum().nlargest(10).reset_index()
        if not asm_sales.empty:
            fig18 = px.bar(asm_sales, x='ASM_Name', y='Final_Line_Amount',
                           title='Top 10 Sales by ASM Name',
                           labels={'ASM_Name': 'ASM Name', 'Final_Line_Amount': 'Total Sales Amount'},
                           color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Cividis)
            st.plotly_chart(fig18, use_container_width=True)
        else:
            st.info("No data for Sales Performance by ASM Name.")

        # Chart 19: Sales by Item Category
        st.markdown("### Sales by Item Category")
        st.markdown("This visualization shows the distribution of sales across different item categories. It helps in understanding which product types are most popular.")
        item_category_sales = filtered_df.groupby('Item_Category')['Final_Line_Amount'].sum().reset_index()
        if not item_category_sales.empty:
            fig19 = px.bar(item_category_sales, x='Item_Category', y='Final_Line_Amount',
                           title='Sales by Item Category',
                           labels={'Item_Category': 'Item Category', 'Final_Line_Amount': 'Total Sales Amount'},
                           color='Final_Line_Amount', color_continuous_scale=px.colors.sequential.Inferno)
            st.plotly_chart(fig19, use_container_width=True)
        else:
            st.info("No data for Sales by Item Category.")

        # Chart 20: Sales by Online Store (if applicable)
        if 'Online_Store' in filtered_df.columns and not filtered_df['Online_Store'].isnull().all():
            st.markdown("### Sales by Online/Offline Store")
            st.markdown("This chart compares sales generated through online platforms versus offline stores. It helps in evaluating the performance of different sales channels.")
            online_store_sales = filtered_df.groupby('Online_Store')['Final_Line_Amount'].sum().reset_index()
            if not online_store_sales.empty:
                fig20 = px.pie(online_store_sales, values='Final_Line_Amount', names='Online_Store',
                               title='Sales by Online/Offline Store',
                               labels={'Final_Line_Amount': 'Total Sales Amount'},
                               hole=0.3)
                st.plotly_chart(fig20, use_container_width=True)
            else:
                st.info("No data for Sales by Online/Offline Store.")
        else:
            st.info("Online_Store data not available or all null for visualization.")

    with tab6:
        st.header("Detailed Data View")
        st.markdown("This table provides a raw view of the filtered sales data, allowing for detailed inspection of individual transactions. You can sort and search within this table.")
        st.dataframe(filtered_df) 
