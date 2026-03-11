#include "core/settings_dialog.h"
#include "core/add_agent_dialog.h"
#include "core/cookies_dialog.h"
#include "core/theme_manager.h"
#include "core/translator.h"
#include "core/icon_defs.h"
#include "core/toggle_switch.h"
#include "core/api_client.h"
#include "utils/feedback.h"

#include <QJsonArray>
#include <QJsonObject>
#include <QDateTime>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QHeaderView>
#include <QFrame>
#include <memory>
#include <QPointer>

// ════════════════════════════════════════
// SettingsDialog
// ════════════════════════════════════════

SettingsDialog::SettingsDialog(ThemeManager* theme, Translator* tr,
                               ApiClient* api, QWidget* parent)
    : QDialog(parent), m_theme(theme), m_tr(tr), m_api(api)
{
    setWindowFlags(windowFlags() & ~Qt::WindowContextHelpButtonHint);
    setFixedSize(1000, 580);
    m_feedback = new Feedback(this, m_theme);
    setup_ui();
    load_agents();
    apply_theme();
}

void SettingsDialog::setup_ui()
{
    auto* root = new QVBoxLayout(this);
    root->setContentsMargins(0, 0, 0, 0);
    root->setSpacing(0);

    m_title_label = new QLabel(m_tr->t("settings.agent_list_title"));
    m_title_label->setAlignment(Qt::AlignCenter);
    m_title_label->setFixedHeight(IconDefs::k_table_row_height + 4);
    m_title_label->setStyleSheet("font-size: 14px; font-weight: bold;");
    root->addWidget(m_title_label);

    auto* header = new QWidget;
    auto* header_lay = new QHBoxLayout(header);
    header_lay->setContentsMargins(20, 8, 20, 8);
    header_lay->setSpacing(8);
    header_lay->addStretch();

    m_btn_check_all = new QPushButton(QIcon(":/icons/check_all"), m_tr->t("settings.check_all"));
    m_btn_check_all->setCursor(Qt::PointingHandCursor);
    m_btn_check_all->setFixedHeight(IconDefs::k_header_btn_height);
    m_btn_check_all->setIconSize(IconDefs::header_icon());
    header_lay->addWidget(m_btn_check_all);

    m_btn_login_all = new QPushButton(QIcon(":/icons/login_agent"), m_tr->t("settings.login_all"));
    m_btn_login_all->setCursor(Qt::PointingHandCursor);
    m_btn_login_all->setFixedHeight(IconDefs::k_header_btn_height);
    m_btn_login_all->setIconSize(IconDefs::header_icon());
    header_lay->addWidget(m_btn_login_all);

    m_btn_delete_all = new QPushButton(QIcon(":/icons/delete"), m_tr->t("settings.delete_all"));
    m_btn_delete_all->setCursor(Qt::PointingHandCursor);
    m_btn_delete_all->setFixedHeight(IconDefs::k_header_btn_height);
    m_btn_delete_all->setIconSize(IconDefs::header_icon());
    header_lay->addWidget(m_btn_delete_all);

    m_btn_add = new QPushButton(QIcon(":/icons/add_agent"), m_tr->t("settings.add_agent"));
    m_btn_add->setCursor(Qt::PointingHandCursor);
    m_btn_add->setFixedHeight(IconDefs::k_header_btn_height);
    m_btn_add->setIconSize(IconDefs::header_icon());
    header_lay->addWidget(m_btn_add);

    root->addWidget(header);

    auto* sep = new QFrame;
    sep->setFrameShape(QFrame::HLine);
    sep->setFixedHeight(IconDefs::k_separator_height);
    root->addWidget(sep);

    m_table = new QTableWidget;
    m_table->setColumnCount(7);
    m_table->setHorizontalHeaderLabels({
        m_tr->t("settings.col_code"),
        m_tr->t("settings.col_name"),
        m_tr->t("settings.col_account"),
        m_tr->t("settings.col_status"),
        m_tr->t("settings.col_created"),
        m_tr->t("settings.col_actions"),
        m_tr->t("settings.col_auto_login")
    });
    m_table->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_table->setSelectionMode(QAbstractItemView::SingleSelection);
    m_table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_table->verticalHeader()->setVisible(false);
    m_table->setShowGrid(true);
    m_table->horizontalHeader()->setStretchLastSection(false);
    m_table->horizontalHeader()->setSectionResizeMode(5, QHeaderView::Stretch);

    m_table->setWordWrap(false);
    m_table->setColumnWidth(0, 55);
    m_table->setColumnWidth(1, 140);
    m_table->setColumnWidth(2, 95);
    m_table->setColumnWidth(3, 90);
    m_table->setColumnWidth(4, 140);
    m_table->setColumnWidth(6, 80);

    root->addWidget(m_table, 1);

    connect(m_btn_check_all, &QPushButton::clicked, this, &SettingsDialog::on_check_all);
    connect(m_btn_login_all, &QPushButton::clicked, this, &SettingsDialog::on_login_all);
    connect(m_btn_delete_all, &QPushButton::clicked, this, &SettingsDialog::on_delete_all);
    connect(m_btn_add, &QPushButton::clicked, this, &SettingsDialog::on_add_agent);

    setWindowTitle(m_tr->t("settings.agent_list_title"));
}

