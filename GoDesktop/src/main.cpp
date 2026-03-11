#include "core/auth_window.h"

#include <QApplication>
#include <QFont>

#ifdef _WIN32
#include <windows.h>
#include <io.h>
#include <fcntl.h>
#endif

#include <cstdio>

// Custom message handler: xuất UTF-8 trực tiếp, bypass toLocal8Bit() mất ký tự
static void utf8_message_handler(QtMsgType type, const QMessageLogContext& ctx, const QString& msg)
{
    Q_UNUSED(ctx);
    const char* prefix = "";
    switch (type) {
    case QtDebugMsg:    prefix = "[DEBUG] ";    break;
    case QtInfoMsg:     prefix = "[INFO] ";     break;
    case QtWarningMsg:  prefix = "[WARN] ";     break;
    case QtCriticalMsg: prefix = "[CRITICAL] "; break;
    case QtFatalMsg:    prefix = "[FATAL] ";    break;
    }
    QByteArray utf8 = msg.toUtf8();
    fprintf(stderr, "%s%s\n", prefix, utf8.constData());
    fflush(stderr);
    if (type == QtFatalMsg)
        abort();
}

int main(int argc, char* argv[])
{
#ifdef _WIN32
    // Force UTF-8 console output — hiển thị Vietnamese/CJK
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
    // Set stderr to binary mode — tránh CR/LF conversion làm hỏng UTF-8
    _setmode(_fileno(stderr), _O_BINARY);
#endif

    // Cài message handler UTF-8 TRƯỚC khi tạo QApplication
    qInstallMessageHandler(utf8_message_handler);

    QApplication app(argc, argv);
    app.setApplicationName("MaxHub");
    app.setOrganizationName("MaxHub");

    // Font mặc định — Segoe UI + Microsoft YaHei fallback cho CJK
    QFont default_font("Segoe UI", 10);
    default_font.setFamilies({"Segoe UI", "Microsoft YaHei", "SimSun"});
    app.setFont(default_font);

    AuthWindow window;
    window.show();

    return app.exec();
}
