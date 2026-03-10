#include "core/auth_window.h"

#include <QApplication>
#include <QFont>

int main(int argc, char* argv[])
{
    QApplication app(argc, argv);
    app.setApplicationName("MaxHub");
    app.setOrganizationName("MaxHub");

    // Font mặc định
    QFont default_font("Segoe UI", 10);
    app.setFont(default_font);

    AuthWindow window;
    window.show();

    return app.exec();
}
