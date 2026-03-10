#include "core/auth_widget.h"
#include "core/api_client.h"

#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QFont>
#include <QPixmap>
#include <QMap>
#include <QRegularExpression>
#include <QJsonObject>

// ═══════════════════════════════════════════════
// i18n translations
// ═══════════════════════════════════════════════
static const QMap<QString, QMap<QString, QString>> I18N = {
    {"vi", {
        {"brand_tagline", QString::fromUtf8("Quản lý thông minh,\nKết nối mọi thứ")},
        {"brand_desc", QString::fromUtf8("Nền tảng quản lý tập trung giúp bạn kiểm soát,\ntự động hóa và tối ưu hiệu suất làm việc.")},
        {"tab_login", QString::fromUtf8("Đăng nhập")},
        {"tab_register", QString::fromUtf8("Đăng ký")},
        {"login_title", QString::fromUtf8("Chào mừng trở lại")},
        {"login_desc", QString::fromUtf8("Đăng nhập để tiếp tục quản lý dự án của bạn")},
        {"register_title", QString::fromUtf8("Tạo tài khoản")},
        {"register_desc", QString::fromUtf8("Đăng ký để bắt đầu sử dụng MaxHub")},
        {"username", QString::fromUtf8("Tên tài khoản")},
        {"username_ph", QString::fromUtf8("Nhập tên tài khoản")},
        {"password", QString::fromUtf8("Mật khẩu")},
        {"password_ph", QString::fromUtf8("Tối thiểu 8 ký tự")},
        {"confirm", QString::fromUtf8("Xác nhận mật khẩu")},
        {"confirm_ph", QString::fromUtf8("Nhập lại mật khẩu")},
        {"remember", QString::fromUtf8("Ghi nhớ đăng nhập")},
        {"btn_login", QString::fromUtf8("Đăng nhập")},
        {"btn_register", QString::fromUtf8("Đăng ký")},
        {"btn_cancel", QString::fromUtf8("Huỷ")},
        {"or_continue", QString::fromUtf8("Hoặc tiếp tục với")},
        {"no_account", QString::fromUtf8("Chưa có tài khoản?")},
        {"has_account", QString::fromUtf8("Đã có tài khoản?")},
        {"register_now", QString::fromUtf8("Đăng ký ngay")},
        {"login_now", QString::fromUtf8("Đăng nhập")},
        {"agree_terms", QString::fromUtf8("Tôi đồng ý với Điều khoản và Chính sách bảo mật")},
        {"strength_weak", QString::fromUtf8("Yếu")},
        {"strength_fair", QString::fromUtf8("Trung bình")},
        {"strength_good", QString::fromUtf8("Tốt")},
        {"strength_strong", QString::fromUtf8("Mạnh")},
        {"err_required", QString::fromUtf8("Vui lòng nhập đầy đủ thông tin")},
        {"err_min_pass", QString::fromUtf8("Mật khẩu phải có tối thiểu 8 ký tự")},
        {"err_confirm", QString::fromUtf8("Mật khẩu xác nhận không khớp")},
        {"err_terms", QString::fromUtf8("Vui lòng đồng ý với điều khoản sử dụng")},
        {"err_login", QString::fromUtf8("Đăng nhập thất bại")},
        {"err_register", QString::fromUtf8("Đăng ký thất bại")},
        {"loading_login", QString::fromUtf8("Đang đăng nhập...")},
        {"loading_register", QString::fromUtf8("Đang đăng ký...")},
        {"terms_title", QString::fromUtf8("Điều khoản sử dụng")},
        {"privacy_title", QString::fromUtf8("Chính sách bảo mật")},
    }},
    {"en", {
        {"brand_tagline", "Smart Management,\nConnect Everything"},
        {"brand_desc", "A centralized management platform to help you\ncontrol, automate, and optimize your workflow."},
        {"tab_login", "Login"},
        {"tab_register", "Register"},
        {"login_title", "Welcome Back"},
        {"login_desc", "Sign in to continue managing your projects"},
        {"register_title", "Create Account"},
        {"register_desc", "Register to start using MaxHub"},
        {"username", "Username"},
        {"username_ph", "Enter username"},
        {"password", "Password"},
        {"password_ph", "Minimum 8 characters"},
        {"confirm", "Confirm Password"},
        {"confirm_ph", "Re-enter password"},
        {"remember", "Remember me"},
        {"btn_login", "Sign In"},
        {"btn_register", "Register"},
        {"btn_cancel", "Cancel"},
        {"or_continue", "Or continue with"},
        {"no_account", "Don't have an account?"},
        {"has_account", "Already have an account?"},
        {"register_now", "Register now"},
        {"login_now", "Sign In"},
        {"agree_terms", "I agree to the Terms of Service and Privacy Policy"},
        {"strength_weak", "Weak"},
        {"strength_fair", "Fair"},
        {"strength_good", "Good"},
        {"strength_strong", "Strong"},
        {"err_required", "Please fill in all fields"},
        {"err_min_pass", "Password must be at least 8 characters"},
        {"err_confirm", "Passwords do not match"},
        {"err_terms", "Please agree to the terms of service"},
        {"err_login", "Login failed"},
        {"err_register", "Registration failed"},
        {"loading_login", "Signing in..."},
        {"loading_register", "Registering..."},
        {"terms_title", "Terms of Service"},
        {"privacy_title", "Privacy Policy"},
    }},
    {"zh", {
        {"brand_tagline", QString::fromUtf8("智能管理,\n连接一切")},
        {"brand_desc", QString::fromUtf8("一个集中管理平台，帮助您控制、\n自动化和优化工作流程。")},
        {"tab_login", QString::fromUtf8("登录")},
        {"tab_register", QString::fromUtf8("注册")},
        {"login_title", QString::fromUtf8("欢迎回来")},
        {"login_desc", QString::fromUtf8("登录以继续管理您的项目")},
        {"register_title", QString::fromUtf8("创建账号")},
        {"register_desc", QString::fromUtf8("注册以开始使用 MaxHub")},
        {"username", QString::fromUtf8("用户名")},
        {"username_ph", QString::fromUtf8("输入用户名")},
        {"password", QString::fromUtf8("密码")},
        {"password_ph", QString::fromUtf8("最少8个字符")},
        {"confirm", QString::fromUtf8("确认密码")},
        {"confirm_ph", QString::fromUtf8("再次输入密码")},
        {"remember", QString::fromUtf8("记住登录")},
        {"btn_login", QString::fromUtf8("登录")},
        {"btn_register", QString::fromUtf8("注册")},
        {"btn_cancel", QString::fromUtf8("取消")},
        {"or_continue", QString::fromUtf8("或者通过以下方式继续")},
        {"no_account", QString::fromUtf8("没有账号？")},
        {"has_account", QString::fromUtf8("已有账号？")},
        {"register_now", QString::fromUtf8("立即注册")},
        {"login_now", QString::fromUtf8("登录")},
        {"agree_terms", QString::fromUtf8("我同意服务条款和隐私政策")},
        {"strength_weak", QString::fromUtf8("弱")},
        {"strength_fair", QString::fromUtf8("一般")},
        {"strength_good", QString::fromUtf8("良好")},
        {"strength_strong", QString::fromUtf8("强")},
        {"err_required", QString::fromUtf8("请填写所有字段")},
        {"err_min_pass", QString::fromUtf8("密码至少需要8个字符")},
        {"err_confirm", QString::fromUtf8("两次密码不一致")},
        {"err_terms", QString::fromUtf8("请同意服务条款")},
        {"err_login", QString::fromUtf8("登录失败")},
        {"err_register", QString::fromUtf8("注册失败")},
        {"loading_login", QString::fromUtf8("正在登录...")},
        {"loading_register", QString::fromUtf8("正在注册...")},
        {"terms_title", QString::fromUtf8("服务条款")},
        {"privacy_title", QString::fromUtf8("隐私政策")},
    }},
};

