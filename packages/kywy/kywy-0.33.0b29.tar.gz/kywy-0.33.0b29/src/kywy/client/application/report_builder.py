import json
from dataclasses import asdict
from .application_building_utils import info
from .report_blocks import ReportBlock
from .app_widget import WidgetFactory
from datetime import datetime


class ReportBuilder:

    def __init__(self, kawa_client, name, unique_tag=None):
        self._k = kawa_client
        self._name = name
        self._tag = unique_tag or f'#{name}'
        self._dashboard_id = None
        self._blocks = []
        self._widgets = {}

        self._widget_factory = WidgetFactory(
            kawa=kawa_client,
            dashboard_id_supplier=lambda: self._dashboard_id,
            default_sheet_id_supplier=None
        )

    def publish(self):
        self._sync()
        meta = self._meta()
        return json.dumps(meta)

    def header1(self, content):
        self._add_block(ReportBlock.header(1, content))

    def header2(self, content):
        self._add_block(ReportBlock.header(2, content))

    def header3(self, content):
        self._add_block(ReportBlock.header(3, content))

    def paragraph(self, content):
        self._add_block(ReportBlock.content('paragraph', 'text', content))

    def code(self, content):
        self._add_block(ReportBlock.content('code', 'code', content))

    def line_chart(self, **kwargs):
        chart = self._widget_factory.line_chart(**kwargs)
        self._add_block(self._init_chart_block(chart))

    def bar_chart(self, **kwargs):
        chart = self._widget_factory.bar_chart(**kwargs)
        self._add_block(self._init_chart_block(chart))

    def indicator_chart(self, **kwargs):
        chart = self._widget_factory.indicator_chart(**kwargs)
        self._add_block(self._init_chart_block(chart))

    def boxplot(self, **kwargs):
        chart = self._widget_factory.boxplot(**kwargs)
        self._add_block(self._init_chart_block(chart))

    def scatter_chart(self, **kwargs):
        chart = self._widget_factory.scatter_chart(**kwargs)
        self._add_block(self._init_chart_block(chart))

    def pie_chart(self, **kwargs):
        chart = self._widget_factory.pie_chart(**kwargs)
        self._add_block(self._init_chart_block(chart))

    def table(self, **kwargs):
        chart = self._widget_factory.table(**kwargs)
        self._add_block(self._init_chart_block(chart))

    def _get_block(self, block_id):
        return [b for b in self._blocks if b.id == block_id][0]

    def _add_block(self, block):
        self._blocks.append(block)

    def _sync(self):
        if not self._blocks:
            raise Exception('No blocks were added')

        self._create_dashboard()

        # We can now sync the widgets and register their ids in the block
        for block_id, widget in self._widgets.items():
            widget.sync()
            block = self._get_block(block_id=block_id)
            block.data['widgetId'] = widget.widget_id

        now = datetime.now()
        self._k.commands.run_command(
            command_name='replaceDashboardBlockEditorLayout',
            command_parameters={
                'dashboardId': self._dashboard_id,
                'blockEditorLayout': {
                    'version': "2.31.0-rc.7",
                    'time': round(now.timestamp() * 1000),
                    'blocks': [asdict(b) for b in self._blocks],
                }
            }
        )

    def _create_dashboard(self):
        info(f"Creating new dashboard with name={self._name}")
        extended_dashboard = self._k.commands.run_command(
            command_name='createDashboard',
            command_parameters={
                "displayInformation": {
                    "displayName": self._name,
                },
                "layoutType": "REPORT"
            }
        )
        self._dashboard_id = extended_dashboard['dashboard']['id']

    def _init_chart_block(self, chart):
        block_id = ReportBlock.generate_random_id()
        self._widgets[block_id] = chart
        return ReportBlock(
            id=block_id,
            type='kawaEmbed',
            data={}
        )

    def _meta(self):
        return {
            'dashboardId': f'{self._dashboard_id}'
        }
