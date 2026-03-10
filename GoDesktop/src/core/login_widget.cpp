#include "core/login_widget.h"
#include "core/api_client.h"

#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QGraphicsDropShadowEffect>
#include <QFont>
#include <QPixmap>
#include <QAction>
#include <QPainter>
#include <QTimer>

LoginWidget::LoginWidget(ApiClient* api, QWidget* parent)
    : QWidget(parent)
    , m_api(api)
    , m_loading(false)
{
    setup_ui();
}

void LoginWidget::setup_ui()
{
    // ── MaxHub Dark Theme Colors (matching web) ──
    const QString bg_deep     = "#060B18";
    const QString bg_panel    = "#0A1128";
    const QString bg_input    = "#0B1226";
    const QString border_sub  = "rgba(255,255,255,0.04)";
    const QString border_in   = "rgba(255,255,255,0.08)";
    const QString cyan        = "#00BCD4";
    const QString cyan_dark   = "#0097A7";
    const QString blue        = "#1565C0";
    const QString orange      = "#F57C00";
    const QString text_pri    = "#EDF1F9";
    const QString text_sec    = "#94A3BE";
    const QString text_muted  = "#5A6E8A";
    const QString text_bright = "#FFFFFF";
    const QString err_color   = "#F87171";

    setStyleSheet(QString("LoginWidget { background: %1; }").arg(bg_deep));

    auto* outer = new QHBoxLayout(this);
    outer->setAlignment(Qt::AlignCenter);
    outer->setContentsMargins(0, 0, 0, 0);

    // ── Main container ──
    auto* auth_container = new QWidget;
    auth_container->setFixedSize(900, 540);
    auth_container->setStyleSheet(QString("background: transparent; border: none;"));

    auto* container_layout = new QHBoxLayout(auth_container);
    container_layout->setContentsMargins(0, 0, 0, 0);
    container_layout->setSpacing(0);

    // ════════════════════════════════════════
    // BÊN TRÁI — Dark brand panel (45%)
    // ════════════════════════════════════════
    auto* left = new QWidget;
    left->setFixedWidth(405);
    left->setStyleSheet(QString(
        "background: %1;"
        "border: none;"
    ).arg(bg_panel));

    auto* left_layout = new QVBoxLayout(left);
    left_layout->setAlignment(Qt::AlignCenter);
    left_layout->setContentsMargins(40, 48, 40, 48);
    left_layout->setSpacing(0);

    left_layout->addStretch();

    // Logo PNG
    auto* logo_label = new QLabel;
    QPixmap logo_pix(":/icons/app");
    logo_label->setPixmap(logo_pix.scaled(260, 130, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    logo_label->setAlignment(Qt::AlignCenter);
    logo_label->setStyleSheet("background: transparent; border: none;");
    left_layout->addWidget(logo_label);
    left_layout->addSpacing(32);

    // Heading
    auto* heading = new QLabel(QString::fromUtf8(
        "Quản lý thông minh,\nKết nối mọi thứ"
    ));
    heading->setStyleSheet(QString(
        "color: %1; font-size: 20px; font-weight: bold; "
        "background: transparent; border: none; line-height: 1.4;"
    ).arg(text_bright));
    heading->setAlignment(Qt::AlignCenter);
    heading->setWordWrap(true);
    left_layout->addWidget(heading);
    left_layout->addSpacing(12);

    // Description
    auto* desc = new QLabel(QString::fromUtf8(
        "Nền tảng quản lý tập trung giúp bạn kiểm soát,\ntự động hóa và tối ưu hiệu suất làm việc."
    ));
    desc->setStyleSheet(QString(
        "color: %1; font-size: 12px; "
        "background: transparent; border: none;"
    ).arg(text_sec));
    desc->setAlignment(Qt::AlignCenter);
    desc->setWordWrap(true);
    left_layout->addWidget(desc);
    left_layout->addSpacing(28);

    // Feature pills
    const QStringList pill_texts = {"Realtime Sync", "AI Powered", "Enterprise"};
    const QStringList pill_dots = {cyan, orange, "#29B6F6"};

    auto* pills_container = new QWidget;
    pills_container->setStyleSheet("background: transparent; border: none;");
    auto* pills_layout = new QHBoxLayout(pills_container);
    pills_layout->setAlignment(Qt::AlignCenter);
    pills_layout->setContentsMargins(0, 0, 0, 0);
    pills_layout->setSpacing(8);

    for (int i = 0; i < pill_texts.size(); ++i) {
        auto* pill = new QLabel(
            QString("<span style='color:%1;'>●</span> %2")
                .arg(pill_dots[i], pill_texts[i])
        );
        pill->setTextFormat(Qt::RichText);
        pill->setStyleSheet(QString(
            "background: rgba(255,255,255,0.05);"
            "color: %1;"
            "border: 1px solid rgba(255,255,255,0.08);"
            "border-radius: 14px;"
            "padding: 5px 14px;"
            "font-size: 11px;"
        ).arg(text_pri));
        pills_layout->addWidget(pill);
    }
    left_layout->addWidget(pills_container);

    left_layout->addStretch();

    container_layout->addWidget(left);

    // ════════════════════════════════════════
    // BÊN PHẢI — Form panel on dark bg
    // ════════════════════════════════════════
    auto* right = new QWidget;
    right->setStyleSheet(QString("background: %1; border: none;").arg(bg_deep));

    auto* right_outer = new QHBoxLayout(right);
    right_outer->setAlignment(Qt::AlignCenter);
    right_outer->setContentsMargins(32, 24, 32, 24);

    // ── Floating card ──
    auto* card = new QWidget;
    card->setFixedWidth(380);
    card->setStyleSheet(QString(
        "background: %1;"
        "border: 1px solid %2;"
    ).arg(bg_panel, border_sub));

    auto* card_shadow = new QGraphicsDropShadowEffect;
    card_shadow->setBlurRadius(60);
    card_shadow->setOffset(0, 8);
    card_shadow->setColor(QColor(0, 0, 0, 80));
    card->setGraphicsEffect(card_shadow);

    auto* form_layout = new QVBoxLayout(card);
    form_layout->setContentsMargins(28, 28, 28, 28);
    form_layout->setSpacing(0);

    // ── Nút X đóng ──
    auto* close_row = new QWidget;
    close_row->setStyleSheet("background: transparent; border: none;");
    auto* close_rl = new QHBoxLayout(close_row);
    close_rl->setContentsMargins(0, 0, 0, 0);
    close_rl->addStretch();
    auto* close_btn = new QPushButton(QString::fromUtf8("\u2715"));
    close_btn->setFixedSize(28, 28);
    close_btn->setCursor(Qt::PointingHandCursor);
    close_btn->setStyleSheet(QString(
        "QPushButton {"
        "  background: transparent; color: %1; border: none;"
        "  font-size: 14px; font-weight: bold;"
        "}"
        "QPushButton:hover { color: %2; background: rgba(248,113,113,0.1); }"
    ).arg(text_muted, err_color));
    connect(close_btn, &QPushButton::clicked, this, [this]() {
        window()->close();
    });
    close_rl->addWidget(close_btn);
    form_layout->addWidget(close_row);
    form_layout->addSpacing(4);

    // Title
    auto* title = new QLabel(QString::fromUtf8("Chào mừng trở lại"));
    title->setStyleSheet(QString(
        "color: %1; font-size: 22px; font-weight: bold; "
        "background: transparent; border: none; letter-spacing: -0.5px;"
    ).arg(text_bright));
    form_layout->addWidget(title);
    form_layout->addSpacing(4);

    // Subtitle
    auto* subtitle = new QLabel(QString::fromUtf8(
        "Đăng nhập để tiếp tục quản lý dự án của bạn"
    ));
    subtitle->setStyleSheet(QString(
        "color: %1; font-size: 12px; background: transparent; border: none;"
    ).arg(text_sec));
    form_layout->addWidget(subtitle);
    form_layout->addSpacing(20);

    // ── Input styles (dark theme) ──
    const QString input_style = QString(
        "QLineEdit {"
        "  border: 1px solid %1;"
        "  padding: 10px 12px 10px 40px;"
        "  font-size: 13px;"
        "  background: %2;"
        "  color: %3;"
        "}"
        "QLineEdit:focus {"
        "  border: 1px solid %4;"
        "}"
        "QLineEdit::placeholder {"
        "  color: %5;"
        "}"
    ).arg(border_in, bg_input, text_pri, cyan, text_muted);

    const QString icon_style = QString(
        "color: %1; background: transparent; border: none;"
    ).arg(text_muted);

    // ── Username label + input ──
    auto* user_lbl = new QLabel(QString::fromUtf8("Tên tài khoản"));
    user_lbl->setStyleSheet(QString(
        "color: %1; font-size: 11px; font-weight: bold; "
        "background: transparent; border: none;"
    ).arg(text_sec));
    form_layout->addWidget(user_lbl);
    form_layout->addSpacing(4);

    m_username_input = new QLineEdit;
    m_username_input->setPlaceholderText(QString::fromUtf8("Nhập tên tài khoản"));
    m_username_input->setStyleSheet(input_style);
    m_username_input->setFixedHeight(42);

    // SVG-style icon overlay
    auto* user_icon = new QLabel(m_username_input);
    user_icon->setText(QString::fromUtf8("👤"));
    user_icon->setFixedSize(20, 20);
    user_icon->move(12, 11);
    user_icon->setStyleSheet(icon_style);

    connect(m_username_input, &QLineEdit::returnPressed, this, [this]() {
        m_password_input->setFocus();
    });
    form_layout->addWidget(m_username_input);
    form_layout->addSpacing(12);

    // ── Password label + input ──
    auto* pwd_lbl = new QLabel(QString::fromUtf8("Mật khẩu"));
    pwd_lbl->setStyleSheet(QString(
        "color: %1; font-size: 11px; font-weight: bold; "
        "background: transparent; border: none;"
    ).arg(text_sec));
    form_layout->addWidget(pwd_lbl);
    form_layout->addSpacing(4);

    m_password_input = new QLineEdit;
    m_password_input->setPlaceholderText(QString::fromUtf8("••••••••"));
    m_password_input->setEchoMode(QLineEdit::Password);
    m_password_input->setStyleSheet(input_style);
    m_password_input->setFixedHeight(42);

    auto* pwd_icon = new QLabel(m_password_input);
    pwd_icon->setText(QString::fromUtf8("🔒"));
    pwd_icon->setFixedSize(20, 20);
    pwd_icon->move(12, 11);
    pwd_icon->setStyleSheet(icon_style);

    connect(m_password_input, &QLineEdit::returnPressed, this, &LoginWidget::on_submit);
    form_layout->addWidget(m_password_input);
    form_layout->addSpacing(12);

    // Error box (dark theme)
    m_error_box = new QWidget;
    m_error_box->setStyleSheet(QString(
        "background: rgba(248,113,113,0.08);"
        "border: 1px solid rgba(248,113,113,0.2);"
    ));
    m_error_box->setVisible(false);

    auto* err_layout = new QHBoxLayout(m_error_box);
    err_layout->setContentsMargins(10, 7, 10, 7);
    err_layout->setSpacing(6);

    m_error_label = new QLabel;
    m_error_label->setStyleSheet(QString(
        "color: %1; font-size: 12px; background: transparent; border: none;"
    ).arg(err_color));
    m_error_label->setWordWrap(true);
    err_layout->addWidget(m_error_label, 1);

    form_layout->addWidget(m_error_box);
    form_layout->addSpacing(12);

    // ── Button row: gradient Submit + Cancel ──
    auto* btn_row = new QWidget;
    btn_row->setStyleSheet("background: transparent; border: none;");
    auto* btn_layout = new QHBoxLayout(btn_row);
    btn_layout->setContentsMargins(0, 0, 0, 0);
    btn_layout->setSpacing(10);

    // Gradient primary button (cyan → blue → orange)
    m_submit_btn = new QPushButton(QString::fromUtf8("Đăng nhập"));
    m_submit_btn->setFixedHeight(42);
    m_submit_btn->setCursor(Qt::PointingHandCursor);
    m_submit_btn->setStyleSheet(QString(
        "QPushButton {"
        "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
        "    stop:0 %1, stop:0.5 %2, stop:1 %3);"
        "  color: #fff;"
        "  border: none;"
        "  font-size: 14px;"
        "  font-weight: bold;"
        "  letter-spacing: 0.5px;"
        "}"
        "QPushButton:hover {"
        "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
        "    stop:0 %4, stop:0.5 %2, stop:1 %3);"
        "}"
        "QPushButton:pressed {"
        "  background: %2;"
        "}"
        "QPushButton:disabled {"
        "  background: rgba(0,188,212,0.4);"
        "  color: rgba(255,255,255,0.6);"
        "}"
    ).arg(cyan, blue, orange, cyan_dark));
    connect(m_submit_btn, &QPushButton::clicked, this, &LoginWidget::on_submit);
    btn_layout->addWidget(m_submit_btn, 1);

    // Cancel button (red border, dark bg)
    auto* cancel_btn = new QPushButton(QString::fromUtf8("Huỷ"));
    cancel_btn->setFixedHeight(42);
    cancel_btn->setCursor(Qt::PointingHandCursor);
    cancel_btn->setStyleSheet(QString(
        "QPushButton {"
        "  background: transparent;"
        "  color: %1;"
        "  border: 1px solid rgba(248,113,113,0.3);"
        "  font-size: 14px;"
        "  font-weight: bold;"
        "}"
        "QPushButton:hover {"
        "  background: rgba(248,113,113,0.1);"
        "  border-color: %1;"
        "}"
        "QPushButton:pressed {"
        "  background: rgba(248,113,113,0.2);"
        "}"
    ).arg(err_color));
    connect(cancel_btn, &QPushButton::clicked, this, [this]() {
        m_username_input->clear();
        m_password_input->clear();
        clear_error();
        window()->close();
    });
    btn_layout->addWidget(cancel_btn, 1);

    form_layout->addWidget(btn_row);
    form_layout->addSpacing(16);

    // ── Social divider ──
    auto* divider_row = new QWidget;
    divider_row->setStyleSheet("background: transparent; border: none;");
    auto* divider_layout = new QHBoxLayout(divider_row);
    divider_layout->setContentsMargins(0, 0, 0, 0);
    divider_layout->setSpacing(10);

    auto make_line = [&]() {
        auto* line = new QWidget;
        line->setFixedHeight(1);
        line->setStyleSheet(QString("background: %1; border: none;").arg(border_in));
        return line;
    };

    divider_layout->addWidget(make_line(), 1);
    auto* or_label = new QLabel(QString::fromUtf8("Hoặc tiếp tục với"));
    or_label->setStyleSheet(QString(
        "color: %1; font-size: 10px; background: transparent; border: none;"
    ).arg(text_muted));
    divider_layout->addWidget(or_label);
    divider_layout->addWidget(make_line(), 1);

    form_layout->addWidget(divider_row);
    form_layout->addSpacing(12);

    // ── Social buttons ──
    auto* social_row = new QWidget;
    social_row->setStyleSheet("background: transparent; border: none;");
    auto* social_layout = new QHBoxLayout(social_row);
    social_layout->setContentsMargins(0, 0, 0, 0);
    social_layout->setSpacing(10);

    const QString social_style = QString(
        "QPushButton {"
        "  background: rgba(255,255,255,0.03);"
        "  color: %1;"
        "  border: 1px solid %2;"
        "  font-size: 12px;"
        "  font-weight: 500;"
        "  padding: 8px 0;"
        "}"
        "QPushButton:hover {"
        "  background: rgba(255,255,255,0.06);"
        "  border-color: %3;"
        "  color: %4;"
        "}"
    ).arg(text_sec, border_in, cyan, text_pri);

    auto* google_btn = new QPushButton("Google");
    google_btn->setFixedHeight(38);
    google_btn->setCursor(Qt::PointingHandCursor);
    google_btn->setStyleSheet(social_style);
    social_layout->addWidget(google_btn, 1);

    auto* github_btn = new QPushButton("GitHub");
    github_btn->setFixedHeight(38);
    github_btn->setCursor(Qt::PointingHandCursor);
    github_btn->setStyleSheet(social_style);
    social_layout->addWidget(github_btn, 1);

    form_layout->addWidget(social_row);
    form_layout->addSpacing(16);

    // Footer
    auto* footer = new QWidget;
    footer->setStyleSheet("background: transparent; border: none;");
    auto* footer_layout = new QHBoxLayout(footer);
    footer_layout->setAlignment(Qt::AlignCenter);
    footer_layout->setContentsMargins(0, 0, 0, 0);
    footer_layout->setSpacing(4);

    auto* footer_text = new QLabel(QString::fromUtf8("Chưa có tài khoản?"));
    footer_text->setStyleSheet(QString(
        "color: %1; font-size: 12px; background: transparent; border: none;"
    ).arg(text_muted));
    footer_layout->addWidget(footer_text);

    auto* register_link = new QPushButton(QString::fromUtf8("Đăng ký ngay"));
    register_link->setFlat(true);
    register_link->setCursor(Qt::PointingHandCursor);
    register_link->setStyleSheet(QString(
        "QPushButton { color: %1; font-size: 12px; font-weight: 600; "
        "border: none; background: transparent; padding: 0; }"
        "QPushButton:hover { color: %2; }"
    ).arg(cyan, "#00E5FF"));
    connect(register_link, &QPushButton::clicked, this, &LoginWidget::switch_to_register);
    footer_layout->addWidget(register_link);

    form_layout->addWidget(footer);

    right_outer->addWidget(card);
    container_layout->addWidget(right, 1);

    outer->addWidget(auth_container);
}

void LoginWidget::on_submit()
{
    if (m_loading) {
        return;
    }

    const auto username = m_username_input->text().trimmed();
    const auto password = m_password_input->text();

    if (username.isEmpty() || password.isEmpty()) {
        set_error(QString::fromUtf8("Vui lòng nhập đầy đủ thông tin"));
        return;
    }

    m_loading = true;
    clear_error();
    m_submit_btn->setEnabled(false);
    m_submit_btn->setText(QString::fromUtf8("Đang đăng nhập..."));

    m_api->login(username, password, [this](bool success, const QJsonObject& data) {
        m_loading = false;
        m_submit_btn->setEnabled(true);
        m_submit_btn->setText(QString::fromUtf8("Đăng nhập"));

        if (success && data.contains("token")) {
            m_api->set_token(data["token"].toString());
            if (data.contains("user")) {
                m_api->set_username(data["user"].toObject().value("username").toString());
            }
            emit login_success();
        } else {
            const auto error = data.value("message").toString(
                QString::fromUtf8("Đăng nhập thất bại")
            );
            set_error(error);
        }
    });
}

void LoginWidget::set_error(const QString& msg)
{
    m_error_label->setText(msg);
    m_error_box->setVisible(true);
}

void LoginWidget::clear_error()
{
    m_error_box->setVisible(false);
    m_error_label->clear();
}
