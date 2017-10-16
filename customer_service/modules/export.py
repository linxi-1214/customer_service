# -*- coding=utf-8 -*-

import xlsxwriter

from django.db import connection


class ExcelReporter:
    def __init__(self, filename, headers=None):
        self.filename = filename
        self.workbook = xlsxwriter.Workbook(self.filename)
        self.headers = headers

        self.data_set = None

        self.role_row_format = self.workbook.add_format(
            {
                'bg_color': '#D6ECF0',
                'border': 1,
                'font_size': 14,
                'valign': 'vcenter',
            }
        )

        self.person_row_format = self.workbook.add_format(
            {
                'bg_color': '#FFFBF0',
                'border': 1,
                'font_size': 14,
                'valign': 'vcenter',
            }
        )

        self.normal_row_format = self.workbook.add_format(
            {
                'bg_color': '#F2ECDE',
                'border': 1,
                'valign': 'vcenter',
                'font_size': 14
            }
        )
        self.color_row_format = self.workbook.add_format(
            {
                'bg_color': '#FFFBF0',
                'border': 1,
                'valign': 'vcenter',
                'font_size': 14
            }
        )
        self.head_row_format = self.workbook.add_format(
            {
                'bg_color': "#161823",
                'color': 'white',
                'font_name': 'Times New Roman',
                'font_size': 20,
                'align': 'center',
            }
        )
        self.error_row_format = self.workbook.add_format(
            {
                'bg_color': "#DC3023",
                'border': 1,
                'color': 'white',
                'font_size': 14,
                'valign': 'vcenter',
            }
        )

    def init_data(self):
        raise NotImplementedError

    def report(self):
        worksheet = self.workbook.add_worksheet(u'玩家信息')

        if self.headers is not None:
            head_data = []
            for ind, header in list(enumerate(self.headers)):
                if ind <= 26:
                    head_data.append(('%s1' % (chr(65+ind)), header))
                else:
                    first_chr = chr(65 + (ind / 26) - 1)
                    second_char = chr(65 + (ind % 26) - 1)
                    head_data.append(('%s%s1' % (first_chr, second_char), header))
        else:
            head_data = (
                ('A1', '#'),
                ('B1', '账号'),
                ('C1', u'姓名'),
                ('D1', u'手机号'),
                ('E1', u'QQ号码'),
                ('F1', u'注册游戏'),
                ('G1', u'注册时间'),
                ('H1', u'所属客服'),
                ('I1', u'渠道'),
                ('J1', u'最近登录游戏'),
                ('K1', u'最近登录时间'),
                ('L1', u'充值次数'),
                ('M1', u'充值总额'),
                ('N1', u'最近充值游戏'),
                ('O1', u'最近充值金额'),
                ('P1', u'最近充值时间'),
                ('Q1', u'备注')
            )

        cols_width = [len(header) * 10 for header in head_data]

        for ind, width in list(enumerate(cols_width)):
            worksheet.set_column(ind, ind, width)

        worksheet.set_row(0, 30)
        for pos, data in head_data:
            worksheet.write(pos, data, self.head_row_format)

        line_num = 1
        cell_format_set = (self.color_row_format, self.normal_row_format)

        for player_info in self.data_set:
            cell_format = cell_format_set[line_num % 2]
            worksheet.write_row('A%d' % line_num, player_info, cell_format=cell_format)
            line_num += 1

        for i in range(1, line_num):
            worksheet.set_row(i, 24)

        self.workbook.close()
