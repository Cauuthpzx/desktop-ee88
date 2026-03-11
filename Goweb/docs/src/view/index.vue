<template>
  <div class="index-wrapper">
    <div class="index-side" :class="{ collapsed: sideCollapsed }">
      <ul class="layui-menu layui-menu-lg layui-menu-docs">
        <li class="layui-menu-item-group">
          <div class="layui-menu-body-title">{{ t("sidebar.navigation") }}</div>
          <hr />
          <ul>
            <li
              v-for="item in sideMenus"
              :key="item.path"
              :class="[currentPath === item.path ? 'layui-menu-item-checked2' : '']"
              @click="router.push(item.path)"
            >
              <div class="layui-menu-body-title">
                <router-link :to="item.path">
                  <lay-icon :type="item.icon" size="14px" style="margin-right: 6px" />
                  <span>{{ t(item.label) }}</span>
                </router-link>
              </div>
            </li>
          </ul>
        </li>
        <li class="layui-menu-item-group">
          <div class="layui-menu-body-title">{{ t("sidebar.reports") }}</div>
          <hr />
          <ul>
            <li
              v-for="item in reportMenus"
              :key="item.path"
              :class="[currentPath === item.path ? 'layui-menu-item-checked2' : '']"
              @click="router.push(item.path)"
            >
              <div class="layui-menu-body-title">
                <router-link :to="item.path">
                  <lay-icon :type="item.icon" size="14px" style="margin-right: 6px" />
                  <span>{{ t(item.label) }}</span>
                </router-link>
              </div>
            </li>
          </ul>
        </li>
        <li class="layui-menu-item-group">
          <div class="layui-menu-body-title">{{ t("sidebar.system") }}</div>
          <hr />
          <ul>
            <li
              v-for="item in systemMenus"
              :key="item.path"
              :class="[currentPath === item.path ? 'layui-menu-item-checked2' : '']"
              @click="router.push(item.path)"
            >
              <div class="layui-menu-body-title">
                <router-link :to="item.path">
                  <lay-icon :type="item.icon" size="14px" style="margin-right: 6px" />
                  <span>{{ t(item.label) }}</span>
                </router-link>
              </div>
            </li>
          </ul>
        </li>
      </ul>
    </div>
    <div class="sidebar-toggle" :class="{ 'toggle-collapsed': sideCollapsed }" @click="sideCollapsed = !sideCollapsed">
      <lay-icon :type="sideCollapsed ? 'layui-icon-right' : 'layui-icon-left'" size="12px" />
    </div>
    <div class="index-body">
      <div class="site-container">
        <div class="site-layui-main">
          <div class="site-zfj">
            <img src="/icons/duango_logo.png" alt="MaxHub" style="width: 360px; height: auto;" />
          </div>
          <div class="site-desc">
            <cite>{{ t("home.tagline") }}</cite>
          </div>
          <div class="site-download">
            <router-link class="layui-inline site-down site-down-primary" to="/zh-CN/components">
              {{ t("home.explore") }}
            </router-link>
            <a
              class="layui-inline site-down"
              href="javascript:void(0);"
              @click="changeTheme"
            >
              {{ appStore.theme === "dark" ? t("home.lightMode") : t("home.darkMode") }}
            </a>
          </div>
          <div class="site-welcome" v-if="authStore.user">
            <lay-icon type="layui-icon-username" size="14px" color="#16baaa" />
            <span>{{ t("home.welcome") }}, <strong>{{ authStore.user.username }}</strong></span>
          </div>
        </div>
        <div class="box-list">
          <lay-row :space="16">
            <lay-col :md="8" :sm="12" :xs="12">
              <div class="box">
                <div class="icon">
                  <lay-icon type="layui-icon-engine" size="24px" color="#16baaa" />
                </div>
                <h2 class="title">Go Backend</h2>
                <p class="details">{{ t("home.features.goDesc") }}</p>
              </div>
            </lay-col>
            <lay-col :md="8" :sm="12" :xs="12">
              <div class="box">
                <div class="icon">
                  <lay-icon type="layui-icon-website" size="24px" color="#1e9fff" />
                </div>
                <h2 class="title">Vue 3 Web</h2>
                <p class="details">{{ t("home.features.vueDesc") }}</p>
              </div>
            </lay-col>
            <lay-col :md="8" :sm="12" :xs="12">
              <div class="box">
                <div class="icon">
                  <lay-icon type="layui-icon-app" size="24px" color="#e67e22" />
                </div>
                <h2 class="title">Qt6 Desktop</h2>
                <p class="details">{{ t("home.features.qtDesc") }}</p>
              </div>
            </lay-col>
            <lay-col :md="8" :sm="12" :xs="12">
              <div class="box">
                <div class="icon">
                  <lay-icon type="layui-icon-template-1" size="24px" color="#16b777" />
                </div>
                <h2 class="title">77+ Components</h2>
                <p class="details">{{ t("home.features.compDesc") }}</p>
              </div>
            </lay-col>
            <lay-col :md="8" :sm="12" :xs="12">
              <div class="box">
                <div class="icon">
                  <lay-icon type="layui-icon-moon" size="24px" color="#9b59b6" />
                </div>
                <h2 class="title">Dark Theme</h2>
                <p class="details">{{ t("home.features.themeDesc") }}</p>
              </div>
            </lay-col>
            <lay-col :md="8" :sm="12" :xs="12">
              <div class="box">
                <div class="icon">
                  <lay-icon type="layui-icon-log" size="24px" color="#ff5722" />
                </div>
                <h2 class="title">Logging</h2>
                <p class="details">{{ t("home.features.logDesc") }}</p>
              </div>
            </lay-col>
          </lay-row>
        </div>
        <div class="footer footer-index">
          <p>MaxHub &copy; {{ new Date().getFullYear() }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAppStore } from "../store/app";
