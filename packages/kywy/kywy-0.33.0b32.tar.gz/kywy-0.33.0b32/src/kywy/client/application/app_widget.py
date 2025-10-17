from abc import ABC, abstractmethod
from uuid import uuid4
import json
import time
from .application_building_utils import to_tuple, info


class Widget(ABC):

    def __init__(self, kawa, dashboard_id_supplier):
        self._k = kawa
        self._dashboard_id_supplier = dashboard_id_supplier
        self._widget_id = None
        self._x = None
        self._y = None
        self._width = None
        self._height = None

    def set_position(self, x, y, width):
        self._x = x
        self._y = y
        self._width = width
        self._height = self.compute_height(width)

    @abstractmethod
    def compute_height(self, width):
        ...

    def set_widget_id(self, widget_id):
        self._widget_id = widget_id

    def widget_id(self):
        return self._widget_id

    def position(self):
        return {
            "widgetId": str(self._widget_id),
            "positioning": {
                "width": self._width,
                "height": self._height,
                "x": self._x,
                "y": self._y,
                "slide": "dashboard"
            }
        }


class TextWidget(Widget):

    def __init__(self, kawa, dashboard_id_supplier, content):
        super().__init__(kawa=kawa, dashboard_id_supplier=dashboard_id_supplier)
        self._content = content

    @property
    def title(self):
        return self._content

    def compute_height(self, width):
        return 7

    def sync(self):
        info("💬 Creating text widget")
        dashboard_id = self._dashboard_id_supplier()
        widget_id = 'text_' + str(uuid4())
        self._k.commands.run_command('addDashboardWidgets', {
            "dashboardId": str(dashboard_id),
            "widgets": [
                {
                    "definition": {
                        "type": "RICH_TEXT_EDITOR",
                        "content": ""
                    },
                    "widgetId": widget_id,
                    "displayInformation": {
                        "displayName": "",
                        "description": ""
                    },
                    "displayParameters": {}
                }
            ]
        })
        self._k.commands.run_command('replaceWidgetDefinition', {
            "dashboardId": str(dashboard_id),
            "widgetId": widget_id,
            "widgetDefinition": {
                "type": "RICH_TEXT_EDITOR",
                "content": self._content
            }
        })
        self.set_widget_id(widget_id)


class DataWidget(Widget, ABC):

    def __init__(self,
                 kawa,
                 dashboard_id_supplier,
                 sheet_id_supplier,
                 layout_type,
                 title,
                 filters,
                 order_by,
                 order_direction,
                 limit):
        super().__init__(
            kawa=kawa,
            dashboard_id_supplier=dashboard_id_supplier
        )
        self._title = title
        self._sheet_id_supplier = sheet_id_supplier
        self._layout_id = None
        self._layout_type = layout_type
        self._cached_sheet = None
        self._filters = filters
        self._order_by = order_by
        self._order_direction = order_direction
        self._limit = limit or -1

    def sync(self):
        start_time = time.time()
        self._register()
        layout_id = self.sync_layout()
        elapsed_time = time.time() - start_time
        info(f'📊 A new {self._layout_type} widget was created in {elapsed_time:.4f}s: {self._title}')
        return {
            'layout_id': str(layout_id),
            'sheet_id': str(self.sheet_id),
        }

    @abstractmethod
    def sync_layout(self):
        ...

    def compute_height(self, width):
        # TODO: Adjust this
        return 10

    @property
    def title(self):
        return self._title

    @property
    def layout_id(self):
        return self._layout_id

    @property
    def sheet_id(self):
        return self._sheet_id_supplier()

    @property
    def sheet(self):
        if not self._cached_sheet:
            self._cached_sheet = self._k.entities.sheets().get_entity_by_id(self.sheet_id)
        return self._cached_sheet

    @property
    def widget_id(self):
        return self._widget_id

    def filters_as_list_of_dict(self):
        return [f.to_dict() for f in (self._filters or [])]

    def column(self, column_name):
        sheet = self.sheet
        all_columns = sheet.get('indicatorColumns', []) + sheet.get('computedColumns', [])
        for column in all_columns:
            display_name = column['displayInformation']['displayName']
            if display_name == column_name:
                return column
        raise Exception(f'The column {column_name} was not found in the sheet')

    def _register(self):

        layout_type = self._layout_type
        dashboard_id = self._dashboard_id()
        widget_id = f'{self._layout_type}-{uuid4()}'

        if not self.sheet_id:
            raise Exception('There is no sheet for this layout')

        if not dashboard_id:
            layout = self._k.commands.run_command('createLayout', {
                "layoutType": layout_type,
                "status": 'ACTIVE',
                "sheetId": self.sheet_id,
                "forcedName": self._title,
                "shared": False,
                "createLayoutWithoutFields": True,
                "standalone": False,
            })
            self._layout_id = layout['id']
        else:
            extended_dashboard = self._k.commands.run_command('createViewAndAddDashboardWidget', {
                "layoutType": layout_type,
                "sheetId": self.sheet_id,
                "widgetId": widget_id,
                "name": self._title,
                "dashboardId": str(dashboard_id),
            })

            widgets = extended_dashboard['dashboard']['widgets']
            widget = [w for w in widgets if w['widgetId'] == widget_id][0]

            self._layout_id = widget['definition']['layoutId']
            self.set_widget_id(widget_id)

        return self._layout_id

    def _dashboard_id(self):
        return None if not self._dashboard_id_supplier else self._dashboard_id_supplier()


