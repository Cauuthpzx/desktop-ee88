#include "core/report_pages.h"
#include "core/date_range_picker.h"
#include "core/flow_layout.h"
#include "core/theme_manager.h"
#include "core/report_page_builder.h"

#include <QLineEdit>

static QPushButton* make_search_button(const QString& icon_path, const QString& text, const QString& obj_name)
{
    auto* btn = new QPushButton(QIcon(icon_path), text);
    btn->setObjectName(obj_name);
    btn->setCursor(Qt::PointingHandCursor);
    btn->setFixedHeight(32);
    btn->setIconSize(QSize(16, 16));
    return btn;
}

static QComboBox* make_quick_date_combo(bool only_today_yesterday = false)
{
    auto* combo = new QComboBox;
    combo->addItem(QString::fromUtf8("Hôm nay"), "today");
    combo->addItem(QString::fromUtf8("Hôm qua"), "yesterday");
    if (!only_today_yesterday) {
        combo->addItem(QString::fromUtf8("Tuần này"), "thisWeek");
        combo->addItem(QString::fromUtf8("Tháng này"), "thisMonth");
        combo->addItem(QString::fromUtf8("Tháng trước"), "lastMonth");
    }
    combo->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    combo->setFixedHeight(32);
    return combo;
}

ReportPages::ReportPages(ThemeManager* theme, QObject* parent)
    : QObject(parent)
    , m_theme(theme)
{
}

