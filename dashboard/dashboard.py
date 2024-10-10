import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import streamlit as st
import urllib

class DataAnalyzer:
    def __init__(self, df):
        self.df = df

    def generate_daily_orders_df(self):
        daily_orders_df = self.df.resample(rule='D', on='order_approved_at').agg({
            "order_id": "nunique",
            "payment_value": "sum"
        })
        daily_orders_df = daily_orders_df.reset_index()
        daily_orders_df.rename(columns={
            "order_id": "order_count",
            "payment_value": "revenue"
        }, inplace=True)
        
        return daily_orders_df
    
    def generate_monthly_sales_df(self):
        # Hapus baris dengan NaT pada 'order_approved_at'
        self.df = self.df.dropna(subset=['order_approved_at'])

        # Aggregate sales data by month
        monthly_sales_df = self.df.resample(rule='M', on='order_approved_at').agg({
            "payment_value": "sum"
        }).reset_index().rename(columns={
            "payment_value": "total_revenue"
        })

        # Identify top products each month
        top_products_df = self.df.groupby([self.df['order_approved_at'].dt.to_period('M'), "product_id"]).size().reset_index(name='order_count')
        top_products_df = top_products_df.loc[top_products_df.groupby('order_approved_at')['order_count'].idxmax()]

        # Merge sales and top products data
        monthly_summary_df = pd.merge(monthly_sales_df, top_products_df, how='left', left_on='order_approved_at', right_on='order_approved_at')
        monthly_summary_df['order_approved_at'] = pd.to_datetime(monthly_summary_df['order_approved_at'], errors='coerce')

        # Tambahkan kolom bulan dan tahun untuk pengurutan
        monthly_summary_df['month'] = monthly_summary_df['order_approved_at'].dt.month
        monthly_summary_df['year'] = monthly_summary_df['order_approved_at'].dt.year

        # Urutkan berdasarkan tahun dan bulan
        monthly_summary_df.sort_values(by=['year', 'month'], inplace=True)

        return monthly_summary_df[['order_approved_at', 'total_revenue', 'product_id', 'order_count']]

    def review_scores_analysis(self):
        review_scores = self.df['review_score'].value_counts().sort_values(ascending=False)
        most_frequent_score = review_scores.idxmax()

        return review_scores, most_frequent_score

    def state_customer_distribution(self):
        state_df = self.df.groupby(by="customer_state").customer_id.nunique().reset_index()
        state_df.rename(columns={
            "customer_id": "customer_count"
        }, inplace=True)
        most_common_state = state_df.loc[state_df['customer_count'].idxmax(), 'customer_state']
        state_df = state_df.sort_values(by='customer_count', ascending=False)

        return state_df, most_common_state

    def order_status_distribution(self):
        order_status_df = self.df["order_status"].value_counts().sort_values(ascending=False)
        most_common_status = order_status_df.idxmax()

        return order_status_df, most_common_status
    
class BrazilMapPlotter:
    def __init__(self, data, plt, mpimg, urllib, st):
        self.data = data
        self.plt = plt
        self.mpimg = mpimg
        self.urllib = urllib
        self.st = st

    def display_map(self):
        brazil_map = self.mpimg.imread(self.urllib.request.urlopen('https://i.pinimg.com/originals/3a/0c/e1/3a0ce18b3c842748c255bc0aa445ad41.jpg'), 'jpg')
        ax = self.data.plot(kind="scatter", x="geolocation_lng", y="geolocation_lat", figsize=(10, 10), alpha=0.3, s=0.3, c='blue')
        self.plt.axis('off')
        self.plt.imshow(brazil_map, extent=[-73.98283055, -33.8, -33.75116944, 5.4])
        self.st.pyplot()

