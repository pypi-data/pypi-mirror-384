import pandas as pd

from ...client.kawa_client import KawaClient
from ...client.kawa_decorators import kawa_tool

from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from faker import Faker


def kawa():
    k = KawaClient(kawa_api_url='http://localhost:4200')
    k.set_api_key(api_key_file='/Users/emmanuel/doc/local-pristine/.key')
    k.set_active_workspace_id(workspace_id='79')
    return k


from kywy.client.kawa_client import KawaClient
from kywy.client.kawa_decorators import kawa_tool
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from faker import Faker
from kywy.client.kawa_client import KawaClient
from kywy.client.kawa_decorators import kawa_tool
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from faker import Faker

app = kawa().app(
    'Superstore App II',
    sidebar_color="#040506",
    theme='classic2'
)


# Declare the way your data are loaded through regular python functions.
# Here, we are downloading CSV files from internet and we are parsing into dataframes.
@kawa_tool(outputs={
    'Row ID': float, 'Order ID': str, 'Order Date': date, 'Ship Date': date, 'Ship Mode': str,
    'Customer ID': str, 'Customer Name': str, 'Segment': str, 'Country': str, 'City': str, 'State': str,
    'Postal Code': str, 'Region': str, 'Product ID': str, 'Category': str, 'Sub-Category': str, 'Product Name': str,
    'Sales': float, 'Quantity': float, 'Discount': float, 'Profit': float,
})
def load_store_data():
    url = "https://learn.kawa.ai/readme-assets/store.csv"
    df = pd.read_csv(
        url,
        parse_dates=['Ship Date', 'Order Date'],
        date_format='%Y-%m-%d',
    )
    df['Postal Code'] = df['Postal Code'].astype('string')
    return df


@kawa_tool(outputs={'event id': float, 'event date': date, 'guest name': str, 'event type': str, 'event cost': float,
                    'event state': str})
def load_events_data():
    url = "https://learn.kawa.ai/readme-assets/events.csv"
    df = pd.read_csv(
        url,
        parse_dates=['event date'],
        date_format='%Y-%m-%d',
    )
    return df


# Register your two datasets in the application
store_dataset = app.create_dataset('Store', load_store_data)
event_dataset = app.create_dataset('event', load_events_data)

model = app.create_model(store_dataset)

# We create a join between STORE and EVENTS at the state level
# We then add to the model the COST PER STATE column, the SUM of COST per state, for all events in each state.
events_relationship = model.create_relationship(
    name='Event per State',
    dataset=event_dataset,
    link={'State': 'event state'},
)
events_relationship.add_column(
    name='event cost',
    aggregation='SUM',
    new_column_name='Cost per State',
)

# We add a new variable to the model
model.create_variable(
    name='Profit Threshold',
    kawa_type='decimal',
    initial_value=10,
)

# And we create three metrics
model.create_metric(
    name='Net Profit',
    formula='SUM("Profit") - SUM("Cost per State")'
)
model.create_metric(
    name='Shipping Delay',
    prompt='How many days between ship date and order date'
)

model.create_metric(
    name='Profit above Threshold',
    formula="""SUM(CASE WHEN "Profit" >= "Profit Threshold" THEN "Profit" ELSE 0 END)""",
)

# Here, we are adding one filter, State Filter, that will filter both state columns from both datasets
app.create_text_filter(
    name='State Filter',
    filtered_column='State',
    source=store_dataset
)

app.create_text_filter(
    name='State Filter',
    filtered_column='event state',
    source=event_dataset
)

orders_page = app.create_page('Orders Analytics')


def box_plot_section(page):
    col1, col2 = page.create_section('Box Plots', 2)
    col1.boxplot(
        title='Profit per Year ($)',
        x='Order Date',
        y='Profit',
        time_sampling='YEAR',
    )
    col2.boxplot(
        title='Profit per Sub-Category ($)',
        x='Sub-Category',
        y='Profit',
    )


