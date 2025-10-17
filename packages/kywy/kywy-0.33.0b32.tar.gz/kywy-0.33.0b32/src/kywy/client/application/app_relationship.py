from .application_building_utils import get_column, load_sheet
from .app_synchronizer import Synchronizer
import re

ACCEPTABLE_AGGREGATIONS = [
    'FIRST',
    'SUM',
    'AVERAGE',
    'COUNT',
    'MEDIAN',
    'COUNT_UNIQUE',
    'MIN',
    'MAX'
]


class Relationship:

    def __init__(self, kawa, reporter, name, model, link,
                 description=None, dataset=None, target_sheet=None, ):
        self._k = kawa
        self._reporter = reporter
        self._name = name
        self._description = description
        self._dataset = dataset
        self._target_sheet = target_sheet
        self._model = model
        self._link = link
        self._cached_sheet = None
        self._columns = []

    @property
    def source_sheet(self):
        return self._model.sheet

    @property
    def target_sheet(self):
        return self._target_sheet if self._target_sheet else self._dataset.sheet

    @property
    def name(self):
        return self._name

    def add_column(self,
                   aggregation,
                   new_column_name,
                   filters=None,
                   name=None,
                   origin_column=None):
        uc_aggregation = aggregation.upper()
        uc_aggregation = 'FIRST' if uc_aggregation == 'ANY_VALUE' else uc_aggregation
        if uc_aggregation not in ACCEPTABLE_AGGREGATIONS:
            raise Exception('The aggregation is not known, please use one of: ' + ','.join(ACCEPTABLE_AGGREGATIONS))

        self._columns.append({
            'name': name or origin_column,
            'aggregation': uc_aggregation,
            'new_column_name': new_column_name,
            'filters': filters,
        })

    def sync(self):
        if not self._columns:
            return

        if not self._link:
            raise Exception('There is no definition for the link in this relationship')

        for column in self._columns:
            Relationship._Synchronizer(
                kawa=self._k,
                relationship=self,
                column=column
            ).sync()

        self._reporter.report(
            object_type='Relationship',
            name=self._name,
        )

    def build_join_definition(self):
        joins = []
        for source, target in self._link.items():
            source_column = get_column(
                sheet=self.source_sheet,
                column_name=source,
                kawa=self._k,
                force_refresh_sheet=True
            )

            target_column = get_column(
                sheet=self.target_sheet,
                column_name=target,
                kawa=self._k,
                force_refresh_sheet=True
            )

            joins.append({
                "targetColumnId": target_column['columnId'],
                "sourceColumnId": source_column['columnId'],
            })
        return joins

    def to_ascii(self):

        source_sheet_name = remove_uuid_suffix(self.source_sheet['displayInformation']['displayName'])
        target_sheet_name = remove_uuid_suffix(self.target_sheet['displayInformation']['displayName'])

        on_clause_collector = []

        for source, target in self._link.items():
            on_clause = f'"{source_sheet_name}"."{source}"="{target_sheet_name}"."{target}"'
            on_clause_collector.append(on_clause)

        on_clauses = ' and '.join(on_clause_collector)
        ascii_representation = f'"{source_sheet_name}" LINKED WITH "{target_sheet_name}" ON ({on_clauses}):\n'

        ascii_representation += "  |\n"
        for col in self._columns:
            col_ascii = f"  |-> {col['aggregation']}({col['name']})\n"
            ascii_representation += col_ascii

        return ascii_representation.strip()

    class _Synchronizer(Synchronizer):
        def __init__(self, kawa, relationship, column):
            super().__init__(
                kawa=kawa,
                icon='🔗',
                entity_description=f'Relationship "{relationship.name}"',
            )
            self._relationship = relationship
            self._column = column

        def _load_state(self):
            existing_columns = {
                c['displayInformation']['displayName']: c
                for c in self._relationship.source_sheet['computedColumns']
                if c['columnNature'] == 'LINKED' and c['columnStatus'] == 'ACTIVE'
            }
            return existing_columns.get(self._column['new_column_name'])

        def _raise_if_state_invalid(self):
            ...

        def _should_create(self):
            return self._state is None

        def _create_new_entity(self):
            source_sheet = self._relationship.source_sheet
            target_sheet = self._relationship.target_sheet

            target_column = get_column(
                sheet=target_sheet,
                column_name=self._column['name'],
                kawa=self._k,
                force_refresh_sheet=True
            )

            joins = self._relationship.build_join_definition()

            filters = [f.to_dict() for f in (self._column.get('filters') or [])]
            self._k.commands.run_command(
                command_name='addLookupField',
                command_parameters={
                    "filters": filters,
                    "layoutId": str(source_sheet['defaultLayoutId']),  # This is the source layout
                    "linkedSheetId": str(target_sheet['id']),  # This is the target sheet
                    "columnDefinitions": [
                        {
                            "columnId": target_column['columnId'],
                            "aggregation": self._column['aggregation'],
                            "lookupColumnName": self._column['new_column_name'],
                        }
                    ],
                    "joins": joins
                }
            )

        def _update_entity(self):
            existing_lookup_column = self._state
            existing_joins = existing_lookup_column['joins']
            new_joins = self._relationship.build_join_definition()

            existing_joins_for_comparison = sorted([(j['sourceColumnId'], j['targetColumnId']) for j in existing_joins])
            new_joins_for_comparison = sorted([(j['sourceColumnId'], j['targetColumnId']) for j in new_joins])
            if existing_joins_for_comparison != new_joins_for_comparison:
                # TODO We need to update the join for this column
                ...

            # TODO: Update aggregation -> Need to upgrade definition view

            # TODO: Update the target column (We need BE support for this)

            ...

        def _build_new_state(self):
            pass


def remove_uuid_suffix(s: str) -> str:
    return re.sub(r'\s*\([0-9a-fA-F\-]{36}\)\s*$', '', s)
