#include "core/main_widget.h"
#include "core/date_range_picker.h"
#include "core/flow_layout.h"
#include "core/api_client.h"
#include "core/theme_manager.h"
#include "core/translator.h"
#include "core/report_page_builder.h"

#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QGridLayout>
#include <QPixmap>
#include <QScrollArea>
#include <QInputDialog>
#include <QMessageBox>
#include <QActionGroup>
#include <QFileDialog>
#include <QTextStream>
#include <QPrinter>
#include <QPrintDialog>
#include <QTextDocument>
#include <QCheckBox>
#include <QDialogButtonBox>
#include <QDialog>

MainWidget::MainWidget(ApiClient* api, ThemeManager* theme, Translator* tr, QWidget* parent)
    : QWidget(parent)
    , m_api(api)
    , m_theme(theme)
    , m_tr(tr)
{
    setup_ui();

    connect(m_theme, &ThemeManager::theme_changed, this, &MainWidget::on_theme_changed);
    connect(m_tr, &Translator::locale_changed, this, &MainWidget::on_locale_changed);
}

void MainWidget::set_username(const QString& username)
{
    m_username = username;
    m_username_label->setText(username);
    m_welcome_name->setText(username);
    m_account_button->setText(username);
}

void MainWidget::setup_ui()
{
    auto* root = new QVBoxLayout(this);
    root->setContentsMargins(0, 0, 0, 0);
    root->setSpacing(0);

    setup_toolbar();
    root->addWidget(m_toolbar);

    m_content_stack = new QStackedWidget;
    m_home_page = create_home_page();
    m_content_stack->addWidget(m_home_page);                   // 0
    m_content_stack->addWidget(create_customers_page());        // 1
    m_content_stack->addWidget(create_lottery_report_page());   // 2
    m_content_stack->addWidget(create_transaction_log_page());  // 3
    m_content_stack->addWidget(create_provider_report_page());  // 4
    m_content_stack->addWidget(create_lottery_bets_page());     // 5
    m_content_stack->addWidget(create_provider_bets_page());    // 6
    m_content_stack->addWidget(create_withdrawal_history_page()); // 7 (Nhật ký rút → Lịch sử rút tiền)
    m_content_stack->addWidget(create_deposit_history_page());    // 8 (Nhật ký nạp → Danh sách nạp tiền)
    root->addWidget(m_content_stack, 1);

    apply_theme();
}

// ════════════════════════════════════════
// TOOLBAR (Cqt style)
// ════════════════════════════════════════
void MainWidget::setup_toolbar()
{
    m_toolbar = new QToolBar;
    m_toolbar->setMovable(false);
    m_toolbar->setFloatable(false);
    m_toolbar->setIconSize(QSize(18, 18));
    m_toolbar->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);

    // ── Trang Chủ (ngoài cùng bên trái) ──
    m_home_action = m_toolbar->addAction(
        QIcon(":/icons/home"),
        QString::fromUtf8("Trang Chủ"));
    connect(m_home_action, &QAction::triggered, this, [this]() { navigate_to(0); });

    // ── Quản Lý Khách Hàng (y hệt Cqt) ──
    m_customers_action = m_toolbar->addAction(
        QIcon(":/icons/customers"),
        QString::fromUtf8("Quản Lý Khách Hàng"));
    connect(m_customers_action, &QAction::triggered, this, [this]() { navigate_to(1); });

    // ── Báo Cáo — dropdown menu ──
    m_report_menu = new QMenu(this);
    auto* act_lottery_report = m_report_menu->addAction(QIcon(":/icons/menu_lottery_report"),
        QString::fromUtf8("Báo cáo xổ số"));
    auto* act_transaction_log = m_report_menu->addAction(QIcon(":/icons/menu_transaction_log"),
        QString::fromUtf8("Sao kê giao dịch"));
    auto* act_provider_report = m_report_menu->addAction(QIcon(":/icons/menu_provider_report"),
        QString::fromUtf8("Báo cáo nhà cung cấp"));
    connect(act_lottery_report, &QAction::triggered, this, [this]() { navigate_to(2); });
    connect(act_transaction_log, &QAction::triggered, this, [this]() { navigate_to(3); });
    connect(act_provider_report, &QAction::triggered, this, [this]() { navigate_to(4); });

    m_report_button = new QToolButton(this);
    m_report_button->setIcon(QIcon(":/icons/report"));
    m_report_button->setText(QString::fromUtf8("Báo Cáo"));
    m_report_button->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    m_report_button->setPopupMode(QToolButton::InstantPopup);
    m_report_button->setMenu(m_report_menu);
    m_toolbar->addWidget(m_report_button);

    // ── Đơn Cược — dropdown menu ──
    m_bet_order_menu = new QMenu(this);
    auto* act_provider_bets = m_bet_order_menu->addAction(QIcon(":/icons/menu_third_party_bet"),
        QString::fromUtf8("Đơn cược bên thứ 3"));
    auto* act_lottery_bets = m_bet_order_menu->addAction(QIcon(":/icons/menu_lottery_bet"),
        QString::fromUtf8("Đơn cược xổ số"));
    connect(act_provider_bets, &QAction::triggered, this, [this]() { navigate_to(6); });
    connect(act_lottery_bets, &QAction::triggered, this, [this]() { navigate_to(5); });

    m_bet_order_button = new QToolButton(this);
    m_bet_order_button->setIcon(QIcon(":/icons/bet_order"));
    m_bet_order_button->setText(QString::fromUtf8("Đơn Cược"));
    m_bet_order_button->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    m_bet_order_button->setPopupMode(QToolButton::InstantPopup);
    m_bet_order_button->setMenu(m_bet_order_menu);
    m_toolbar->addWidget(m_bet_order_button);

    // ── Nạp - Rút — dropdown menu ──
    m_deposit_withdraw_menu = new QMenu(this);
    auto* act_deposit_log = m_deposit_withdraw_menu->addAction(QIcon(":/icons/menu_deposit_log"),
        QString::fromUtf8("Danh sách nạp tiền"));
    auto* act_withdraw_log = m_deposit_withdraw_menu->addAction(QIcon(":/icons/menu_withdraw_log"),
        QString::fromUtf8("Lịch sử rút tiền"));
    connect(act_deposit_log, &QAction::triggered, this, [this]() { navigate_to(8); });
    connect(act_withdraw_log, &QAction::triggered, this, [this]() { navigate_to(7); });

    m_deposit_withdraw_button = new QToolButton(this);
    m_deposit_withdraw_button->setIcon(QIcon(":/icons/deposit_withdraw"));
    m_deposit_withdraw_button->setText(QString::fromUtf8("Nạp - Rút"));
    m_deposit_withdraw_button->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    m_deposit_withdraw_button->setPopupMode(QToolButton::InstantPopup);
    m_deposit_withdraw_button->setMenu(m_deposit_withdraw_menu);
    m_toolbar->addWidget(m_deposit_withdraw_button);

    // ── Spacer đẩy các nút còn lại sang phải ──
    auto* spacer = new QWidget(this);
    spacer->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Preferred);
    spacer->setStyleSheet("background: transparent; border: none;");
    m_toolbar->addWidget(spacer);

    // ── Theme toggle (icon màu) ──
    m_theme_action = m_toolbar->addAction(
        QIcon(m_theme->theme() == "dark" ? ":/icons/sun_theme" : ":/icons/moon_theme"),
        m_theme->theme() == "dark" ? QString::fromUtf8("Sáng") : QString::fromUtf8("Tối"));
    connect(m_theme_action, &QAction::triggered, this, [this]() {
        m_theme->toggle_theme();
    });

    // ── Language switcher (icon lá cờ) ──
    m_lang_menu = new QMenu(this);
    const QStringList locales = {"vi_VN", "en_US", "zh_CN"};
    const QStringList locale_names = {
        QString::fromUtf8("Tiếng Việt"),
        "English",
        QString::fromUtf8("\u4e2d\u6587")
    };
    const QStringList flag_icons = {
        ":/icons/flag_vn", ":/icons/flag_us", ":/icons/flag_cn"
    };
    for (int i = 0; i < locales.size(); ++i) {
        auto* action = m_lang_menu->addAction(
            QIcon(flag_icons[i]), locale_names[i]);
        connect(action, &QAction::triggered, this, [this, locale = locales[i]]() {
            m_tr->set_locale(locale);
        });
    }

    m_lang_button = new QToolButton(this);
    m_lang_button->setIcon(lang_flag_icon(m_tr->locale()));
    m_lang_button->setText(m_tr->locale_label(m_tr->locale()));
    m_lang_button->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    m_lang_button->setPopupMode(QToolButton::InstantPopup);
    m_lang_button->setMenu(m_lang_menu);
    m_toolbar->addWidget(m_lang_button);

    // ── Tài khoản — dropdown menu (giống Cqt "Báo Cáo") ──
    m_account_menu = new QMenu(this);

    m_change_pwd_action = m_account_menu->addAction(
        QIcon(":/icons/password"), m_tr->t("auth.change_password"));
    connect(m_change_pwd_action, &QAction::triggered, this, &MainWidget::on_change_password);

    m_account_menu->addSeparator();

    m_logout_action = m_account_menu->addAction(
        QIcon(":/icons/logout"), m_tr->t("auth.logout"));
    connect(m_logout_action, &QAction::triggered, this, &MainWidget::on_logout);

    m_account_button = new QToolButton(this);
    m_account_button->setIcon(QIcon(":/icons/user"));
    m_account_button->setText(m_username.isEmpty() ? "User" : m_username);
    m_account_button->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    m_account_button->setPopupMode(QToolButton::InstantPopup);
    m_account_button->setMenu(m_account_menu);
    m_toolbar->addWidget(m_account_button);

    // ── Cài Đặt (y hệt Cqt) ──
    m_settings_action = m_toolbar->addAction(
        QIcon(":/icons/settings"),
        QString::fromUtf8("Cài Đặt"));

    // Hidden label for username data
    m_username_label = new QLabel;
    m_username_label->setVisible(false);
}