class ScatterChart(DataWidget):

    def __init__(self,
                 kawa,
                 dashboard_id_supplier,
                 sheet_id_supplier,
                 title,
                 x,
                 aggregation_x,
                 y,
                 aggregation_y,
                 granularity,
                 time_sampling=None,
                 color=None,
                 aggregation_color=None,
                 filters=None,
                 order_by=None,
                 order_direction=None,
                 limit=None,
                 ):
        super().__init__(
            kawa=kawa,
            dashboard_id_supplier=dashboard_id_supplier,
            sheet_id_supplier=sheet_id_supplier,
            title=title,
            layout_type='CHART',
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
        )

        self._x = x
        self._aggregation_x = aggregation_x

        self._y = y
        self._aggregation_y = aggregation_y or 'SUM'

        self._granularity = granularity or 'SUM'

        self._color = color
        self._aggregation_color = aggregation_color or 'COUNT'

        self._time_sampling = time_sampling

        self._chart_type = 'scatter'

    def sync_layout(self):
        layout_id = self.layout_id
        x_column = self.column(self._x)
        y_column = self.column(self._y)
        granularity_column = self.column(self._granularity)
        color_column = self.column(self._color) if self._color else None

        groupings = []
        series = []

        # Takes care of granularity (The grouping) // Applies Time segmentation if defined
        group = {
            "fieldId": 'granularity',
            "columnId": granularity_column['columnId'],
            "displayInformation": {"displayName": self._granularity}
        }
        if self._time_sampling:
            sampling_type = 'DATE_TIME_SAMPLER' if granularity_column['type'] == 'date_time' else 'DATE_SAMPLER'
            sampling_type_key = 'dateTimeSamplerType' if granularity_column[
                                                             'type'] == 'date_time' else 'dateSamplerType'
            group['sampler'] = {
                "samplerType": sampling_type,
                sampling_type_key: self._time_sampling,
            }

        groupings.append(group)

        # X and Y
        series.append({
            "fieldId": "x",
            "columnId": x_column['columnId'],
            "displayInformation": {"displayName": self._x},
            "seriesType": self._chart_type,
            "aggregationMethod": self._aggregation_x,
        })
        series.append({
            "fieldId": "y",
            "columnId": y_column['columnId'],
            "displayInformation": {"displayName": self._y},
            "seriesType": self._chart_type,
            "aggregationMethod": self._aggregation_y,
        })

        # Color if defined
        if color_column:
            series.append({
                "fieldId": "color",
                "columnId": color_column['columnId'],
                "displayInformation": {"displayName": self._color},
                "seriesType": self._chart_type,
                "aggregationMethod": self._aggregation_color,
            })

        chart_display_configuration = {
            **series_and_axis(
                chart_type=self._chart_type,
                series_field_ids=['x', 'y', 'color'] if color_column else ['x', 'y'],
            ),
            **chart_settings(
                chart_type=self._chart_type,
                scatter_color_mode=bool(self._color)
            ),
        }

        self._k.commands.run_command('configureChart', {
            "filters": self.filters_as_list_of_dict(),
            "orderBy": self._order_by,
            "sortDirection": self._order_direction,
            "limit": self._limit,
            "layoutId": str(layout_id),
            "groupingParameters": groupings,
            "seriesParameters": series,
            "chartDisplayConfiguration": chart_display_configuration,
        })
        return layout_id