QWidget* ReportPages::create_lottery_report_page()
{
    FlowLayout* flow = nullptr;
    m_lottery_report = ReportPageBuilder::build_page(
        ":/icons/menu_lottery_report",
        QString::fromUtf8("BÁO CÁO XỔ SỐ"),
        {
            QString::fromUtf8("Tên tài khoản"),
            QString::fromUtf8("Thuộc đại lý"),
            QString::fromUtf8("Số lần cược"),
            QString::fromUtf8("Tiền cược"),
            QString::fromUtf8("Tiền cược hợp lệ (trừ cược hoà)"),
            QString::fromUtf8("Hoàn trả"),
            QString::fromUtf8("Thắng thua"),
            QString::fromUtf8("Kết quả thắng thua (không gồm hoàn trả)"),
            QString::fromUtf8("Tiền trúng"),
            QString::fromUtf8("Tên loại xổ"),
        },
        flow
    );

    m_date_pickers[0] = new DateRangePicker;
    m_date_pickers[0]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(m_date_pickers[0]);

    m_quick_date_combos[0] = make_quick_date_combo();
    flow->addWidget(m_quick_date_combos[0]);

    auto* lottery_select = new QComboBox;
    lottery_select->addItem(QString::fromUtf8("Chọn hoặc nhập để tìm kiếm"), QVariant());
    lottery_select->setEditable(true);
    lottery_select->setFixedHeight(32);
    lottery_select->setFixedWidth(200);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Tên loại xổ："), lottery_select, m_lottery_report.search_labels));

    auto* username = new QLineEdit;
    username->setPlaceholderText(QString::fromUtf8("Nhập tên tài khoản"));
    username->setFixedWidth(200);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Tên tài khoản："), username, m_lottery_report.search_labels));

    flow->addWidget(make_search_button(":/icons/search", QString::fromUtf8("Tìm kiếm"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", QString::fromUtf8("Đặt lại"), "resetBtn"));

    ReportPageBuilder::add_summary(m_lottery_report,
        QString::fromUtf8("Phương pháp tổng hợp [nhóm]:"),
        {
            QString::fromUtf8("Số khách đặt cược"),
            QString::fromUtf8("Số lần cược"),
            QString::fromUtf8("Tiền cược"),
            QString::fromUtf8("Tiền cược hợp lệ (trừ cược hoà)"),
            QString::fromUtf8("Hoàn trả"),
            QString::fromUtf8("Thắng thua"),
            QString::fromUtf8("Kết quả thắng thua (không gồm hoàn trả)"),
            QString::fromUtf8("Tiền trúng"),
        },
        {"0", "0", "0.00", "0.00", "0.00", "0.00", "0.00", "0.00"}
    );

    return m_lottery_report.page;
}

QWidget* ReportPages::create_transaction_log_page()
{
    FlowLayout* flow = nullptr;
    m_transaction_log = ReportPageBuilder::build_page(
        ":/icons/menu_transaction_log",
        QString::fromUtf8("SAO KÊ GIAO DỊCH"),
        {
            QString::fromUtf8("Tên tài khoản"),
            QString::fromUtf8("Thuộc đại lý"),
            QString::fromUtf8("Số lần nạp"),
            QString::fromUtf8("Số tiền nạp"),
            QString::fromUtf8("Số lần rút"),
            QString::fromUtf8("Số tiền rút"),
            QString::fromUtf8("Phí dịch vụ"),
            QString::fromUtf8("Hoa hồng đại lý"),
            QString::fromUtf8("Ưu đãi"),
            QString::fromUtf8("Hoàn trả bên thứ 3"),
            QString::fromUtf8("Tiền thưởng từ bên thứ 3"),
            QString::fromUtf8("Thời gian"),
        },
        flow
    );

    m_date_pickers[1] = new DateRangePicker;
    m_date_pickers[1]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(m_date_pickers[1]);

    m_quick_date_combos[1] = make_quick_date_combo();
    flow->addWidget(m_quick_date_combos[1]);

    auto* username = new QLineEdit;
    username->setPlaceholderText(QString::fromUtf8("Nhập tên tài khoản"));
    username->setFixedWidth(200);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Tên tài khoản："), username, m_transaction_log.search_labels));

    flow->addWidget(make_search_button(":/icons/search", QString::fromUtf8("Tìm kiếm"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", QString::fromUtf8("Đặt lại"), "resetBtn"));

    ReportPageBuilder::add_summary(m_transaction_log,
        QString::fromUtf8("Phương pháp tổng hợp [nhóm]:"),
        {
            QString::fromUtf8("Số tiền nạp"),
            QString::fromUtf8("Số tiền rút"),
            QString::fromUtf8("Phí dịch vụ"),
            QString::fromUtf8("Hoa hồng đại lý"),
            QString::fromUtf8("Ưu đãi"),
            QString::fromUtf8("Hoàn trả bên thứ 3"),
            QString::fromUtf8("Tiền thưởng từ bên thứ 3"),
        },
        {"0.00", "0.00", "0.00", "0.00", "0.00", "0.00", "0"}
    );

    return m_transaction_log.page;
}

QWidget* ReportPages::create_provider_report_page()
{
    FlowLayout* flow = nullptr;
    m_provider_report = ReportPageBuilder::build_page(
        ":/icons/menu_provider_report",
        QString::fromUtf8("BÁO CÁO NHÀ CUNG CẤP"),
        {
            QString::fromUtf8("Tên tài khoản"),
            QString::fromUtf8("Nhà cung cấp game"),
            QString::fromUtf8("Số lần cược"),
            QString::fromUtf8("Tiền cược"),
            QString::fromUtf8("Tiền cược hợp lệ"),
            QString::fromUtf8("Tiền thưởng"),
            QString::fromUtf8("Thắng thua"),
        },
        flow
    );

    m_date_pickers[2] = new DateRangePicker;
    m_date_pickers[2]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(m_date_pickers[2]);

    m_quick_date_combos[2] = make_quick_date_combo();
    flow->addWidget(m_quick_date_combos[2]);

    auto* username = new QLineEdit;
    username->setPlaceholderText(QString::fromUtf8("Nhập tên tài khoản"));
    username->setFixedWidth(200);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Tên tài khoản："), username, m_provider_report.search_labels));

    auto* provider_select = new QComboBox;
    provider_select->addItem(QString::fromUtf8("Chọn"), QVariant());
    const QStringList providers = {
        "PA", "BBIN", "WM", "MINI", "KY", "PGSOFT", "LUCKYWIN", "SABA", "PT",
        "RICH88", "ASTAR", "FB", "JILI", "KA", "MW", "SBO", "NEXTSPIN", "AMB",
        "FunTa", "MG", "WS168", "DG CASINO", "V8", "AE", "TP", "FC", "JDB",
        "CQ9", "PP", "VA", "BNG", "DB CASINO", "EVO CASINO", "CMD SPORTS",
        "PG NEW", "FBLIVE", "ON CASINO", "MT", "JILI NEW", "fC NEW"
    };
    for (const auto& p : providers) {
        provider_select->addItem(p, p);
    }
    provider_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    provider_select->setFixedHeight(32);
    provider_select->setFixedWidth(200);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Nhà cung cấp game："), provider_select, m_provider_report.search_labels));

    flow->addWidget(make_search_button(":/icons/search", QString::fromUtf8("Tìm kiếm"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", QString::fromUtf8("Đặt lại"), "resetBtn"));

    ReportPageBuilder::add_summary(m_provider_report,
        QString::fromUtf8("Dữ liệu tổng hợp:"),
        {
            QString::fromUtf8("Số lần cược"),
            QString::fromUtf8("Số khách đặt cược"),
            QString::fromUtf8("Tiền cược"),
            QString::fromUtf8("Tiền cược hợp lệ"),
            QString::fromUtf8("Tiền thưởng"),
            QString::fromUtf8("Thắng thua"),
        },
        {"0", "0", "0.00", "0.00", "0.00", "0.00"}
    );

    return m_provider_report.page;
}

QWidget* ReportPages::create_lottery_bets_page()
{
    FlowLayout* flow = nullptr;
    m_lottery_bets = ReportPageBuilder::build_page(
        ":/icons/menu_lottery_bet",
        QString::fromUtf8("DANH SÁCH ĐƠN CƯỢC"),
        {
            QString::fromUtf8("Mã giao dịch"),
            QString::fromUtf8("Tên người dùng"),
            QString::fromUtf8("Thời gian cược"),
            QString::fromUtf8("Trò chơi"),
            QString::fromUtf8("Loại trò chơi"),
            QString::fromUtf8("Cách chơi"),
            QString::fromUtf8("Kỳ"),
            QString::fromUtf8("Thông tin cược"),
            QString::fromUtf8("Tiền cược"),
            QString::fromUtf8("Tiền hoàn trả"),
            QString::fromUtf8("Thắng thua"),
            QString::fromUtf8("Trạng thái"),
        },
        flow
    );

    m_date_pickers[3] = new DateRangePicker;
    m_date_pickers[3]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(m_date_pickers[3]);

    m_quick_date_combos[3] = make_quick_date_combo(true);
    flow->addWidget(m_quick_date_combos[3]);

    auto* username = new QLineEdit;
    username->setPlaceholderText(QString::fromUtf8("Vui lòng nhập đầy đủ Tên người dùng"));
    username->setFixedWidth(200);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Tên người dùng："), username, m_lottery_bets.search_labels));

    auto* serial_no = new QLineEdit;
    serial_no->setPlaceholderText(QString::fromUtf8("Nhập đầy đủ mã giao dịch"));
    serial_no->setFixedWidth(200);
    serial_no->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Mã giao dịch："), serial_no, m_lottery_bets.search_labels));

    auto* game_select = new QComboBox;
    game_select->addItem(QString::fromUtf8("Chọn"), QVariant());
    game_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    game_select->setFixedHeight(32);
    game_select->setFixedWidth(150);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Trò chơi："), game_select, m_lottery_bets.search_labels));

    auto* play_type = new QComboBox;
    play_type->addItem(QString::fromUtf8("Chọn"), QVariant());
    play_type->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    play_type->setFixedHeight(32);
    play_type->setFixedWidth(180);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Loại trò chơi："), play_type, m_lottery_bets.search_labels));

    auto* play_method = new QComboBox;
    play_method->addItem(QString::fromUtf8("Chọn"), QVariant());
    play_method->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    play_method->setFixedHeight(32);
    play_method->setFixedWidth(180);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Cách chơi："), play_method, m_lottery_bets.search_labels));

    auto* status_select = new QComboBox;
    status_select->addItem(QString::fromUtf8("Chọn"), QVariant());
    status_select->addItem(QString::fromUtf8("Chưa thanh toán"), "-9");
    status_select->addItem(QString::fromUtf8("Trúng"), "1");
    status_select->addItem(QString::fromUtf8("Không trúng"), "-1");
    status_select->addItem(QString::fromUtf8("Hoà"), "2");
    status_select->addItem(QString::fromUtf8("Khách huỷ đơn"), "3");
    status_select->addItem(QString::fromUtf8("Hệ thống huỷ đơn"), "4");
    status_select->addItem(QString::fromUtf8("Đơn cược bất thường"), "5");
    status_select->addItem(QString::fromUtf8("Chưa thanh toán (khôi phục thủ công)"), "6");
    status_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    status_select->setFixedHeight(32);
    status_select->setFixedWidth(150);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Trạng thái："), status_select, m_lottery_bets.search_labels));

    flow->addWidget(make_search_button(":/icons/search", QString::fromUtf8("Tìm kiếm"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", QString::fromUtf8("Đặt lại"), "resetBtn"));

    ReportPageBuilder::add_summary(m_lottery_bets,
        QString::fromUtf8("Dữ liệu tổng hợp:"),
        {
            QString::fromUtf8("Tiền cược"),
            QString::fromUtf8("Tiền hoàn trả"),
            QString::fromUtf8("Thắng thua"),
        },
        {"0.00", "0.00", "0.00"}
    );

    return m_lottery_bets.page;
}

QWidget* ReportPages::create_provider_bets_page()
{
    FlowLayout* flow = nullptr;
    m_provider_bets = ReportPageBuilder::build_page(
        ":/icons/menu_third_party_bet",
        QString::fromUtf8("ĐƠN CƯỢC BÊN THỨ 3"),
        {
            QString::fromUtf8("Mã giao dịch"),
            QString::fromUtf8("Nhà cung cấp game bên thứ 3"),
            QString::fromUtf8("Tên tài khoản thuộc nhà cái"),
            QString::fromUtf8("Loại hình trò chơi"),
            QString::fromUtf8("Tên trò chơi bên thứ 3"),
            QString::fromUtf8("Tiền cược"),
            QString::fromUtf8("Tiền cược hợp lệ"),
            QString::fromUtf8("Tiền thưởng"),
            QString::fromUtf8("Thắng thua"),
            QString::fromUtf8("Thời gian cược"),
        },
        flow
    );

    m_date_pickers[4] = new DateRangePicker;
    m_date_pickers[4]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Thời gian cược："), m_date_pickers[4], m_provider_bets.search_labels));

    m_quick_date_combos[4] = make_quick_date_combo();
    flow->addWidget(m_quick_date_combos[4]);

    auto* serial_no = new QLineEdit;
    serial_no->setPlaceholderText(QString::fromUtf8("Nhập hoàn chỉnh đơn giao dịch"));
    serial_no->setFixedWidth(200);
    serial_no->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Mã giao dịch："), serial_no, m_provider_bets.search_labels));

    auto* platform_user = new QLineEdit;
    platform_user->setPlaceholderText(QString::fromUtf8("Nhập tên tài khoản thuộc nhà cái"));
    platform_user->setFixedWidth(200);
    platform_user->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Tên tài khoản thuộc nhà cái："), platform_user, m_provider_bets.search_labels));

    flow->addWidget(make_search_button(":/icons/search", QString::fromUtf8("Tìm kiếm"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", QString::fromUtf8("Đặt lại"), "resetBtn"));

    return m_provider_bets.page;
}

QWidget* ReportPages::create_withdrawal_history_page()
{
    FlowLayout* flow = nullptr;
    m_withdrawal_history = ReportPageBuilder::build_page(
        ":/icons/menu_withdraw_log",
        QString::fromUtf8("LỊCH SỬ RÚT TIỀN"),
        {
            QString::fromUtf8("Mã giao dịch"),
            QString::fromUtf8("Thời gian tạo đơn"),
            QString::fromUtf8("Tên tài khoản"),
            QString::fromUtf8("Thuộc đại lý"),
            QString::fromUtf8("Số tiền"),
            QString::fromUtf8("Phí hội viên"),
            QString::fromUtf8("Số tiền thực tế"),
            QString::fromUtf8("Trạng thái giao dịch"),
        },
        flow
    );

    m_date_pickers[5] = new DateRangePicker;
    m_date_pickers[5]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Thời gian tạo đơn："), m_date_pickers[5], m_withdrawal_history.search_labels));

    auto* username = new QLineEdit;
    username->setPlaceholderText(QString::fromUtf8("Nhập tên tài khoản"));
    username->setFixedWidth(150);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Tên tài khoản："), username, m_withdrawal_history.search_labels));

    auto* serial_no = new QLineEdit;
    serial_no->setPlaceholderText(QString::fromUtf8("Nhập mã giao dịch"));
    serial_no->setFixedWidth(300);
    serial_no->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Mã giao dịch："), serial_no, m_withdrawal_history.search_labels));

    auto* status_select = new QComboBox;
    status_select->addItem(QString::fromUtf8("Chọn"), QVariant());
    status_select->addItem(QString::fromUtf8("Chờ xử lí"), "0");
    status_select->addItem(QString::fromUtf8("Hoàn tất"), "1");
    status_select->addItem(QString::fromUtf8("Đang xử lí"), "2");
    status_select->addItem(QString::fromUtf8("Trạng thái không thành công"), "3");
    status_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    status_select->setFixedHeight(32);
    status_select->setFixedWidth(200);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Trạng thái giao dịch："), status_select, m_withdrawal_history.search_labels));

    flow->addWidget(make_search_button(":/icons/search", QString::fromUtf8("Tìm kiếm"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", QString::fromUtf8("Đặt lại"), "resetBtn"));

    return m_withdrawal_history.page;
}

QWidget* ReportPages::create_deposit_history_page()
{
    FlowLayout* flow = nullptr;
    m_deposit_history = ReportPageBuilder::build_page(
        ":/icons/menu_deposit_log",
        QString::fromUtf8("DANH SÁCH NẠP TIỀN"),
        {
            QString::fromUtf8("Tên tài khoản"),
            QString::fromUtf8("Thuộc đại lý"),
            QString::fromUtf8("Số tiền"),
            QString::fromUtf8("Loại hình giao dịch"),
            QString::fromUtf8("Trạng thái giao dịch"),
            QString::fromUtf8("Thời gian tạo đơn"),
        },
        flow
    );

    m_date_pickers[6] = new DateRangePicker;
    m_date_pickers[6]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Thời gian tạo đơn："), m_date_pickers[6], m_deposit_history.search_labels));

    auto* username = new QLineEdit;
    username->setPlaceholderText(QString::fromUtf8("Nhập tên tài khoản"));
    username->setFixedWidth(300);
    username->setFixedHeight(32);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Tên tài khoản："), username, m_deposit_history.search_labels));

    auto* type_select = new QComboBox;
    type_select->addItem(QString::fromUtf8("Chọn"), QVariant());
    type_select->addItem(QString::fromUtf8("Nạp tiền"), "1");
    type_select->addItem(QString::fromUtf8("Rút tiền"), "2");
    type_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    type_select->setFixedHeight(32);
    type_select->setFixedWidth(220);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Loại hình giao dịch："), type_select, m_deposit_history.search_labels));

    auto* status_select = new QComboBox;
    status_select->addItem(QString::fromUtf8("Chọn"), QVariant());
    status_select->addItem(QString::fromUtf8("Chờ xử lí"), "0");
    status_select->addItem(QString::fromUtf8("Hoàn tất"), "1");
    status_select->addItem(QString::fromUtf8("Đang xử lí"), "2");
    status_select->addItem(QString::fromUtf8("Trạng thái không thành công"), "3");
    status_select->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    status_select->setFixedHeight(32);
    status_select->setFixedWidth(180);
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Trạng thái giao dịch："), status_select, m_deposit_history.search_labels));

    flow->addWidget(make_search_button(":/icons/search", QString::fromUtf8("Tìm kiếm"), "searchBtn"));
    flow->addWidget(make_search_button(":/icons/refresh", QString::fromUtf8("Đặt lại"), "resetBtn"));

    return m_deposit_history.page;
}

void ReportPages::apply_theme()
{
    ReportPageBuilder::apply_page_theme(m_lottery_report, m_theme);
    ReportPageBuilder::apply_page_theme(m_transaction_log, m_theme);
    ReportPageBuilder::apply_page_theme(m_provider_report, m_theme);
    ReportPageBuilder::apply_page_theme(m_lottery_bets, m_theme);
    ReportPageBuilder::apply_page_theme(m_provider_bets, m_theme);
    ReportPageBuilder::apply_page_theme(m_withdrawal_history, m_theme);
    ReportPageBuilder::apply_page_theme(m_deposit_history, m_theme);

    const auto bg = m_theme->color("bg");
    const auto text1 = m_theme->color("text_primary");
    const auto border = m_theme->color("border");
    const auto primary = m_theme->color("primary");

    auto date_btn_style = QString(
        "QPushButton { background: %1; color: %2;"
        "  border-style: solid; border-width: 1px; border-color: %3; border-radius: 0px;"
        "  padding: 4px 8px; font-size: 13px; text-align: left; }"
        "QPushButton:hover { border-color: %4; }"
    ).arg(bg, text1, border, primary);
    bool is_dark = m_theme->theme() == "dark";
    for (int i = 0; i < 7; ++i) {
        if (m_date_pickers[i]) {
            m_date_pickers[i]->set_button_style(date_btn_style);
            m_date_pickers[i]->apply_popup_theme(is_dark);
        }
    }
}