void SettingsDialog::load_agents()
{
    QPointer<SettingsDialog> guard(this);
    m_api->get("/api/agents", [guard](const ApiError& err, const QJsonObject& data) {
        if (!guard) return;
        if (!err.is_ok()) {
            guard->m_feedback->msg_error(err.message);
            return;
        }
        guard->m_agents.clear();
        const auto arr = data["agents"].toArray();
        for (const auto& v : arr) {
            auto obj = v.toObject();
            AgentInfo info;
            info.id = static_cast<int64_t>(obj["id"].toDouble());
            info.name = obj["name"].toString();
            info.username = obj["ext_username"].toString();
            info.status = obj["status"].toString();
            info.base_url = obj["base_url"].toString();
            info.auto_login = obj["auto_login"].toBool();
            auto dt = QDateTime::fromString(obj["created_at"].toString(), Qt::ISODate);
            info.created_at = dt.isValid()
                ? dt.toString("yyyy-MM-dd hh:mm:ss")
                : obj["created_at"].toString();
            guard->m_agents.append(info);
        }
        guard->refresh_table();
    });
}

void SettingsDialog::refresh_table()
{
    m_table->setRowCount(m_agents.size());
    for (int i = 0; i < m_agents.size(); ++i) {
        const auto& a = m_agents[i];

        auto* id_item = new QTableWidgetItem(QString::number(a.id));
        id_item->setTextAlignment(Qt::AlignCenter);
        m_table->setItem(i, 0, id_item);

        auto* name_item = new QTableWidgetItem(a.name);
        name_item->setTextAlignment(Qt::AlignCenter);
        m_table->setItem(i, 1, name_item);

        auto* user_item = new QTableWidgetItem(a.username);
        user_item->setTextAlignment(Qt::AlignCenter);
        m_table->setItem(i, 2, user_item);

        auto* status_widget = new QWidget;
        auto* status_lay = new QHBoxLayout(status_widget);
        status_lay->setContentsMargins(4, 2, 4, 2);
        status_lay->setAlignment(Qt::AlignCenter);
        auto* status_label = new QLabel;
        status_label->setAlignment(Qt::AlignCenter);
        status_label->setFixedHeight(IconDefs::k_status_tag_height);

        QString status_text, status_color;
        if (a.status == "active") {
            status_text = "Online";
            status_color = "#16b777";
        } else if (a.status == "logging_in") {
            status_text = QString::fromUtf8("Đang login...");
            status_color = "#ffb800";
        } else if (a.status == "error") {
            status_text = QString::fromUtf8("Lỗi");
            status_color = "#ff5722";
        } else {
            status_text = "Offline";
            status_color = "#ff5722";
        }
        status_label->setText(status_text);
        status_label->setStyleSheet(QString(
            "QLabel { color: #fff; background: %1; padding: 2px 10px;"
            "  font-size: 11px; border: none; }"
        ).arg(status_color));
        status_lay->addWidget(status_label);
        m_table->setCellWidget(i, 3, status_widget);

        auto* date_item = new QTableWidgetItem(a.created_at);
        date_item->setTextAlignment(Qt::AlignCenter);
        m_table->setItem(i, 4, date_item);

        m_table->setCellWidget(i, 5, make_action_buttons(i));

        auto* auto_widget = new QWidget;
        auto* auto_lay = new QHBoxLayout(auto_widget);
        auto_lay->setContentsMargins(0, 0, 0, 0);
        auto_lay->setAlignment(Qt::AlignCenter);
        auto* toggle = new ToggleSwitch(a.auto_login);
        connect(toggle, &ToggleSwitch::toggled, this, [this, i](bool checked) {
            m_agents[i].auto_login = checked;
            on_toggle_auto_login(i);
        });
        auto_lay->addWidget(toggle);
        m_table->setCellWidget(i, 6, auto_widget);
    }

    for (int i = 0; i < m_agents.size(); ++i)
        m_table->setRowHeight(i, IconDefs::k_table_row_height);
}