QString AuthWidget::t(const QString& key) const
{
    if (I18N.contains(m_lang) && I18N[m_lang].contains(key))
        return I18N[m_lang][key];
    return I18N["vi"][key];
}

AuthWidget::AuthWidget(ApiClient* api, QWidget* parent)
    : QWidget(parent)
    , m_api(api)
    , m_dark(true)
    , m_lang("vi")
    , m_active_tab(0)
    , m_password_strength(0)
    , m_loading(false)
{
    setup_ui();
    apply_theme();
}

void AuthWidget::show_login_tab()  { switch_tab(0); }
void AuthWidget::show_register_tab() { switch_tab(1); }

// ═══════════════════════════════════════════════
// BUILD UI
// ═══════════════════════════════════════════════
void AuthWidget::setup_ui()
{
    auto* outer = new QHBoxLayout(this);
    outer->setContentsMargins(0, 0, 0, 0);
    outer->setSpacing(0);

    m_root = new QWidget;

    auto* root_layout = new QHBoxLayout(m_root);
    root_layout->setContentsMargins(0, 0, 0, 0);
    root_layout->setSpacing(0);

    // ════════════════════════════════════════
    // LEFT PANEL — Brand (50%)
    // ════════════════════════════════════════
    m_left_panel = new QWidget;

    auto* left_layout = new QVBoxLayout(m_left_panel);
    left_layout->setAlignment(Qt::AlignCenter);
    left_layout->setContentsMargins(40, 48, 40, 48);
    left_layout->setSpacing(0);

    left_layout->addStretch();

    // Logo
    m_logo_label = new QLabel;
    QPixmap logo_pix(":/icons/app");
    m_logo_label->setPixmap(logo_pix.scaled(260, 130, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    m_logo_label->setAlignment(Qt::AlignCenter);
    m_logo_label->setStyleSheet("background: transparent; border: none;");
    left_layout->addWidget(m_logo_label);
    left_layout->addSpacing(28);

    // Heading
    m_heading = new QLabel;
    m_heading->setAlignment(Qt::AlignCenter);
    m_heading->setWordWrap(true);
    m_heading->setStyleSheet("background: transparent; border: none;");
    left_layout->addWidget(m_heading);
    left_layout->addSpacing(12);

    // Description
    m_desc = new QLabel;
    m_desc->setAlignment(Qt::AlignCenter);
    m_desc->setWordWrap(true);
    m_desc->setStyleSheet("background: transparent; border: none;");
    left_layout->addWidget(m_desc);
    left_layout->addSpacing(24);

    // Feature pills
    const QStringList pill_texts = {"Realtime Sync", "AI Powered", "Enterprise"};
    auto* pills_container = new QWidget;
    pills_container->setStyleSheet("background: transparent; border: none;");
    auto* pills_layout = new QHBoxLayout(pills_container);
    pills_layout->setAlignment(Qt::AlignCenter);
    pills_layout->setContentsMargins(0, 0, 0, 0);
    pills_layout->setSpacing(8);

    const QStringList pill_dot_colors = {"#00BCD4", "#F57C00", "#29B6F6"};
    for (int i = 0; i < pill_texts.size(); ++i) {
        auto* pill = new QLabel(
            QString("<span style='color:%1;'>\u25CF</span> %2")
                .arg(pill_dot_colors[i], pill_texts[i])
        );
        pill->setTextFormat(Qt::RichText);
        m_pills.append(pill);
        pills_layout->addWidget(pill);
    }
    left_layout->addWidget(pills_container);
    left_layout->addStretch();

    root_layout->addWidget(m_left_panel, 1);

    // ════════════════════════════════════════
    // RIGHT PANEL — Forms (50%, no card, flush to left)
    // ════════════════════════════════════════
    m_right_panel = new QWidget;
    m_card = m_right_panel; // alias — no separate card widget

    auto* card_layout = new QVBoxLayout(m_right_panel);
    card_layout->setContentsMargins(24, 16, 24, 16);
    card_layout->setSpacing(0);

    // ── Top bar: close + theme + lang ──
    auto* top_bar = new QWidget;
    top_bar->setStyleSheet("background: transparent; border: none;");
    auto* top_layout = new QHBoxLayout(top_bar);
    top_layout->setContentsMargins(0, 0, 0, 0);
    top_layout->setSpacing(6);

    // Language buttons
    const QStringList lang_codes = {"vi", "en", "zh"};
    const QStringList lang_labels = {"VN", "EN", "CN"};
    for (int i = 0; i < lang_codes.size(); ++i) {
        auto* btn = new QPushButton(lang_labels[i]);
        btn->setFixedSize(32, 24);
        btn->setCursor(Qt::PointingHandCursor);
        m_lang_btns.append(btn);
        connect(btn, &QPushButton::clicked, this, [this, i, lang_codes]() {
            m_lang = lang_codes[i];
            // Update all text
            m_heading->setText(t("brand_tagline"));
            m_desc->setText(t("brand_desc"));
            m_tab_login_btn->setText(t("tab_login"));
            m_tab_register_btn->setText(t("tab_register"));
            m_login_title->setText(t("login_title"));
            m_login_subtitle->setText(t("login_desc"));
            m_login_user_lbl->setText(t("username"));
            m_login_user->setPlaceholderText(t("username_ph"));
            m_login_pass_lbl->setText(t("password"));
            m_login_submit->setText(t("btn_login"));
            m_login_remember_lbl->setText(t("remember"));
            m_reg_title->setText(t("register_title"));
            m_reg_subtitle->setText(t("register_desc"));
            m_reg_user_lbl->setText(t("username"));
            m_reg_user->setPlaceholderText(t("username_ph"));
            m_reg_pass_lbl->setText(t("password"));
            m_reg_pass->setPlaceholderText(t("password_ph"));
            m_reg_confirm_lbl->setText(t("confirm"));
            m_reg_confirm->setPlaceholderText(t("confirm_ph"));
            m_reg_submit->setText(t("btn_register"));
            m_reg_terms_lbl->setText(t("agree_terms"));
            m_or_label->setText(t("or_continue"));
            m_cancel_btn->setText(t("btn_cancel"));
            if (m_active_tab == 0) {
                m_footer_text->setText(t("no_account"));
                m_footer_link->setText(t("register_now"));
            } else {
                m_footer_text->setText(t("has_account"));
                m_footer_link->setText(t("login_now"));
            }
            apply_theme(); // re-apply for active lang btn
        });
        top_layout->addWidget(btn);
    }

    top_layout->addStretch();

    // Theme toggle
    m_theme_toggle = new QPushButton;
    m_theme_toggle->setFixedSize(28, 28);
    m_theme_toggle->setCursor(Qt::PointingHandCursor);
    connect(m_theme_toggle, &QPushButton::clicked, this, &AuthWidget::toggle_theme);
    top_layout->addWidget(m_theme_toggle);

    // Close
    m_close_btn = new QPushButton(QString::fromUtf8("\u2715"));
    m_close_btn->setFixedSize(28, 28);
    m_close_btn->setCursor(Qt::PointingHandCursor);
    connect(m_close_btn, &QPushButton::clicked, this, [this]() { window()->close(); });
    top_layout->addWidget(m_close_btn);

    card_layout->addWidget(top_bar);
    card_layout->addSpacing(4);

    // ── Tab Switcher ──
    auto* tab_row = new QWidget;
    tab_row->setStyleSheet("background: transparent; border: none;");
    tab_row->setFixedHeight(32);
    auto* tab_layout = new QHBoxLayout(tab_row);
    tab_layout->setContentsMargins(0, 0, 0, 0);
    tab_layout->setSpacing(0);

    m_tab_login_btn = new QPushButton(t("tab_login"));
    m_tab_login_btn->setFixedHeight(30);
    m_tab_login_btn->setCursor(Qt::PointingHandCursor);
    connect(m_tab_login_btn, &QPushButton::clicked, this, [this]() { switch_tab(0); });
    tab_layout->addWidget(m_tab_login_btn, 1);

    m_tab_register_btn = new QPushButton(t("tab_register"));
    m_tab_register_btn->setFixedHeight(30);
    m_tab_register_btn->setCursor(Qt::PointingHandCursor);
    connect(m_tab_register_btn, &QPushButton::clicked, this, [this]() { switch_tab(1); });
    tab_layout->addWidget(m_tab_register_btn, 1);

    card_layout->addWidget(tab_row);
    card_layout->addSpacing(10);

    // ── Form Stack ──
    m_form_stack = new QStackedWidget;
    m_form_stack->setStyleSheet("background: transparent; border: none;");

    // ═══ LOGIN PAGE ═══
    m_login_page = new QWidget;
    m_login_page->setStyleSheet("background: transparent; border: none;");
    auto* lf = new QVBoxLayout(m_login_page);
    lf->setContentsMargins(0, 0, 0, 0);
    lf->setSpacing(0);

    m_login_title = new QLabel(t("login_title"));
    m_login_title->setStyleSheet("background: transparent; border: none;");
    lf->addWidget(m_login_title);
    lf->addSpacing(2);

    m_login_subtitle = new QLabel(t("login_desc"));
    m_login_subtitle->setStyleSheet("background: transparent; border: none;");
    lf->addWidget(m_login_subtitle);
    lf->addSpacing(10);

    m_login_user_lbl = new QLabel(t("username"));
    m_login_user_lbl->setStyleSheet("background: transparent; border: none;");
    lf->addWidget(m_login_user_lbl);
    lf->addSpacing(3);

    m_login_user = new QLineEdit;
    m_login_user->setPlaceholderText(t("username_ph"));
    m_login_user->setFixedHeight(32);
    connect(m_login_user, &QLineEdit::returnPressed, this, [this]() { m_login_pass->setFocus(); });
    lf->addWidget(m_login_user);
    lf->addSpacing(8);

    m_login_pass_lbl = new QLabel(t("password"));
    m_login_pass_lbl->setStyleSheet("background: transparent; border: none;");
    lf->addWidget(m_login_pass_lbl);
    lf->addSpacing(3);

    m_login_pass = new QLineEdit;
    m_login_pass->setPlaceholderText(QString::fromUtf8("••••••••"));
    m_login_pass->setEchoMode(QLineEdit::Password);
    m_login_pass->setFixedHeight(32);
    connect(m_login_pass, &QLineEdit::returnPressed, this, &AuthWidget::on_login_submit);
    lf->addWidget(m_login_pass);
    lf->addSpacing(6);

    // Remember me
    m_login_remember_lbl = new QLabel(t("remember"));
    m_login_remember_lbl->setStyleSheet("background: transparent; border: none;");
    lf->addWidget(m_login_remember_lbl);
    lf->addSpacing(6);

    m_form_stack->addWidget(m_login_page);

    // ═══ REGISTER PAGE ═══
    m_register_page = new QWidget;
    m_register_page->setStyleSheet("background: transparent; border: none;");
    auto* rf = new QVBoxLayout(m_register_page);
    rf->setContentsMargins(0, 0, 0, 0);
    rf->setSpacing(0);

    m_reg_title = new QLabel(t("register_title"));
    m_reg_title->setStyleSheet("background: transparent; border: none;");
    rf->addWidget(m_reg_title);
    rf->addSpacing(2);

    m_reg_subtitle = new QLabel(t("register_desc"));
    m_reg_subtitle->setStyleSheet("background: transparent; border: none;");
    rf->addWidget(m_reg_subtitle);
    rf->addSpacing(8);

    m_reg_user_lbl = new QLabel(t("username"));
    m_reg_user_lbl->setStyleSheet("background: transparent; border: none;");
    rf->addWidget(m_reg_user_lbl);
    rf->addSpacing(3);

    m_reg_user = new QLineEdit;
    m_reg_user->setPlaceholderText(t("username_ph"));
    m_reg_user->setFixedHeight(32);
    rf->addWidget(m_reg_user);
    rf->addSpacing(6);

    m_reg_pass_lbl = new QLabel(t("password"));
    m_reg_pass_lbl->setStyleSheet("background: transparent; border: none;");
    rf->addWidget(m_reg_pass_lbl);
    rf->addSpacing(3);

    m_reg_pass = new QLineEdit;
    m_reg_pass->setPlaceholderText(t("password_ph"));
    m_reg_pass->setEchoMode(QLineEdit::Password);
    m_reg_pass->setFixedHeight(32);
    connect(m_reg_pass, &QLineEdit::textChanged, this, [this]() { update_strength(); });
    rf->addWidget(m_reg_pass);
    rf->addSpacing(3);

    // Strength meter
    m_strength_row = new QWidget;
    m_strength_row->setStyleSheet("background: transparent; border: none;");
    m_strength_row->setFixedHeight(16);
    auto* str_layout = new QHBoxLayout(m_strength_row);
    str_layout->setContentsMargins(0, 0, 0, 0);
    str_layout->setSpacing(3);

    m_strength_bar_1 = new QWidget; m_strength_bar_1->setFixedHeight(3);
    m_strength_bar_2 = new QWidget; m_strength_bar_2->setFixedHeight(3);
    m_strength_bar_3 = new QWidget; m_strength_bar_3->setFixedHeight(3);
    m_strength_bar_4 = new QWidget; m_strength_bar_4->setFixedHeight(3);
    str_layout->addWidget(m_strength_bar_1, 1);
    str_layout->addWidget(m_strength_bar_2, 1);
    str_layout->addWidget(m_strength_bar_3, 1);
    str_layout->addWidget(m_strength_bar_4, 1);

    m_strength_label = new QLabel;
    m_strength_label->setFixedWidth(60);
    m_strength_label->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
    m_strength_label->setStyleSheet("background: transparent; border: none;");
    str_layout->addWidget(m_strength_label);

    m_strength_row->setVisible(false);
    rf->addWidget(m_strength_row);
    rf->addSpacing(4);

    m_reg_confirm_lbl = new QLabel(t("confirm"));
    m_reg_confirm_lbl->setStyleSheet("background: transparent; border: none;");
    rf->addWidget(m_reg_confirm_lbl);
    rf->addSpacing(3);

    m_reg_confirm = new QLineEdit;
    m_reg_confirm->setPlaceholderText(t("confirm_ph"));
    m_reg_confirm->setEchoMode(QLineEdit::Password);
    m_reg_confirm->setFixedHeight(32);
    connect(m_reg_confirm, &QLineEdit::returnPressed, this, &AuthWidget::on_register_submit);
    rf->addWidget(m_reg_confirm);
    rf->addSpacing(4);

    // Terms checkbox label
    m_reg_terms_lbl = new QLabel(t("agree_terms"));
    m_reg_terms_lbl->setStyleSheet("background: transparent; border: none;");
    m_reg_terms_lbl->setWordWrap(true);
    rf->addWidget(m_reg_terms_lbl);
    rf->addSpacing(4);

    m_form_stack->addWidget(m_register_page);

    card_layout->addWidget(m_form_stack);
    card_layout->addSpacing(4);

    // ── Error box (shared) ──
    m_error_box = new QWidget;
    m_error_box->setVisible(false);
    auto* err_layout = new QHBoxLayout(m_error_box);
    err_layout->setContentsMargins(8, 4, 8, 4);
    err_layout->setSpacing(4);
    m_error_label = new QLabel;
    m_error_label->setWordWrap(true);
    m_error_label->setStyleSheet("background: transparent; border: none;");
    err_layout->addWidget(m_error_label, 1);
    card_layout->addWidget(m_error_box);
    card_layout->addSpacing(6);

    // ── Button row ──
    auto* btn_row = new QWidget;
    btn_row->setStyleSheet("background: transparent; border: none;");
    auto* btn_layout = new QHBoxLayout(btn_row);
    btn_layout->setContentsMargins(0, 0, 0, 0);
    btn_layout->setSpacing(8);

    m_login_submit = new QPushButton(t("btn_login"));
    m_login_submit->setFixedHeight(34);
    m_login_submit->setCursor(Qt::PointingHandCursor);
    connect(m_login_submit, &QPushButton::clicked, this, &AuthWidget::on_login_submit);

    m_reg_submit = new QPushButton(t("btn_register"));
    m_reg_submit->setFixedHeight(34);
    m_reg_submit->setCursor(Qt::PointingHandCursor);
    m_reg_submit->setVisible(false);
    connect(m_reg_submit, &QPushButton::clicked, this, &AuthWidget::on_register_submit);

    m_cancel_btn = new QPushButton(t("btn_cancel"));
    m_cancel_btn->setFixedHeight(34);
    m_cancel_btn->setCursor(Qt::PointingHandCursor);
    connect(m_cancel_btn, &QPushButton::clicked, this, [this]() {
        m_login_user->clear();
        m_login_pass->clear();
        m_reg_user->clear();
        m_reg_pass->clear();
        m_reg_confirm->clear();
        clear_error();
        window()->close();
    });

    btn_layout->addWidget(m_login_submit, 1);
    btn_layout->addWidget(m_reg_submit, 1);
    btn_layout->addWidget(m_cancel_btn, 1);

    card_layout->addWidget(btn_row);
    card_layout->addSpacing(6);

    // ── Social divider ──
    m_divider_row = new QWidget;
    m_divider_row->setStyleSheet("background: transparent; border: none;");
    auto* div_layout = new QHBoxLayout(m_divider_row);
    div_layout->setContentsMargins(0, 0, 0, 0);
    div_layout->setSpacing(6);
    m_divider_line_1 = new QWidget; m_divider_line_1->setFixedHeight(1);
    m_divider_line_2 = new QWidget; m_divider_line_2->setFixedHeight(1);
    m_or_label = new QLabel(t("or_continue"));
    m_or_label->setStyleSheet("background: transparent; border: none;");
    div_layout->addWidget(m_divider_line_1, 1);
    div_layout->addWidget(m_or_label);
    div_layout->addWidget(m_divider_line_2, 1);
    card_layout->addWidget(m_divider_row);
    card_layout->addSpacing(6);

    // ── Social buttons ──
    m_social_row = new QWidget;
    m_social_row->setStyleSheet("background: transparent; border: none;");
    auto* soc_layout = new QHBoxLayout(m_social_row);
    soc_layout->setContentsMargins(0, 0, 0, 0);
    soc_layout->setSpacing(8);
    m_social_google = new QPushButton("Google");
    m_social_google->setFixedHeight(30);
    m_social_google->setCursor(Qt::PointingHandCursor);
    m_social_github = new QPushButton("GitHub");
    m_social_github->setFixedHeight(30);
    m_social_github->setCursor(Qt::PointingHandCursor);
    soc_layout->addWidget(m_social_google, 1);
    soc_layout->addWidget(m_social_github, 1);
    card_layout->addWidget(m_social_row);
    card_layout->addSpacing(8);

    // ── Footer ──
    auto* footer = new QWidget;
    footer->setStyleSheet("background: transparent; border: none;");
    auto* footer_layout = new QHBoxLayout(footer);
    footer_layout->setAlignment(Qt::AlignCenter);
    footer_layout->setContentsMargins(0, 0, 0, 0);
    footer_layout->setSpacing(4);

    m_footer_text = new QLabel(t("no_account"));
    m_footer_text->setStyleSheet("background: transparent; border: none;");
    footer_layout->addWidget(m_footer_text);

    m_footer_link = new QPushButton(t("register_now"));
    m_footer_link->setFlat(true);
    m_footer_link->setCursor(Qt::PointingHandCursor);
    connect(m_footer_link, &QPushButton::clicked, this, [this]() {
        switch_tab(m_active_tab == 0 ? 1 : 0);
    });
    footer_layout->addWidget(m_footer_link);

    card_layout->addWidget(footer);

    root_layout->addWidget(m_right_panel, 1);

    outer->addWidget(m_root);

    // Default tab
    switch_tab(0);
}

// ═══════════════════════════════════════════════
// THEME
// ═══════════════════════════════════════════════
void AuthWidget::toggle_theme()
{
    m_dark = !m_dark;
    apply_theme();
}

void AuthWidget::apply_theme()
{
    // Color palette
    QString bg_deep, bg_panel, bg_input, border_sub, border_in;
    QString cyan = "#00BCD4", blue = "#1565C0", orange = "#F57C00";
    QString txt_pri, txt_sec, txt_muted, txt_bright, err_color = "#F87171";

    if (m_dark) {
        bg_deep    = "#060B18";
        bg_panel   = "#0A1128";
        bg_input   = "#0B1226";
        border_sub = "rgba(255,255,255,0.04)";
        border_in  = "rgba(255,255,255,0.08)";
        txt_pri    = "#EDF1F9";
        txt_sec    = "#94A3BE";
        txt_muted  = "#5A6E8A";
        txt_bright = "#FFFFFF";
    } else {
        bg_deep    = "#F4F7FB";
        bg_panel   = "#FFFFFF";
        bg_input   = "#F0F3F8";
        border_sub = "rgba(0,0,0,0.06)";
        border_in  = "rgba(0,0,0,0.1)";
        txt_pri    = "#1A2332";
        txt_sec    = "#5A6B82";
        txt_muted  = "#9BAABE";
        txt_bright = "#0C1929";
        err_color  = "#DC2626";
    }

    // Root background (no extra bg, panels handle their own)
    setStyleSheet("AuthWidget { background: transparent; }");

    // Left panel (brand side)
    if (m_dark) {
        m_left_panel->setStyleSheet(QString("background: %1; border: none;").arg(bg_deep));
    } else {
        m_left_panel->setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            "stop:0 #EAF1FA, stop:0.4 #F7FAFF, stop:1 #FFF8F0); "
            "border: none;"
        );
    }

    // Right panel (form area — no separate card)
    m_right_panel->setStyleSheet(QString("background: %1; border: none;").arg(bg_panel));

    // Heading & desc
    m_heading->setText(t("brand_tagline"));
    m_heading->setStyleSheet(QString(
        "color: %1; font-size: 16px; font-weight: bold; background: transparent; border: none;"
    ).arg(txt_bright));

    m_desc->setText(t("brand_desc"));
    m_desc->setStyleSheet(QString(
        "color: %1; font-size: 11px; background: transparent; border: none;"
    ).arg(txt_sec));

    // Pills
    for (auto* pill : m_pills) {
        pill->setStyleSheet(QString(
            "background: %1; color: %2; border: 1px solid %3; "
            "border-radius: 10px; padding: 3px 10px; font-size: 11px;"
        ).arg(
            m_dark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.03)",
            txt_pri,
            m_dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)"
        ));
    }

    // Input style
    QString input_ss = QString(
        "QLineEdit {"
        "  border: 1px solid %1; padding: 5px 10px; font-size: 13px;"
        "  background: %2; color: %3;"
        "}"
        "QLineEdit:focus { border: 1px solid %4; }"
    ).arg(border_in, bg_input, txt_pri, cyan);

    // Apply to all inputs
    for (auto* input : {m_login_user, m_login_pass, m_reg_user, m_reg_pass, m_reg_confirm}) {
        input->setStyleSheet(input_ss);
    }

    // Labels
    QString lbl_ss = QString("color: %1; font-size: 11px; font-weight: bold; background: transparent; border: none;").arg(txt_sec);
    for (auto* lbl : {m_login_user_lbl, m_login_pass_lbl, m_reg_user_lbl, m_reg_pass_lbl, m_reg_confirm_lbl}) {
        lbl->setStyleSheet(lbl_ss);
    }

    // Title styles
    QString title_ss = QString("color: %1; font-size: 16px; font-weight: bold; background: transparent; border: none;").arg(txt_bright);
    QString sub_ss = QString("color: %1; font-size: 11px; background: transparent; border: none;").arg(txt_sec);
    m_login_title->setStyleSheet(title_ss);
    m_login_subtitle->setStyleSheet(sub_ss);
    m_reg_title->setStyleSheet(title_ss);
    m_reg_subtitle->setStyleSheet(sub_ss);

    // Remember & terms
    m_login_remember_lbl->setStyleSheet(QString("color: %1; font-size: 11px; background: transparent; border: none;").arg(txt_sec));
    m_reg_terms_lbl->setStyleSheet(QString("color: %1; font-size: 11px; background: transparent; border: none;").arg(txt_sec));

    // Tab buttons
    QString tab_active_ss = QString(
        "QPushButton { background: rgba(%1); color: %2; border: 1px solid rgba(%3); font-size: 13px; font-weight: 600; }"
    ).arg(
        m_dark ? "0,188,212,0.12" : "255,255,255,1",
        txt_bright,
        m_dark ? "0,188,212,0.2" : "0,0,0,0.08"
    );
    QString tab_inactive_ss = QString(
        "QPushButton { background: transparent; color: %1; border: none; font-size: 13px; font-weight: 600; }"
        "QPushButton:hover { color: %2; }"
    ).arg(txt_muted, txt_sec);

    m_tab_login_btn->setStyleSheet(m_active_tab == 0 ? tab_active_ss : tab_inactive_ss);
    m_tab_register_btn->setStyleSheet(m_active_tab == 1 ? tab_active_ss : tab_inactive_ss);

    // Primary button (gradient)
    QString primary_ss = QString(
        "QPushButton {"
        "  background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 %1, stop:0.5 %2, stop:1 %3);"
        "  color: #fff; border: none; font-size: 13px; font-weight: bold;"
        "}"
        "QPushButton:hover {"
        "  background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0097A7, stop:0.5 %2, stop:1 %3);"
        "}"
        "QPushButton:disabled { background: rgba(0,188,212,0.4); color: rgba(255,255,255,0.6); }"
    ).arg(cyan, blue, orange);

    m_login_submit->setStyleSheet(primary_ss);
    m_reg_submit->setStyleSheet(primary_ss);

    // Cancel button
    m_cancel_btn->setStyleSheet(QString(
        "QPushButton { background: transparent; color: %1; border: 1px solid rgba(248,113,113,0.3); font-size: 13px; font-weight: bold; }"
        "QPushButton:hover { background: rgba(248,113,113,0.1); border-color: %1; }"
    ).arg(err_color));

    // Error box
    m_error_box->setStyleSheet("background: rgba(248,113,113,0.08); border: 1px solid rgba(248,113,113,0.2);");
    m_error_label->setStyleSheet(QString("color: %1; font-size: 12px; background: transparent; border: none;").arg(err_color));

    // Social buttons
    QString social_ss = QString(
        "QPushButton { background: %1; color: %2; border: 1px solid %3; font-size: 12px; }"
        "QPushButton:hover { background: %4; border-color: %5; color: %6; }"
    ).arg(
        m_dark ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.03)",
        txt_sec, border_in,
        m_dark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)",
        cyan, txt_pri
    );
    m_social_google->setStyleSheet(social_ss);
    m_social_github->setStyleSheet(social_ss);

    // Divider
    QString line_bg = m_dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)";
    m_divider_line_1->setStyleSheet(QString("background: %1; border: none;").arg(line_bg));
    m_divider_line_2->setStyleSheet(QString("background: %1; border: none;").arg(line_bg));
    m_or_label->setStyleSheet(QString("color: %1; font-size: 10px; background: transparent; border: none;").arg(txt_muted));

    // Footer
    m_footer_text->setStyleSheet(QString("color: %1; font-size: 11px; background: transparent; border: none;").arg(txt_muted));
    m_footer_link->setStyleSheet(QString(
        "QPushButton { color: %1; font-size: 11px; font-weight: 600; border: none; background: transparent; padding: 0; }"
        "QPushButton:hover { color: #00E5FF; }"
    ).arg(cyan));

    // Theme toggle
    m_theme_toggle->setText(m_dark ? QString::fromUtf8("\u263E") : QString::fromUtf8("\u2600"));
    m_theme_toggle->setStyleSheet(QString(
        "QPushButton { background: %1; color: %2; border: 1px solid %3; font-size: 14px; }"
        "QPushButton:hover { border-color: %4; color: %4; background: rgba(0,188,212,0.1); }"
    ).arg(
        m_dark ? "rgba(255,255,255,0.05)" : "rgba(255,255,255,0.8)",
        txt_sec,
        m_dark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)",
        cyan
    ));

    // Close button
    m_close_btn->setStyleSheet(QString(
        "QPushButton { background: transparent; color: %1; border: none; font-size: 14px; font-weight: bold; }"
        "QPushButton:hover { color: %2; background: rgba(248,113,113,0.1); }"
    ).arg(txt_muted, err_color));

    // Lang buttons
    for (int i = 0; i < m_lang_btns.size(); ++i) {
        bool active = (m_lang == QStringList{"vi","en","zh"}[i]);
        m_lang_btns[i]->setStyleSheet(QString(
            "QPushButton { background: %1; color: %2; border: 1px solid %3; font-size: 10px; font-weight: bold; }"
            "QPushButton:hover { border-color: %4; background: rgba(0,188,212,0.1); }"
        ).arg(
            active ? "rgba(0,188,212,0.15)" : (m_dark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.03)"),
            active ? cyan : txt_sec,
            active ? cyan : (m_dark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)"),
            cyan
        ));
    }

    // Strength bars update
    update_strength();
}