import { useAuthStore } from "../store/auth";
import { useI18n } from "layui-component/index";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const appStore = useAppStore();
const authStore = useAuthStore();

const sideCollapsed = ref(false);
const currentPath = ref(route.path);
watch(() => route.path, (val) => { currentPath.value = val; }, { immediate: true });

const changeTheme = () => {
  appStore.theme = appStore.theme === "dark" ? "light" : "dark";
};

const sideMenus = [
  { path: "/zh-CN/index", icon: "layui-icon-home", label: "nav.home" },
  { path: "/zh-CN/customers", icon: "layui-icon-group", label: "nav.customers" },
  { path: "/zh-CN/components", icon: "layui-icon-template-1", label: "nav.components" },
  { path: "/zh-CN/guide", icon: "layui-icon-read", label: "nav.guide" },
  { path: "/zh-CN/resources", icon: "layui-icon-link", label: "nav.resources" },
];

const reportMenus = [
  { path: "/zh-CN/reports/lottery", icon: "layui-icon-chart-screen", label: "nav.report_lottery" },
  { path: "/zh-CN/reports/transaction", icon: "layui-icon-log", label: "nav.report_transaction" },
  { path: "/zh-CN/reports/provider", icon: "layui-icon-survey", label: "nav.report_provider" },
];

const systemMenus = [
  { path: "/zh-CN/bets/lottery", icon: "layui-icon-form", label: "nav.bets_lottery" },
  { path: "/zh-CN/bets/provider", icon: "layui-icon-form", label: "nav.bets_provider" },
  { path: "/zh-CN/commission/withdrawal", icon: "layui-icon-diamond", label: "nav.commission_withdrawal" },
  { path: "/zh-CN/commission/deposit", icon: "layui-icon-diamond", label: "nav.commission_deposit" },
];
</script>

<style scoped>
.index-wrapper {
  display: flex;
  height: 100%;
  position: relative;
}

.index-side {
  width: 200px;
  min-width: 200px;
  height: 100%;
  overflow-y: auto;
  border-right: 1px solid #eeeeee;
  background: #fff;
  transition: width 0.25s ease, min-width 0.25s ease, opacity 0.25s ease;
  padding-top: 10px;
}

.index-side.collapsed {
  width: 0;
  min-width: 0;
  opacity: 0;
  overflow: hidden;
  border-right: none;
}

.sidebar-toggle {
  position: absolute;
  left: 200px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  width: 16px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-left: none;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  transition: left 0.25s ease, background 0.15s;
  color: #999;
}

.sidebar-toggle:hover {
  background: #e8e8e8;
  color: #666;
}

.sidebar-toggle.toggle-collapsed {
  left: 0;
}

.index-body {
  flex: 1;
  height: 100%;
  overflow-y: auto;
}

.site-container {
  background: #fff;
  min-height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.site-layui-main {
  padding: 36px 0 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.site-zfj {
  margin-bottom: 8px;
}

.site-desc {
  position: relative;
  margin-bottom: 10px;
}

.site-desc cite {
  display: block;
  margin-top: 6px;
  color: rgba(60, 60, 60, 0.7);
  font-style: normal;
  font-size: 15px;
}

.site-download {
  margin-top: 18px;
  display: flex;
  gap: 12px;
}

.site-download a {
  padding: 0 20px;
  height: 36px;
  line-height: 36px;
  border-radius: 6px;
  background: #f1f1f1;
  border: 1px solid #e2e2e2;
  font-size: 14px;
  color: #476582;
  font-weight: 500;
  transition: all 0.3s;
  text-decoration: none;
}

.site-download a:hover {
  border-radius: 10px;
}

.site-download .site-down-primary {
  background: #16baaa;
  border-color: #16baaa;
  color: #fff;
}

.site-welcome {
  margin-top: 14px;
  font-size: 13px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 6px;
}

.box-list {
  padding: 16px 60px 10px;
  flex: 1;
}

.box {
  background-color: #f9f9f9;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 16px 20px;
  height: 100%;
  transition: border-color 0.3s;
}

.box:hover {
  border-color: #16baaa;
}

.box .icon {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 10px;
  border-radius: 8px;
  background-color: #f0f0f0;
  width: 40px;
  height: 40px;
}

.box .title {
  line-height: 22px;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.box .details {
  font-size: 12px;
  padding-top: 4px;
  line-height: 20px;
  color: rgba(60, 60, 60, 0.7);
}

.footer {
  width: 100%;
  padding: 14px 0;
  text-align: center;
  border-top: 1px solid #eee;
  color: rgba(60, 60, 60, 0.5);
  font-size: 12px;
  background: #fafafa;
  margin-top: auto;
}

@media screen and (max-width: 768px) {
  .index-side {
    display: none;
  }
  .sidebar-toggle {
    display: none;
  }
}
</style>