QWidget* SettingsDialog::make_action_buttons(int row)
{
    auto* widget = new QWidget;
    auto* lay = new QHBoxLayout(widget);
    lay->setContentsMargins(2, 1, 2, 1);
    lay->setSpacing(3);
    lay->setAlignment(Qt::AlignCenter);

    auto make_btn = [&](const QIcon& icon, const QString& text, const QString& border_color) {
        auto* btn = new QPushButton(icon, text);
        btn->setCursor(Qt::PointingHandCursor);
        btn->setFixedHeight(IconDefs::k_table_btn_height);
        btn->setIconSize(IconDefs::table_icon());
        btn->setStyleSheet(QString(
            "QPushButton { background: transparent; color: %1; border: 1px solid %1;"
            "  padding: 0 5px; font-size: 11px; }"
            "QPushButton:hover { background: %1; color: #fff; }"
        ).arg(border_color));
        lay->addWidget(btn);
        return btn;
    };

    auto* btn_edit = make_btn(QIcon(":/icons/edit"), m_tr->t("settings.edit"), "#1e9fff");
    auto* btn_delete = make_btn(QIcon(":/icons/delete"), m_tr->t("settings.delete"), "#ff5722");
    auto* btn_check = make_btn(QIcon(":/icons/check"), m_tr->t("settings.check"), "#16b777");
    auto* btn_login = make_btn(QIcon(":/icons/login_agent"), m_tr->t("settings.login"), "#ffb800");
    auto* btn_cookies = make_btn(QIcon(":/icons/cookies"), m_tr->t("settings.assign_cookies"), "#16baaa");

    connect(btn_edit, &QPushButton::clicked, this, [this, row]() { on_edit_agent(row); });
    connect(btn_delete, &QPushButton::clicked, this, [this, row]() { on_delete_agent(row); });
    connect(btn_check, &QPushButton::clicked, this, [this, row]() { on_check_agent(row); });
    connect(btn_login, &QPushButton::clicked, this, [this, row]() { on_login_agent(row); });
    connect(btn_cookies, &QPushButton::clicked, this, [this, row]() { on_assign_cookies(row); });

    return widget;
}

void SettingsDialog::apply_theme()
{
    auto bg = m_theme->color("bg");
    auto fg = m_theme->color("text_primary");
    auto border_light = m_theme->color("border_light");
    auto primary = m_theme->color("primary");
    auto bg2 = m_theme->color("bg_secondary");
    auto bg_hover = m_theme->color("bg_hover");

    setStyleSheet(QString("QDialog { background: %1; }").arg(bg));

    m_title_label->setStyleSheet(QString(
        "QLabel { font-size: 14px; font-weight: bold; color: %1;"
        "  background: %2; border-bottom: 1px solid %3; border-top: none;"
        "  border-left: none; border-right: none; }"
    ).arg(fg, bg2, border_light));

    m_btn_check_all->setStyleSheet(
        "QPushButton { background: transparent; color: #16b777; border: 1px solid #16b777;"
        "  padding: 0 12px; font-size: 12px; }"
        "QPushButton:hover { background: #16b777; color: #fff; }");
    m_btn_login_all->setStyleSheet(
        "QPushButton { background: transparent; color: #ffb800; border: 1px solid #ffb800;"
        "  padding: 0 12px; font-size: 12px; }"
        "QPushButton:hover { background: #ffb800; color: #fff; }");
    m_btn_delete_all->setStyleSheet(
        "QPushButton { background: transparent; color: #ff5722; border: 1px solid #ff5722;"
        "  padding: 0 12px; font-size: 12px; }"
        "QPushButton:hover { background: #ff5722; color: #fff; }");
    m_btn_add->setStyleSheet(QString(
        "QPushButton { background: %1; color: #fff; border: none;"
        "  padding: 0 12px; font-size: 12px; }"
        "QPushButton:hover { opacity: 0.9; }"
    ).arg(primary));

    m_table->setStyleSheet(QString(
        "QTableWidget { background: %1; color: %2; border: 1px solid %3;"
        "  gridline-color: %3; font-size: 12px; }"
        "QTableWidget::item { padding: 4px; }"
        "QTableWidget::item:selected { background: %4; }"
        "QHeaderView::section { background: %5; color: %2; border: none;"
        "  border-bottom: 1px solid %3; border-right: 1px solid %3;"
        "  padding: 6px; font-size: 12px; font-weight: normal; }"
        "QHeaderView::section:last { border-right: none; }"
    ).arg(bg, fg, border_light, bg_hover, bg2));
}