// ═══════════════════════════════════════════════
// TAB SWITCHING
// ═══════════════════════════════════════════════
void AuthWidget::switch_tab(int index)
{
    m_active_tab = index;
    m_form_stack->setCurrentIndex(index);
    clear_error();

    m_login_submit->setVisible(index == 0);
    m_reg_submit->setVisible(index == 1);

    if (index == 0) {
        m_footer_text->setText(t("no_account"));
        m_footer_link->setText(t("register_now"));
    } else {
        m_footer_text->setText(t("has_account"));
        m_footer_link->setText(t("login_now"));
    }

    apply_theme(); // re-apply tab styles
}

// ═══════════════════════════════════════════════
// PASSWORD STRENGTH
// ═══════════════════════════════════════════════
void AuthWidget::update_strength()
{
    const auto p = m_reg_pass->text();
    if (p.isEmpty()) {
        m_strength_row->setVisible(false);
        m_password_strength = 0;
        return;
    }
    m_strength_row->setVisible(true);

    int score = 0;
    if (p.length() >= 8) score++;
    if (p.contains(QRegularExpression("[a-z]")) && p.contains(QRegularExpression("[A-Z]"))) score++;
    if (p.contains(QRegularExpression("\\d"))) score++;
    if (p.contains(QRegularExpression("[^a-zA-Z0-9]"))) score++;
    m_password_strength = score;

    QString bar_off = m_dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)";
    QString colors[] = {"", "#F87171", "#FBBF24", "#34D399", "#4ADE80"};
    QString labels[] = {"", "strength_weak", "strength_fair", "strength_good", "strength_strong"};

    auto set_bar = [&](QWidget* bar, int level) {
        bar->setStyleSheet(QString("background: %1; border: none; border-radius: 2px;").arg(
            score >= level ? colors[score] : bar_off
        ));
    };

    set_bar(m_strength_bar_1, 1);
    set_bar(m_strength_bar_2, 2);
    set_bar(m_strength_bar_3, 3);
    set_bar(m_strength_bar_4, 4);

    m_strength_label->setText(score > 0 ? t(labels[score]) : "");
    m_strength_label->setStyleSheet(QString(
        "color: %1; font-size: 10px; font-weight: bold; background: transparent; border: none;"
    ).arg(score > 0 ? colors[score] : "transparent"));
}

