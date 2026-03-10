#include "core/home_page.h"
#include "core/theme_manager.h"
#include "core/translator.h"

#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QGridLayout>
#include <QPixmap>
#include <QScrollArea>

HomePage::HomePage(ThemeManager* theme, Translator* tr, QWidget* parent)
    : QWidget(parent)
    , m_theme(theme)
    , m_tr(tr)
{
    setup_ui();
}

void HomePage::set_username(const QString& username)
{
    m_welcome_name->setText(username.isEmpty() ? "User" : username);
}

void HomePage::setup_ui()
{
    auto* outer = new QVBoxLayout(this);
    outer->setContentsMargins(0, 0, 0, 0);
    outer->setSpacing(0);

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

    m_welcome_name = new QLabel("User");
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
    outer->addWidget(scroll);
}

void HomePage::apply_theme()
{
    const auto bg = m_theme->color("bg");
    const auto bg2 = m_theme->color("bg_secondary");
    const auto bg3 = m_theme->color("bg_tertiary");
    const auto bg_hover = m_theme->color("bg_hover");
    const auto text1 = m_theme->color("text_primary");
    const auto text_m = m_theme->color("text_muted");
    const auto text2 = m_theme->color("text_secondary");
    const auto text_footer = m_theme->color("text_footer");
    const auto border_box = m_theme->color("border_box");
    const auto border_light = m_theme->color("border_light");
    const auto primary = m_theme->color("primary");
    const auto footer_bg = m_theme->color("footer_bg");

    // Scroll area background
    setStyleSheet(QString("background: %1;").arg(bg));

    m_hero_widget->setStyleSheet(QString("background: %1; border: none;").arg(bg));
    m_hero_title->setStyleSheet(QString(
        "color: %1; font-size: 40px; font-weight: 900;"
        "letter-spacing: 2px; opacity: 0.86; border: none;"
    ).arg(text1));
    m_hero_tagline->setStyleSheet(QString(
        "color: %1; font-size: 15px; border: none;"
    ).arg(text_m));

    m_welcome_text->setStyleSheet(QString(
        "color: %1; font-size: 13px; border: none;"
    ).arg(text2));
    m_welcome_name->setStyleSheet(QString(
        "color: %1; font-size: 13px; font-weight: bold; border: none;"
    ).arg(text1));

    m_explore_btn->setStyleSheet(QString(
        "QPushButton {"
        "  background: %1; color: #fff; border: 1px solid %1;"
        "  padding: 0 20px; height: 36px; font-size: 14px; font-weight: 500;"
        "  border-radius: 6px;"
        "}"
        "QPushButton:hover { border-radius: 10px; }"
    ).arg(primary));

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

    m_footer->setStyleSheet(QString(
        "background: %1; border-top: 1px solid %2;"
    ).arg(footer_bg, border_light));
    m_footer_text->setStyleSheet(QString(
        "color: %1; font-size: 12px; border: none;"
    ).arg(text_footer));
}

void HomePage::retranslate()
{
    m_hero_tagline->setText(m_tr->t("home.tagline"));
    m_explore_btn->setText(m_tr->t("home.explore"));
    m_welcome_text->setText(m_tr->t("home.welcome") + ", ");

    const QString feature_keys[] = {"go", "vue", "qt", "comp", "theme", "log"};
    for (int i = 0; i < m_feature_titles.size(); ++i) {
        m_feature_titles[i]->setText(m_tr->t("features." + feature_keys[i] + "_title"));
        m_feature_descs[i]->setText(m_tr->t("features." + feature_keys[i] + "_desc"));
    }
}
