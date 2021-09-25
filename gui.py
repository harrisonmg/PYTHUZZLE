import PySimpleGUI as gui

from common import resource_path
from jigsaw import run


if __name__ == '__main__':
    [gui.Text('Image'), gui.Input(size=(20, 11), key='image')]

    join_layout = [[gui.Text('IP Address'), gui.Input(size=(20, 11), key='ip')],
                   [gui.Text('Port', ), gui.Input('7777', size=(6, 1), key='join_port')],
                   [gui.Button('Connect', key='join')]]

    host_layout = [[gui.Text('Image'), gui.Input(size=(50, 11), key='host_image'),
                    gui.FileBrowse('Browse', enable_events=True, key='host_browse')],
                   [gui.Text('Piece Count'),
                    gui.Input('1000', size=(6, 1), key='host_piece_count')],
                   [gui.Text('Port', ), gui.Input('7777', size=(6, 1), key='host_port')],
                   [gui.Button('Start Server', key='host')]]

    offline_layout = [[gui.Text('Image'), gui.Input(size=(50, 11), key='offline_image'),
                       gui.FileBrowse('Browse', enable_events=True, key='offline_browse')],
                      [gui.Text('Piece Count'),
                       gui.Input('1000', size=(6, 1), key='offline_piece_count')],
                      [gui.Button('Play', key='offline')]]

    tabs = [[gui.TabGroup([[gui.Tab('Join Server', join_layout)],
                           [gui.Tab('Host Server', host_layout)],
                           [gui.Tab('Play Offline', offline_layout)]])]]

    window = gui.Window('Rompecabezas', tabs, icon=resource_path('icon.ico'))

    thread = None

    while True:
        event, values = window.read()
        if event == gui.WIN_CLOSED:
            window.close()
            break
        elif event == 'host_browse':
            window['host_image'].update(values['host_browse'])
        elif event == 'offline_browse':
            window['offline_image'].update(values['offline_browse'])
        elif event == 'join':
            args = ['-c', values['ip'], '-p', values['join_port']]
            window.close()
            run(args)
            break
        elif event == 'host':
            args = [values['host_piece_count'], '-s', values['host_image'],
                    '-p', values['host_port']]
            window.close()
            run(args)
            break
        elif event == 'offline':
            args = [values['offline_piece_count'], '-o', values['offline_image']]
            window.close()
            run(args)
            break
