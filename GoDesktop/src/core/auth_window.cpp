#include "core/auth_window.h"
#include "core/api_client.h"
#include "core/auth_widget.h"
#include "core/main_widget.h"
#include "core/theme_manager.h"
#include "core/translator.h"

#include <QApplication>
#include <QDir>
#include <QIcon>

AuthWindow::~AuthWindow() = default;

AuthWindow::AuthWindow(QWidget* parent)
    : QMainWindow(parent)
    , m_api(std::make_unique<ApiClient>(this))
    , m_dragging(false)
{
    setWindowTitle("MaxHub");
    setWindowIcon(QIcon(":/icons/app_icon"));
    setWindowFlags(Qt::FramelessWindowHint);
    setMinimumSize(700, 448);
    resize(742, 476);
    setAttribute(Qt::WA_TranslucentBackground);

    // ── Shared config path ──
    auto app_dir = QApplication::applicationDirPath();
    auto shared_dir = QDir(app_dir).filePath("../../shared");
    if (!QDir(shared_dir).exists()) {
        shared_dir = QDir::currentPath() + "/../shared";
    }

    // ── Theme Manager ──
    m_theme = new ThemeManager(this);
    m_theme->load_colors(QDir(shared_dir).filePath("theme/colors.json"));

    // ── Translator ──
    m_tr = new Translator(this);
    m_tr->load_language("vi_VN", QDir(shared_dir).filePath("lang/vi_VN.json"));
    m_tr->load_language("en_US", QDir(shared_dir).filePath("lang/en_US.json"));
    m_tr->load_language("zh_CN", QDir(shared_dir).filePath("lang/zh_CN.json"));
    m_tr->set_locale("vi_VN");

    m_stack = new QStackedWidget(this);
    setCentralWidget(m_stack);

    // Auth page (unified login + register)
    m_auth = new AuthWidget(m_api.get(), this);
    m_stack->addWidget(m_auth);

    // Main page (post-login)
    m_main = new MainWidget(m_api.get(), m_theme, m_tr, this);
    m_stack->addWidget(m_main);

    // Connect auth success
    connect(m_auth, &AuthWidget::login_success, this, &AuthWindow::on_auth_success);

    // Connect logout
    connect(m_main, &MainWidget::logout_requested, this, &AuthWindow::show_login);

    // Try restore saved session
    if (m_api->load_session()) {
        on_auth_success();
    } else {
        m_stack->setCurrentWidget(m_auth);
    }
}

void AuthWindow::mousePressEvent(QMouseEvent* event)
{
    if (event->button() == Qt::LeftButton) {
        m_dragging = true;
        m_drag_pos = event->globalPosition().toPoint() - frameGeometry().topLeft();
        event->accept();
    }
}

void AuthWindow::mouseMoveEvent(QMouseEvent* event)
{
    if (m_dragging && (event->buttons() & Qt::LeftButton)) {
        move(event->globalPosition().toPoint() - m_drag_pos);
        event->accept();
    }
}

void AuthWindow::mouseReleaseEvent(QMouseEvent* event)
{
    if (event->button() == Qt::LeftButton) {
        m_dragging = false;
        event->accept();
    }
}

void AuthWindow::show_login()
{
    // Clear saved session on logout
    m_api->clear_session();

    hide();

    setWindowFlags(Qt::FramelessWindowHint);
    setAttribute(Qt::WA_TranslucentBackground);
    setStyleSheet("");

    setMinimumSize(700, 448);
    resize(742, 476);
    m_auth->show_login_tab();
    m_stack->setCurrentWidget(m_auth);

    show();
}

void AuthWindow::on_auth_success()
{
    m_api->save_session();

    setWindowFlags(Qt::Window);
    setAttribute(Qt::WA_TranslucentBackground, false);
    setStyleSheet(QString("QMainWindow { background: %1; }").arg(m_theme->color("bg")));

    setMinimumSize(1100, 700);
    resize(1200, 800);

    m_main->set_username(m_api->username());
    m_stack->setCurrentWidget(m_main);

    show();
}
