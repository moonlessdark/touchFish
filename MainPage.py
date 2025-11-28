import json
import sys
from datetime import datetime, date
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QTime
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QStyle, \
    QSystemTrayIcon, QMenu
from dateutil.relativedelta import relativedelta
import requests
from requests import Response
from pathlib import Path


class TaskDayWork(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.req = requests

        self.setWindowTitle("摸鱼之王")
        self.setFixedSize(480, 270)
        # self.setStyleSheet("background-color: rgb(237, 237, 236);")

        background_confing_file: str = './_internal/background.png'
        logo_path = Path(background_confing_file)
        if logo_path.exists():
            background_confing_file: str = background_confing_file
        else:
            background_confing_file: str = './background.png'

        pixmap = QtGui.QPixmap(background_confing_file)
        scaled_pixmap = pixmap.scaled(self.size(),
                                      QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                      QtCore.Qt.TransformationMode.SmoothTransformation)
        palette = self.palette()
        palette.setBrush(QtGui.QPalette.ColorRole.Window, QtGui.QBrush(scaled_pixmap))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        confing_file: str = './_internal/config.ini'
        logo_path = Path(confing_file)
        if logo_path.exists():
            image_path: str = confing_file
        else:
            image_path: str = './config.ini'

        self.settings = QtCore.QSettings(image_path, QtCore.QSettings.defaultFormat().IniFormat)

        # 设置窗口属性（可选：使窗口不显示在任务栏）
        self.setWindowFlags(QtCore.Qt.WindowType.Tool)

        # 创建系统托盘
        self.create_system_tray_icon()

        self.fish_money = 45.50
        self.days_until_friday = 0
        self.days_until_halloween = 0

        # 工作时间设置
        self.start_time = QtCore.QTime(9, 0, 0)  # 上班时间
        self.end_time = QtCore.QTime(18, 0, 0)   # 下班时间
        self.work_schedule = "双休"  # 工作安排：双休、单休、大小周

        # 创建UI组件
        self.setup_ui()

        # 启动定时器
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # 每秒更新一次

        # 设置初始状态
        self.update_timer()
        # self.get_holiday()

    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 设置按钮（右上角）
        self.setting_button = QPushButton("⚙️")
        self.setting_button.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        padding: 5px;
                        font-size: 16px;
                        color: black;
                    }
                    QPushButton:hover {
                        background-color: rgba(0, 0, 0, 0:1);
                        border-radius: 5px;
                    }
                """)
        self.setting_button.clicked.connect(self.show_settings)

        # 标题标签
        title_label = QLabel("再不摸鱼就下班了")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; color: black; font-weight: bold;")

        _first_layout = QtWidgets.QHBoxLayout()
        _first_layout.addWidget(title_label, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        _first_layout.addWidget(self.setting_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(_first_layout)

        # 倒计时标签
        self.time_label = QLabel("06:39:06")
        self.time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-size: 36px; font-weight: bold; color: black;")
        main_layout.addWidget(self.time_label, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        # 状态信息容器
        status_container = QHBoxLayout()
        status_container.setSpacing(10)
        status_container.addStretch()  # 添加伸缩项，让图片靠右

        # 发薪日卡片
        self.salary_card = self.create_status_card("距离发薪", str(self.next_payday()), "天", "black")
        status_container.addWidget(self.salary_card)

        # 周五倒计时卡片
        _day_str, _day_num = self.next_day_off()
        self.friday_card = self.create_status_card(_day_str, str(_day_num), "天", "#666")
        status_container.addWidget(self.friday_card)

        # 节假日倒计时
        _holiday_name, _holiday_diff = self.get_holiday()
        self.halloween_card = self.create_status_card(_holiday_name, str(_holiday_diff), "天", "#666")
        status_container.addWidget(self.halloween_card)

        # 今日收入卡片
        self.income_card = self.create_status_card("今日赚了", str(self.had_how_many_money()), "¥", "#FFA500")
        status_container.addWidget(self.income_card)

        # 右侧插图
        self.cat_image = QLabel()
        pixmap = self.create_cat_pixmap()
        if pixmap:
            self.cat_image.setPixmap(pixmap)
            self.cat_image.setScaledContents(True)
            self.cat_image.setMaximumWidth(150)
            self.cat_image.setMaximumHeight(120)
        else:
            self.cat_image.setText("图片加载失败")
            self.cat_image.setStyleSheet("color: red; font-size: 14px;")
        # status_container.addWidget(self.cat_image)

        main_layout.addLayout(status_container)

        # 将设置按钮添加到主布局中
        self.setLayout(main_layout)  # <-- 先设置主布局

    def create_status_card(self, title, value, unit, color):
        """创建状态卡片"""
        card_widget = QWidget()
        card_widget.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            padding: 8px;
            margin: 3px;
        """)

        card_widget.setFixedWidth(100)

        layout = QVBoxLayout()
        layout.setSpacing(2)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 12px; color: {color};")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 数值
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        # 单位
        unit_label = QLabel(unit)
        unit_label.setStyleSheet(f"font-size: 12px; color: {color};")
        unit_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(unit_label)

        card_widget.setLayout(layout)
        return card_widget

    def update_status_cards(self):
        """更新所有状态卡片的内容"""
        # 更新发薪日卡片
        self.update_card_content(self.salary_card, "距离发薪", str(self.next_payday()), "天")

        # 更新周五倒计时卡片
        _day_str, _day_num = self.next_day_off()
        self.update_card_content(self.friday_card, _day_str, str(_day_num), "天")

        # 更新节假日卡片
        holiday_name, holiday_diff = self.get_holiday()
        self.update_card_content(self.halloween_card, holiday_name, str(holiday_diff), "天")

        # 更新收入卡片
        self.update_card_content(self.income_card, "今日赚了", str(self.had_how_many_money()), "¥")

    def update_card_content(self, card_widget, title, value, unit):
        """更新指定卡片的内容"""
        # 获取卡片布局中的所有QLabel组件
        layout = card_widget.layout()

        # 标题标签（索引0）
        title_label = layout.itemAt(0).widget()
        title_label.setText(title)

        # 数值标签（索引1）
        value_label = layout.itemAt(1).widget()
        value_label.setText(value)

    def create_cat_pixmap(self):
        """创建猫的插图 - 使用本地图片"""
        # 假设图片文件名为 cat.png，位于项目根目录
        logo_file: str = './_internal/background.svg'
        logo_path = Path(logo_file)
        if logo_path.exists():
            image_path: str = logo_file
        else:
            image_path: str = './background.svg'
        # image_path = "./_internal/background.svg"  # 修改为您的实际图片路径

        try:
            pixmap = QtGui.QPixmap(image_path)
            if pixmap.isNull():
                # print(f"无法加载图片: {image_path}")
                return None
            return pixmap.scaled(150, 120, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        except Exception as e:
            # print(f"加载图片时出错: {e}")
            return None

    def update_timer(self):
        """
        更新倒计时时间
        :return:
        """

        _until_next_day_off = 5 if self.settings.value('dayWorkSleepType') == '双休' else 6
        # 获取当前日期
        today = date.today()
        # 计算今天是星期几（0=Monday, 1=Tuesday, ..., 6=Sunday）
        weekday = today.weekday() + 1

        if any([_until_next_day_off == 5 and weekday in [6, 7], _until_next_day_off == 6 and weekday == 7]):
            self.time_label.setText("今天休息哦")
            return

        # 初始化数据
        _until_time = '18:00' if self.settings.value('dayWorkEndTime') is None else self.settings.value('dayWorkEndTime')
        # 获取当前日期
        today = datetime.now().date()
        # 将时间字符串转换为datetime对象，并设置为今天
        time_obj = datetime.strptime(_until_time, "%H:%M")
        work_end_time = datetime.combine(today, time_obj.time())

        today = datetime.now().date()
        # 将时间字符串转换为datetime对象，并设置为今天
        _day_start_time = self.settings.value('dayWorkStartTime')
        time_obj_start = datetime.strptime(_day_start_time, "%H:%M")
        work_start_time = datetime.combine(today, time_obj_start.time())

        """更新倒计时"""
        current_time = datetime.now()
        remaining_time = work_end_time - current_time
        starting_time = current_time - work_start_time

        if starting_time.total_seconds() <= 0:
            self.time_label.setText("还没上班呢")
            return

        if remaining_time.total_seconds() <= 0:
            self.time_label.setText("下班啦！")
            self.timer.stop()
            return

        hours = int(remaining_time.seconds // 3600)
        minutes = int((remaining_time.seconds % 3600) // 60)
        seconds = int(remaining_time.seconds % 60)

        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        self.update_status_cards()

    def next_payday(self):
        """计算下一次发薪日"""
        _until_next_day = '1' if self.settings.value('dayWorkMoneyDay') is None else self.settings.value('dayWorkMoneyDay')
        # 获取当前日期
        today = datetime.now().date()
        next_pay_day = datetime.now().date()
        # 如果当前日期大于发薪日，则将发薪日设置为下个月
        next_pay_day = next_pay_day.replace(day=int(_until_next_day))
        if today.day > int(_until_next_day):
            next_pay_day += relativedelta(months=+1)
        # 设置发薪日的日期
        until_payday = next_pay_day - today
        return until_payday.days

    def next_day_off(self) -> tuple:
        """
        离下一个休息日还有多久
        :return:
        """
        _until_next_day_off = 5 if self.settings.value('dayWorkSleepType') == '双休' else 6

        _until_next_day_off_str: str = "距离周五" if _until_next_day_off == 5 else "距离周六"

        # 获取当前日期
        today = date.today()

        # 计算今天是星期几（0=Monday, 1=Tuesday, ..., 6=Sunday）
        weekday = today.weekday() + 1

        # 计算距离下一个星期五的天数
        if weekday < _until_next_day_off:  # 如果今天是星期一至星期四
            days_to_next_friday = _until_next_day_off - weekday
        else:  # 如果今天是星期五或之后（包括周末）
            days_to_next_friday = (7-weekday) + _until_next_day_off
        return _until_next_day_off_str, days_to_next_friday

    def get_holiday(self):
        """
        获取节假日
        :return:
        """

        to_year = datetime.now().year
        _holiday_list = self.settings.value(f'holidayList{to_year}')
        if _holiday_list is None:
            headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "zh-CN,zh;q=0.9",
                "cache-control": "no-cache",
                "dnt": "1",
                "pragma": "no-cache",
                "priority": "u=0, i",
                "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "macOS",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
            }
            # 获取一下当年的节日
            _holiday_response: Response = self.req.get(f'https://timor.tech/api/holiday/year/{to_year}', headers=headers)
            if _holiday_response.status_code == 200:
                _holiday_list = json.dumps(_holiday_response.text)
                self.settings.setValue(f'holidayList{to_year}', str(_holiday_list))
                _holiday_list: str = _holiday_response.text

        _holiday_dict = json.loads(str(_holiday_list))
        if type(_holiday_dict) is not dict:
            _holiday_dict = json.loads(_holiday_dict)
        _holiday: dict = _holiday_dict.get('holiday')
        _index_day = datetime.now().date()
        _holiday_name: str = ''
        _holiday_date_diff: int = 0
        for keys in _holiday:
            index_holiday: dict = _holiday.get(keys)
            holiday_name: str = index_holiday.get("name")
            holiday_date = datetime.strptime(index_holiday.get("date"), "%Y-%m-%d")
            date_obj = holiday_date.date()
            difference_day = date_obj - _index_day
            if difference_day.days > 0:
                # 如果节日减去当前日期，为正数，说明还没有到这一天，那么就可以返回这个数据了
                _holiday_name = holiday_name
                _holiday_date_diff = difference_day.days
                return _holiday_name, _holiday_date_diff
        if _holiday_name == "" and _holiday_date_diff == 0:
            # 说明这一年没有匹配到数据，那么匹配下一年的
            _holiday_name = "没节日了"
        return _holiday_name, _holiday_date_diff

    def had_how_many_money(self) -> float:
        """
        今天获得几多钱了？
        :return:
        """
        _money_num: float = 0

        _until_next_day_off = 5 if self.settings.value('dayWorkSleepType') == '双休' else 6
        # 获取当前日期
        today = date.today()
        # 计算今天是星期几（0=Monday, 1=Tuesday, ..., 6=Sunday）
        weekday = today.weekday() + 1
        if any([_until_next_day_off == 5 and weekday in [6, 7], _until_next_day_off == 6 and weekday == 7]):
            return _money_num

        day_work_duration_m = float(0 if self.settings.value('dayWorkDurationM') is None else self.settings.value('dayWorkDurationM'))

        if _until_next_day_off == 5:
            _money_num_all = day_work_duration_m * 22
        else:
            _money_num_all = day_work_duration_m * 26

        month_money = int(0 if self.settings.value('monthMoney') is None else self.settings.value('monthMoney'))
        day_minute_money: float = round(float(month_money)/float(_money_num_all), 2)  # 每分钟多少钱

        day_start_date = '8:00' if self.settings.value('dayWorkStartTime') is None else self.settings.value('dayWorkStartTime')
        day_start_date = datetime.strptime(day_start_date, '%H:%M')

        day_end_date = '8:00' if self.settings.value('dayWorkEndTime') is None else self.settings.value('dayWorkEndTime')
        day_end_date = datetime.strptime(day_end_date, '%H:%M')

        day_now = datetime.now()
        day_start_date = day_start_date.replace(year=day_now.year, month=int(day_now.month), day=day_now.day)
        day_end_date = day_end_date.replace(year=day_now.year, month=int(day_now.month), day=day_now.day)

        diff_minute_running = day_now - day_start_date

        diff_minute_stop = day_now - day_end_date  # 当前时间比结束时间还大，表示下班了

        if diff_minute_running.seconds/60 > 0 > diff_minute_stop.days:
            # 如果当前时间剪去开始时间，大于0，表示已经开始上班了
            _money_num = diff_minute_running.seconds/60 * day_minute_money
        else:
            # 下班了，你获得了今天100%的钱
            _money_num = day_work_duration_m * day_minute_money
        return int(_money_num)

    def show_settings(self):
        """显示设置对话框"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("设置")
        dialog.resize(100, 120)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)

        # 标题
        title_label = QLabel("工作设置")
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 上班时间段设置
        time_label = QtWidgets.QLabel("上班时间段:")
        layout.addWidget(time_label)

        # 开始时间选择
        start_time_layout = QHBoxLayout()
        start_time_label = QtWidgets.QLabel("开始时间:")
        start_time_layout.addWidget(start_time_label)

        self.start_time_edit = QtWidgets.QTimeEdit()
        self.start_time_edit.setTime(self.start_time)

        start_time_layout.addWidget(self.start_time_edit)
        layout.addLayout(start_time_layout)

        # 结束时间选择
        end_time_layout = QHBoxLayout()
        end_time_label = QtWidgets.QLabel("结束时间:")
        end_time_layout.addWidget(end_time_label)

        self.end_time_edit = QtWidgets.QTimeEdit()
        self.end_time_edit.setTime(self.end_time)

        end_time_layout.addWidget(self.end_time_edit)
        layout.addLayout(end_time_layout)

        # 工作安排选择
        layout_work_schedule = QtWidgets.QHBoxLayout()
        schedule_label = QtWidgets.QLabel("工作安排:")
        layout_work_schedule.addWidget(schedule_label)

        self.schedule_combo = QtWidgets.QComboBox()
        self.schedule_combo.addItems(["双休", "单休"])
        self.schedule_combo.setCurrentText(self.work_schedule)

        layout_work_schedule.addWidget(self.schedule_combo)
        layout.addLayout(layout_work_schedule)

        # 发薪日
        layout_money_day = QtWidgets.QHBoxLayout()
        money_label = QtWidgets.QLabel("发薪日:")
        layout_money_day.addWidget(money_label)

        self.money_day_combo = QtWidgets.QComboBox()
        # 添加1-30的数值选项
        numbers = [str(i) for i in range(1, 31)]
        self.money_day_combo.addItems(numbers)
        layout_money_day.addWidget(self.money_day_combo)
        layout.addLayout(layout_money_day)

        # 当前月薪
        layout_money_month_day = QtWidgets.QHBoxLayout()
        money_month_label = QtWidgets.QLabel("当前月薪:    ")

        layout_money_month_day.addWidget(money_month_label)

        self.money_month_input = QtWidgets.QLineEdit()
        int_validator = QIntValidator(0, 9999999)  # 限制输入0-100的整数
        self.money_month_input.setValidator(int_validator)
        layout_money_month_day.addWidget(self.money_month_input)
        layout.addLayout(layout_money_month_day)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()

        # 取消按钮
        cancel_btn = QtWidgets.QPushButton("取消")

        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        # 确认按钮
        confirm_btn = QtWidgets.QPushButton("确认")

        confirm_btn.clicked.connect(lambda: self.save_settings())
        button_layout.addWidget(confirm_btn)

        layout.addLayout(button_layout)

        self.load_setting()

        dialog.setLayout(layout)
        dialog.exec()

    def save_settings(self):
        """保存设置"""
        # 保存上班时间段
        start_time = self.start_time_edit.time().toString("HH:mm")
        end_time = self.end_time_edit.time().toString("HH:mm")
        self.settings.setValue("dayWorkStartTime", self.start_time_edit.time().toString("HH:mm"))
        self.settings.setValue("dayWorkEndTime", self.end_time_edit.time().toString("HH:mm"))

        # 计算时间差
        time_difference = abs(datetime.strptime(end_time, "%H:%M") - datetime.strptime(start_time, "%H:%M"))
        work_duration = time_difference.total_seconds()
        self.settings.setValue("dayWorkDurationM", str(work_duration/60))

        # 保存工作安排
        work_schedule = self.schedule_combo.currentText()
        self.settings.setValue("dayWorkSleepType", str(work_schedule))

        # 保存发薪日
        money_day = self.money_day_combo.currentText()
        self.settings.setValue("dayWorkMoneyDay", str(money_day))

        # 保存月薪
        money_number = self.money_month_input.text()
        self.settings.setValue("monthMoney", str(money_number))

        # 重新计算倒计时
        self.update_timer()

        self.show_simple_dialog()

    def load_setting(self):
        """
        加载配置文件中的设置信息
        :return:
        """
        _start_time: str = self.settings.value('dayWorkStartTime')
        _end_time: str = self.settings.value('dayWorkEndTime')
        _payday: str = self.settings.value('dayWorkMoneyDay')  # 发薪日
        _payoff_type: str = self.settings.value('dayWorkSleepType')  # 双休还是单休
        _month_money: str = self.settings.value('monthMoney')  # 月薪

        self.start_time_edit.setTime(QTime.fromString(_start_time, 'hh:mm'))
        self.end_time_edit.setTime(QTime.fromString(_end_time, 'hh:mm'))
        self.schedule_combo.setCurrentText(_payoff_type)
        self.money_month_input.setText(_month_money)
        self.money_day_combo.setCurrentText(_payday)

    def show_simple_dialog(self):
        """显示简单消息对话框"""
        dialog = QtWidgets.QMessageBox(self)
        dialog.setWindowTitle("提示")
        dialog.setText("操作成功！请重启程序!")
        dialog.exec()

    def create_system_tray_icon(self):
        """创建系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)

        # 可以使用内置标准图标
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        # 或者使用自定义图标
        # self.tray_icon.setIcon(QIcon(":/icons/app_icon.png"))

        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示主窗口")
        exit_action = tray_menu.addAction("退出")

        show_action.triggered.connect(self.show_normal)
        exit_action.triggered.connect(QApplication.instance().quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        """处理托盘图标点击"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible() and not self.isMinimized():
                self.hide()
            else:
                self.show_normal()

    def show_normal(self):
        """正常显示窗口"""
        self.show()
        if self.isMinimized():
            self.setWindowState(QtCore.Qt.WindowState.WindowNoState)  # 恢复正常窗口状态
        self.raise_()
        self.activateWindow()
        self.setFocus()  # 设置焦点到窗口


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TaskDayWork()
    window.show()
    sys.exit(app.exec())