def kpis_section(page):
    col1, col2, col3, col4 = page.create_section('KPIs', 4)
    col1.indicator_chart(title='Total Profit ($)', indicator='Profit above Threshold')
    col2.indicator_chart(title='Total Sales ($)', indicator='Sales')
    col3.indicator_chart(title='Total Quantity', indicator='Quantity')
    col4.indicator_chart(title='Avg Discount ($)', indicator='Discount', aggregation='AVERAGE')


def trends_section(page):
    col1 = page.create_section('Trends', 1)
    col1.line_chart(
        title='Evolution of Profit and Sales ($)',
        x='Order Date',
        y=('Profit', 'Sales'),
        aggregation=('SUM', 'SUM'),
        time_sampling='YEAR_AND_MONTH',
        show_values=False,
        area=True,
        fill_in_temporal_gaps=True,
    )


def breakdowns_section(page):
    col1, col2 = page.create_section('Breakdowns', 2)
    col1.bar_chart(
        title='Shipping delay per Ship Mode (days)',
        x='Ship Mode',
        y='Shipping Delay',
        aggregation='AVERAGE',
        color='Segment',
        show_totals=True,
    )
    col2.bar_chart(
        title='Profit per Sub-Category and Ship Mode ($)',
        x='Sub-Category',
        y='Profit above Threshold',
        color='Ship Mode',
        show_totals=True,
    )
    col1.bar_chart(
        title='Profit per Year and Segment ($)',
        x='Order Date',
        y='Profit above Threshold',
        color='Segment',
        time_sampling='YEAR',
        show_values=True,
        show_totals=True,
    )
    col2.bar_chart(
        title='Profit per Year and Ship Mode ($)',
        x='Order Date',
        y='Profit above Threshold',
        color='Ship Mode',
        time_sampling='YEAR',
        show_values=True,
        show_totals=True,
    )


def pies_section(page):
    col1, col2, col3, col4 = page.create_section('Pies', 4)
    col1.pie_chart(
        title='Quantity per Ship Mode',
        labels='Ship Mode',
        values='Quantity',
        show_values=True,
        show_labels=True,
    )
    col2.pie_chart(
        title='Quantity per Year',
        labels='Order Date',
        values='Quantity',
        show_values=True,
        show_labels=True,
        time_sampling='YEAR',
    )
    col3.pie_chart(
        title='Quantity per Segment',
        labels='Segment',
        values='Quantity',
        show_values=True,
        show_labels=True,
        doughnut=True,
    )
    col4.pie_chart(
        title='Quantity per Category',
        labels='Category',
        values='Quantity',
        show_values=True,
        show_labels=True,
        doughnut=True,
    )


def scatters_section(page):
    col1, col2 = page.create_section('Scatters', 2)

    col1.scatter_chart(
        title='Profit vs. Quantity per City ⛱️',
        granularity='City',
        x='Profit',
        y='Quantity',
        color='Order ID',
        aggregation_color='COUNT'
    )

    col2.scatter_chart(
        title='Profit vs. Quantity per Customer',
        granularity='Customer Name',
        x='Profit above Threshold',
        y='Quantity',
        color='Order ID',
        aggregation_color='COUNT'
    )

    col1.scatter_chart(
        title='Profit vs. Quantity per Date',
        granularity='Order Date',
        x='Profit above Threshold',
        y='Quantity',
        color='Order ID',
        aggregation_color='COUNT'
    )

    col2.scatter_chart(
        title='Profit vs. Quantity per Product',
        granularity='Product Name',
        x='Profit above Threshold',
        y='Quantity',
        color='Order ID',
        aggregation_color='COUNT'
    )


def profit_section(page):
    col1 = page.create_section('Profit', 1)
    col1.bar_chart(
        title='Profit and Net Profit per State',
        x='State',
        y=('Profit above Threshold', 'Net Profit'),
        aggregation=('SUM', 'SUM'),
        color_offset=1,
    )


def raw_data_section(page):
    col = page.create_section('Table', 1)
    col.table(title='Store Data')


kpis_section(orders_page)
scatters_section(orders_page)
trends_section(orders_page)
pies_section(orders_page)
breakdowns_section(orders_page)
raw_data_section(orders_page)
box_plot_section(orders_page)
profit_section(orders_page)

app.publish()
