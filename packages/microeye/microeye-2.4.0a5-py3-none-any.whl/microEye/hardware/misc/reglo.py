import traceback

from microEye.qt import (
    QApplication,
    QDateTime,
    QMainWindow,
    Qt,
    QtCore,
    QtGui,
    QtSerialPort,
    QtWidgets,
)
from microEye.utils.start_gui import StartGUI


class RegloDigital(QtSerialPort.QSerialPort):
    _ACK_ = '*'
    _ERR_ = '#'
    _YES_ = '+'
    _NO_ = '-'

    # general
    _address_alloc_ = '@'
    _CR_ = '\r'
    _reset_ = '-'

    # control
    _start_ = 'H'
    _stop_ = 'I'
    _clk_wise_ = 'J'
    _counter_clk_wise_ = 'K'
    _manual_panel_ = 'A'
    _inactive_panel_ = 'B'
    _disp_numbers_ = 'D'
    _disp_letters_ = 'DA'

    # modes
    _pump_rpm_mode_ = 'L'
    _pump_flowrate_mode_ = 'M'
    _disp_time_mode_ = 'N'
    _disp_vol_mode_ = 'O'
    _pause_time_mode_ = ']'
    _disp_time_pause_mode_ = 'P'
    _disp_vol_pause_mode_ = 'Q'
    _vol_period_mode_ = 'G'
    _total_mode_ = 'R'

    # inquiry & input
    _status_ = 'E'
    _type_ = '#'
    _version_ = '('
    _id_number_ = ')'
    _speed_ = 'S'
    _def_flowrate_ = '?'
    _cal_flowrate_ = '!'
    _digits_after_decimal_ = '['
    _tubing_inner_diameter_ = '+'  # in 1/100 mm
    _disp_time_ = 'V'  # in 1/10 sec (0-9999)
    _disp_time_min_ = 'VM'  # (0-899)
    _disp_time_hour_ = 'VH'  # (0-999)
    _roller_steps_ = 'U'  # (00001-65535)
    _roller_steps_plus_ = 'u'  # u*65535 + U
    _roller_step_nanoliter_ = 'r'  # mmmmee
    _roller_step_default_ = 'r000000'
    _flowrate_mlmin_ = 'f'  # mmmmee
    _disp_volume_ml_ = 'v'  # mmmmee
    _roller_back_steps_ = '%'  # 0-100
    _pause_time_ = 'T'  # in 1/10 sec (0-9999)
    _pause_time_min_ = 'TM'  # (0-899)
    _pause_time_hour_ = 'TH'  # (0-999)
    _disp_cycles_ = '"'  # (0-9999)
    _total_vol_ = ':'
    _reset_total_vol_ = 'W'
    _store_app_params_ = '*'
    _set_default_vals_ = '0'
    _foot_switch_ = 'C'

    def __init__(self, Port: str, Address: int, *args, **kwargs):
        super().__init__(Port)
        self.Address = str(Address)
        # self.setPortName(Port)
        self.setBaudRate(9600)
        self.response = ''
        self.active = False
        self.clockwise = False

    def _send_command(self, command: str, waitCount: int = 1) -> str:
        if self.isOpen():
            self.write((command + self._CR_).encode())
            self.waitForBytesWritten(500)
            time = QDateTime.currentDateTime()
            while self.bytesAvailable() < waitCount:
                self.waitForReadyRead(500)
                msec = time.msecsTo(QDateTime.currentDateTime())
                if msec > 3000:
                    break
            self.response = str(self.readAll(), encoding='utf8').strip('\r\n').strip()
            return self.response
        else:
            return None

    def start(self) -> str:
        return self._send_command(self.Address + self._start_)

    def stop(self) -> str:
        return self._send_command(self.Address + self._stop_)

    def pause(self) -> str:
        return self._send_command(self.Address + self._p)

    def set_clockwise(self) -> str:
        res = self._send_command(self.Address + self._clk_wise_)
        if res == self._ACK_:
            self.clockwise = True
        return res

    def set_counter_clockwise(self) -> str:
        res = self._send_command(self.Address + self._counter_clk_wise_)
        if res == self._ACK_:
            self.clockwise = False
        return res

    def set_pump_rpm_mode(self) -> str:
        return self._send_command(self.Address + self._pump_rpm_mode_)

    def set_pump_flowrate_mode(self) -> str:
        return self._send_command(self.Address + self._pump_flowrate_mode_)

    def set_disp_time_mode(self) -> str:
        return self._send_command(self.Address + self._disp_time_mode_)

    def set_disp_vol_mode(self) -> str:
        return self._send_command(self.Address + self._disp_vol_mode_)

    def set_pause_time_mode(self) -> str:
        return self._send_command(self.Address + self._pause_time_mode_)

    def set_disp_time_pause_mode(self) -> str:
        return self._send_command(self.Address + self._disp_time_pause_mode_)

    def set_disp_vol_pause_mode(self) -> str:
        return self._send_command(self.Address + self._disp_vol_pause_mode_)

    def set_vol_period_mode(self) -> str:
        return self._send_command(self.Address + self._vol_period_mode_)

    def set_total_mode(self) -> str:
        return self._send_command(self.Address + self._total_mode_)

    def get_status(self) -> str:
        res = self._send_command(self.Address + self._status_)
        self.active = res == RegloDigital._YES_
        return res

    def get_pump_type(self) -> str:
        return self._send_command(self.Address + self._type_)

    def get_soft_version(self) -> str:
        return self._send_command(self.Address + self._version_)

    def get_pump_head_id(self) -> str:
        return self._send_command(self.Address + self._id_number_)

    def set_pump_head_id(self, new_id: int) -> str:
        return self._send_command(self.Address + self._id_number_ + f'{new_id:04d}')

    def get_speed(self) -> str:
        return self._send_command(self.Address + self._speed_, 8)

    def set_speed(self, speed: float) -> str:
        return self._send_command(
            self.Address + self._speed_ + (f'{speed:07.2f}').replace('.', '')
        )

    def get_default_flowrate(self) -> str:
        return self._send_command(self.Address + self._def_flowrate_)

    def get_calibrated_flowrate(self) -> str:
        return self._send_command(self.Address + self._cal_flowrate_)

    def get_digits_after_decimal(self) -> str:
        return self._send_command(self.Address + self._digits_after_decimal_)

    def set_calibrated_flowrate(self, flowrate: float) -> str:
        digits = self.get_digits_after_decimal()
        if digits == '#':
            return '#'
        else:
            # Format with right number of decimal places, then remove decimal point
            formatted = f'{flowrate:.{int(digits)}f}'.replace('.', '')
            # Ensure total length is 5 by padding with zeros if needed
            formatted = formatted.zfill(5)
            return self._send_command(self.Address + self._cal_flowrate_ + formatted)

    def get_tubing_inner_diameter(self) -> str:
        return self._send_command(self.Address + self._tubing_inner_diameter_, 6)

    def set_tubing_inner_diameter(self, diameter: int) -> str:
        res = self._send_command(
            self.Address
            + self._tubing_inner_diameter_
            + f'{diameter:04d}'.replace('.', '')
        )
        return res

    def get_disp_time(self) -> str:
        return self._send_command(self.Address + self._disp_time_, 2)

    def set_disp_time(self, time: int) -> str:
        value = min(9999, max(0, time))
        return self._send_command(
            self.Address + self._disp_time_ + f'{value:04d}'.replace('.', '')
        )

    def set_disp_time_min(self, time: int) -> str:
        value = min(899, max(0, time))
        return self._send_command(
            self.Address + self._disp_time_min_ + f'{value:03d}'.replace('.', '')
        )

    def set_disp_time_hour(self, time: int) -> str:
        value = min(999, max(0, time))
        return self._send_command(
            self.Address + self._disp_time_hour_ + f'{value:03d}'.replace('.', '')
        )

    def get_roller_steps(self) -> str:
        return self._send_command(self.Address + self._roller_steps_)

    def set_roller_steps(self, steps: int) -> str:
        value = min(65535, max(1, steps))
        return self._send_command(
            self.Address + self._roller_steps_ + f'{value:05d}'.replace('.', '')
        )

    def set_roller_steps_plus(self, steps: int) -> str:
        value = min(9999, max(0, steps))
        return self._send_command(
            self.Address + self._roller_steps_plus_ + f'{value:04d}'.replace('.', '')
        )

    def get_roller_step_nanoliter(self) -> str:
        return self._send_command(self.Address + self._roller_step_nanoliter_)

    def set_roller_step_nanoliter(self, volume: float) -> str:
        return self._send_command(
            self.Address + self._roller_step_nanoliter_ + self.float_to_mmmmee(volume)
        )

    def get_flowrate_mlmin(self) -> str:
        res = self._send_command(self.Address + self._flowrate_mlmin_, 9)
        if res != RegloDigital._ERR_:
            return self.mmmmee_to_float(res)
        else:
            return res

    def set_flowrate_mlmin(self, flowrate: float) -> str:
        return self._send_command(
            self.Address + self._flowrate_mlmin_ + self.float_to_mmmmee(flowrate)
        )

    def get_disp_volume_ml(self) -> str:
        res = self._send_command(self.Address + self._disp_volume_ml_, 9)
        if res != RegloDigital._ERR_:
            return self.mmmmee_to_float(res)
        else:
            return res

    def set_disp_volume_ml(self, volume: float) -> str:
        return self._send_command(
            self.Address + self._disp_volume_ml_ + self.float_to_mmmmee(volume)
        )

    def get_roller_back_steps(self) -> str:
        return self._send_command(self.Address + self._roller_back_steps_)

    def set_roller_back_steps(self, steps: int) -> str:
        value = min(100, max(0, steps))
        return self._send_command(
            self.Address + self._roller_back_steps_ + f'{value:04d}'.replace('.', '')
        )

    def get_pause_time(self) -> str:
        return self._send_command(self.Address + self._pause_time_, 2)

    def set_pause_time(self, time: int) -> str:
        value = min(9999, max(0, time))
        return self._send_command(
            self.Address + self._pause_time_ + f'{value:04d}'.replace('.', '')
        )

    def set_pause_time_min(self, time: int) -> str:
        value = min(899, max(0, time))
        return self._send_command(
            self.Address + self._pause_time_min_ + f'{value:04d}'.replace('.', '')
        )

    def set_pause_time_hour(self, time: int) -> str:
        value = min(999, max(0, time))
        return self._send_command(
            self.Address + self._pause_time_hour_ + f'{value:04d}'.replace('.', '')
        )

    def get_disp_cycles(self) -> str:
        return self._send_command(self.Address + self._disp_cycles_)

    def set_disp_cycles(self, cycles: int) -> str:
        value = min(9999, max(0, cycles))
        return self._send_command(
            self.Address + self._pause_time_ + f'{value:04d}'.replace('.', '')
        )

    def get_total_vol(self) -> str:
        return self._send_command(self.Address + self._total_vol_)

    def get_reset_total_vol(self) -> str:
        return self._send_command(self.Address + self._reset_total_vol_)

    def store_app_params(self) -> str:
        return self._send_command(self.Address + self._store_app_params_)

    def set_default_vals(self) -> str:
        return self._send_command(self.Address + self._set_default_vals_)

    def get_foot_switch(self) -> str:
        return self._send_command(self.Address + self._foot_switch_)

    def set_foot_switch_toggle(self) -> str:
        return self._send_command(self.Address + self._foot_switch_ + '0000')

    def set_foot_switch_direct(self) -> str:
        return self._send_command(self.Address + self._foot_switch_ + '0001')

    def float_to_mmmmee(self, value: float) -> str:
        s_val = f'{value:0.3E}'
        s_val = s_val[0:-2] + s_val[-1:]

        s_val = s_val.replace('.', '').replace('E', '')
        return s_val

    def mmmmee_to_float(self, value: str) -> str:
        if len(value) > 1:
            return value[0] + '.' + value[1:]
        else:
            return value