void SettingsDialog::retranslate()
{
    setWindowTitle(m_tr->t("settings.agent_list_title"));
    m_title_label->setText(m_tr->t("settings.agent_list_title"));
    m_btn_check_all->setText(m_tr->t("settings.check_all"));
    m_btn_login_all->setText(m_tr->t("settings.login_all"));
    m_btn_delete_all->setText(m_tr->t("settings.delete_all"));
    m_btn_add->setText(m_tr->t("settings.add_agent"));
    m_table->setHorizontalHeaderLabels({
        m_tr->t("settings.col_code"),
        m_tr->t("settings.col_name"),
        m_tr->t("settings.col_account"),
        m_tr->t("settings.col_status"),
        m_tr->t("settings.col_created"),
        m_tr->t("settings.col_actions"),
        m_tr->t("settings.col_auto_login")
    });
    refresh_table();
}

// ── Slots — API calls ──

void SettingsDialog::on_add_agent()
{
    AddAgentDialog dlg(m_theme, m_tr, this);
    if (dlg.exec() != QDialog::Accepted) return;

    if (dlg.agent_name().trimmed().isEmpty() || dlg.agent_username().trimmed().isEmpty()) {
        m_feedback->msg_warn(m_tr->t("settings.msg_fill_required"));
        return;
    }

    auto* loading = m_feedback->show_loading();
    QJsonObject body;
    body["name"] = dlg.agent_name().trimmed();
    body["ext_username"] = dlg.agent_username().trimmed();
    body["ext_password"] = dlg.agent_password();
    body["base_url"] = dlg.agent_base_url().trimmed();

    QPointer<SettingsDialog> guard(this);
    m_api->post("/api/agents", body, [guard, loading](const ApiError& err, const QJsonObject&) {
        if (!guard) return;
        Feedback::close_loading(loading);
        if (!err.is_ok()) {
            guard->m_feedback->msg_error(err.message);
            return;
        }
        guard->m_feedback->msg_success(guard->m_tr->t("settings.msg_agent_added"));
        guard->load_agents();
    });
}

void SettingsDialog::on_check_all()
{
    if (m_agents.isEmpty()) {
        m_feedback->msg_info(m_tr->t("settings.msg_no_agents"));
        return;
    }
    auto* loading = m_feedback->show_loading(m_tr->t("settings.msg_checking_all"));

    QPointer<SettingsDialog> guard(this);
    m_api->get("/api/agents/cookie-health", [guard, loading](const ApiError& err, const QJsonObject& data) {
        if (!guard) return;
        Feedback::close_loading(loading);
        if (!err.is_ok()) {
            guard->m_feedback->msg_error(guard->m_tr->t("settings.msg_check_failed"));
            return;
        }
        int alive = 0, dead = 0;
        const auto results = data["results"].toArray();
        for (const auto& v : results) {
            auto obj = v.toObject();
            auto id = static_cast<int64_t>(obj["id"].toDouble());
            bool is_alive = obj["alive"].toBool();
            is_alive ? alive++ : dead++;
            for (auto& a : guard->m_agents) {
                if (a.id == id) {
                    a.status = is_alive ? "active" : "offline";
                    break;
                }
            }
        }
        guard->refresh_table();
        auto msg = QString::fromUtf8("Kiểm tra xong: %1 online, %2 offline")
                       .arg(alive).arg(dead);
        alive > 0 ? guard->m_feedback->msg_success(msg) : guard->m_feedback->msg_error(msg);
    });
}

