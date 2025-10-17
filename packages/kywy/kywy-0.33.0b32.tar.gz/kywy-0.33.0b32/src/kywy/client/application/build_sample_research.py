import pandas as pd

from ...client.kawa_client import KawaClient as K
from datetime import datetime, date, timedelta
import numpy as np
from faker import Faker
import json


def kawa():
    k = K(kawa_api_url='http://localhost:8080')
    k.set_api_key(api_key_file='/Users/emmanuel/doc/local-pristine/.key')
    k.set_active_workspace_id(workspace_id='107')
    return k


research = kawa().research('Some research')
orders_model = research.register_model('3597')
events_model = research.register_model('3598')
main_model = orders_model

events_relationship = orders_model.create_relationship(
    name='Event per State..',
    description="""
      We are joining the events to the orders to get the cost per state on the State.
      """,
    origin_model=events_model,
    link={'State': 'event state'},
)

events_relationship.add_column(
    origin_column='event cost',
    aggregation='SUM',
    new_column_name='Cost per State..',
)

orders_relationship = orders_model.create_relationship(
    name='Cost per State',
    description="""
      We are joining the orders to the event to get the profit per state on the State
      """,
    target_model=orders_model,
    link={'State': 'State'},
)

orders_relationship.add_column(
    name='Profit',
    aggregation='SUM',
    new_column_name='Profit per State..',
    filters=[
        K.col('State').in_list('Ohio', 'Maine')
    ]
)

orders_model.create_metric(
    name='This is FOO',
    formula='"Profit" / "Quantity"'
)

orders_model.create_metric(
    name='This is BAR',
    formula='"This is FOO" / 2 '
)

print(research.publish_main_model(main_model=main_model))

# research.bar_chart(
#     title='Profit per State',
#     x='State',
#     y='Unit Profit',
#     color='Segment',
#     show_values=True,
#     show_totals=True,
#     model=orders_model,
#     filters=[
#         # K.col("State").in_list("California", "Ohio"),
#         K.col("Unit Profit").gt(1)
#     ],
#     order_by='Unit Profit',
#     order_direction='DESCENDING',
#     limit=5,
# )
#
# research.scatter_chart(
#     title='Order Count vs. Profit by Month',
#     granularity='Order Date',
#     x='Order ID',
#     aggregation_x='COUNT',
#     y='Profit',
#     aggregation_y='SUM',
#     color='Profit',
#     aggregation_color='SUM',
#     model=orders_model,
#     time_sampling='YEAR_AND_MONTH',
# )
#
# df = (orders_model
#       .select(
#     K.col('State'),
#     K.col('Unit Profit III').avg().alias('Average profit'),
#     K.col('Cost per State').sum().alias('Total per state'),
#     K.col('Profit per State').median().alias('Median profit per state'),
# )
#       .group_by('State')
#       .query_description('This is the description')
#       .collect())
#
# research.register_result(
#     description='Dataframe containing data about cost and profit',
#     df=df
# )
# print(research.publish_results())