# Load the datasets
datetime_columns = [
    "order_approved_at", 
    "order_delivered_carrier_date", 
    "order_delivered_customer_date", 
    "order_estimated_delivery_date", 
    "order_purchase_timestamp", 
    "shipping_limit_date"
]
# all_data_df = pd.read_csv('all_data.csv')
all_data_df = pd.read_csv('https://drive.google.com/file/d/1f2lelsl0CwWr8836GF80dE9IJeOr1fXh/view?usp=sharing')
all_data_df.sort_values(by="order_approved_at", inplace=True)
all_data_df.reset_index(inplace=True)

# Load the geolocation data
geolocation_df = pd.read_csv('../data/customers_geo.csv') 
geolocation_unique = geolocation_df.drop_duplicates(subset='customer_unique_id')

# Convert specified columns to datetime
for column in datetime_columns:
    all_data_df[column] = pd.to_datetime(all_data_df[column])

# Extract minimum and maximum order approval dates
start_date = all_data_df["order_approved_at"].min()
end_date = all_data_df["order_approved_at"].max()

# Streamlit app layout
st.title("Dashboard Grafik Analisis E-Commerce di Brazil")

# Sidebar for date range selection
with st.sidebar:
    st.write("## Pilih Tanggal:")
    selected_dates = st.date_input(
        label="Pilih Rentang Tanggal (Tanggal Awal dan Akhir)",
        value=[start_date, end_date],
        min_value=start_date,
        max_value=end_date
    )

# Filter DataFrame based on the chosen date range
filtered_orders_df = all_data_df[(all_data_df["order_approved_at"] >= pd.to_datetime(selected_dates[0])) & 
                                    (all_data_df["order_approved_at"] <= pd.to_datetime(selected_dates[1]))]

# Create an instance of DataAnalyzer
data_analyzer = DataAnalyzer(filtered_orders_df)

# Generate analysis data frames
monthly_sales_df = data_analyzer.generate_monthly_sales_df()
daily_orders_df = data_analyzer.generate_daily_orders_df()
review_scores, common_review_score = data_analyzer.review_scores_analysis()
state_distribution_df, most_common_state = data_analyzer.state_customer_distribution()
order_status_df, most_common_order_status = data_analyzer.order_status_distribution()

# Visualization of analysis results

st.subheader("Data Pendapatan Perbulan")
# Tambahkan kolom nama bulan untuk visualisasi
monthly_sales_df['month_name'] = monthly_sales_df['order_approved_at'].dt.strftime('%B')
# Urutkan data berdasarkan bulan
monthly_sales_df['month'] = monthly_sales_df['order_approved_at'].dt.month
monthly_sales_df.sort_values(by='month', inplace=True)

# Plot grafik line chart
line_chart_data = monthly_sales_df.groupby('month_name')['total_revenue'].sum().reindex(
    ['January', 'February', 'March', 'April', 'May', 'June', 
     'July', 'August', 'September', 'October', 'November', 'December']
)

# Tampilkan line chart
st.line_chart(line_chart_data)

st.subheader("Data Penjualan Harian")
st.line_chart(daily_orders_df.set_index('order_approved_at')['order_count'])

st.subheader("Data Penilaian Review Pelanggan")
st.bar_chart(review_scores)

st.subheader("Data Pelanggan Berdasarkan Negara Bagian")
st.bar_chart(state_distribution_df.set_index('customer_state')['customer_count'])

# Plot customer distribution on Brazil map
map_plotter_instance = BrazilMapPlotter(geolocation_unique, plt, mpimg, urllib, st)
st.subheader("Distribusi Pelanggan E-Commerce di Brazil")
map_plotter_instance.display_map()

with st.expander("Penjelasan"):
        st.write('Daerah dengan jumlah pelanggan terbanyak terletak di bagian Tenggara dan Selatan Brazil. Berdasarkan data yang tersedia, kota-kota seperti São Paulo, Rio de Janeiro, dan Belo Horizonte menjadi pusat dengan pelanggan paling banyak. Penyebaran pelanggan yang signifikan di area ini dapat dimanfaatkan untuk strategi pemasaran yang lebih efektif.')

# Footer
st.write("Copyright (C) Nurul Izzah")

