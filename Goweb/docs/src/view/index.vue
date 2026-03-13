<template>
  <div class="site-container">
    <!-- Right Sidebar -->
    <aside :class="classAside" style="display: flex; flex-direction: column;">
      <div class="lay-aside-top">
        <lay-button type="primary" size="xs" :class="classAsideBtn" @click="toggleSidebar()">
          <lay-icon :type="sidebarIcon" size="40"></lay-icon>
        </lay-button>
      </div>
      <div style="flex: 1;"></div>
    </aside>
    <div class="site-layui-main">
      <div class="site-zfj">
        <img src="/icons/duango_logo.png" alt="MaxHub" style="width: 360px; height: auto;" />
      </div>
      <div class="site-desc">
        <cite>{{ t("home.tagline") }}</cite>
      </div>
      <div class="site-download">
        <a class="layui-inline site-down site-down-download" href="/GoDesktop-v1.0.zip" download>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          {{ t("home.download_pc") }}
        </a>
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
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useAppStore } from "../store/app";
import { useAuthStore } from "../store/auth";
import { useI18n } from "layui-component/index";

const { t } = useI18n();
const appStore = useAppStore();
const authStore = useAuthStore();

const changeTheme = () => {
  appStore.theme = appStore.theme === "dark" ? "light" : "dark";
};

// Right sidebar
const sidebarShow = ref(false);
let enableAnimation = false;
const sidebarIcon = ref("layui-icon-right");

const classAside = computed(() => [
  "lay-aside",
  { "lay-aside-animation": enableAnimation },
  { "lay-aside-collapse": !sidebarShow.value },
]);

const classAsideBtn = computed(() => {
  let classBtn: any[];
  if (enableAnimation) {
    classBtn = [
      "lay-aside-collapse-btn",
      "lay-aside-animation",
      { "lay-aside-collapse-btn-collapse": !sidebarShow.value },
    ];
  } else {
    classBtn = [
      "lay-aside-collapse-btn",
      { "lay-aside-collapse-btn-collapse": !sidebarShow.value },
    ];
    enableAnimation = true;
  }
  return classBtn;
});

const toggleSidebar = () => {
  sidebarShow.value = !sidebarShow.value;
  sidebarIcon.value = sidebarShow.value ? "layui-icon-left" : "layui-icon-right";
};
</script>

<style scoped>
.site-container {
  background: #fff;
  margin-top: 60px;
  min-height: calc(100vh - 60px);
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

.site-download .site-down-download {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  color: #fff;
  font-size: 15px;
  padding: 0 28px;
  height: 42px;
  line-height: 42px;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  display: inline-flex;
  align-items: center;
}

.site-download .site-down-download:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
  transform: translateY(-2px);
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
  padding: 16px 200px 10px;
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

/* Left Sidebar */
.lay-aside {
  position: fixed;
  top: 65px;
  left: 0px;
  box-sizing: border-box;
  width: 180px;
  padding: 0 25px;
  border-right: 1px solid rgb(229 230 235);
  transition: none;
  -webkit-transition: none;
  height: calc(100% - 60px);
  z-index: 100;
  background: #fff;
}

.lay-aside-collapse {
  left: -180px;
  opacity: 0.7;
}

.lay-aside-top {
  height: 29px;
}

.lay-aside-collapse-btn {
  position: fixed;
  left: 180px;
  top: calc(50% - 20px);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 40px;
  background-color: #16baaa;
  border-radius: 0px;
  border-top-right-radius: 4px;
  border-bottom-right-radius: 4px;
  border: #16baaa 1px solid;
  border-left: none;
  box-shadow: 2px 0 8px 0 rgb(29 35 41 / 10%);
  transition: none;
  -webkit-transition: none;
  color: #fff;
  font-weight: bold;
}

.lay-aside-collapse-btn:hover {
  background-color: #13a89a;
}

.lay-aside-collapse-btn-collapse {
  left: 0px;
}

.lay-aside-animation {
  transition: left 200ms;
  -webkit-transition: left 200ms;
}

@media screen and (max-width: 768px) {
  .lay-aside {
    width: 100px;
  }
  .lay-aside-collapse {
    left: -100px;
  }
  .lay-aside-collapse-btn {
    left: 100px;
  }
  .lay-aside-collapse-btn-collapse {
    left: 0px;
  }
}
</style>
