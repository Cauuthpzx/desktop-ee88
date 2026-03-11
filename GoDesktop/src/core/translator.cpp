#include "core/translator.h"

#include <QFile>
#include <QJsonDocument>

Translator::Translator(QObject* parent)
    : QObject(parent)
    , m_locale("vi_VN")
{
    init_auth_translations();
}

void Translator::load_language(const QString& locale, const QString& json_path)
{
    QFile file(json_path);
    if (!file.open(QIODevice::ReadOnly)) {
        return;
    }
    m_translations[locale] = QJsonDocument::fromJson(file.readAll()).object();
}

void Translator::set_locale(const QString& locale)
{
    if (m_locale != locale && m_translations.contains(locale)) {
        m_locale = locale;
        emit locale_changed(m_locale);
    }
}

QString Translator::locale() const
{
    return m_locale;
}

QString Translator::t(const QString& key) const
{
    if (!m_translations.contains(m_locale)) {
        return key;
    }
    const auto parts = key.split('.');
    return resolve(m_translations[m_locale], parts);
}

QStringList Translator::available_locales() const
{
    return m_translations.keys();
}

QString Translator::locale_label(const QString& locale) const
{
    if (locale == "vi_VN") return "VN";
    if (locale == "en_US") return "EN";
    if (locale == "zh_CN") return QString::fromUtf8("\u4e2d");
    return locale;
}

QString Translator::auth_t(const QString& lang, const QString& key) const
{
    if (m_auth_translations.contains(lang) && m_auth_translations[lang].contains(key))
        return m_auth_translations[lang][key];
    return m_auth_translations["vi"][key];
}

QString Translator::resolve(const QJsonObject& obj, const QStringList& parts) const
{
    if (parts.isEmpty()) {
        return {};
    }

    auto value = obj.value(parts.first());
    if (parts.size() == 1) {
        return value.toString(parts.first());
    }

    if (value.isObject()) {
        return resolve(value.toObject(), parts.mid(1));
    }

    return parts.join('.');
}