class SimpleChart(DataWidget):

    def __init__(self,
                 kawa,
                 dashboard_id_supplier,
                 sheet_id_supplier,
                 title,
                 x,
                 y,
                 chart_type,
                 aggregation,
                 legend='BOTTOM',
                 show_values=False,
                 show_totals=False,
                 show_labels=False,
                 time_sampling=None,
                 color=None,
                 stack=True,
                 area=False,
                 align_zero=True,
                 fill_in_temporal_gaps=False,
                 color_offset=0,
                 doughnut=False,
                 filters=None,
                 order_by=None,
                 order_direction=None,
                 limit=None,
                 ):

        super().__init__(
            kawa=kawa,
            dashboard_id_supplier=dashboard_id_supplier,
            sheet_id_supplier=sheet_id_supplier,
            title=title,
            layout_type='CHART',
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
        )

        aggr_as_tuple = to_tuple(aggregation)
        y_as_tuple = to_tuple(y)

        if len(aggr_as_tuple) != len(y_as_tuple):
            raise Exception('Both y and aggregation must have the same length')

        if len(y_as_tuple) == 0:
            raise Exception('At least one Y axis is necessary')

        self._x = x
        self._y = y_as_tuple
        self._aggregation = aggr_as_tuple
        self._color = color
        self._stack = stack
        self._chart_type = chart_type
        self._time_sampling = time_sampling
        self._legend = legend
        self._show_values = show_values
        self._show_totals = show_totals
        self._area = area
        self._align_zero = align_zero
        self._show_labels = show_labels
        self._fill_in_temporal_gaps = fill_in_temporal_gaps
        self._color_offset = color_offset
        self._doughnut = doughnut

    def sync_layout(self):

        layout_id = self.layout_id

        if not self._color:
            stacking = 0
        else:
            stacking = 2

        x_column = self.column(self._x)
        c_column = self.column(self._color) if self._color else None
        groupings = []
        series = []

        x = {
            "fieldId": 'x',
            "columnId": x_column['columnId'],
            "displayInformation": {"displayName": self._x}
        }
        if self._time_sampling:
            sampling_type = 'DATE_TIME_SAMPLER' if x_column['type'] == 'date_time' else 'DATE_SAMPLER'
            sampling_type_key = 'dateTimeSamplerType' if x_column['type'] == 'date_time' else 'dateSamplerType'
            x['sampler'] = {
                "samplerType": sampling_type,
                sampling_type_key: self._time_sampling,
            }

        groupings.append(x)

        if c_column:
            groupings.append({
                "fieldId": 'color',
                "columnId": c_column['columnId'],
                "displayInformation": {"displayName": self._color}
            })

        # Takes care of all y_axis:
        field_id = 0
        series_field_ids = []
        for y, aggr in zip(self._y, self._aggregation):
            field_id += 1
            series_field_ids.append(f'field{field_id}')
            y_column = self.column(y)
            series.append({
                "fieldId": f'field{field_id}',
                "columnId": y_column['columnId'],
                "displayInformation": {"displayName": y},
                "seriesType": self._chart_type,
                "aggregationMethod": "boxplot" if self._chart_type == 'boxplot' else aggr,
            })

        self._k.commands.run_command('configureChart', {
            "filters": self.filters_as_list_of_dict(),
            "orderBy": self._order_by,
            "sortDirection": self._order_direction,
            "limit": self._limit,
            "layoutId": str(layout_id),
            "groupingParameters": groupings,
            "seriesParameters": series,
            "chartDisplayConfiguration": {
                **series_and_axis(
                    chart_type=self._chart_type,
                    series_field_ids=series_field_ids,
                    show_label=self._show_values,
                    show_label_names=self._show_labels,
                    line_area=self._area,
                    color_offset=self._color_offset,
                ),
                **chart_settings(
                    legend_position=self._legend,
                    chart_type=self._chart_type,
                    stacking=stacking,
                    totals=self._show_totals,
                    fill_in_temporal_gaps=self._fill_in_temporal_gaps,
                    align_zero=self._align_zero,
                    doughnut=self._doughnut,
                ),
            },
        })

        return layout_id


