// Import shared translations và map sang format GoWeb dùng
import vi_VN_shared from "../../../../shared/lang/vi_VN.json";
import en_US_shared from "../../../../shared/lang/en_US.json";
import zh_CN_shared from "../../../../shared/lang/zh_CN.json";

// Web-only fields không nằm trong shared
const web_extras: Record<string, Record<string, string>> = {
  vi_VN: { changelog: "Nhật ký thay đổi", version: "Phiên bản", download: "Tải về", sponsors: "Nhà tài trợ", join_sponsors: "Trở thành nhà tài trợ" },
  en_US: { changelog: "Changelog", version: "Version", download: "Downloads", sponsors: "Sponsors", join_sponsors: "Become a Sponsor" },
  zh_CN: { changelog: "更新日志", version: "当前版本", download: "下载量", sponsors: "赞助商", join_sponsors: "成为赞助商" },
};

function map_shared(shared: Record<string, any>, locale: string) {
  const extras = web_extras[locale] || web_extras.en_US;
  return {
    nav: shared.nav,
    sidebar: shared.sidebar,
    common: shared.common,
    customers: shared.customers,
    settings: shared.settings,
    lottery_report: shared.lottery_report,
    transaction_log: shared.transaction_log,
    provider_report: shared.provider_report,
    lottery_bets: shared.lottery_bets,
    provider_bets: shared.provider_bets,
    withdrawal_history: shared.withdrawal_history,
    deposit_history: shared.deposit_history,
    home: {
      description: shared.home.description,
      tagline: shared.home.tagline,
      explore: shared.home.explore,
      download_pc: shared.home.download_pc,
      lightMode: shared.home.light_mode,
      darkMode: shared.home.dark_mode,
      welcome: shared.home.welcome,
      ...extras,
      features: {
        goDesc: shared.features.go_desc,
        vueDesc: shared.features.vue_desc,
        qtDesc: shared.features.qt_desc,
        compDesc: shared.features.comp_desc,
        themeDesc: shared.features.theme_desc,
        logDesc: shared.features.log_desc,
      },
    },
  };
}

export const vi_VN = map_shared(vi_VN_shared, "vi_VN");
export const en_US = map_shared(en_US_shared, "en_US");
export const zh_CN = map_shared(zh_CN_shared, "zh_CN");