void Translator::init_auth_translations()
{
    m_auth_translations = {
        {"vi", {
            {"brand_tagline", QString::fromUtf8("Qu\xe1\xba\xa3n l\xc3\xbd th\xc3\xb4ng minh,\nK\xe1\xba\xbft n\xe1\xbb\x91i m\xe1\xbb\x8di th\xe1\xbb\xa9")},
            {"brand_desc", QString::fromUtf8("N\xe1\xbb\x81n t\xe1\xba\xa3ng qu\xe1\xba\xa3n l\xc3\xbd t\xe1\xba\xadp trung gi\xc3\xbap b\xe1\xba\xa1n ki\xe1\xbb\x83m so\xc3\xa1t,\nt\xe1\xbb\xb1 \xc4\x91\xe1\xbb\x99ng h\xc3\xb3\x61 v\xc3\xa0 t\xe1\xbb\x91i \xc6\xb0u hi\xe1\xbb\x87u su\xe1\xba\xa5t l\xc3\xa0m vi\xe1\xbb\x87\x63.")},
            {"tab_login", QString::fromUtf8("\xc4\x90\xc4\x83ng nh\xe1\xba\xadp")},
            {"tab_register", QString::fromUtf8("\xc4\x90\xc4\x83ng k\xc3\xbd")},
            {"login_title", QString::fromUtf8("Ch\xc3\xa0o m\xe1\xbb\xabng tr\xe1\xbb\x9f l\xe1\xba\xa1i")},
            {"login_desc", QString::fromUtf8("\xc4\x90\xc4\x83ng nh\xe1\xba\xadp \xc4\x91\xe1\xbb\x83 ti\xe1\xba\xbfp t\xe1\xbb\xa5\x63 qu\xe1\xba\xa3n l\xc3\xbd d\xe1\xbb\xb1 \xc3\xa1n c\xe1\xbb\xa7\x61 b\xe1\xba\xa1n")},
            {"register_title", QString::fromUtf8("T\xe1\xba\xa1o t\xc3\xa0i kho\xe1\xba\xa3n")},
            {"register_desc", QString::fromUtf8("\xc4\x90\xc4\x83ng k\xc3\xbd \xc4\x91\xe1\xbb\x83 b\xe1\xba\xaft \xc4\x91\xe1\xba\xa7u s\xe1\xbb\xad d\xe1\xbb\xa5ng MaxHub")},
            {"username", QString::fromUtf8("T\xc3\xaan t\xc3\xa0i kho\xe1\xba\xa3n")},
            {"username_ph", QString::fromUtf8("Nh\xe1\xba\xadp t\xc3\xaan t\xc3\xa0i kho\xe1\xba\xa3n")},
            {"password", QString::fromUtf8("M\xe1\xba\xadt kh\xe1\xba\xa9u")},
            {"password_ph", QString::fromUtf8("T\xe1\xbb\x91i thi\xe1\xbb\x83u 8 k\xc3\xbd t\xe1\xbb\xb1")},
            {"confirm", QString::fromUtf8("X\xc3\xa1\x63 nh\xe1\xba\xadn m\xe1\xba\xadt kh\xe1\xba\xa9u")},
            {"confirm_ph", QString::fromUtf8("Nh\xe1\xba\xadp l\xe1\xba\xa1i m\xe1\xba\xadt kh\xe1\xba\xa9u")},
            {"remember", QString::fromUtf8("Ghi nh\xe1\xbb\x9b \xc4\x91\xc4\x83ng nh\xe1\xba\xadp")},
            {"btn_login", QString::fromUtf8("\xc4\x90\xc4\x83ng nh\xe1\xba\xadp")},
            {"btn_register", QString::fromUtf8("\xc4\x90\xc4\x83ng k\xc3\xbd")},
            {"btn_cancel", QString::fromUtf8("Hu\xe1\xbb\xb7")},
            {"or_continue", QString::fromUtf8("Ho\xe1\xba\xb7\x63 ti\xe1\xba\xbfp t\xe1\xbb\xa5\x63 v\xe1\xbb\x9bi")},
            {"no_account", QString::fromUtf8("Ch\xc6\xb0\x61 c\xc3\xb3 t\xc3\xa0i kho\xe1\xba\xa3n?")},
            {"has_account", QString::fromUtf8("\xc4\x90\xc3\xa3 c\xc3\xb3 t\xc3\xa0i kho\xe1\xba\xa3n?")},
            {"register_now", QString::fromUtf8("\xc4\x90\xc4\x83ng k\xc3\xbd ngay")},
            {"login_now", QString::fromUtf8("\xc4\x90\xc4\x83ng nh\xe1\xba\xadp")},
            {"agree_terms", QString::fromUtf8("T\xc3\xb4i \xc4\x91\xe1\xbb\x93ng \xc3\xbd v\xe1\xbb\x9bi \xc4\x90i\xe1\xbb\x81u kho\xe1\xba\xa3n v\xc3\xa0 Ch\xc3\xadnh s\xc3\xa1\x63h b\xe1\xba\xa3o m\xe1\xba\xadt")},
            {"strength_weak", QString::fromUtf8("Y\xe1\xba\xbfu")},
            {"strength_fair", QString::fromUtf8("Trung b\xc3\xacnh")},
            {"strength_good", QString::fromUtf8("T\xe1\xbb\x91t")},
            {"strength_strong", QString::fromUtf8("M\xe1\xba\xa1nh")},
            {"err_required", QString::fromUtf8("Vui l\xc3\xb2ng nh\xe1\xba\xadp \xc4\x91\xe1\xba\xa7y \xc4\x91\xe1\xbb\xa7 th\xc3\xb4ng tin")},
            {"err_min_pass", QString::fromUtf8("M\xe1\xba\xadt kh\xe1\xba\xa9u ph\xe1\xba\xa3i c\xc3\xb3 t\xe1\xbb\x91i thi\xe1\xbb\x83u 8 k\xc3\xbd t\xe1\xbb\xb1")},
            {"err_confirm", QString::fromUtf8("M\xe1\xba\xadt kh\xe1\xba\xa9u x\xc3\xa1\x63 nh\xe1\xba\xadn kh\xc3\xb4ng kh\xe1\xbb\x9bp")},
            {"err_terms", QString::fromUtf8("Vui l\xc3\xb2ng \xc4\x91\xe1\xbb\x93ng \xc3\xbd v\xe1\xbb\x9bi \xc4\x91i\xe1\xbb\x81u kho\xe1\xba\xa3n s\xe1\xbb\xad d\xe1\xbb\xa5ng")},
            {"err_login", QString::fromUtf8("\xc4\x90\xc4\x83ng nh\xe1\xba\xadp th\xe1\xba\xa5t b\xe1\xba\xa1i")},
            {"err_register", QString::fromUtf8("\xc4\x90\xc4\x83ng k\xc3\xbd th\xe1\xba\xa5t b\xe1\xba\xa1i")},
            {"loading_login", QString::fromUtf8("\xc4\x90\x61ng \xc4\x91\xc4\x83ng nh\xe1\xba\xadp...")},
            {"loading_register", QString::fromUtf8("\xc4\x90\x61ng \xc4\x91\xc4\x83ng k\xc3\xbd...")},
            {"terms_title", QString::fromUtf8("\xc4\x90i\xe1\xbb\x81u kho\xe1\xba\xa3n s\xe1\xbb\xad d\xe1\xbb\xa5ng")},
            {"privacy_title", QString::fromUtf8("Ch\xc3\xadnh s\xc3\xa1\x63h b\xe1\xba\xa3o m\xe1\xba\xadt")},
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
            {"brand_tagline", QString::fromUtf8("\xe6\x99\xba\xe8\x83\xbd\xe7\xae\xa1\xe7\x90\x86,\n\xe8\xbf\x9e\xe6\x8e\xa5\xe4\xb8\x80\xe5\x88\x87")},
            {"brand_desc", QString::fromUtf8("\xe4\xb8\x80\xe4\xb8\xaa\xe9\x9b\x86\xe4\xb8\xad\xe7\xae\xa1\xe7\x90\x86\xe5\xb9\xb3\xe5\x8f\xb0\xef\xbc\x8c\xe5\xb8\xae\xe5\x8a\xa9\xe6\x82\xa8\xe6\x8e\xa7\xe5\x88\xb6\xe3\x80\x81\n\xe8\x87\xaa\xe5\x8a\xa8\xe5\x8c\x96\xe5\x92\x8c\xe4\xbc\x98\xe5\x8c\x96\xe5\xb7\xa5\xe4\xbd\x9c\xe6\xb5\x81\xe7\xa8\x8b\xe3\x80\x82")},
            {"tab_login", QString::fromUtf8("\xe7\x99\xbb\xe5\xbd\x95")},
            {"tab_register", QString::fromUtf8("\xe6\xb3\xa8\xe5\x86\x8c")},
            {"login_title", QString::fromUtf8("\xe6\xac\xa2\xe8\xbf\x8e\xe5\x9b\x9e\xe6\x9d\xa5")},
            {"login_desc", QString::fromUtf8("\xe7\x99\xbb\xe5\xbd\x95\xe4\xbb\xa5\xe7\xbb\xa7\xe7\xbb\xad\xe7\xae\xa1\xe7\x90\x86\xe6\x82\xa8\xe7\x9a\x84\xe9\xa1\xb9\xe7\x9b\xae")},
            {"register_title", QString::fromUtf8("\xe5\x88\x9b\xe5\xbb\xba\xe8\xb4\xa6\xe5\x8f\xb7")},
            {"register_desc", QString::fromUtf8("\xe6\xb3\xa8\xe5\x86\x8c\xe4\xbb\xa5\xe5\xbc\x80\xe5\xa7\x8b\xe4\xbd\xbf\xe7\x94\xa8 MaxHub")},
            {"username", QString::fromUtf8("\xe7\x94\xa8\xe6\x88\xb7\xe5\x90\x8d")},
            {"username_ph", QString::fromUtf8("\xe8\xbe\x93\xe5\x85\xa5\xe7\x94\xa8\xe6\x88\xb7\xe5\x90\x8d")},
            {"password", QString::fromUtf8("\xe5\xaf\x86\xe7\xa0\x81")},
            {"password_ph", QString::fromUtf8("\xe6\x9c\x80\xe5\xb0\x91" "8\xe4\xb8\xaa\xe5\xad\x97\xe7\xac\xa6")},
            {"confirm", QString::fromUtf8("\xe7\xa1\xae\xe8\xae\xa4\xe5\xaf\x86\xe7\xa0\x81")},
            {"confirm_ph", QString::fromUtf8("\xe5\x86\x8d\xe6\xac\xa1\xe8\xbe\x93\xe5\x85\xa5\xe5\xaf\x86\xe7\xa0\x81")},
            {"remember", QString::fromUtf8("\xe8\xae\xb0\xe4\xbd\x8f\xe7\x99\xbb\xe5\xbd\x95")},
            {"btn_login", QString::fromUtf8("\xe7\x99\xbb\xe5\xbd\x95")},
            {"btn_register", QString::fromUtf8("\xe6\xb3\xa8\xe5\x86\x8c")},
            {"btn_cancel", QString::fromUtf8("\xe5\x8f\x96\xe6\xb6\x88")},
            {"or_continue", QString::fromUtf8("\xe6\x88\x96\xe8\x80\x85\xe9\x80\x9a\xe8\xbf\x87\xe4\xbb\xa5\xe4\xb8\x8b\xe6\x96\xb9\xe5\xbc\x8f\xe7\xbb\xa7\xe7\xbb\xad")},
            {"no_account", QString::fromUtf8("\xe6\xb2\xa1\xe6\x9c\x89\xe8\xb4\xa6\xe5\x8f\xb7\xef\xbc\x9f")},
            {"has_account", QString::fromUtf8("\xe5\xb7\xb2\xe6\x9c\x89\xe8\xb4\xa6\xe5\x8f\xb7\xef\xbc\x9f")},
            {"register_now", QString::fromUtf8("\xe7\xab\x8b\xe5\x8d\xb3\xe6\xb3\xa8\xe5\x86\x8c")},
            {"login_now", QString::fromUtf8("\xe7\x99\xbb\xe5\xbd\x95")},
            {"agree_terms", QString::fromUtf8("\xe6\x88\x91\xe5\x90\x8c\xe6\x84\x8f\xe6\x9c\x8d\xe5\x8a\xa1\xe6\x9d\xa1\xe6\xac\xbe\xe5\x92\x8c\xe9\x9a\x90\xe7\xa7\x81\xe6\x94\xbf\xe7\xad\x96")},
            {"strength_weak", QString::fromUtf8("\xe5\xbc\xb1")},
            {"strength_fair", QString::fromUtf8("\xe4\xb8\x80\xe8\x88\xac")},
            {"strength_good", QString::fromUtf8("\xe8\x89\xaf\xe5\xa5\xbd")},
            {"strength_strong", QString::fromUtf8("\xe5\xbc\xba")},
            {"err_required", QString::fromUtf8("\xe8\xaf\xb7\xe5\xa1\xab\xe5\x86\x99\xe6\x89\x80\xe6\x9c\x89\xe5\xad\x97\xe6\xae\xb5")},
            {"err_min_pass", QString::fromUtf8("\xe5\xaf\x86\xe7\xa0\x81\xe8\x87\xb3\xe5\xb0\x91\xe9\x9c\x80\xe8\xa6\x81" "8\xe4\xb8\xaa\xe5\xad\x97\xe7\xac\xa6")},
            {"err_confirm", QString::fromUtf8("\xe4\xb8\xa4\xe6\xac\xa1\xe5\xaf\x86\xe7\xa0\x81\xe4\xb8\x8d\xe4\xb8\x80\xe8\x87\xb4")},
            {"err_terms", QString::fromUtf8("\xe8\xaf\xb7\xe5\x90\x8c\xe6\x84\x8f\xe6\x9c\x8d\xe5\x8a\xa1\xe6\x9d\xa1\xe6\xac\xbe")},
            {"err_login", QString::fromUtf8("\xe7\x99\xbb\xe5\xbd\x95\xe5\xa4\xb1\xe8\xb4\xa5")},
            {"err_register", QString::fromUtf8("\xe6\xb3\xa8\xe5\x86\x8c\xe5\xa4\xb1\xe8\xb4\xa5")},
            {"loading_login", QString::fromUtf8("\xe6\xad\xa3\xe5\x9c\xa8\xe7\x99\xbb\xe5\xbd\x95...")},
            {"loading_register", QString::fromUtf8("\xe6\xad\xa3\xe5\x9c\xa8\xe6\xb3\xa8\xe5\x86\x8c...")},
            {"terms_title", QString::fromUtf8("\xe6\x9c\x8d\xe5\x8a\xa1\xe6\x9d\xa1\xe6\xac\xbe")},
            {"privacy_title", QString::fromUtf8("\xe9\x9a\x90\xe7\xa7\x81\xe6\x94\xbf\xe7\xad\x96")},
        }},
    };
}