// ═══════════════════════════════════════════════
// ERROR
// ═══════════════════════════════════════════════
void AuthWidget::set_error(const QString& msg)
{
    m_error_label->setText(msg);
    m_error_box->setVisible(true);
}

void AuthWidget::clear_error()
{
    m_error_box->setVisible(false);
    m_error_label->clear();
}

// ═══════════════════════════════════════════════
// LOGIN SUBMIT
// ═══════════════════════════════════════════════
void AuthWidget::on_login_submit()
{
    if (m_loading) return;

    const auto username = m_login_user->text().trimmed();
    const auto password = m_login_pass->text();

    if (username.isEmpty() || password.isEmpty()) {
        set_error(t("err_required"));
        return;
    }

    m_loading = true;
    clear_error();
    m_login_submit->setEnabled(false);
    m_login_submit->setText(t("loading_login"));

    m_api->login(username, password, [this](bool success, const QJsonObject& data) {
        m_loading = false;
        m_login_submit->setEnabled(true);
        m_login_submit->setText(t("btn_login"));

        if (success && data.contains("token")) {
            m_api->set_token(data["token"].toString());
            if (data.contains("user")) {
                m_api->set_username(data["user"].toObject().value("username").toString());
            }
            emit login_success();
        } else {
            set_error(data.value("message").toString(t("err_login")));
        }
    });
}

// ═══════════════════════════════════════════════
// REGISTER SUBMIT
// ═══════════════════════════════════════════════
void AuthWidget::on_register_submit()
{
    if (m_loading) return;

    const auto username = m_reg_user->text().trimmed();
    const auto password = m_reg_pass->text();
    const auto confirm = m_reg_confirm->text();

    if (username.isEmpty() || password.isEmpty()) {
        set_error(t("err_required"));
        return;
    }
    if (password.length() < 8) {
        set_error(t("err_min_pass"));
        return;
    }
    if (password != confirm) {
        set_error(t("err_confirm"));
        return;
    }

    m_loading = true;
    clear_error();
    m_reg_submit->setEnabled(false);
    m_reg_submit->setText(t("loading_register"));

    m_api->register_user(username, password, [this](bool success, const QJsonObject& data) {
        m_loading = false;
        m_reg_submit->setEnabled(true);
        m_reg_submit->setText(t("btn_register"));

        if (success && data.contains("token")) {
            m_api->set_token(data["token"].toString());
            if (data.contains("user")) {
                m_api->set_username(data["user"].toObject().value("username").toString());
            }
            emit login_success();
        } else {
            set_error(data.value("message").toString(t("err_register")));
        }
    });
}