class reglo_digital_module(QMainWindow):
    '''A GUI for RegloDigital control | Inherits QMainWindow'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # setting title
        self.setWindowTitle('microEye RegloDigital module')

        # setting geometry
        self.setGeometry(0, 0, 800, 600)

        # Statusbar time
        self.statusBar().showMessage(
            'Time: ' + QDateTime.currentDateTime().toString('hh:mm:ss,zzz')
        )

        # RegloDigital
        self.regloDigital = RegloDigital(Port='COM8', Address=1)
        self.regloMessage = ''
        self.cycle = None

        # Layout
        self.LayoutInit()

        # We need to store a reference to the plotted line
        # somewhere, so we can apply the new data to it.
        self._plot_ref = None

        # Statues Bar Timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_gui)
        self.timer.start()

        # Threading
        self._threadpool = QtCore.QThreadPool.globalInstance()
        print(
            f'Multithreading with maximum {self._threadpool.maxThreadCount()} threads'
        )

        self.show()

        # centered
        self.center()

    def center(self):
        '''Centers the window within the screen.'''
        qtRectangle = self.frameGeometry()
        centerPoint = QApplication.primaryScreen().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def LayoutInit(self):
        # the main tab widget
        self.main_widget = QtWidgets.QWidget()
        self.main_view = QtWidgets.QHBoxLayout()
        self.main_widget.setLayout(self.main_view)
        self.setCentralWidget(self.main_widget)

        # columns
        self.first_col = QtWidgets.QVBoxLayout()
        self.second_col = QtWidgets.QVBoxLayout()

        self.main_view.addLayout(self.first_col)
        self.main_view.addLayout(self.second_col)

        # general
        self.general_group = QtWidgets.QGroupBox('General')
        self.general_Layout = QtWidgets.QVBoxLayout()
        self.general_group.setLayout(self.general_Layout)

        # modes
        self.modes_group = QtWidgets.QGroupBox('Modes')
        self.modes_Layout = QtWidgets.QVBoxLayout()
        self.modes_group.setLayout(self.modes_Layout)

        # configurations
        self.config_group = QtWidgets.QGroupBox('Config.')
        self.config_Layout = QtWidgets.QVBoxLayout()
        self.config_group.setLayout(self.config_Layout)

        # incremental cycles
        self.cycle_group = QtWidgets.QGroupBox('Cycles')
        self.cycle_Layout = QtWidgets.QVBoxLayout()
        self.cycle_group.setLayout(self.cycle_Layout)

        self.first_col.addWidget(self.general_group)
        self.first_col.addWidget(self.modes_group)
        self.second_col.addWidget(self.config_group)
        self.second_col.addWidget(self.cycle_group)

        self.portname_comboBox = QtWidgets.QComboBox()

        # adding available serial ports
        for info in QtSerialPort.QSerialPortInfo.availablePorts():
            self.portname_comboBox.addItem(info.portName())

        self.connect_btn = QtWidgets.QPushButton(
            'connect', clicked=lambda: self.connect()
        )
        self.toggle_btn = QtWidgets.QPushButton(
            'start (Idle)', clicked=lambda: self.toggle_pump()
        )
        self.clockwise_btn = QtWidgets.QPushButton(
            'clockwise (Flow Back)', clicked=lambda: self.regloDigital.set_clockwise()
        )
        self.c_clockwise_btn = QtWidgets.QPushButton(
            'counter-clockwise (Empty)',
            clicked=lambda: self.regloDigital.set_counter_clockwise(),
        )

        # mode buttons
        self.rpm_mode_btn = QtWidgets.QPushButton(
            'RPM Mode', clicked=lambda: self.regloDigital.set_pump_rpm_mode()
        )
        self.flowrate_mode_btn = QtWidgets.QPushButton(
            'Flowrate Mode', clicked=lambda: self.regloDigital.set_pump_flowrate_mode()
        )
        self.disp_time_mode_btn = QtWidgets.QPushButton(
            'Dispense Time Mode', clicked=lambda: self.regloDigital.set_disp_time_mode()
        )
        self.disp_vol_mode_btn = QtWidgets.QPushButton(
            'Dispense Volume Mode',
            clicked=lambda: self.regloDigital.set_disp_vol_mode(),
        )
        self.pause_mode_btn = QtWidgets.QPushButton(
            'Pause Time Mode', clicked=lambda: self.regloDigital.set_pause_time_mode()
        )
        self.disp_pause_mode_btn = QtWidgets.QPushButton(
            'Dispense Time / Pause Time Mode',
            clicked=lambda: self.regloDigital.set_disp_time_pause_mode(),
        )
        self.vol_period_mode_btn = QtWidgets.QPushButton(
            'Volume dependent dispensing within a period mode',
            clicked=lambda: self.regloDigital.set_vol_period_mode(),
        )
        self.total_mode_btn = QtWidgets.QPushButton(
            'Total Mode', clicked=lambda: self.regloDigital.set_total_mode()
        )

        self.get_tubing_diameter_btn = QtWidgets.QPushButton(
            'Set flowrate', clicked=lambda: self.regloDigital.set_flowrate_mlmin(80)
        )

        self.general_Layout.addWidget(QtWidgets.QLabel('Pump Serial Port:'))
        self.general_Layout.addWidget(self.portname_comboBox)
        self.general_Layout.addWidget(self.connect_btn)
        self.general_Layout.addWidget(self.toggle_btn)
        self.general_Layout.addWidget(self.clockwise_btn)
        self.general_Layout.addWidget(self.c_clockwise_btn)

        self.modes_Layout.addWidget(self.rpm_mode_btn)
        self.modes_Layout.addWidget(self.flowrate_mode_btn)
        self.modes_Layout.addWidget(self.disp_time_mode_btn)
        self.modes_Layout.addWidget(self.disp_vol_mode_btn)
        self.modes_Layout.addWidget(self.pause_mode_btn)
        self.modes_Layout.addWidget(self.disp_pause_mode_btn)
        self.modes_Layout.addWidget(self.vol_period_mode_btn)
        self.modes_Layout.addWidget(self.total_mode_btn)
        self.modes_Layout.addWidget(self.get_tubing_diameter_btn)
        self.modes_Layout.addStretch()

        speed_layout = QtWidgets.QHBoxLayout()
        self.speed_box = QtWidgets.QLineEdit()
        self.speed_box.setValidator(QtGui.QDoubleValidator(0.0, 160.0, 2))
        self.set_speed_btn = QtWidgets.QPushButton(
            'Set',
            clicked=lambda: self.regloDigital.set_speed(float(self.speed_box.text())),
        )
        self.get_speed_btn = QtWidgets.QPushButton(
            'Get', clicked=lambda: self.speed_box.setText(self.regloDigital.get_speed())
        )

        speed_layout.addWidget(QtWidgets.QLabel('Speed (rpm): '))
        speed_layout.addWidget(self.speed_box)
        speed_layout.addWidget(self.set_speed_btn)
        speed_layout.addWidget(self.get_speed_btn)

        flowrate_layout = QtWidgets.QHBoxLayout()
        self.flowrate_box = QtWidgets.QLineEdit()
        self.flowrate_box.setValidator(QtGui.QDoubleValidator(0.0, 2.683e-3, 3))
        self.set_flowrate_btn = QtWidgets.QPushButton(
            'Set',
            clicked=lambda: self.regloDigital.set_flowrate_mlmin(
                float(self.flowrate_box.text())
            ),
        )
        self.get_flowrate_btn = QtWidgets.QPushButton(
            'Get',
            clicked=lambda: self.flowrate_box.setText(
                self.regloDigital.get_flowrate_mlmin()
            ),
        )

        flowrate_layout.addWidget(QtWidgets.QLabel('Flow Rate (l/min): '))
        flowrate_layout.addWidget(self.flowrate_box)
        flowrate_layout.addWidget(self.set_flowrate_btn)
        flowrate_layout.addWidget(self.get_flowrate_btn)

        disp_vol_layout = QtWidgets.QHBoxLayout()
        self.disp_vol_box = QtWidgets.QLineEdit()
        self.disp_vol_box.setValidator(QtGui.QDoubleValidator(0.0, 1000, 3))
        self.set_disp_vol_btn = QtWidgets.QPushButton(
            'Set',
            clicked=lambda: self.regloDigital.set_disp_volume_ml(
                float(self.disp_vol_box.text())
            ),
        )

        disp_vol_layout.addWidget(QtWidgets.QLabel('Dispensed Vol (l): '))
        disp_vol_layout.addWidget(self.disp_vol_box)
        disp_vol_layout.addWidget(self.set_disp_vol_btn)

        disp_time_layout = QtWidgets.QHBoxLayout()
        self.disp_time_box = QtWidgets.QLineEdit()
        self.disp_time_box.setValidator(QtGui.QIntValidator(0, 9999))
        self.set_disp_time_btn = QtWidgets.QPushButton(
            'Set',
            clicked=lambda: self.regloDigital.set_disp_time(
                float(self.disp_time_box.text())
            ),
        )

        disp_time_layout.addWidget(QtWidgets.QLabel('Dispensed Time (1/10s): '))
        disp_time_layout.addWidget(self.disp_time_box)
        disp_time_layout.addWidget(self.set_disp_time_btn)

        pause_time_layout = QtWidgets.QHBoxLayout()
        self.pause_time_box = QtWidgets.QLineEdit()
        self.pause_time_box.setValidator(QtGui.QIntValidator(0, 9999))
        self.set_pause_time_btn = QtWidgets.QPushButton(
            'Set',
            clicked=lambda: self.regloDigital.set_pause_time(
                float(self.pause_time_box.text())
            ),
        )

        pause_time_layout.addWidget(QtWidgets.QLabel('Pause Time (1/10s): '))
        pause_time_layout.addWidget(self.pause_time_box)
        pause_time_layout.addWidget(self.set_pause_time_btn)

        self.config_Layout.addLayout(speed_layout)
        self.config_Layout.addLayout(flowrate_layout)
        self.config_Layout.addLayout(disp_vol_layout)
        self.config_Layout.addLayout(disp_time_layout)
        self.config_Layout.addLayout(pause_time_layout)

        self.cycle_label = QtWidgets.QLabel('Number of Cycles: 1')
        self.cycle_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.cycle_slider.setMinimum(2)
        self.cycle_slider.setMaximum(50)
        self.cycle_slider.valueChanged.connect(self.cycles_changed)

        self.inc_label = QtWidgets.QLabel('Speed Increment: 1')
        self.inc_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.inc_slider.setMinimum(1)
        self.inc_slider.setMaximum(50)
        self.inc_slider.valueChanged.connect(self.inc_changed)

        self.cycles_table = QtWidgets.QTableWidget()
        self.cycles_table.setRowCount(1)
        self.cycles_table.setColumnCount(1)
        self.cycles_table.setHorizontalHeaderLabels(['Speed Increment'])
        self.cycles_table.resizeColumnsToContents()
        for r in range(1):
            self.cycles_table.setItem(
                r, 0, QtWidgets.QTableWidgetItem(str(self.inc_slider.value()))
            )

        self.start_cycle_btn = QtWidgets.QPushButton(
            'Start Cycles', clicked=lambda: self.cycles_start()
        )

        self.stop_cycle_btn = QtWidgets.QPushButton(
            'Stop Cycles', clicked=lambda: self.cycles_stop()
        )

        self.cycle_Layout.addWidget(self.cycle_label)
        self.cycle_Layout.addWidget(self.cycle_slider)
        self.cycle_Layout.addWidget(self.inc_label)
        self.cycle_Layout.addWidget(self.inc_slider)
        self.cycle_Layout.addWidget(self.cycles_table)
        self.cycle_Layout.addWidget(self.start_cycle_btn)
        self.cycle_Layout.addWidget(self.stop_cycle_btn)
        self.cycle_Layout.addStretch()

    def toggle_pump(self):
        if self.regloDigital.isOpen():
            if self.regloDigital.active:
                self.regloDigital.stop()
            else:
                self.regloDigital.start()

    def cycles_changed(self, value):
        self.cycle_label.setText(f'Number of Cycles: {value:d}')
        self.cycles_table.setRowCount(value)
        for r in range(value):
            self.cycles_table.setItem(
                r, 0, QtWidgets.QTableWidgetItem(str(self.inc_slider.value()))
            )

    def inc_changed(self, value):
        self.inc_label.setText(f'Speed Increment: {value:d}')
        self.cycles_table.setRowCount(self.cycle_slider.value())
        for r in range(self.cycle_slider.value()):
            self.cycles_table.setItem(
                r, 0, QtWidgets.QTableWidgetItem(str(self.inc_slider.value()))
            )

    def cycles_start(self):
        if self.regloDigital.isOpen():
            self.cycle = {
                'cycles': self.cycle_slider.value(),
                'incr': [
                    float(self.cycles_table.item(j, 0).text())
                    for j in range(self.cycle_slider.value())
                ],
                'start': QDateTime.currentDateTime(),
                'duration': int(self.disp_time_box.text()) * 100,
                'index': 0,
            }
            self.cycle['cycle_dur'] = self.cycle['duration'] / self.cycle['cycles']

            self.regloDigital.stop()
            self.regloDigital.set_disp_time_mode()
            self.regloDigital.start()

    def cycles_stop(self):
        self.cycle = None
        self.regloDigital.stop()

    def update_gui(self):
        self.regloDigital.get_status()

        msec = None
        if self.cycle is not None:
            msec = self.cycle['start'].msecsTo(QDateTime.currentDateTime())

            if msec > self.cycle['duration']:
                self.cycle = None
            elif msec > self.cycle['index'] * self.cycle['cycle_dur']:
                speed = (
                    float(self.speed_box.text())
                    + self.cycle['incr'][self.cycle['index']]
                )
                speed = min(max(speed, 0), 160.0)
                self.regloDigital.set_speed(speed)
                self.speed_box.setText(f'{speed:.2f}')
                self.flowrate_box.setText(self.regloDigital.get_flowrate_mlmin())
                self.cycle['index'] = self.cycle['index'] + 1

        self.statusBar().showMessage(
            'Time: {} | Rx: {} | Status {} | Direction {} | Cycle {} sec'.format(
                QDateTime.currentDateTime().toString('hh:mm:ss,zzz'),
                self.regloDigital.response,
                ('Active' if self.regloDigital.active else 'Idle'),
                ('CW' if self.regloDigital.clockwise else 'CCW'),
                0.00 if msec is None else msec / 1000,
            )
        )

        # update indicators
        if self.regloDigital.isOpen():
            self.connect_btn.setStyleSheet('background-color: green')
            self.connect_btn.setText('disconnect')
        else:
            self.connect_btn.setStyleSheet('background-color: red')
            self.connect_btn.setText('connect')

        if self.regloDigital.active:
            self.toggle_btn.setStyleSheet('background-color: green')
            self.toggle_btn.setText('stop (Active)')
        else:
            self.toggle_btn.setStyleSheet('background-color: red')
            self.toggle_btn.setText('start (Idle)')

    def connect(self):
        try:
            if not self.regloDigital.isOpen():
                if 'COM' in self.portname_comboBox.currentText():
                    self.regloDigital.setPortName(self.portname_comboBox.currentText())
                self.regloDigital.open(QtCore.QIODevice.OpenModeFlag.ReadWrite)
                self.regloDigital.get_status()
                self.speed_box.setText(self.regloDigital.get_speed())
                self.flowrate_box.setText(self.regloDigital.get_flowrate_mlmin())
                self.disp_vol_box.setText(self.regloDigital.get_disp_volume_ml())
                self.disp_time_box.setText(self.regloDigital.get_disp_time())
                self.pause_time_box.setText(self.regloDigital.get_pause_time())
            else:
                self.regloDigital.close()
        except Exception:
            traceback.print_exc()

    def StartGUI():
        '''Initializes a new QApplication and reglo_digital_module.

        Use
        -------
        app, window = reglo_digital_module.StartGUI()

        app.exec()

        Returns
        -------
        tuple (QApplication, reglo_digital_module)
            Returns a tuple with QApp and reglo_digital_module main window.
        '''
        return StartGUI(reglo_digital_module)


if __name__ == '__main__':
    app, window = reglo_digital_module.StartGUI()
    app.exec()
