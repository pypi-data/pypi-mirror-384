from datetime import datetime

import json

from .app_model import DataModel
from .app_reporter import Reporter
from .report_builder import ReportBuilder
from .app_widget import WidgetFactory


class ResearchBuilder:

    def __init__(self, kawa_client, name):
        self._k = kawa_client
        self._name = name
        self._models = []
        self._results = []
        self._charts = []

        self._reporter = Reporter(name=name)
        self._widget_factory = WidgetFactory(
            kawa=kawa_client
        )

    def publish_main_model(self, main_model):
        for model in self._models:
            model.sync()

        relationships = self._analyse_relationships()
        metrics = self._analyse_metrics()

        return json.dumps(
            obj={
                'relationships': relationships,
                'metrics': metrics,
                'mainSheetId': main_model.sheet_id,
            },
            indent=4
        )

    def publish_results(self):
        created_grids = []
        created_charts = []

        created_chart_collector = {}
        for chart in self._charts:
            created_layout = chart.sync()
            sheet_id = created_layout['sheet_id']
            if created_layout['sheet_id'] not in created_chart_collector:
                created_chart_collector[sheet_id] = []
            created_chart_collector[sheet_id].append(created_layout['layout_id'])

        for sheet_id, view_ids in created_chart_collector.items():
            created_charts.append({
                'sheetId': sheet_id,
                'viewIds': view_ids
            })

        relationships = self._analyse_relationships()

        for model in self._models:
            view_ids = model.create_views()
            created_grids.append({
                'sheetId': str(model.sheet_id),
                'viewIds': view_ids
            })

        result = {
            'grids': [v for v in created_grids if v['viewIds']],
            'charts': [v for v in created_charts if v['viewIds']],
            'data': self._results,
            'relationships': relationships,
        }

        return json.dumps(result)

    def register_result(self, description, df, from_select=True):
        self._results.append({
            'description': description,
            'fromSelect': from_select,
            'df': df.to_csv(),
        })

    def register_model(self, model_id, **kwargs):
        sheet = self._k.entities.sheets().get_entity_by_id(model_id)
        if not sheet:
            raise Exception(f'Sheet with id={model_id} not found')
        model = DataModel(
            kawa=self._k,
            reporter=self._reporter,
            name=sheet['displayInformation']['displayName'],
            sheet=sheet
        )
        self._models.append(model)
        return model

    # Charts
    def bar_chart(self, **kwargs):
        self._register_chart(self._widget_factory.bar_chart, **kwargs)

    def line_chart(self, **kwargs):
        self._register_chart(self._widget_factory.line_chart, **kwargs)

    def indicator_chart(self, **kwargs):
        self._register_chart(self._widget_factory.indicator_chart, **kwargs)

    def boxplot(self, **kwargs):
        self._register_chart(self._widget_factory.boxplot, **kwargs)

    def scatter_chart(self, **kwargs):
        self._register_chart(self._widget_factory.scatter_chart, **kwargs)

    def pie_chart(self, **kwargs):
        self._register_chart(self._widget_factory.pie_chart, **kwargs)

    def _register_chart(self, chart_generator, **kwargs):
        kwargs['sheet_id'] = kwargs['model'].sheet_id
        del kwargs['model']
        chart = chart_generator(**kwargs)
        self._charts.append(chart)

    def _analyse_relationships(self):
        relationships = []
        for model in self._models:
            ascii_rep = [rel.to_ascii() for rel in model.relationships]
            if ascii_rep:
                relationships.append({
                    'sheetName': model.name,
                    'asciiRepresentations': ascii_rep,
                })
        return relationships

    def _analyse_metrics(self):
        metrics = []
        for model in self._models:
            ascii_rep = [m.to_ascii() for m in model.metrics]
            if ascii_rep:
                metrics.append({
                    'sheetName': model.name,
                    'asciiRepresentations': ascii_rep,
                })
        return metrics