void SettingsDialog::on_login_all()
{
    if (m_agents.isEmpty()) {
        m_feedback->msg_info(m_tr->t("settings.msg_no_agents"));
        return;
    }
    auto* loading = m_feedback->show_loading(m_tr->t("settings.msg_logging_in_all"));

    QPointer<SettingsDialog> guard(this);
    m_api->post("/api/ee88-auth/login-all", QJsonObject{},
        [guard, loading](const ApiError& err, const QJsonObject& data) {
            if (!guard) return;
            Feedback::close_loading(loading);
            if (!err.is_ok()) {
                guard->m_feedback->msg_error(guard->m_tr->t("settings.msg_login_all_failed"));
                return;
            }
            int success = data["success"].toInt();
            int failed = data["failed"].toInt();
            guard->load_agents();
            auto msg = QString::fromUtf8("Đăng nhập xong: %1 thành công, %2 thất bại")
                           .arg(success).arg(failed);
            failed > 0 ? guard->m_feedback->msg_error(msg) : guard->m_feedback->msg_success(msg);
        });
}

void SettingsDialog::on_delete_all()
{
    if (m_agents.isEmpty()) {
        m_feedback->msg_info(m_tr->t("settings.msg_no_agents"));
        return;
    }
    if (!m_feedback->confirm(
            m_tr->t("settings.msg_confirm_delete_all"),
            m_tr->t("settings.confirm"), m_tr->t("settings.cancel"))) {
        return;
    }

    auto* loading = m_feedback->show_loading();
    auto remaining = std::make_shared<int>(m_agents.size());
    auto had_error = std::make_shared<bool>(false);
    QPointer<SettingsDialog> guard(this);

    for (const auto& agent : m_agents) {
        auto path = QString("/api/agents/%1?mode=destroy").arg(agent.id);
        m_api->del(path, [guard, loading, remaining, had_error](const ApiError& err, const QJsonObject&) {
            if (!guard) return;
            if (!err.is_ok()) *had_error = true;
            (*remaining)--;
            if (*remaining <= 0) {
                Feedback::close_loading(loading);
                if (*had_error) {
                    guard->m_feedback->msg_error(guard->m_tr->t("settings.msg_delete_failed"));
                } else {
                    guard->m_feedback->msg_success(guard->m_tr->t("settings.msg_all_deleted"));
                }
                guard->load_agents();
            }
        });
    }
}

void SettingsDialog::on_edit_agent(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    const auto& agent = m_agents[row];

    AddAgentDialog dlg(m_theme, m_tr, this);
    dlg.set_edit_mode(agent.name, agent.username, agent.base_url);

    if (dlg.exec() != QDialog::Accepted) return;

    auto* loading = m_feedback->show_loading();
    QJsonObject body;
    body["name"] = dlg.agent_name().trimmed();
    if (!dlg.agent_password().isEmpty())
        body["ext_password"] = dlg.agent_password();
    if (!dlg.agent_base_url().trimmed().isEmpty())
        body["base_url"] = dlg.agent_base_url().trimmed();

    auto path = QString("/api/agents/%1").arg(agent.id);
    QPointer<SettingsDialog> guard(this);
    m_api->patch(path, body, [guard, loading](const ApiError& err, const QJsonObject&) {
        if (!guard) return;
        Feedback::close_loading(loading);
        if (!err.is_ok()) {
            guard->m_feedback->msg_error(err.message);
            return;
        }
        guard->m_feedback->msg_success(guard->m_tr->t("settings.msg_agent_updated"));
        guard->load_agents();
    });
}

void SettingsDialog::on_delete_agent(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    const auto& agent = m_agents[row];

    if (!m_feedback->confirm(
            m_tr->t("settings.msg_confirm_delete").replace("%s", agent.name),
            m_tr->t("settings.delete"), m_tr->t("settings.cancel"))) {
        return;
    }

    auto* loading = m_feedback->show_loading();
    auto path = QString("/api/agents/%1?mode=destroy").arg(agent.id);
    QPointer<SettingsDialog> guard(this);
    m_api->del(path, [guard, loading](const ApiError& err, const QJsonObject&) {
        if (!guard) return;
        Feedback::close_loading(loading);
        if (!err.is_ok()) {
            guard->m_feedback->msg_error(guard->m_tr->t("settings.msg_delete_failed"));
            return;
        }
        guard->m_feedback->msg_success(guard->m_tr->t("settings.msg_agent_deleted"));
        guard->load_agents();
    });
}

