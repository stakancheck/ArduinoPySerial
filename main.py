from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from serial_asyncio import open_serial_connection
from configparser import ConfigParser
from matplotlib import style

import matplotlib.pyplot as plt
from datetime import datetime
import tkinter as tk
import customtkinter
import numpy as np
import aiofiles
import asyncio
import logging
import serial
import glob
import sys


logging.basicConfig(level=logging.INFO)
customtkinter.set_appearance_mode("System")
style.use('ggplot')

config = ConfigParser()
config.read('preferences.cfg')
config = config['DEFAULT']

FILENAME: str = config['FILENAME']
SERIAL_SPEEDS: list[str] = config['SERIAL_SPEEDS'].split(',')
MAX_VALUE_SENSOR: int = int(config['MAX_VALUE_SENSOR'])
GRAPH_TIME_LIMITS: int = int(config['GRAPH_TIME_LIMITS'])
FPS_GRAPH: int = int(config['FPS_GRAPH'])
FPS_USER_INTERFACE: int = int(config['FPS_USER_INTERFACE'])
DEFAULT_THRESHOLD_VALUE: int = int(config['DEFAULT_THRESHOLD_VALUE'])
SERIAL_ENCODING: str = config['SERIAL_ENCODING']
SERIAL_DELIMITER: str = config['SERIAL_DELIMITER']
SAVE_TIME: bool = config.getboolean('SAVE_TIME')