class IndicatorChart(DataWidget):

    def __init__(self,
                 kawa,
                 dashboard_id_supplier,
                 sheet_id_supplier,
                 title,
                 indicator,
                 aggregation,
                 filters=None,
                 order_by=None,
                 order_direction=None,
                 limit=None,
                 ):
        super().__init__(
            kawa=kawa,
            dashboard_id_supplier=dashboard_id_supplier,
            sheet_id_supplier=sheet_id_supplier,
            title=title,
            layout_type='CHART',
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
        )

        self._indicator = indicator
        self._aggregation = aggregation
        self._chart_type = 'indicator'

    def sync_layout(self):
        layout_id = self.layout_id

        indicator_column = self.column(self._indicator)
        modified_layout = self._k.commands.run_command('addChartSeries', {
            "layoutId": str(layout_id),
            "columnId": indicator_column['columnId'],
            "displayInformation": {
                "displayName": self._title,
                "description": "",
            },
            "seriesType": self._chart_type,
            "aggregationMethod": self._aggregation,
        })

        series_field_ids = modified_layout['fieldIdsForSeries']
        self._k.commands.run_command('replaceChartDisplayConfiguration', {
            "layoutId": str(layout_id),
            "chartDisplayConfiguration": {
                **series_and_axis(
                    chart_type=self._chart_type,
                    series_field_ids=series_field_ids,
                ),
                **chart_settings(
                    chart_type=self._chart_type
                ),
            }
        })
        return layout_id

    def compute_height(self, width):
        return width // 2


class Table(DataWidget):

    def __init__(self,
                 kawa,
                 dashboard_id_supplier,
                 sheet_id_supplier,
                 title,
                 group_by=None,
                 column_names=None):
        super().__init__(
            kawa=kawa,
            dashboard_id_supplier=dashboard_id_supplier,
            sheet_id_supplier=sheet_id_supplier,
            title=title,
            layout_type='GRID',
            filters=None,
            order_by=None,
            order_direction=None,
            limit=None,
        )
        self._column_names = column_names
        self._group_by = group_by

    def sync_layout(self):
        if not self._column_names:
            return

        layout_id = self.layout_id
        self._k.commands.run_command('configureGrid', {
            "name": self.title,
            "layoutId": str(layout_id),
            "groupBy": self._group_by,
            "columnNames": self._column_names,
        })

        return layout_id