void SettingsDialog::on_check_agent(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    const auto& agent = m_agents[row];

    auto* loading = m_feedback->show_loading(
        m_tr->t("settings.msg_checking").replace("%s", agent.name));

    auto path = QString("/api/ee88-auth/%1/check").arg(agent.id);
    QPointer<SettingsDialog> guard(this);
    m_api->post(path, QJsonObject{}, [guard, loading, row](const ApiError& err, const QJsonObject& data) {
        if (!guard) return;
        Feedback::close_loading(loading);
        if (row >= guard->m_agents.size()) return;

        if (!err.is_ok()) {
            guard->m_feedback->msg_error(guard->m_agents[row].name + ": " + guard->m_tr->t("settings.msg_check_failed"));
            return;
        }
        bool valid = data["valid"].toBool();
        guard->m_agents[row].status = valid ? "active" : "offline";
        guard->refresh_table();

        auto msg = guard->m_agents[row].name + ": " +
            (valid ? QString::fromUtf8("Session còn hoạt động")
                   : QString::fromUtf8("Session hết hạn"));
        valid ? guard->m_feedback->msg_success(msg) : guard->m_feedback->msg_error(msg);
    });
}

void SettingsDialog::on_login_agent(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    m_agents[row].status = "logging_in";
    refresh_table();

    auto* loading = m_feedback->show_loading(
        m_tr->t("settings.msg_logging_in").replace("%s", m_agents[row].name));

    auto path = QString("/api/ee88-auth/%1/login").arg(m_agents[row].id);
    QPointer<SettingsDialog> guard(this);
    m_api->post(path, QJsonObject{}, [guard, loading, row](const ApiError& err, const QJsonObject& data) {
        if (!guard) return;
        Feedback::close_loading(loading);
        if (row >= guard->m_agents.size()) return;

        if (!err.is_ok()) {
            guard->m_agents[row].status = "error";
            guard->refresh_table();
            guard->m_feedback->msg_error(guard->m_agents[row].name + ": " + err.message);
            return;
        }
        bool success = data["success"].toBool();
        guard->m_agents[row].status = success ? "active" : "error";
        guard->refresh_table();

        if (success) {
            guard->m_feedback->msg_success(guard->m_agents[row].name + QString::fromUtf8(": Đăng nhập thành công"));
        } else {
            auto err_msg = data["error_message"].toString();
            guard->m_feedback->msg_error(guard->m_agents[row].name + ": " +
                (err_msg.isEmpty() ? QString::fromUtf8("Đăng nhập thất bại") : err_msg));
        }
    });
}

void SettingsDialog::on_assign_cookies(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    const auto& agent = m_agents[row];

    CookiesDialog dlg(m_theme, m_tr, this);
    dlg.set_agent(agent.name, agent.username);
    if (dlg.exec() != QDialog::Accepted) return;

    if (dlg.cookies_value().trimmed().isEmpty()) {
        m_feedback->msg_warn(m_tr->t("settings.msg_cookies_empty"));
        return;
    }

    auto* loading = m_feedback->show_loading();
    QJsonObject body;
    body["cookie"] = dlg.cookies_value().trimmed();

    auto path = QString("/api/ee88-auth/%1/cookie").arg(agent.id);
    QPointer<SettingsDialog> guard(this);
    m_api->patch(path, body, [guard, loading](const ApiError& err, const QJsonObject&) {
        if (!guard) return;
        Feedback::close_loading(loading);
        if (!err.is_ok()) {
            guard->m_feedback->msg_error(guard->m_tr->t("settings.msg_cookies_failed"));
            return;
        }
        guard->m_feedback->msg_success(guard->m_tr->t("settings.msg_cookies_saved"));
        guard->load_agents();
    });
}

void SettingsDialog::on_toggle_auto_login(int row)
{
    if (row < 0 || row >= m_agents.size()) return;
    const auto& agent = m_agents[row];

    QJsonObject body;
    body["auto_login"] = agent.auto_login;

    auto path = QString("/api/agents/%1").arg(agent.id);
    QPointer<SettingsDialog> guard(this);
    m_api->patch(path, body, [guard, row](const ApiError& err, const QJsonObject&) {
        if (!guard) return;
        if (row >= guard->m_agents.size()) return;
        if (!err.is_ok()) {
            guard->m_agents[row].auto_login = !guard->m_agents[row].auto_login;
            guard->refresh_table();
            guard->m_feedback->msg_error(guard->m_tr->t("settings.msg_update_failed"));
            return;
        }
        auto msg = guard->m_agents[row].auto_login
            ? guard->m_tr->t("settings.msg_auto_login_on")
            : guard->m_tr->t("settings.msg_auto_login_off");
        guard->m_feedback->msg_success(msg.replace("%s", guard->m_agents[row].name));
    });
}
