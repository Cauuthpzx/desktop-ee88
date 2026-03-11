#include "core/auth_window.h"

#include <QApplication>
#include <QFont>

int main(int argc, char* argv[])
{
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