class WidgetFactory:

    def __init__(self, kawa, default_sheet_id_supplier=None, dashboard_id_supplier=None):
        self._k = kawa
        self._dashboard_id_supplier = dashboard_id_supplier
        self._default_sheet_id_supplier = default_sheet_id_supplier

    def sheet_id_supplier(self, sheet_id=None, source=None, model=None):
        if sheet_id:
            return sheet_id
        elif source:
            return source.sheet_id
        elif model:
            return model.sheet_id
        elif self._default_sheet_id_supplier:
            return self._default_sheet_id_supplier()
        else:
            raise Exception('No mean to get a sheet id was provided')

    def table(self, title, source=None, sheet_id=None, column_names=None, group_by=None):
        return Table(
            kawa=self._k,
            dashboard_id_supplier=self._dashboard_id_supplier,
            sheet_id_supplier=lambda: self.sheet_id_supplier(sheet_id, source),
            title=title,
            group_by=group_by,
            column_names=column_names,
        )

    def indicator_chart(self, title, indicator, aggregation='SUM', source=None, sheet_id=None, filters=None,
                        order_by=None, order_direction=None, limit=None, ):
        return IndicatorChart(
            kawa=self._k,
            dashboard_id_supplier=self._dashboard_id_supplier,
            sheet_id_supplier=lambda: self.sheet_id_supplier(sheet_id, source),
            title=title,
            indicator=indicator,
            aggregation=aggregation,
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
        )

    def pie_chart(self, title, labels, values, aggregation='SUM', source=None, show_values=False, show_labels=False,
                  legend='NONE', time_sampling=None, doughnut=False, sheet_id=None, filters=None,
                  order_by=None, order_direction=None, limit=None, ):
        return self._simple_chart(
            title=title,
            x=labels,
            y=values,
            aggregation=aggregation,
            chart_type='pie',
            legend=legend,
            source=source,
            show_values=show_values,
            show_labels=show_labels,
            time_sampling=time_sampling,
            doughnut=doughnut,
            sheet_id=sheet_id,
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
        )

    def boxplot(self, title, x, y, aggregation='SUM', source=None, show_values=False,
                time_sampling=None, sheet_id=None, filters=None,
                order_by=None, order_direction=None, limit=None, ):
        return self._simple_chart(
            title=title,
            x=x,
            y=y,
            aggregation=aggregation,
            chart_type='boxplot',
            legend='NONE',
            source=source,
            show_values=show_values,
            time_sampling=time_sampling,
            sheet_id=sheet_id,
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
        )

    def scatter_chart(self, title, x, y, granularity, aggregation_x='SUM', aggregation_y='SUM',
                      aggregation_color='COUNT', time_sampling=None,
                      color=None, source=None, sheet_id=None, filters=None,
                      order_by=None, order_direction=None, limit=None, ):

        return ScatterChart(
            kawa=self._k,
            dashboard_id_supplier=self._dashboard_id_supplier,
            sheet_id_supplier=lambda: self.sheet_id_supplier(sheet_id, source),
            title=title,
            x=x,
            aggregation_x=aggregation_x,
            y=y,
            aggregation_y=aggregation_y,
            granularity=granularity,
            color=color,
            aggregation_color=aggregation_color,
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
            time_sampling=time_sampling,
        )

    def line_chart(self, title, x, y, aggregation='SUM', legend='BOTTOM', show_values=False, time_sampling=None,
                   color=None, source=None, area=False, align_zero=True, fill_in_temporal_gaps=False, color_offset=0,
                   sheet_id=None, filters=None, order_by=None, order_direction=None, limit=None, ):
        return self._simple_chart(
            title=title,
            x=x,
            y=y,
            aggregation=aggregation,
            chart_type='line',
            color=color,
            source=source,
            legend=legend,
            time_sampling=time_sampling,
            show_values=show_values,
            align_zero=align_zero,
            area=area,
            fill_in_temporal_gaps=fill_in_temporal_gaps,
            color_offset=color_offset,
            sheet_id=sheet_id,
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
        )

    def bar_chart(self, title, x, y, aggregation='SUM', legend='BOTTOM', show_values=False, time_sampling=None,
                  color=None, source=None, show_totals=False, color_offset=0, sheet_id=None, filters=None,
                  order_by=None, order_direction=None, limit=None,
                  ):
        return self._simple_chart(
            title=title,
            x=x,
            y=y,
            aggregation=aggregation,
            chart_type='bar',
            color=color,
            source=source,
            time_sampling=time_sampling,
            legend=legend,
            show_values=show_values,
            show_totals=show_totals,
            color_offset=color_offset,
            sheet_id=sheet_id,
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
        )

    def _simple_chart(self, title, x, y, aggregation, chart_type, time_sampling=None, color=None, source=None,
                      legend='BOTTOM', show_values=False, show_totals=False, area=False, align_zero=True,
                      fill_in_temporal_gaps=False, show_labels=False, color_offset=0, doughnut=False, sheet_id=None,
                      filters=None, order_by=None, order_direction=None, limit=None):

        return SimpleChart(
            kawa=self._k,
            dashboard_id_supplier=self._dashboard_id_supplier,
            sheet_id_supplier=lambda: self.sheet_id_supplier(sheet_id, source),
            title=title,
            chart_type=chart_type,
            x=x,
            y=y,
            color=color,
            aggregation=aggregation,
            time_sampling=time_sampling,
            legend=legend,
            show_values=show_values,
            show_totals=show_totals,
            show_labels=show_labels,
            area=area,
            align_zero=align_zero,
            fill_in_temporal_gaps=fill_in_temporal_gaps,
            color_offset=color_offset,
            doughnut=doughnut,
            filters=filters,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
        )


