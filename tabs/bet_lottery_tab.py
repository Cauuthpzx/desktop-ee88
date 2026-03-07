"""
tabs/bet_lottery_tab.py — Tab Đơn cược xổ số (upstream: /agent/bet.html)
"""
from tabs._upstream_tab import UpstreamTab, _fmt_currency
from utils.upstream import upstream


# Danh sách trò chơi xổ số — giữ nguyên value/label từ upstream
_LOTTERY_OPTIONS = [
    ("search.all", ""),
    # Sicbo
    ("Sicbo 30 giây", "67"),
    ("Sicbo 20 giây", "66"),
    ("Sicbo 40 giây", "68"),
    ("Sicbo 50 giây", "69"),
    ("Sicbo 1 phút", "70"),
    ("Sicbo 1.5 phút", "71"),
    # Miền Bắc
    ("Miền Bắc", "32"),
    ("Xổ số Miền Bắc", "63"),
    ("M.bắc nhanh 3 phút", "46"),
    ("M.bắc nhanh 5 phút", "45"),
    ("Miền Bắc VIP 45 giây", "47"),
    ("Miền Bắc VIP 75 giây", "48"),
    ("Miền Bắc VIP 2 phút", "49"),
    # Miền Nam
    ("Miền Nam VIP 5 phút", "44"),
    ("Miền Nam VIP 45 giây", "57"),
    ("Miền Nam VIP 1 phút", "58"),
    ("Miền Nam VIP 90 giây", "59"),
    ("Miền Nam VIP 2 phút", "60"),
    # Keno
    ("Keno VIP 20 giây", "51"),
    ("Keno VIP 30 giây", "52"),
    ("Keno VIP 40 giây", "53"),
    ("Keno VIP 50 giây", "54"),
    ("Keno VIP 1 phút", "55"),
    ("Keno VIP 5 phút", "56"),
    # Win go
    ("Win go 30 giây", "77"),
    ("Win go 45 giây", "73"),
    ("Win go 1 phút", "74"),
    ("Win go 3 phút", "75"),
    ("Win go 5 phút", "76"),
    # Miền Nam tỉnh
    ("Bạc Liêu", "1"),
    ("Vũng Tàu", "2"),
    ("Tiền Giang", "3"),
    ("Kiên Giang", "4"),
    ("Đà Lạt", "5"),
    ("Bình Phước", "6"),
    ("Bình Dương", "7"),
    ("An Giang", "8"),
    ("Bình Thuận", "9"),
    ("Cà Mau", "10"),
    ("Cần Thơ", "11"),
    ("Hậu Giang", "12"),
    ("Đồng Tháp", "13"),
    ("Tây Ninh", "14"),
    ("Sóc Trăng", "15"),
    ("TP Hồ Chí Minh", "16"),
    ("Đồng Nai", "17"),
    ("Trà Vinh", "42"),
    ("Vĩnh Long", "43"),
    # Miền Trung
    ("Đà Nẵng", "18"),
    ("Thừa Thiên Huế", "19"),
    ("Quảng Trị", "20"),
    ("Phú Yên", "21"),
    ("Quảng Bình", "22"),
    ("Quảng Nam", "23"),
    ("Quảng Ngãi", "24"),
    ("Ninh Thuận", "25"),
    ("Kon Tum", "26"),
    ("Khánh Hoà", "27"),
    ("Gia Lai", "28"),
    ("Bình Định", "29"),
    ("Đắk Lắk", "30"),
    ("Đắk Nông", "31"),
]


class BetLotteryTab(UpstreamTab):
    _title_key = "bet_lottery.title"
    _columns_keys = [
        ("bet_lottery.col_agent",    "_agentName"),
        ("bet_lottery.col_serial",   "serial_no"),
        ("bet_lottery.col_user",     "username"),
        ("bet_lottery.col_time",     "create_time"),
        ("bet_lottery.col_game",     "lottery_name"),
        ("bet_lottery.col_type",     "play_type_name"),
        ("bet_lottery.col_method",   "play_name"),
        ("bet_lottery.col_period",   "issue"),
        ("bet_lottery.col_info",     "content"),
        ("bet_lottery.col_amount",   "money"),
        ("bet_lottery.col_rebate",   "rebate_amount"),
        ("bet_lottery.col_result",   "result"),
        ("bet_lottery.col_status",   "status_text"),
    ]
    _search_fields = [
        {"key": "create_time", "type": "date_range",
         "label": "search.bet_time", "default": "today"},
        {"key": "username", "type": "text",
         "label": "search.username", "placeholder": "search.username_ph",
         "width": 160},
        {"key": "serial_no", "type": "text",
         "label": "search.serial_no", "placeholder": "search.serial_no_ph",
         "width": 180},
        {"key": "lottery_id", "type": "select", "label": "search.lottery_game",
         "options": _LOTTERY_OPTIONS, "width": 180},
        {"key": "status", "type": "select", "label": "search.status",
         "options": [
             ("search.all", ""),
             ("search.bet_unpaid", "-9"),
             ("search.bet_won", "1"),
             ("search.bet_lost", "-1"),
             ("search.bet_tie", "2"),
             ("search.bet_user_cancel", "3"),
             ("search.bet_sys_cancel", "4"),
             ("search.bet_abnormal", "5"),
             ("search.bet_unpaid_manual", "6"),
         ], "width": 160},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_bet_lottery(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        return {
            "money": _fmt_currency,
            "rebate_amount": _fmt_currency,
            "result": _fmt_currency,
        }
