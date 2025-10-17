from nicegui import ui

# Define columns and rows
columns = [{'name': 'item_id',
            'label': 'Item ID',
            'field': 'item_id',
            'align': 'left',
            'sortable': True},
           {'name': 'name',
            'label': 'Name',
            'field': 'name',
            'sortable': True},
           {'name': 'component_id',
            'label': 'Component ID',
            'field': 'component_id',
            'sortable': True},
           {'name': 'actions',
            'label': 'actions',
            'field': 'actions',
            'sortable': False}
           ]

rows = [{'item_id': '0', 'name': 'test1', 'component_id': '1894'},
        {'item_id': '1', 'name': 'test1', 'component_id': '1894'},
        {'item_id': '2', 'name': 'test1', 'component_id': '1894'},]

# Create the table
table = ui.table(columns=columns, rows=rows, row_key='name').classes('w-72')


table.add_slot('header', r'''
    <q-tr :props="props">
        <q-th auto-width />
        <q-th v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.label }}
        </q-th>
    </q-tr>
''')

# Modify the table body slot for delete functionality
table.add_slot('body', r'''
    <q-tr :props="props">
        <q-td v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.value }}
        </q-td>
        <q-td auto-width>
            <q-btn size="sm" color="negative" round dense
                   @click="$parent.$emit('delete', props)"
                   icon="delete" />
            <q-btn size="sm" color="positive" round dense
                   @click="$parent.$emit('up', props)"
                   icon="keyboard_arrow_up" />
            <q-btn size="sm" color="positive" round dense
                   @click="$parent.$emit('down', props)"
                   icon="keyboard_arrow_down" />
        </q-td>
    </q-tr>
''')


# Define and connect the event handler for delete
def handle_delete(props):
    print(f"Delete row: {props}")
    # Further deletion logic goes here


def handle_up(props):
    print(f"up row: {props}")


table.on('delete', handle_delete)
table.on('up', handle_up)
table.on('down', handle_up)

# Run the UI
ui.run()