class Window(customtkinter.CTk):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__()

        self.loop = loop
        self.tasks = {}
        self.ports = []
        self.plot_data = []
        self.threshold_value = DEFAULT_THRESHOLD_VALUE
        self.event_saved = False

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.title('Arduino <-> Computer')
        self.geometry("720x640")
        self.minsize(720, 640)

        self.init_ui()
        self.run_loops()

    def init_ui(self):

        self.tabview = customtkinter.CTkTabview(
            master=self,
            command=self.tab_changed)
        self.tabview.pack(fill=tk.BOTH, expand=1, pady=10, padx=10)

        self.tabview.add('Settings')
        self.tabview.add('Monitor')

        customtkinter.CTkLabel(
            master=self.tabview.tab('Settings'),
            text='Port'
        ).pack()

        self.ports_box = customtkinter.CTkOptionMenu(
            master=self.tabview.tab('Settings'),
            values=self.ports,
            state='readonly'
        )
        self.ports_box.pack(fill=tk.BOTH, padx=40)

        customtkinter.CTkLabel(
            master=self.tabview.tab('Settings'),
            text='Speed'
        ).pack()

        self.speed_box = customtkinter.CTkOptionMenu(
            master=self.tabview.tab('Settings'),
            values=SERIAL_SPEEDS,
            state='readonly'
        )
        self.speed_box.pack(fill=tk.BOTH, padx=40)

        button = customtkinter.CTkButton(
            master=self.tabview.tab('Settings'),
            text='Update',
            command=self.update_ports)
        button.pack(pady=10, padx=10, anchor='s', expand=True)

        coordinate_frame = customtkinter.CTkFrame(
            master=self.tabview.tab("Monitor")
        )
        coordinate_frame.pack(padx=10, pady=10, fill=tk.BOTH)

        customtkinter.CTkLabel(
            master=coordinate_frame,
            text='Coordinates'
        ).grid(row=0, column=0, padx=20, pady=20)

        customtkinter.CTkLabel(
            master=coordinate_frame,
            text='X'
        ).grid(row=0, column=1, sticky=tk.E)

        self.x_coor = customtkinter.CTkLabel(
            width=100,
            master=coordinate_frame,
            fg_color='gray100',
            corner_radius=5,
            anchor='w',
            text='None',
            padx=10
        )
        self.x_coor.grid(row=0, column=2, padx=20)

        customtkinter.CTkLabel(
            master=coordinate_frame,
            text='Y'
        ).grid(row=0, column=3, sticky=tk.E)

        self.y_coor = customtkinter.CTkLabel(
            width=100,
            master=coordinate_frame,
            fg_color='gray100',
            corner_radius=5,
            anchor='w',
            text='None',
            padx=10
        )
        self.y_coor.grid(row=0, column=4, padx=20)

        self.plot_frame = customtkinter.CTkFrame(
            master=self.tabview.tab("Monitor"),
            fg_color='transparent'
        )
        self.plot_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.threshold_label = customtkinter.CTkLabel(
            master=self.plot_frame,
            text=f'Sensor threshold value:  {self.threshold_value}'
        )
        self.threshold_label.pack(padx=10, anchor=tk.W)

        self.slider_2 = customtkinter.CTkSlider(self.plot_frame,
                                                orientation='vertical',
                                                command=self.change_threshold,
                                                from_=0,
                                                to=MAX_VALUE_SENSOR,
                                                number_of_steps=MAX_VALUE_SENSOR)
        self.slider_2.set(DEFAULT_THRESHOLD_VALUE)
        self.slider_2.pack(padx=5, pady=30, side=tk.RIGHT, fill=tk.BOTH)

        self.plot_bar_frame = customtkinter.CTkFrame(
            master=self.tabview.tab("Monitor")
        )
        self.plot_bar_frame.pack(padx=10, pady=10, fill=tk.BOTH)

        self.draw_plot()

    def tab_changed(self):
        tab_name = self.tabview.get()

        if tab_name == 'Monitor':
            if self.ports_box.get() and self.speed_box.get():
                self.tasks['read'] = (self.loop.create_task(
                    self.read_data(self.ports_box.get(), self.speed_box.get())))

                self.tasks['plot'] = (self.loop.create_task(self.plot_updater(1 / FPS_GRAPH)))

        elif tab_name == 'Settings':
            ports = serial_ports()
            self.ports_box.configure(values=ports)

            if 'read' in self.tasks.keys():
                self.tasks['read'].cancel()

            if 'plot' in self.tasks.keys():
                self.tasks['plot'].cancel()

    def run_loops(self):
        self.tasks['ui'] = self.loop.create_task(self.updater(1 / FPS_USER_INTERFACE))

    async def read_data(self, port, speed):
        reader, writer = await open_serial_connection(url=port, baudrate=int(speed))
        while True:
            try:
                line = await reader.readline()
                line = line.decode(encoding=SERIAL_ENCODING)
                if line.count(SERIAL_DELIMITER) == 2:
                    x, y, val = line.split(SERIAL_DELIMITER)
                    self.plot_data.append(int(val))
                    if len(self.plot_data) > GRAPH_TIME_LIMITS:
                        self.plot_data = self.plot_data[-GRAPH_TIME_LIMITS:]

                    if int(val) >= self.threshold_value:
                        await self.trig_event(x, y, val)
                    else:
                        self.event_saved = False

                    self.x_coor.configure(text=str(x))
                    self.y_coor.configure(text=str(y))

            except Exception as e:
                logging.error(e)

    async def trig_event(self, *values):
        if not self.event_saved:
            async with aiofiles.open(FILENAME, 'a+') as out:
                await out.write(f'X: {values[0]} Y: {values[1]} VALUE: {int(values[2])} TIME: {datetime.now()}\n')
                await out.flush()
            logging.info(f'Event was triggered: X -> {values[0]} Y -> {values[1]} VALUE -> {values[2]}')
            self.event_saved = True

    def change_threshold(self, val):
        self.threshold_value = int(val)
        self.threshold_label.configure(text=f'Sensor threshold value: {self.threshold_value}')

    def update_ports(self):
        self.ports_box.set('')
        self.speed_box.set('')
        ports = serial_ports()
        self.ports_box.configure(values=ports)

    async def plot_updater(self, interval):
        while True:
            if len(self.plot_data) == GRAPH_TIME_LIMITS:
                x = np.arange(0, GRAPH_TIME_LIMITS, 1)
                y = self.plot_data
                self.plot1.clear()
                self.plot1.set_xlim((0, GRAPH_TIME_LIMITS))
                self.plot1.set_ylim((0, MAX_VALUE_SENSOR))
                self.plot1.get_xaxis().set_visible(False)
                self.plot1.axhline(self.threshold_value, color='red', ls='--')
                self.plot1.plot(x, y, color='#36719f')
                self.canvas.draw()
            await asyncio.sleep(interval)

    async def updater(self, interval):
        self.tab_changed()
        self.ports_box.set('')
        self.speed_box.set('')
        while True:
            self.update()
            await asyncio.sleep(interval)

    def draw_plot(self):
        fig = plt.figure(figsize=(5, 3), dpi=120)
        plt.subplots_adjust(left=0.09, right=0.98, top=0.9, bottom=0.08)
        self.plot1 = fig.add_subplot(111)
        self.plot1.set_facecolor('#dbdbdb')
        fig.set_facecolor('#dbdbdb')
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_bar_frame)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, padx=10, fill=tk.BOTH)

    def close(self):
        for task in self.tasks.values():
            task.cancel()
        self.loop.stop()
        self.destroy()


def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")

    Window(loop)
    loop.run_forever()
    loop.close()


if __name__ == '__main__':
    main()





