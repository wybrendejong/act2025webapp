from nicegui import ui

maxZoom = 13
minZoom = 8

class Demo:
    def __init__(self):
        self.number = 1

with ui.grid().classes('grid; grid-cols-1 md:grid-cols-[3fr_1fr] w-full gap-5'):
    with ui.card():
        ui.html("<b>Rat Monitor</b>").style('font-size: 24pt')
    with ui.card():
        dark = ui.dark_mode()
        ui.switch('Dark mode').bind_value(dark)

with ui.grid().classes('grid grid-cols-1 md:grid-cols-[3fr_1fr] w-full gap-5'):
    with ui.card().tight():
        m = ui.leaflet(center=(52.375, 4.935)).style('width: 100%; position: relative; padding-top: 60%;')
        m.tile_layer(
            url_template=r'https://tiles.stadiamaps.com/tiles/osm_bright/{z}/{x}/{y}{r}.png',
            options={
            'maxZoom': maxZoom,
            'minZoom': minZoom,
            'attribution': '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            },
        )
        # m.generic_layer(name='polygon', args=[PUT YOUR GEOMETRY HERE])
        # ui.label().bind_text_from(m, 'center', lambda center: f'Center: {center[0]:.3f}, {center[1]:.3f}')
        # ui.label().bind_text_from(m, 'zoom', lambda zoom: f'Zoom: {zoom}')

    with ui.card().classes("p-10"):
        demo = Demo()

        with ui.column().classes("w-full gap-4"):  # stack all vertically
            with ui.column().classes('w-full'):
                ui.label('Slider 1')
                ui.slider(min=1, max=10).set_value(3)

            with ui.column().classes('w-full'):
                ui.label('Slider 2')
                ui.slider(min=1, max=10).set_value(2)

            with ui.column().classes('w-full'):
                ui.label('Slider 3')
                ui.slider(min=1, max=10).set_value(8)

            with ui.column().classes('w-full'):
                ui.label('Bound Slider')
                ui.slider(min=1, max=3).bind_value(demo, 'number')

            with ui.column().classes('w-full'):
                ui.label('Toggle')
                ui.toggle({1: 'A', 2: 'B', 3: 'C'}).bind_value(demo, 'number')

            with ui.column().classes('w-full'):
                ui.label('Number')
                ui.number().bind_value(demo, 'number')


ui.run()