def chart_settings(chart_type, label_items_number=50, label_item_rotation=25, scatter_symbol_size=10, stacking=0,
                   scatter_color_mode=False, legend_position='AUTO', totals=False, align_zero=True,
                   fill_in_temporal_gaps=False, doughnut=False, ):
    return {
        "scatterSymbolSize": scatter_symbol_size,
        "fillInTemporalGaps": fill_in_temporal_gaps,
        "chartType": chart_type,
        "columnValuesCustomColorsList": [],
        "comparisonColors": [],
        "comparisonsConfig": {},
        "multigrid": False,
        "doughnut": doughnut,
        "alignZero": align_zero,
        "labelItemsNumber": label_items_number,
        "labelItemRotation": label_item_rotation,
        "stacking": stacking,
        "showDataZoom": True,
        "useScale": scatter_color_mode,
        "smoothLine": False,
        "showYAxisLabel": False,
        "showPoints": True,
        "totals": totals,
        "scatterVisualMap": False,
        "scatterColorMode": scatter_color_mode,
        "scatterSeriesColor": {"colorIndexInPalette": 0},
        "legend": [{"positionMode": legend_position, "currentSize": "S"}, {"positionMode": "NONE"}],
        "formatters": {},
        "lineWidth": 1,
        "isMultiSeriesMode": True
    }


def series_and_axis(chart_type, series_field_ids, show_label=False,
                    show_label_names=False, line_area=False, color_offset=0):
    y_axis = [{"type": "value", "id": f"axis{i}"} for i in range(1, 5)]
    series_to_axis_map = {}
    series = []
    counter = 0

    for series_field_id in series_field_ids:
        counter += 1
        series_id = f'series{counter}'
        axis_id = f'axis{counter}'
        series.append({
            "id": series_id,
            "isVisible": True,
            "label": show_label,
            "labelNames": show_label_names,
            "type": chart_type,
            "lineAreaStyle": line_area,
            "colorIndexInPalette": (color_offset + counter - 1) % 7,
            "fieldId": str(series_field_id),
            "showPoints": True,
        })
        series_to_axis_map[series_id] = axis_id

    return {
        "containers": [{"id": "c1"}],
        "yAxis": y_axis,
        "map": {
            "seriesToYAxis": series_to_axis_map,
            "yAxisToContainer": {"axis1": "c1", "axis2": "c1", "axis3": "c1", "axis4": "c1"}
        },
        "series": series,
    }