// ════════════════════════════════════════
// HOME PAGE
// ════════════════════════════════════════
QWidget* MainWidget::create_home_page()
{
    auto* scroll = new QScrollArea;
    scroll->setWidgetResizable(true);
    scroll->setObjectName("homeScroll");
    scroll->setStyleSheet(
        "QScrollArea#homeScroll { border: none; }"
        "QScrollBar:vertical { width: 6px; background: transparent; }"
        "QScrollBar::handle:vertical { background: #ddd; min-height: 30px; }"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
    );

    auto* page = new QWidget;
    page->setObjectName("homePage");

    auto* page_layout = new QVBoxLayout(page);
    page_layout->setContentsMargins(0, 0, 0, 0);
    page_layout->setSpacing(0);

    // ── Hero section ──
    m_hero_widget = new QWidget;
    m_hero_widget->setObjectName("heroWidget");
    auto* hero_layout = new QVBoxLayout(m_hero_widget);
    hero_layout->setAlignment(Qt::AlignCenter);
    hero_layout->setContentsMargins(0, 36, 0, 20);
    hero_layout->setSpacing(0);

    auto* hero_logo = new QLabel;
    QPixmap hero_pix(":/icons/app");
    hero_logo->setPixmap(hero_pix.scaled(320, 160, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    hero_logo->setAlignment(Qt::AlignCenter);
    hero_logo->setStyleSheet("border: none;");
    hero_layout->addWidget(hero_logo);
    hero_layout->addSpacing(12);

    // Giữ m_hero_title ẩn (cần cho theme update)
    m_hero_title = new QLabel("");
    m_hero_title->setVisible(false);
    hero_layout->addWidget(m_hero_title);

    m_hero_tagline = new QLabel(m_tr->t("home.tagline"));
    m_hero_tagline->setStyleSheet("font-size: 15px; border: none;");
    m_hero_tagline->setAlignment(Qt::AlignCenter);
    hero_layout->addWidget(m_hero_tagline);
    hero_layout->addSpacing(18);

    // Action buttons
    auto* btn_row = new QWidget;
    btn_row->setStyleSheet("border: none;");
    auto* btn_layout = new QHBoxLayout(btn_row);
    btn_layout->setAlignment(Qt::AlignCenter);
    btn_layout->setContentsMargins(0, 0, 0, 0);
    btn_layout->setSpacing(12);

    m_explore_btn = new QPushButton(m_tr->t("home.explore"));
    m_explore_btn->setCursor(Qt::PointingHandCursor);
    m_explore_btn->setStyleSheet(
        "QPushButton {"
        "  background: #16baaa; color: #fff; border: none;"
        "  padding: 0 20px; height: 36px; font-size: 14px; font-weight: 500;"
        "}"
        "QPushButton:hover { background: #0d8a7e; }"
    );
    btn_layout->addWidget(m_explore_btn);

    hero_layout->addWidget(btn_row);
    hero_layout->addSpacing(14);

    // Welcome message
    auto* welcome = new QWidget;
    welcome->setStyleSheet("border: none;");
    auto* welcome_layout = new QHBoxLayout(welcome);
    welcome_layout->setAlignment(Qt::AlignCenter);
    welcome_layout->setContentsMargins(0, 0, 0, 0);
    welcome_layout->setSpacing(6);

    auto* w_icon = new QLabel;
    QPixmap w_pix(":/icons/user");
    w_icon->setPixmap(w_pix.scaled(14, 14, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    w_icon->setStyleSheet("border: none;");
    welcome_layout->addWidget(w_icon);

    m_welcome_text = new QLabel(m_tr->t("home.welcome") + ", ");
    m_welcome_text->setStyleSheet("font-size: 13px; border: none;");
    welcome_layout->addWidget(m_welcome_text);

    m_welcome_name = new QLabel(m_username.isEmpty() ? "User" : m_username);
    m_welcome_name->setStyleSheet("font-size: 13px; font-weight: bold; border: none;");
    welcome_layout->addWidget(m_welcome_name);

    hero_layout->addWidget(welcome);

    page_layout->addWidget(m_hero_widget);

    // ── Feature boxes — 6 boxes in 3x2 grid ──
    m_boxes_container = new QWidget;
    m_boxes_container->setObjectName("boxesContainer");
    auto* boxes_outer = new QHBoxLayout(m_boxes_container);
    boxes_outer->setContentsMargins(200, 16, 200, 10);

    auto* grid = new QGridLayout;
    grid->setSpacing(16);

    const QString feature_keys[] = {"go", "vue", "qt", "comp", "theme", "log"};
    const QString icon_paths[] = {
        ":/icons/server", ":/icons/webdesign", ":/icons/monitor",
        ":/icons/widgets", ":/icons/moon_feature", ":/icons/journal"
    };

    for (int i = 0; i < 6; ++i) {
        auto* box = new QWidget;
        box->setObjectName("featureBox");
        m_feature_boxes.push_back(box);

        auto* box_layout = new QVBoxLayout(box);
        box_layout->setContentsMargins(16, 16, 16, 16);
        box_layout->setSpacing(0);

        auto* icon_container = new QWidget;
        icon_container->setFixedSize(40, 40);
        m_feature_icon_bgs.push_back(icon_container);
        auto* icon_inner = new QHBoxLayout(icon_container);
        icon_inner->setContentsMargins(0, 0, 0, 0);
        icon_inner->setAlignment(Qt::AlignCenter);

        auto* icon_label = new QLabel;
        QPixmap icon_pix(icon_paths[i]);
        icon_label->setPixmap(icon_pix.scaled(24, 24, Qt::KeepAspectRatio, Qt::SmoothTransformation));
        icon_label->setAlignment(Qt::AlignCenter);
        icon_label->setStyleSheet("border: none;");
        icon_inner->addWidget(icon_label);

        box_layout->addWidget(icon_container);
        box_layout->addSpacing(10);

        auto* title_label = new QLabel(m_tr->t("features." + feature_keys[i] + "_title"));
        title_label->setStyleSheet("font-size: 15px; font-weight: 600; border: none;");
        box_layout->addWidget(title_label);
        box_layout->addSpacing(4);
        m_feature_titles.push_back(title_label);

        auto* desc_label = new QLabel(m_tr->t("features." + feature_keys[i] + "_desc"));
        desc_label->setStyleSheet("font-size: 12px; border: none;");
        desc_label->setWordWrap(true);
        box_layout->addWidget(desc_label);
        m_feature_descs.push_back(desc_label);

        box_layout->addStretch();
        grid->addWidget(box, i / 3, i % 3);
    }

    boxes_outer->addLayout(grid);
    page_layout->addWidget(m_boxes_container, 1);

    // ── Footer ──
    m_footer = new QWidget;
    m_footer->setObjectName("footer");
    auto* footer_layout = new QHBoxLayout(m_footer);
    footer_layout->setAlignment(Qt::AlignCenter);
    footer_layout->setContentsMargins(0, 14, 0, 14);

    m_footer_text = new QLabel(QString::fromUtf8("MaxHub \u00a9 2026"));
    m_footer_text->setStyleSheet("font-size: 12px; border: none;");
    footer_layout->addWidget(m_footer_text);

    page_layout->addWidget(m_footer);

    scroll->setWidget(page);
    return scroll;
}

// ════════════════════════════════════════
// CUSTOMERS PAGE (giống hệt web customers.vue)
// ════════════════════════════════════════
QWidget* MainWidget::create_customers_page()
{
    m_customers_page = new QWidget;
    m_customers_page->setObjectName("customersPage");

    auto* page_layout = new QVBoxLayout(m_customers_page);
    page_layout->setContentsMargins(10, 10, 10, 10);
    page_layout->setSpacing(0);

    // ── Card container (lay-card) ──
    m_customers_card = new QWidget;
    m_customers_card->setObjectName("customersCard");
    auto* card_layout = new QVBoxLayout(m_customers_card);
    card_layout->setContentsMargins(16, 16, 16, 16);
    card_layout->setSpacing(12);

    // ── Field header: icon + title (lay-field title) ──
    m_customers_field_header = new QWidget;
    auto* header_layout = new QHBoxLayout(m_customers_field_header);
    header_layout->setContentsMargins(0, 0, 0, 8);
    header_layout->setSpacing(6);
    header_layout->setAlignment(Qt::AlignLeft);

    auto* header_icon = new QLabel;
    QPixmap icon_pix(":/icons/customers");
    header_icon->setPixmap(icon_pix.scaled(18, 18, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    header_icon->setStyleSheet("border: none;");
    header_layout->addWidget(header_icon);

    m_customers_title = new QLabel(QString::fromUtf8("QUẢN LÍ HỘI VIÊN THUỘC CẤP"));
    m_customers_title->setStyleSheet("font-size: 16px; font-weight: 700; border: none;");
    header_layout->addWidget(m_customers_title);
    header_layout->addStretch();

    card_layout->addWidget(m_customers_field_header);

    // ── Separator line (giống lay-field border) ──
    auto* separator = new QWidget;
    separator->setFixedHeight(1);
    separator->setObjectName("fieldSeparator");
    card_layout->addWidget(separator);
    card_layout->addSpacing(12);

    // ── Search form (inline flow, giống web flex-wrap) ──
    // Helper lambda: tạo cặp label + widget nằm ngang
    auto make_field = [this](const QString& label_text, QWidget* field) -> QWidget* {
        auto* w = new QWidget;
        w->setStyleSheet("border: none;");
        auto* h = new QHBoxLayout(w);
        h->setContentsMargins(0, 0, 0, 0);
        h->setSpacing(6);
        auto* lbl = new QLabel(label_text);
        lbl->setObjectName("searchLabel");
        m_search_labels.push_back(lbl);
        h->addWidget(lbl);
        h->addWidget(field);
        return w;
    };

    auto* form_widget = new QWidget;
    form_widget->setObjectName("searchForm");
    auto* flow = new FlowLayout(form_widget, 0, 12, 8);
    Q_UNUSED(flow);

    // Tên tài khoản
    m_search_username = new QLineEdit;
    m_search_username->setPlaceholderText(QString::fromUtf8("Nhập tên tài khoản"));
    m_search_username->setFixedWidth(160);
    m_search_username->setFixedHeight(32);
    flow->addWidget(make_field(QString::fromUtf8("Tên tài khoản："), m_search_username));

    // Thời gian nạp đầu (single-calendar date range picker)
    m_date_range_picker = new DateRangePicker;
    m_date_range_picker->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc")
    );
    flow->addWidget(make_field(QString::fromUtf8("Thời gian nạp đầu："), m_date_range_picker));

    // Trạng thái
    m_search_status = new QComboBox;
    m_search_status->addItem(QString::fromUtf8("-- Chọn --"), QVariant());
    m_search_status->addItem(QString::fromUtf8("Chưa đánh giá"), "unrated");
    m_search_status->addItem(QString::fromUtf8("Bình thường"), "normal");
    m_search_status->addItem(QString::fromUtf8("Đóng băng"), "frozen");
    m_search_status->addItem(QString::fromUtf8("Khoá"), "locked");
    m_search_status->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_search_status->setFixedHeight(32);
    flow->addWidget(make_field(QString::fromUtf8("Trạng thái："), m_search_status));

    // Sắp xếp theo trường
    m_search_sort_field = new QComboBox;
    m_search_sort_field->addItem(QString::fromUtf8("-- Chọn --"), QVariant());
    m_search_sort_field->addItem(QString::fromUtf8("Số dư"), "balance");
    m_search_sort_field->addItem(QString::fromUtf8("Lần đăng nhập cuối"), "last_login");
    m_search_sort_field->addItem(QString::fromUtf8("Thời gian đăng ký"), "created_at");
    m_search_sort_field->addItem(QString::fromUtf8("Tổng tiền nạp"), "total_deposit");
    m_search_sort_field->addItem(QString::fromUtf8("Tổng tiền rút"), "total_withdraw");
    m_search_sort_field->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_search_sort_field->setFixedHeight(32);
    flow->addWidget(make_field(QString::fromUtf8("Sắp xếp theo trường："), m_search_sort_field));

    // Sắp xếp theo hướng
    m_search_sort_dir = new QComboBox;
    m_search_sort_dir->addItem(QString::fromUtf8("Từ lớn đến bé"), "desc");
    m_search_sort_dir->addItem(QString::fromUtf8("Từ bé đến lớn"), "asc");
    m_search_sort_dir->setSizeAdjustPolicy(QComboBox::AdjustToContents);
    m_search_sort_dir->setFixedHeight(32);
    flow->addWidget(make_field(QString::fromUtf8("Sắp xếp theo hướng："), m_search_sort_dir));

    // Buttons: Tìm kiếm + Đặt lại
    m_search_btn = new QPushButton(QIcon(":/icons/search"), QString::fromUtf8("Tìm kiếm"));
    m_search_btn->setObjectName("searchBtn");
    m_search_btn->setCursor(Qt::PointingHandCursor);
    m_search_btn->setFixedHeight(32);
    m_search_btn->setIconSize(QSize(16, 16));
    flow->addWidget(m_search_btn);

    m_reset_btn = new QPushButton(QIcon(":/icons/refresh"), QString::fromUtf8("Đặt lại"));
    m_reset_btn->setObjectName("resetBtn");
    m_reset_btn->setCursor(Qt::PointingHandCursor);
    m_reset_btn->setFixedHeight(32);
    m_reset_btn->setIconSize(QSize(16, 16));
    flow->addWidget(m_reset_btn);

    connect(m_reset_btn, &QPushButton::clicked, this, [this]() {
        m_search_username->clear();
        m_date_range_picker->clear_dates();
        m_search_status->setCurrentIndex(0);
        m_search_sort_field->setCurrentIndex(0);
        m_search_sort_dir->setCurrentIndex(0);
    });

    card_layout->addWidget(form_widget);

    // ── Table group: toolbar + table + pagination gắn liền nhau ──
    auto* table_group = new QWidget;
    auto* tg_layout = new QVBoxLayout(table_group);
    tg_layout->setContentsMargins(0, 0, 0, 0);
    tg_layout->setSpacing(0);

    // ── Table toolbar (giống web lay-table toolbar) ──
    m_table_toolbar = new QWidget;
    m_table_toolbar->setObjectName("tableToolbar");
    auto* tb_layout = new QHBoxLayout(m_table_toolbar);
    tb_layout->setContentsMargins(0, 0, 0, 0);
    tb_layout->setSpacing(0);

    // Left: action buttons
    auto* tb_left = new QWidget;
    auto* tb_left_layout = new QHBoxLayout(tb_left);
    tb_left_layout->setContentsMargins(8, 6, 0, 6);
    tb_left_layout->setSpacing(0);

    m_add_member_btn = new QPushButton(QString::fromUtf8("+ Thêm hội viên"));
    m_add_member_btn->setObjectName("tbBtn");
    m_add_member_btn->setCursor(Qt::PointingHandCursor);
    m_add_member_btn->setFixedHeight(26);
    tb_left_layout->addWidget(m_add_member_btn);

    m_add_agent_btn = new QPushButton(QString::fromUtf8("+ Đại lý mới thêm"));
    m_add_agent_btn->setObjectName("tbBtn");
    m_add_agent_btn->setCursor(Qt::PointingHandCursor);
    m_add_agent_btn->setFixedHeight(26);
    tb_left_layout->addWidget(m_add_agent_btn);

    tb_left_layout->addStretch();
    tb_layout->addWidget(tb_left, 1);

    // Right: filter/export/print icons
    auto* tb_right = new QWidget;
    auto* tb_right_layout = new QHBoxLayout(tb_right);
    tb_right_layout->setContentsMargins(0, 6, 8, 6);
    tb_right_layout->setSpacing(4);

    auto make_tool_icon = [](const QString& icon_path, const QString& tooltip) -> QPushButton* {
        auto* btn = new QPushButton;
        btn->setObjectName("toolIcon");
        btn->setIcon(QIcon(icon_path));
        btn->setIconSize(QSize(16, 16));
        btn->setFixedSize(28, 26);
        btn->setCursor(Qt::PointingHandCursor);
        btn->setToolTip(tooltip);
        return btn;
    };

    m_filter_btn = make_tool_icon(":/icons/settings", QString::fromUtf8("Lọc cột"));
    m_export_btn = make_tool_icon(":/icons/report", QString::fromUtf8("Xuất file"));
    m_print_btn = make_tool_icon(":/icons/browser", QString::fromUtf8("In"));
    tb_right_layout->addWidget(m_filter_btn);
    tb_right_layout->addWidget(m_export_btn);
    tb_right_layout->addWidget(m_print_btn);

    connect(m_filter_btn, &QPushButton::clicked, this, &MainWidget::on_filter_columns);
    connect(m_export_btn, &QPushButton::clicked, this, &MainWidget::on_export_csv);
    connect(m_print_btn, &QPushButton::clicked, this, &MainWidget::on_print_table);

    tb_layout->addWidget(tb_right);
    tg_layout->addWidget(m_table_toolbar);

    // ── Table (QTableWidget giống web lay-table) ──
    m_customers_table = new QTableWidget(0, 12);
    m_customers_table->setObjectName("customersTable");

    const QStringList headers = {
        QString::fromUtf8("Hội viên"),
        QString::fromUtf8("Loại hình hội viên"),
        QString::fromUtf8("Tài khoản đại lý"),
        QString::fromUtf8("Số dư"),
        QString::fromUtf8("Lần nạp"),
        QString::fromUtf8("Lần rút"),
        QString::fromUtf8("Tổng tiền nạp"),
        QString::fromUtf8("Tổng tiền rút"),
        QString::fromUtf8("Lần đăng nhập cuối"),
        QString::fromUtf8("Thời gian đăng ký"),
        QString::fromUtf8("Trạng thái"),
        QString::fromUtf8("Thao tác"),
    };
    m_customers_table->setHorizontalHeaderLabels(headers);

    // Tất cả cột co giãn đều (Stretch), căn trái
    m_customers_table->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    m_customers_table->horizontalHeader()->setDefaultAlignment(Qt::AlignLeft | Qt::AlignVCenter);
    m_customers_table->verticalHeader()->setVisible(false);
    m_customers_table->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_customers_table->setSelectionMode(QAbstractItemView::SingleSelection);
    m_customers_table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_customers_table->setAlternatingRowColors(false);
    m_customers_table->setShowGrid(true);
    m_customers_table->horizontalHeader()->setHighlightSections(false);

    // Sample data (giống web)
    m_customers_table->insertRow(0);
    const QStringList sample = {
        "an10tynghichoi",
        QString::fromUtf8("Hội viên chính thức"),
        "vozer123",
        "0.0000", "0", "0", "0.0000", "0.0000",
        "",
        "2026-03-09 16:20:58",
        QString::fromUtf8("Bình thường"),
        ""
    };
    for (int c = 0; c < 11; ++c) {
        auto* item = new QTableWidgetItem(sample[c]);
        item->setTextAlignment(Qt::AlignLeft | Qt::AlignVCenter);
        m_customers_table->setItem(0, c, item);
    }
    // Thao tác column: button
    auto* rebate_btn = new QPushButton(QString::fromUtf8("Cài đặt hoàn trả"));
    rebate_btn->setObjectName("rebateBtn");
    rebate_btn->setCursor(Qt::PointingHandCursor);
    rebate_btn->setFixedHeight(24);
    m_customers_table->setCellWidget(0, 11, rebate_btn);
    m_customers_table->setRowHeight(0, 38);

    tg_layout->addWidget(m_customers_table, 1);

    // ── Pagination bar (giống web layui-table-page) ──
    m_pagination_bar = new QWidget;
    m_pagination_bar->setObjectName("paginationBar");
    auto* pg_layout = new QHBoxLayout(m_pagination_bar);
    pg_layout->setContentsMargins(8, 6, 8, 6);
    pg_layout->setSpacing(8);

    m_page_prev_btn = new QPushButton("<");
    m_page_prev_btn->setObjectName("pageBtn");
    m_page_prev_btn->setFixedSize(30, 28);
    m_page_prev_btn->setEnabled(false);
    pg_layout->addWidget(m_page_prev_btn);

    m_page_number = new QLabel("1");
    m_page_number->setObjectName("pageNumber");
    m_page_number->setFixedSize(30, 28);
    m_page_number->setAlignment(Qt::AlignCenter);
    pg_layout->addWidget(m_page_number);

    m_page_next_btn = new QPushButton(">");
    m_page_next_btn->setObjectName("pageBtn");
    m_page_next_btn->setFixedSize(30, 28);
    m_page_next_btn->setEnabled(false);
    pg_layout->addWidget(m_page_next_btn);

    pg_layout->addSpacing(12);

    m_page_info = new QLabel(QString::fromUtf8("Tổng 1 dòng"));
    m_page_info->setObjectName("pageInfo");
    pg_layout->addWidget(m_page_info);

    pg_layout->addSpacing(8);

    m_page_size_combo = new QComboBox;
    m_page_size_combo->setObjectName("pageSizeCombo");
    const int page_sizes[] = {10, 20, 30, 40, 50, 60, 70, 80, 90};
    for (int ps : page_sizes) {
        m_page_size_combo->addItem(
            QString::fromUtf8("%1 dòng/trang").arg(ps), ps);
    }
    m_page_size_combo->setFixedHeight(28);
    pg_layout->addWidget(m_page_size_combo);

    pg_layout->addStretch();
    tg_layout->addWidget(m_pagination_bar);

    card_layout->addWidget(table_group, 1);

    page_layout->addWidget(m_customers_card, 1);

    return m_customers_page;
}

// ════════════════════════════════════════
// HELPER: tạo quick date combo + date range picker
// ════════════════════════════════════════
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

// ════════════════════════════════════════
// BÁO CÁO XỔ SỐ (index 2)
// ════════════════════════════════════════
QWidget* MainWidget::create_lottery_report_page()
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

    // Search fields
    m_report_date_pickers[0] = new DateRangePicker;
    m_report_date_pickers[0]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(m_report_date_pickers[0]);

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

    // Summary
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

// ════════════════════════════════════════
// SAO KÊ GIAO DỊCH (index 3)
// ════════════════════════════════════════
QWidget* MainWidget::create_transaction_log_page()
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

    m_report_date_pickers[1] = new DateRangePicker;
    m_report_date_pickers[1]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(m_report_date_pickers[1]);

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

// ════════════════════════════════════════
// BÁO CÁO NHÀ CUNG CẤP (index 4)
// ════════════════════════════════════════
QWidget* MainWidget::create_provider_report_page()
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

    m_report_date_pickers[2] = new DateRangePicker;
    m_report_date_pickers[2]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(m_report_date_pickers[2]);

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

// ════════════════════════════════════════
// DANH SÁCH ĐƠN CƯỢC (index 5)
// ════════════════════════════════════════
QWidget* MainWidget::create_lottery_bets_page()
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

    m_report_date_pickers[3] = new DateRangePicker;
    m_report_date_pickers[3]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(m_report_date_pickers[3]);

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

// ════════════════════════════════════════
// ĐƠN CƯỢC BÊN THỨ 3 (index 6)
// ════════════════════════════════════════
QWidget* MainWidget::create_provider_bets_page()
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

    m_report_date_pickers[4] = new DateRangePicker;
    m_report_date_pickers[4]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Thời gian cược："), m_report_date_pickers[4], m_provider_bets.search_labels));

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

// ════════════════════════════════════════
// LỊCH SỬ RÚT TIỀN (index 7)
// ════════════════════════════════════════
QWidget* MainWidget::create_withdrawal_history_page()
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

    m_report_date_pickers[5] = new DateRangePicker;
    m_report_date_pickers[5]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Thời gian tạo đơn："), m_report_date_pickers[5], m_withdrawal_history.search_labels));

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

// ════════════════════════════════════════
// DANH SÁCH NẠP TIỀN (index 8)
// ════════════════════════════════════════
QWidget* MainWidget::create_deposit_history_page()
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

    m_report_date_pickers[6] = new DateRangePicker;
    m_report_date_pickers[6]->set_placeholder(
        QString::fromUtf8("Thời gian bắt đầu"),
        QString::fromUtf8("Thời gian kết thúc"));
    flow->addWidget(ReportPageBuilder::make_field(
        QString::fromUtf8("Thời gian tạo đơn："), m_report_date_pickers[6], m_deposit_history.search_labels));

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

QIcon MainWidget::lang_flag_icon(const QString& locale) const
{
    if (locale == "vi_VN") return QIcon(":/icons/flag_vn");
    if (locale == "zh_CN") return QIcon(":/icons/flag_cn");
    return QIcon(":/icons/flag_us");
}

void MainWidget::navigate_to(int index)
{
    if (index < m_content_stack->count()) {
        m_content_stack->setCurrentIndex(index);
    }
    apply_theme(); // refresh active state
}

// ════════════════════════════════════════
// THEME — apply dark/light colors
// ════════════════════════════════════════
void MainWidget::apply_theme()
{
    // Lấy tất cả màu từ shared/theme/colors.json — chính xác với web
    const auto bg = m_theme->color("bg");                     // web: #fff / #181a1b
    const auto bg2 = m_theme->color("bg_secondary");          // web: #f9f9f9 / #1f2122
    const auto bg3 = m_theme->color("bg_tertiary");           // web: #f0f0f0 / #2b2d2e
    const auto bg_hover = m_theme->color("bg_hover");         // web: #f5f5f5 / #2b2d2e
    const auto text1 = m_theme->color("text_primary");        // web: #213547 / #d8d4cf
    const auto text2 = m_theme->color("text_secondary");      // web: #666 / #b0ada8
    const auto text_m = m_theme->color("text_muted");         // web: rgba(60,60,60,0.7)
    const auto text_footer = m_theme->color("text_footer");   // web: rgba(60,60,60,0.5)
    const auto text_nav = m_theme->color("text_nav");         // web: rgba(0,0,0,0.8)
    const auto logo_text = m_theme->color("logo_text");       // web: #213547
    const auto border = m_theme->color("border");             // web: #e2e2e2 / #3c3f41
    const auto border_light = m_theme->color("border_light"); // web: #eee / #2e3133
    const auto border_box = m_theme->color("border_box");     // web: #f0f0f0 / #2e3133
    const auto primary = m_theme->color("primary");           // web: #16baaa
    const auto header_bg = m_theme->color("header_bg");       // web: #fff / #1f2122
    const auto footer_bg = m_theme->color("footer_bg");       // web: #fafafa / #1a1c1d

    // ── Toolbar — web header: 60px, border-bottom: 1px solid #eee, bg: #fff ──
    m_toolbar->setStyleSheet(QString(
        "QToolBar { spacing: 0px; padding: 2px 0px; border-bottom: 1px solid %1;"
        "  background: %2; }"
        "QToolBar > QWidget { background: transparent; }"
        "QToolButton { padding: 3px 6px; border: 1px solid %3; border-right: none;"
        "  border-radius: 0px; background-color: %4; font-size: 12px; color: %5; }"
        "QToolButton:hover { background-color: %6; border-color: %7; }"
        "QToolButton::menu-indicator { image: none; }"
    ).arg(border_light, header_bg, border, bg2, text_nav, bg_hover, text2));

    // Theme toggle icon + text
    m_theme_action->setIcon(QIcon(m_theme->theme() == "dark"
        ? ":/icons/sun_theme" : ":/icons/moon_theme"));
    m_theme_action->setText(m_theme->theme() == "dark"
        ? QString::fromUtf8("Sáng") : QString::fromUtf8("Tối"));

    // Lang button icon + text
    m_lang_button->setIcon(lang_flag_icon(m_tr->locale()));
    m_lang_button->setText(m_tr->locale_label(m_tr->locale()));

    // ── Menu styling — web: font-size 14px ──
    auto menu_style = QString(
        "QMenu { background: %1; border: 1px solid %2; padding: 4px; font-size: 14px; }"
        "QMenu::item { padding: 6px 12px; color: %3; }"
        "QMenu::item:selected { background: %4; color: %5; }"
        "QMenu::separator { height: 1px; background: %2; margin: 4px 8px; }"
    ).arg(bg, border, text1, bg_hover, primary);

    m_lang_menu->setStyleSheet(menu_style);
    m_account_menu->setStyleSheet(menu_style);
    m_report_menu->setStyleSheet(menu_style);
    m_bet_order_menu->setStyleSheet(menu_style);
    m_deposit_withdraw_menu->setStyleSheet(menu_style);

    // ── Hero — web: title #213547 40px 900, tagline rgba(60,60,60,0.7) 15px ──
    m_hero_widget->setStyleSheet(QString("background: %1; border: none;").arg(bg));
    m_hero_title->setStyleSheet(QString(
        "color: %1; font-size: 40px; font-weight: 900;"
        "letter-spacing: 2px; opacity: 0.86; border: none;"
    ).arg(text1));
    m_hero_tagline->setStyleSheet(QString(
        "color: %1; font-size: 15px; border: none;"
    ).arg(text_m));

    // ── Welcome — web: font-size 13px, color #666 ──
    m_welcome_text->setStyleSheet(QString(
        "color: %1; font-size: 13px; border: none;"
    ).arg(text2));
    m_welcome_name->setStyleSheet(QString(
        "color: %1; font-size: 13px; font-weight: bold; border: none;"
    ).arg(text1));

    // ── Explore button — web: bg #16baaa, color #fff, 14px 500, height 36px, border-radius 6px ──
    m_explore_btn->setStyleSheet(QString(
        "QPushButton {"
        "  background: %1; color: #fff; border: 1px solid %1;"
        "  padding: 0 20px; height: 36px; font-size: 14px; font-weight: 500;"
        "  border-radius: 6px;"
        "}"
        "QPushButton:hover { border-radius: 10px; }"
    ).arg(primary));

    // ── Feature boxes — web: bg #f9f9f9, border #f0f0f0, border-radius 6px ──
    // ── Title: #333 15px 600, Desc: rgba(60,60,60,0.7) 12px ──
    for (int i = 0; i < m_feature_boxes.size(); ++i) {
        m_feature_boxes[i]->setStyleSheet(QString(
            "QWidget#featureBox { background: %1; border: 1px solid %2;"
            "  padding: 16px 20px; border-radius: 6px; }"
            "QWidget#featureBox:hover { border-color: %3; }"
        ).arg(bg2, border_box, primary));
        m_feature_icon_bgs[i]->setStyleSheet(QString(
            "background: %1; border: none; border-radius: 8px;"
        ).arg(bg3));
        m_feature_titles[i]->setStyleSheet(QString(
            "color: %1; font-size: 15px; font-weight: 600;"
            "line-height: 22px; border: none;"
        ).arg(text1));
        m_feature_descs[i]->setStyleSheet(QString(
            "color: %1; font-size: 12px; line-height: 20px; border: none;"
        ).arg(text_m));
    }
    m_boxes_container->setStyleSheet(QString("background: %1; border: none;").arg(bg));

    // ── Footer — web: bg #fafafa, border-top 1px solid #eee, color rgba(60,60,60,0.5) 12px ──
    m_footer->setStyleSheet(QString(
        "background: %1; border-top: 1px solid %2;"
    ).arg(footer_bg, border_light));
    m_footer_text->setStyleSheet(QString(
        "color: %1; font-size: 12px; border: none;"
    ).arg(text_footer));

    // Page background
    if (auto* home_widget = m_content_stack->widget(0)) {
        home_widget->setStyleSheet(QString("background: %1;").arg(bg));
    }

    // ── Customers page — giống hệt web customers.vue ──
    m_customers_page->setStyleSheet(QString(
        "QWidget#customersPage { background: %1; }"
    ).arg(bg2));

    m_customers_card->setStyleSheet(QString(
        "QWidget#customersCard { background: %1; border: 1px solid %2; }"
    ).arg(bg, border_box));

    m_customers_title->setStyleSheet(QString(
        "font-size: 16px; font-weight: 700; color: %1; border: none;"
    ).arg(text1));

    // Separator
    findChild<QWidget*>("fieldSeparator")->setStyleSheet(QString(
        "background: %1;"
    ).arg(border_light));

    // Search labels
    for (auto* lbl : m_search_labels) {
        lbl->setStyleSheet(QString(
            "font-size: 13px; color: %1; border: none;"
        ).arg(text2));
    }

    // Input fields
    auto input_style = QString(
        "QLineEdit, QComboBox, QDateEdit {"
        "  background: %1; color: %2; border: 1px solid %3;"
        "  padding: 4px 8px; font-size: 13px;"
        "}"
        "QLineEdit:focus, QComboBox:focus, QDateEdit:focus {"
        "  border-color: %4;"
        "}"
        "QComboBox::drop-down {"
        "  subcontrol-origin: padding; subcontrol-position: center right;"
        "  width: 20px; border-left: 1px solid %3;"
        "}"
        "QComboBox::down-arrow {"
        "  image: url(:/icons/dropdown_arrow);"
        "  width: 10px; height: 10px;"
        "}"
        "QComboBox QAbstractItemView {"
        "  background: %1; color: %2; border: 1px solid %3;"
        "  selection-background-color: %5;"
        "}"
    ).arg(bg, text1, border, primary, bg_hover);

    m_search_username->setStyleSheet(input_style);

    // Date range picker button — same border/padding as input fields
    m_date_range_picker->set_button_style(QString(
        "QPushButton { background: %1; color: %2;"
        "  border-style: solid; border-width: 1px; border-color: %3; border-radius: 0px;"
        "  padding: 4px 8px; font-size: 13px; text-align: left; }"
        "QPushButton:hover { border-color: %4; }"
    ).arg(bg, text1, border, primary));

    m_search_status->setStyleSheet(input_style);
    m_search_sort_field->setStyleSheet(input_style);
    m_search_sort_dir->setStyleSheet(input_style);

    // Buttons
    m_search_btn->setStyleSheet(QString(
        "QPushButton { background: %1; color: #fff; border: none;"
        "  padding: 0 16px; font-size: 13px; }"
        "QPushButton:hover { background: #0d8a7e; }"
    ).arg(primary));

    m_reset_btn->setStyleSheet(QString(
        "QPushButton { background: %1; color: %2; border: 1px solid %3;"
        "  padding: 0 16px; font-size: 13px; }"
        "QPushButton:hover { background: %4; }"
    ).arg(bg, text1, border, bg_hover));

    // Date range popup theme
    m_date_range_picker->apply_popup_theme(m_theme->theme() == "dark");

    // ── Table toolbar ──
    m_table_toolbar->setStyleSheet(QString(
        "QWidget#tableToolbar { background: %1; border: 1px solid %2; border-bottom: none; }"
    ).arg(bg2, border));

    auto tb_btn_style = QString(
        "QPushButton#tbBtn { background: %1; color: #fff; border: none;"
        "  padding: 0 10px; font-size: 12px; }"
        "QPushButton#tbBtn:hover { background: #0d8a7e; }"
    ).arg(primary);
    m_add_member_btn->setStyleSheet(tb_btn_style);
    m_add_agent_btn->setStyleSheet(tb_btn_style);

    auto tool_icon_style = QString(
        "QPushButton#toolIcon { background: transparent; border: 1px solid %1; }"
        "QPushButton#toolIcon:hover { background: %2; }"
    ).arg(border, bg_hover);
    for (auto* btn : m_table_toolbar->findChildren<QPushButton*>("toolIcon")) {
        btn->setStyleSheet(tool_icon_style);
    }

    // ── Table ──
    m_customers_table->setStyleSheet(QString(
        "QTableWidget { background: %1; color: %2; border: 1px solid %3;"
        "  gridline-color: %3; font-size: 13px; }"
        "QTableWidget::item { padding: 4px 8px; border: none; }"
        "QTableWidget::item:selected { background: %4; color: %2; }"
        "QHeaderView::section { background: %5; color: %2; border: none;"
        "  border-bottom: 1px solid %3; border-right: 1px solid %3;"
        "  padding: 6px 8px; font-size: 13px; font-weight: 600; }"
        "QHeaderView::section:last { border-right: none; }"
    ).arg(bg, text1, border, bg_hover, bg2));

    // Rebate button in table
    for (int r = 0; r < m_customers_table->rowCount(); ++r) {
        if (auto* w = m_customers_table->cellWidget(r, 11)) {
            w->setStyleSheet(QString(
                "QPushButton { background: %1; color: #fff; border: none;"
                "  padding: 2px 8px; font-size: 11px; }"
                "QPushButton:hover { background: #0d8a7e; }"
            ).arg(primary));
        }
    }

    // ── Pagination bar ──
    m_pagination_bar->setStyleSheet(QString(
        "QWidget#paginationBar { background: %1; border: 1px solid %2; border-top: none; }"
    ).arg(bg, border));

    auto page_btn_style = QString(
        "QPushButton#pageBtn { background: %1; color: %2; border: 1px solid %3;"
        "  font-size: 13px; padding: 0; }"
        "QPushButton#pageBtn:hover { background: %4; }"
        "QPushButton#pageBtn:disabled { color: %5; }"
    ).arg(bg, text1, border, bg_hover, text2);
    m_page_prev_btn->setStyleSheet(page_btn_style);
    m_page_next_btn->setStyleSheet(page_btn_style);

    m_page_number->setStyleSheet(QString(
        "QLabel#pageNumber { background: %1; color: #fff; border: 1px solid %1;"
        "  font-size: 13px; padding: 0; qproperty-alignment: 'AlignCenter'; }"
    ).arg(primary));

    m_page_info->setStyleSheet(QString(
        "font-size: 13px; color: %1; border: none;"
    ).arg(text2));

    m_page_size_combo->setStyleSheet(input_style);

    // ── Report / Bets / Commission pages (dùng ReportPageBuilder) ──
    ReportPageBuilder::apply_page_theme(m_lottery_report, m_theme);
    ReportPageBuilder::apply_page_theme(m_transaction_log, m_theme);
    ReportPageBuilder::apply_page_theme(m_provider_report, m_theme);
    ReportPageBuilder::apply_page_theme(m_lottery_bets, m_theme);
    ReportPageBuilder::apply_page_theme(m_provider_bets, m_theme);
    ReportPageBuilder::apply_page_theme(m_withdrawal_history, m_theme);
    ReportPageBuilder::apply_page_theme(m_deposit_history, m_theme);

    // Date range pickers cho các trang report/bets/commission
    auto date_btn_style = QString(
        "QPushButton { background: %1; color: %2;"
        "  border-style: solid; border-width: 1px; border-color: %3; border-radius: 0px;"
        "  padding: 4px 8px; font-size: 13px; text-align: left; }"
        "QPushButton:hover { border-color: %4; }"
    ).arg(bg, text1, border, primary);
    bool is_dark = m_theme->theme() == "dark";
    for (int i = 0; i < 7; ++i) {
        if (m_report_date_pickers[i]) {
            m_report_date_pickers[i]->set_button_style(date_btn_style);
            m_report_date_pickers[i]->apply_popup_theme(is_dark);
        }
    }
}

void MainWidget::on_theme_changed()
{
    apply_theme();
}

void MainWidget::on_locale_changed()
{
    // Nav actions — text cố định tiếng Việt (y hệt Cqt)
    // Không cần cập nhật vì menu text là hardcoded

    // Lang button (icon cờ + text)
    m_lang_button->setIcon(lang_flag_icon(m_tr->locale()));
    m_lang_button->setText(m_tr->locale_label(m_tr->locale()));

    // Account menu
    m_change_pwd_action->setText(m_tr->t("auth.change_password"));
    m_logout_action->setText(m_tr->t("auth.logout"));

    // Hero
    m_hero_tagline->setText(m_tr->t("home.tagline"));
    m_explore_btn->setText(m_tr->t("home.explore"));
    m_welcome_text->setText(m_tr->t("home.welcome") + ", ");

    // Feature boxes
    const QString feature_keys[] = {"go", "vue", "qt", "comp", "theme", "log"};
    for (int i = 0; i < m_feature_titles.size(); ++i) {
        m_feature_titles[i]->setText(m_tr->t("features." + feature_keys[i] + "_title"));
        m_feature_descs[i]->setText(m_tr->t("features." + feature_keys[i] + "_desc"));
    }
}

void MainWidget::on_change_password()
{
    bool ok = false;
    const auto old_pwd = QInputDialog::getText(
        this, m_tr->t("auth.change_password"),
        m_tr->t("auth.old_password") + ":",
        QLineEdit::Password, "", &ok
    );
    if (!ok || old_pwd.isEmpty()) return;

    const auto new_pwd = QInputDialog::getText(
        this, m_tr->t("auth.change_password"),
        m_tr->t("auth.new_password") + ":",
        QLineEdit::Password, "", &ok
    );
    if (!ok || new_pwd.isEmpty()) return;

    if (new_pwd.length() < 8) {
        QMessageBox::warning(this,
            QString::fromUtf8("Error"),
            m_tr->t("auth.password_min"));
        return;
    }

    const auto confirm = QInputDialog::getText(
        this, m_tr->t("auth.change_password"),
        m_tr->t("auth.confirm_new") + ":",
        QLineEdit::Password, "", &ok
    );
    if (!ok || confirm != new_pwd) {
        QMessageBox::warning(this,
            QString::fromUtf8("Error"),
            m_tr->t("auth.password_mismatch"));
        return;
    }

    m_api->change_password(old_pwd, new_pwd, [this](bool success, const QJsonObject& data) {
        if (success) {
            QMessageBox::information(this,
                QString::fromUtf8("OK"),
                m_tr->t("auth.change_success"));
        } else {
            const auto msg = data.value("message").toString(m_tr->t("auth.change_failed"));
            QMessageBox::warning(this, QString::fromUtf8("Error"), msg);
        }
    });
}

void MainWidget::on_logout()
{
    m_api->logout([this](bool /*success*/, const QJsonObject& /*data*/) {
        emit logout_requested();
    });
}

// ── Lọc cột: dialog checkbox ẩn/hiện từng cột ──
void MainWidget::on_filter_columns()
{
    QDialog dlg(this);
    dlg.setWindowTitle(QString::fromUtf8("Lọc cột"));
    dlg.setMinimumWidth(250);

    auto* layout = new QVBoxLayout(&dlg);
    QVector<QCheckBox*> checks;

    for (int i = 0; i < m_customers_table->columnCount(); ++i) {
        auto* cb = new QCheckBox(m_customers_table->horizontalHeaderItem(i)->text());
        cb->setChecked(!m_customers_table->isColumnHidden(i));
        layout->addWidget(cb);
        checks.append(cb);
    }

    auto* buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    layout->addWidget(buttons);
    connect(buttons, &QDialogButtonBox::accepted, &dlg, &QDialog::accept);
    connect(buttons, &QDialogButtonBox::rejected, &dlg, &QDialog::reject);

    if (dlg.exec() == QDialog::Accepted) {
        for (int i = 0; i < checks.size(); ++i) {
            m_customers_table->setColumnHidden(i, !checks[i]->isChecked());
        }
    }
}

// ── Xuất CSV ──
void MainWidget::on_export_csv()
{
    QString path = QFileDialog::getSaveFileName(
        this, QString::fromUtf8("Xuất file CSV"), "customers.csv",
        "CSV (*.csv);;All Files (*)");
    if (path.isEmpty()) return;

    QFile file(path);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QMessageBox::warning(this, "Error",
            QString::fromUtf8("Không thể mở file: %1").arg(path));
        return;
    }

    QTextStream out(&file);
    int cols = m_customers_table->columnCount();
    int rows = m_customers_table->rowCount();

    // Header
    QStringList header_parts;
    for (int c = 0; c < cols; ++c) {
        if (!m_customers_table->isColumnHidden(c)) {
            QString h = m_customers_table->horizontalHeaderItem(c)->text();
            h.replace("\"", "\"\"");
            header_parts << "\"" + h + "\"";
        }
    }
    out << header_parts.join(",") << "\n";

    // Data
    for (int r = 0; r < rows; ++r) {
        QStringList row_parts;
        for (int c = 0; c < cols; ++c) {
            if (m_customers_table->isColumnHidden(c)) continue;
            QString val;
            if (auto* item = m_customers_table->item(r, c)) {
                val = item->text();
            } else if (auto* w = m_customers_table->cellWidget(r, c)) {
                if (auto* btn = qobject_cast<QPushButton*>(w))
                    val = btn->text();
            }
            val.replace("\"", "\"\"");
            row_parts << "\"" + val + "\"";
        }
        out << row_parts.join(",") << "\n";
    }

    file.close();
    QMessageBox::information(this, QString::fromUtf8("Thành công"),
        QString::fromUtf8("Đã xuất file: %1").arg(path));
}

// ── In bảng ──
void MainWidget::on_print_table()
{
    QPrinter printer(QPrinter::HighResolution);
    QPrintDialog dlg(&printer, this);
    dlg.setWindowTitle(QString::fromUtf8("In bảng khách hàng"));
    if (dlg.exec() != QDialog::Accepted) return;

    int cols = m_customers_table->columnCount();
    int rows = m_customers_table->rowCount();

    // Build HTML table
    QString html = "<html><head><style>"
        "table { border-collapse: collapse; width: 100%; font-size: 12px; }"
        "th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }"
        "th { background: #f0f0f0; font-weight: bold; }"
        "</style></head><body>";
    html += QString::fromUtf8("<h3>Quản lí hội viên thuộc cấp</h3>");
    html += "<table><tr>";

    for (int c = 0; c < cols; ++c) {
        if (!m_customers_table->isColumnHidden(c)) {
            html += "<th>" + m_customers_table->horizontalHeaderItem(c)->text() + "</th>";
        }
    }
    html += "</tr>";

    for (int r = 0; r < rows; ++r) {
        html += "<tr>";
        for (int c = 0; c < cols; ++c) {
            if (m_customers_table->isColumnHidden(c)) continue;
            QString val;
            if (auto* item = m_customers_table->item(r, c))
                val = item->text();
            html += "<td>" + val + "</td>";
        }
        html += "</tr>";
    }
    html += "</table></body></html>";

    QTextDocument doc;
    doc.setHtml(html);
    doc.print(&printer);
}
