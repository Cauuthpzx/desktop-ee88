<template>
  <lay-config-provider
    v-cloak
    :locale="locale"
    :locales="locales"
    :theme="appStore.theme"
    :themeVariable="appStore.themeVariable"
  >
    <lay-layout class="layui-layout-document" style="height: 100%">
      <lay-header>
        <lay-logo>
          <img src="/icons/maxhub_logo_3.svg" alt="MaxHub" style="height: 42px; width: auto;" />
        </lay-logo>
        <ul
          class="layui-nav layui-layout-left"
          style="margin-top: 0px; margin-bottom: 0px"
        >
          <li
            class="layui-nav-item"
            :class="{ 'layui-active': currentPath.includes('/zh-CN/index') }"
          >
            <router-link to="/zh-CN/index">
              <lay-icon type="layui-icon-home" size="16px" style="margin-right: 4px" />
              {{ t("nav.home") }}
            </router-link>
          </li>
          <li
            class="layui-nav-item"
            :class="{
              'layui-active': currentPath.includes('/zh-CN/customers'),
            }"
          >
            <router-link to="/zh-CN/customers">
              <lay-icon type="layui-icon-group" size="16px" style="margin-right: 4px" />
              {{ t("nav.customers") }}
            </router-link>
          </li>
          <li
            class="layui-nav-item"
            :class="{
              'layui-active': currentPath.includes('/zh-CN/reports'),
            }"
          >
            <a href="javascript:void(0);">
              <lay-icon type="layui-icon-chart-screen" size="16px" style="margin-right: 4px" />
              {{ t("nav.reports") }}
            </a>
            <dl class="layui-nav-child">
              <dd :class="{ 'layui-this': currentPath === '/zh-CN/reports/lottery' }">
                <router-link to="/zh-CN/reports/lottery">{{ t("nav.report_lottery") }}</router-link>
              </dd>
              <dd :class="{ 'layui-this': currentPath === '/zh-CN/reports/transaction' }">
                <router-link to="/zh-CN/reports/transaction">{{ t("nav.report_transaction") }}</router-link>
              </dd>
              <dd :class="{ 'layui-this': currentPath === '/zh-CN/reports/provider' }">
                <router-link to="/zh-CN/reports/provider">{{ t("nav.report_provider") }}</router-link>
              </dd>
            </dl>
          </li>
          <li
            class="layui-nav-item"
            :class="{
              'layui-active': currentPath.includes('/zh-CN/commission'),
            }"
          >
            <a href="javascript:void(0);">
              <lay-icon type="layui-icon-diamond" size="16px" style="margin-right: 4px" />
              {{ t("nav.commission") }}
            </a>
            <dl class="layui-nav-child">
              <dd :class="{ 'layui-this': currentPath === '/zh-CN/commission/withdrawal' }">
                <router-link to="/zh-CN/commission/withdrawal">{{ t("nav.commission_withdrawal") }}</router-link>
              </dd>
              <dd :class="{ 'layui-this': currentPath === '/zh-CN/commission/deposit' }">
                <router-link to="/zh-CN/commission/deposit">{{ t("nav.commission_deposit") }}</router-link>
              </dd>
            </dl>
          </li>
          <li
            class="layui-nav-item"
            :class="{
              'layui-active': currentPath.includes('/zh-CN/bets'),
            }"
          >
            <a href="javascript:void(0);">
              <lay-icon type="layui-icon-form" size="16px" style="margin-right: 4px" />
              {{ t("nav.bets") }}
            </a>
            <dl class="layui-nav-child">
              <dd :class="{ 'layui-this': currentPath === '/zh-CN/bets/lottery' }">
                <router-link to="/zh-CN/bets/lottery">{{ t("nav.bets_lottery") }}</router-link>
              </dd>
              <dd :class="{ 'layui-this': currentPath === '/zh-CN/bets/provider' }">
                <router-link to="/zh-CN/bets/provider">{{ t("nav.bets_provider") }}</router-link>
              </dd>
            </dl>
          </li>
          <li
            class="layui-nav-item"
            :class="{ 'layui-active': currentPath.includes('/zh-CN/guide') }"
          >
            <router-link to="/zh-CN/guide"> {{ t("nav.guide") }} </router-link>
          </li>
          <li
            class="layui-nav-item"
            :class="{
              'layui-active': currentPath.includes('/zh-CN/components'),
            }"
          >
            <router-link to="/zh-CN/components">
              {{ t("nav.components") }}
            </router-link>
          </li>
          <li
            class="layui-nav-item"
            :class="{
              'layui-active': currentPath.includes('/zh-CN/resources'),
            }"
          >
            <router-link to="/zh-CN/resources">
              {{ t("nav.resources") }}
            </router-link>
          </li>
          <li class="layui-nav-item layui-docsearch">
            <lay-form>
              <lay-search :datas="menus" />
            </lay-form>
          </li>
        </ul>
        <ul
          class="layui-nav layui-layout-right"
          style="margin-top: 0px; margin-bottom: 0px"
        >
          <li class="layui-nav-item">
            <lay-dropdown>
              <a href="javascript:void(0);">
                <lay-icon size="17px" type="layui-icon-theme"> </lay-icon>
              </a>
              <template #content>
                <div class="theme-panel">
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-primary-color']"
                  ></lay-color-picker>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-normal-color']"
                  ></lay-color-picker>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-warm-color']"
                  ></lay-color-picker>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-danger-color']"
                  ></lay-color-picker>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-checked-color']"
                  ></lay-color-picker>
                  <lay-input
                    v-model="appStore.themeVariable['--global-border-radius']"
                    style="display: inline-block; width: 130px"
                  ></lay-input>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-neutral-color-1']"
                  ></lay-color-picker>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-neutral-color-2']"
                  ></lay-color-picker>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-neutral-color-3']"
                  ></lay-color-picker>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-neutral-color-4']"
                  ></lay-color-picker>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-neutral-color-5']"
                  ></lay-color-picker>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-neutral-color-6']"
                  ></lay-color-picker>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-neutral-color-7']"
                  ></lay-color-picker>
                  <lay-color-picker
                    v-model="appStore.themeVariable['--global-neutral-color-8']"
                  ></lay-color-picker>
                  <lay-button
                    :fluid="true"
                    border="green"
                    border-style="dashed"
                    @click="resetThemeVariable"
                    >Đặt lại</lay-button
                  >
                </div>
              </template>
            </lay-dropdown>
          </li>
          <li class="layui-nav-item">
            <lay-dropdown>
              <a href="javascript:void(0);" class="locale-trigger">
                <img :src="localeFlags[locale]" class="locale-flag" />
                <span class="locale-label">{{ localeLabels[locale] }}</span>
              </a>
              <template #content>
                <lay-dropdown-menu>
                  <lay-dropdown-menu-item
                    v-for="lang in localeOrder"
                    :key="lang"
                    @click="changeLocale(lang)"
                  >
                    <div class="locale-menu-item">
                      <img :src="localeFlags[lang]" class="locale-flag-sm" />
                      <span>{{ localeLabels[lang] }}</span>
                      <lay-icon
                        v-if="locale === lang"
                        type="layui-icon-ok"
                        size="12px"
                        style="margin-left: auto"
                      />
                    </div>
                  </lay-dropdown-menu-item>
                </lay-dropdown-menu>
              </template>
            </lay-dropdown>
          </li>
          <li class="layui-nav-item" v-if="authStore.is_authenticated">
            <lay-dropdown>
              <a href="javascript:void(0);">
                <lay-icon type="layui-icon-username" size="16px" />
                {{ authStore.user?.username || 'User' }}
              </a>
              <template #content>
                <lay-dropdown-menu>
                  <lay-dropdown-menu-item @click="goChangePassword">
                    <lay-icon type="layui-icon-password" size="14px" />
                    Đổi mật khẩu
                  </lay-dropdown-menu-item>
                  <lay-dropdown-menu-item @click="handleLogout">
                    <lay-icon type="layui-icon-logout" size="14px" />
                    Đăng xuất
                  </lay-dropdown-menu-item>
                </lay-dropdown-menu>
              </template>
            </lay-dropdown>
          </li>
          <li class="layui-nav-item">
            <a href="javascript:void(0)">
              <lay-switch
                v-model="appStore.theme"
                class="switch"
                onswitch-value="dark"
                unswitch-value="light"
                onswitch-color="rgba(255, 255, 255, 0.05)"
                unswitch-color="rgba(255, 255, 255, 0.05)"
              >
                <template #onswitch-icon>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="rgba(60, 60, 60, .7)"
                    aria-hidden="true"
                    focusable="false"
                    viewBox="0 0 24 24"
                    class="vt-switch-appearance-moon"
                  >
                    <path
                      d="M12.1,22c-0.3,0-0.6,0-0.9,0c-5.5-0.5-9.5-5.4-9-10.9c0.4-4.8,4.2-8.6,9-9c0.4,0,0.8,0.2,1,0.5c0.2,0.3,0.2,0.8-0.1,1.1c-2,2.7-1.4,6.4,1.3,8.4c2.1,1.6,5,1.6,7.1,0c0.3-0.2,0.7-0.3,1.1-0.1c0.3,0.2,0.5,0.6,0.5,1c-0.2,2.7-1.5,5.1-3.6,6.8C16.6,21.2,14.4,22,12.1,22zM9.3,4.4c-2.9,1-5,3.6-5.2,6.8c-0.4,4.4,2.8,8.3,7.2,8.7c2.1,0.2,4.2-0.4,5.8-1.8c1.1-0.9,1.9-2.1,2.4-3.4c-2.5,0.9-5.3,0.5-7.5-1.1C9.2,11.4,8.1,7.7,9.3,4.4z"
                    ></path>
                  </svg>
                </template>
                <template #unswitch-icon>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="rgba(60, 60, 60, .7)"
                    aria-hidden="true"
                    focusable="false"
                    viewBox="0 0 24 24"
                    class="vt-switch-appearance-sun"
                  >
                    <path
                      d="M12,18c-3.3,0-6-2.7-6-6s2.7-6,6-6s6,2.7,6,6S15.3,18,12,18zM12,8c-2.2,0-4,1.8-4,4c0,2.2,1.8,4,4,4c2.2,0,4-1.8,4-4C16,9.8,14.2,8,12,8z"
                    ></path>
                    <path
                      d="M12,4c-0.6,0-1-0.4-1-1V1c0-0.6,0.4-1,1-1s1,0.4,1,1v2C13,3.6,12.6,4,12,4z"
                    ></path>
                    <path
                      d="M12,24c-0.6,0-1-0.4-1-1v-2c0-0.6,0.4-1,1-1s1,0.4,1,1v2C13,23.6,12.6,24,12,24z"
                    ></path>
                    <path
                      d="M5.6,6.6c-0.3,0-0.5-0.1-0.7-0.3L3.5,4.9c-0.4-0.4-0.4-1,0-1.4s1-0.4,1.4,0l1.4,1.4c0.4,0.4,0.4,1,0,1.4C6.2,6.5,5.9,6.6,5.6,6.6z"
                    ></path>
                    <path
                      d="M19.8,20.8c-0.3,0-0.5-0.1-0.7-0.3l-1.4-1.4c-0.4-0.4-0.4-1,0-1.4s1-0.4,1.4,0l1.4,1.4c0.4,0.4,0.4,1,0,1.4C20.3,20.7,20,20.8,19.8,20.8z"
                    ></path>
                    <path
                      d="M3,13H1c-0.6,0-1-0.4-1-1s0.4-1,1-1h2c0.6,0,1,0.4,1,1S3.6,13,3,13z"
                    ></path>
                    <path
                      d="M23,13h-2c-0.6,0-1-0.4-1-1s0.4-1,1-1h2c0.6,0,1,0.4,1,1S23.6,13,23,13z"
                    ></path>
                    <path
                      d="M4.2,20.8c-0.3,0-0.5-0.1-0.7-0.3c-0.4-0.4-0.4-1,0-1.4l1.4-1.4c0.4-0.4,1-0.4,1.4,0s0.4,1,0,1.4l-1.4,1.4C4.7,20.7,4.5,20.8,4.2,20.8z"
                    ></path>
                    <path
                      d="M18.4,6.6c-0.3,0-0.5-0.1-0.7-0.3c-0.4-0.4-0.4-1,0-1.4l1.4-1.4c0.4-0.4,1-0.4,1.4,0s0.4,1,0,1.4l-1.4,1.4C18.9,6.5,18.6,6.6,18.4,6.6z"
                    ></path>
                  </svg>
                </template>
              </lay-switch>
            </a>
          </li>
          <li class="layui-nav-item">
            <a href="javascript:void(0);">
              <lay-icon type="layui-icon-set" size="17px" style="margin-right: 4px" />
              {{ t("nav.settings") }}
            </a>
            <dl class="layui-nav-child">
              <dd>
                <a href="javascript:void(0)" @click="showSettings = true">
                  <lay-icon type="layui-icon-username" size="14px" style="margin-right: 6px" />
                  Cài đặt tài khoản EE88
                </a>
              </dd>
            </dl>
          </li>
        </ul>
      </lay-header>
      <lay-layer
        v-model="showSettings"
        title="DANH SÁCH ĐẠI LÝ"
        :area="['1150px', '620px']"
        :shade="true"
        :shadeClose="true"
        :shadeStyle="shadeStyle"
        :shadeOpacity="shadeOpacity"
        :move="false"
      >
        <div class="settings-subpage">
          <div class="ee88-header">
            <div class="ee88-header-right">
              <lay-button size="sm" border="green" @click="checkAllAgents">
                <lay-icon type="layui-icon-ok-circle" size="14px" style="margin-right: 4px" />
                Kiểm tra tất cả
              </lay-button>
              <lay-button size="sm" border="orange" @click="loginAllAgents">
                <lay-icon type="layui-icon-group" size="14px" style="margin-right: 4px" />
                Đăng nhập tất cả
              </lay-button>
              <lay-button size="sm" border="red" @click="deleteAllAgents">
                <lay-icon type="layui-icon-delete" size="14px" style="margin-right: 4px" />
                Xoá tất cả
              </lay-button>
              <lay-button size="sm" type="primary" @click="showAddAgent = true">
                <lay-icon type="layui-icon-addition" size="14px" style="margin-right: 4px" />
                Thêm Đại Lý
              </lay-button>
            </div>
          </div>
          <div class="ee88-table-wrap">
            <lay-table :columns="agentColumns" :data-source="agentList" size="sm" :max-height="'100%'">
              <template #status="{ row }">
                <lay-tag :color="row.status === 'active' ? 'green' : row.status === 'logging_in' ? 'orange' : 'red'" size="sm">
                  {{ row.status === 'active' ? 'Online' : row.status === 'logging_in' ? 'Đang login...' : row.status === 'error' ? 'Lỗi' : 'Offline' }}
                </lay-tag>
              </template>
              <template #action="{ row }">
                <lay-button size="xs" border="blue" @click="editAgent(row)">
                  <lay-icon type="layui-icon-edit" size="12px" style="margin-right: 3px" />
                  Sửa
                </lay-button>
                <lay-button size="xs" border="red" @click="deleteAgent(row)">
                  <lay-icon type="layui-icon-delete" size="12px" style="margin-right: 3px" />
                  Xoá
                </lay-button>
                <lay-button size="xs" border="green" @click="checkAgent(row)">
                  <lay-icon type="layui-icon-ok-circle" size="12px" style="margin-right: 3px" />
                  Kiểm tra
                </lay-button>
                <lay-button size="xs" border="orange" @click="loginAgent(row)">
                  <lay-icon type="layui-icon-login-wechat" size="12px" style="margin-right: 3px" />
                  Đăng nhập
                </lay-button>
                <lay-button size="xs" border="warm" @click="assignCookies(row)">
                  <lay-icon type="layui-icon-key" size="12px" style="margin-right: 3px" />
                  Gán Cookies
                </lay-button>
              </template>
              <template #autoLogin="{ row }">
                <lay-switch v-model="row.auto_login" size="xs" onswitch-text="Auto" unswitch-text="Off" @change="toggleAutoLogin(row)" />
              </template>
            </lay-table>
          </div>
        </div>
      </lay-layer>
      <lay-layer
        v-model="showAddAgent"
        :title="editingAgentId ? 'CẬP NHẬT ĐẠI LÝ' : 'ĐĂNG NHẬP ĐẠI LÝ EE88'"
        :area="['420px', '400px']"
        :shade="true"
        :shadeClose="true"
        :shadeStyle="shadeStyle"
        :shadeOpacity="shadeOpacity"
        :move="false"
      >
        <div class="add-agent-form">
          <lay-form :model="addAgentForm">
            <lay-form-item label="TÊN HIỂN THỊ :">
              <lay-input v-model="addAgentForm.name" placeholder="Nhập tên hiển thị..."></lay-input>
            </lay-form-item>
            <lay-form-item label="TÀI KHOẢN :">
              <lay-input v-model="addAgentForm.username" placeholder="Nhập tài khoản..." :disabled="!!editingAgentId"></lay-input>
            </lay-form-item>
            <lay-form-item label="MẬT KHẨU :">
              <lay-input v-model="addAgentForm.password" type="password" placeholder="Nhập mật khẩu..."></lay-input>
            </lay-form-item>
            <lay-form-item label="URL BASE :">
              <lay-input v-model="addAgentForm.baseUrl" placeholder="https://..."></lay-input>
            </lay-form-item>
            <lay-form-item>
              <div class="add-agent-actions">
                <lay-button border="orange" @click="showAddAgent = false">
                  <lay-icon type="layui-icon-close" size="14px" style="margin-right: 4px" />
                  Huỷ
                </lay-button>
                <lay-button type="primary" @click="submitAddAgent">
                  <lay-icon :type="editingAgentId ? 'layui-icon-ok-circle' : 'layui-icon-addition'" size="14px" style="margin-right: 4px" />
                  {{ editingAgentId ? 'Cập Nhật' : 'Thêm Đại Lý' }}
                </lay-button>
              </div>
            </lay-form-item>
          </lay-form>
        </div>
      </lay-layer>
      <lay-layer
        v-model="showCookies"
        title="GÁN COOKIES ĐẠI LÝ"
        :area="['500px', '350px']"
        :shade="true"
        :shadeClose="true"
        :shadeStyle="shadeStyle"
        :shadeOpacity="shadeOpacity"
        :move="false"
      >
        <div class="add-agent-form">
          <lay-form>
            <lay-form-item label="ĐẠI LÝ :">
              <lay-input :modelValue="cookiesAgent?.name + ' (' + cookiesAgent?.ext_username + ')'" disabled></lay-input>
            </lay-form-item>
            <lay-form-item label="COOKIES :">
              <lay-textarea v-model="cookiesValue" placeholder="Dán cookies vào đây..." :rows="5"></lay-textarea>
            </lay-form-item>
            <lay-form-item>
              <div class="add-agent-actions">
                <lay-button border="orange" @click="showCookies = false">
                  <lay-icon type="layui-icon-close" size="14px" style="margin-right: 4px" />
                  Huỷ
                </lay-button>
                <lay-button type="primary" @click="submitCookies">
                  <lay-icon type="layui-icon-ok-circle" size="14px" style="margin-right: 4px" />
                  Lưu
                </lay-button>
              </div>
            </lay-form-item>
          </lay-form>
        </div>
      </lay-layer>
      <router-view></router-view>
    </lay-layout>
  </lay-config-provider>
</template>
<script>
import { ref, watch, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAppStore } from "../store/app";
import { useAuthStore } from "../store/auth";
import { useI18n } from "layui-component/index";
import menu from "../view/utils/menus";
import zh_CN from "../language/zh_CN.ts";
import en_US from "../language/en_US.ts";
import vi_VN from "../language/vi_VN.ts";
import api from "../utils/api";
import feedback from "../utils/feedback";

export default {
  setup() {
    const { t } = useI18n();
    const route = useRoute();
    const router = useRouter();
    const locale = ref("vi_VN");
    const locales = [
      { name: "zh_CN", locale: zh_CN, merge: true },
      { name: "en_US", locale: en_US, merge: true },
      { name: "vi_VN", locale: vi_VN, merge: true },
    ];

    const localeLabels = {
      vi_VN: "VN",
      en_US: "EN",
      zh_CN: "中",
    };
    const localeFlags = {
      vi_VN: "/icons/flag-vn.svg",
      en_US: "/icons/flag-us.svg",
      zh_CN: "/icons/flag-cn.svg",
    };
    const localeOrder = ["vi_VN", "en_US", "zh_CN"];
    const appStore = useAppStore();
    const authStore = useAuthStore();
    const menus = [];
    const currentPath = ref("/zh-CN/guide");

    watch(
      () => route.path,
      (val) => {
        currentPath.value = val;
      },
      {
        immediate: true,
        deep: true,
      }
    );

    function stringSort(n, m) {
      if (typeof n === "string" && typeof m === "string") {
        var a = n.split("").map((a) => a.charCodeAt());
        var b = m.split("").map((a) => a.charCodeAt());
        try {
          a.forEach((a, i) => {
            if (a - b[i] > 0) {
              throw new Error(1);
            } else if (a - b[i] < 0) {
              throw new Error(-1);
            }
          });
        } catch (e) {
          return e.message;
        }
        return 0;
      }
      return n > m ? 1 : n == m ? 0 : -1;
    }

    menu.forEach((m) => {
      m.children.forEach((c) => {
        menus.push(c);
      });
      m.children.sort((a, b) => stringSort(a.subTitle, b.subTitle));
    });

    watch(
      () => route.path,
      (val) => {
        currentPath.value = val;
      },
      { immediate: true, deep: true }
    );

    const handleClick = function (menu) {
      router.push(menu.path);
    };

    const changeLocale = function (lang) {
      locale.value = lang;
    };

    const resetThemeVariable = function () {
      appStore.themeVariable = {
        "--global-primary-color": "#16baaa",
        "--global-normal-color": "#1e9fff",
        "--global-warm-color": "#ffb800",
        "--global-danger-color": "#ff5722",
        "--global-checked-color": "#16b777",
        "--global-border-radius": "2px",
        "--global-neutral-color-1": "#FAFAFA",
        "--global-neutral-color-2": "#F6F6F6",
        "--global-neutral-color-3": "#eeeeee",
        "--global-neutral-color-4": "#e2e2e2",
        "--global-neutral-color-5": "#dddddd",
        "--global-neutral-color-6": "#d2d2d2",
        "--global-neutral-color-7": "#cccccc",
        "--global-neutral-color-8": "#c2c2c2",
      };
    };

    const shadeStyle = computed(() => feedback.getShadeStyle());
    const shadeOpacity = "1";

    const showSettings = ref(false);
    const showAddAgent = ref(false);
    const editingAgentId = ref(null);
    const addAgentForm = ref({ name: "", username: "", password: "", baseUrl: "" });

    const submitAddAgent = async () => {
      const isEdit = !!editingAgentId.value;
      const result = await feedback.run(async () => {
        if (isEdit) {
          const f = addAgentForm.value;
          const updates = Object.assign({ name: f.name },
            f.password ? { ext_password: f.password } : {},
            f.baseUrl ? { base_url: f.baseUrl } : {}
          );
          return api.patch(`/api/agents/${editingAgentId.value}`, updates);
        } else {
          return api.post("/api/agents", {
            name: addAgentForm.value.name,
            ext_username: addAgentForm.value.username,
            ext_password: addAgentForm.value.password,
            base_url: addAgentForm.value.baseUrl,
          });
        }
      }, { successMsg: isEdit ? "Cập nhật đại lý thành công" : "Thêm đại lý thành công" });
      if (result) {
        addAgentForm.value = { name: "", username: "", password: "", baseUrl: "" };
        editingAgentId.value = null;
        showAddAgent.value = false;
        await loadAgents();
      }
    };

    // EE88 Agent management
    const agentColumns = [
      { title: "Mã ĐL", key: "id", width: "6%", align: "center" },
      { title: "Tên đại lý", key: "name", width: "7%", align: "center" },
      { title: "Tài khoản", key: "ext_username", width: "10%", align: "center" },
      { title: "Trạng thái", key: "status", width: "8%", align: "center", customSlot: "status" },
      { title: "Ngày tạo", key: "created_at", width: "15%", align: "center" },
      { title: "Thao tác", key: "action", width: "44%", align: "center", customSlot: "action" },
      { title: "Auto Login", key: "auto_login", width: "10%", align: "center", customSlot: "autoLogin" },
    ];

    const agentList = ref([]);
    const agentLoading = ref(false);

    const loadAgents = async () => {
      try {
        agentLoading.value = true;
        const res = await api.get("/api/agents");
        agentList.value = (res.data.agents || []).map(a => ({
          ...a,
          created_at: a.created_at ? new Date(a.created_at).toLocaleDateString("vi-VN") : "",
        }));
      } catch (e) {
        console.error("Load agents failed:", e);
      } finally {
        agentLoading.value = false;
      }
    };

    const checkAllAgents = async () => {
      const loading = feedback.showLoading();
      try {
        const res = await api.get("/api/agents/cookie-health");
        const results = res.data.results || [];
        let alive = 0, dead = 0;
        for (const r of results) {
          const agent = agentList.value.find(a => a.id === r.id);
          if (agent) agent.status = r.alive ? "active" : "offline";
          r.alive ? alive++ : dead++;
        }
        (alive > 0 ? feedback.msgSuccess : feedback.msgError)(`Kiểm tra xong: ${alive} online, ${dead} offline`);
      } catch {
        feedback.msgError("Kiểm tra thất bại");
      } finally {
        feedback.closeLoading(loading);
      }
    };

    const loginAllAgents = async () => {
      const loading = feedback.showLoading();
      try {
        const res = await api.post("/api/ee88-auth/login-all");
        const d = res.data;
        await loadAgents();
        const msg = `Đăng nhập xong: ${d.success || 0} thành công, ${d.failed || 0} thất bại`;
        d.failed ? feedback.msgError(msg) : feedback.msgSuccess(msg);
      } catch {
        feedback.msgError("Đăng nhập tất cả thất bại");
      } finally {
        feedback.closeLoading(loading);
      }
    };

    const loginAgent = async (row) => {
      const loading = feedback.showLoading();
      try {
        row.status = "logging_in";
        const res = await api.post(`/api/ee88-auth/${row.id}/login`);
        row.status = res.data.success ? "active" : "error";
        if (res.data.success) {
          feedback.msgSuccess(`${row.name}: Đăng nhập thành công`);
        } else {
          feedback.msgError(`${row.name}: ${res.data.error_message || "Đăng nhập thất bại"}`);
        }
      } catch (e) {
        row.status = "error";
        feedback.msgError(`${row.name}: ${e?.response?.data?.message || "Đăng nhập thất bại"}`);
      } finally {
        feedback.closeLoading(loading);
      }
    };

    const editAgent = (row) => {
      addAgentForm.value = {
        name: row.name,
        username: row.ext_username,
        password: "",
        baseUrl: row.base_url || "",
      };
      editingAgentId.value = row.id;
      showAddAgent.value = true;
    };

    const deleteAgent = async (row) => {
      const result = await feedback.confirmRun({
        confirmMsg: `Xác nhận xoá đại lý "${row.name}"?`,
        yesText: "Xoá",
        successMsg: "Đã xoá đại lý",
        errorMsg: "Xoá thất bại",
      }, () => api.delete(`/api/agents/${row.id}?mode=destroy`));
      if (result) {
        agentList.value = agentList.value.filter(a => a.id !== row.id);
      }
    };

    const checkAgent = async (row) => {
      const loading = feedback.showLoading();
      try {
        const res = await api.post(`/api/ee88-auth/${row.id}/check`);
        row.status = res.data.valid ? "active" : "offline";
        const msg = `${row.name}: ${res.data.valid ? "Session còn hoạt động" : "Session hết hạn"}`;
        res.data.valid ? feedback.msgSuccess(msg) : feedback.msgError(msg);
      } catch {
        feedback.msgError(`${row.name}: Kiểm tra thất bại`);
      } finally {
        feedback.closeLoading(loading);
      }
    };

    const deleteAllAgents = async () => {
      if (!agentList.value.length) {
        feedback.msgInfo("Không có đại lý nào để xoá");
        return;
      }
      const result = await feedback.confirmRun({
        confirmMsg: `Xác nhận xoá tất cả ${agentList.value.length} đại lý?`,
        yesText: "Xoá tất cả",
        successMsg: "Đã xoá tất cả đại lý",
        errorMsg: "Xoá thất bại",
      }, async () => {
        for (const agent of [...agentList.value]) {
          await api.delete(`/api/agents/${agent.id}?mode=destroy`);
        }
      });
      if (result !== null) {
        agentList.value = [];
      } else {
        await loadAgents();
      }
    };

    const showCookies = ref(false);
    const cookiesAgent = ref(null);
    const cookiesValue = ref("");

    const assignCookies = (row) => {
      cookiesAgent.value = row;
      cookiesValue.value = "";
      showCookies.value = true;
    };

    const submitCookies = async () => {
      if (!cookiesValue.value.trim()) {
        feedback.msgInfo("Cookies không được trống");
        return;
      }
      const result = await feedback.run(
        () => api.patch(`/api/ee88-auth/${cookiesAgent.value.id}/cookie`, { cookie: cookiesValue.value }),
        { successMsg: "Gán cookies thành công", errorMsg: "Gán cookies thất bại" }
      );
      if (result) {
        showCookies.value = false;
        await loadAgents();
      }
    };

    const toggleAutoLogin = async (row) => {
      try {
        await api.patch(`/api/agents/${row.id}`, { auto_login: row.auto_login });
        feedback.msgSuccess(`${row.name}: Auto login ${row.auto_login ? "bật" : "tắt"}`);
      } catch {
        row.auto_login = !row.auto_login;
        feedback.msgError("Cập nhật thất bại");
      }
    };

    watch(showSettings, (val) => {
      if (val) loadAgents();
    });

    watch(showAddAgent, (val) => {
      if (!val) editingAgentId.value = null;
    });

    const handleLogout = async () => {
      const confirmed = await feedback.confirm("Xác nhận đăng xuất?", { yesText: "Đăng xuất" });
      if (confirmed) {
        await authStore.logout();
        feedback.msgSuccess("Đã đăng xuất");
        router.push("/login");
      }
    };

    const goChangePassword = () => {
      router.push("/change-password");
    };

    return {
      t,
      menus,
      locale,
      locales,
      localeLabels,
      localeFlags,
      localeOrder,
      appStore,
      authStore,
      currentPath,
      handleClick,
      changeLocale,
      handleLogout,
      goChangePassword,
      resetThemeVariable,
      showSettings,
      showAddAgent,
      agentColumns,
      agentList,
      checkAllAgents,
      loginAllAgents,
      loginAgent,
      deleteAllAgents,
      editAgent,
      deleteAgent,
      checkAgent,
      assignCookies,
      toggleAutoLogin,
      showCookies,
      cookiesAgent,
      cookiesValue,
      submitCookies,
      addAgentForm,
      editingAgentId,
      submitAddAgent,
      agentLoading,
      shadeStyle,
      shadeOpacity,
    };
  },
};
</script>

<style>
.layui-layout-document > .layui-header {
  z-index: 99;
  width: 100%;
  position: fixed;
  border-bottom: 1px solid #eeeeee;
  background-image: radial-gradient(transparent 1px, #ffffff 1px);
  background-size: 4px 4px;
  backdrop-filter: saturate(50%) blur(4px);
}

.layui-layout-document > .layui-layout > .layui-side {
  overflow-x: hidden;
  position: fixed;
  margin-top: 60px;
  z-index: 99;
  height: calc(100% - 60px);
  border-right: 1px solid #eeeeee;
}

.layui-layout-document > .layui-layout > .layui-body {
  margin-top: 60px;
  left: 200px;
  position: absolute;
  width: calc(100% - 200px);
  height: calc(100% - 60px);
}

.layui-layout-document .layui-header .layui-form-switch {
  border: 1px solid rgba(60, 60, 60, 0.29);
  background-color: #f1f1f1 !important;
}

.layui-layout-document .layui-header .layui-nav .layui-nav-item *,
.layui-layout-document .layui-header .layui-nav .layui-nav-item a,
.layui-layout-document .layui-header .layui-nav .layui-nav-item a:hover {
  color: rgba(0, 0, 0, 0.8);
}

.layui-layout-document .layui-header .layui-logo {
  text-align: left;
  padding-left: 10px;
  width: 120px;
}

.layui-layout-document .layui-header .layui-layout-left {
  left: 120px;
}

.layui-logo img {
  margin-top: -5px;
  height: 45px;
  left: 15px;
}

.layui-logo .title {
  margin-left: 12px;
  font-size: 20px;
  color: rgba(0, 0, 0, 0.8);
  letter-spacing: -0.2px;
  opacity: 0.8;
  color: #213547;
  font-weight: 700;
}

.layui-header > .layui-nav {
  background-color: transparent;
}

.layui-header > .layui-nav .layui-active * {
  color: var(--global-checked-color) !important;
}

.locale-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
}

.locale-flag {
  width: 28px;
  height: 20px;
  object-fit: cover;
  border-radius: 2px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  margin-right: 4px;
}

.locale-label {
  font-size: 13px;
  font-weight: 500;
}

.locale-menu-item {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 80px;
}

.locale-flag-sm {
  width: 22px;
  height: 16px;
  object-fit: cover;
  border-radius: 2px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.layui-menu-docs {
  padding-top: 10px;
}

.layui-menu-docs .layui-menu-body-title .layui-font-gray {
  padding-left: 10px;
}

.layui-menu li,
.layui-menu-body-title a {
  padding: 5px 15px;
}

.layui-side hr {
  margin: 8px;
}

.switch svg {
  position: absolute;
  width: 12px;
  height: 12px;
  top: 3px;
  left: 3px;
}

.theme-panel {
  width: 380px;
  padding: 0px 10px 10px 10px;
}

.theme-panel > * {
  margin-top: 9px;
  margin-right: 9px;
}

/* Nav dropdown on hover */
.layui-layout-left .layui-nav-item:hover > .layui-nav-child,
.layui-layout-right .layui-nav-item:hover > .layui-nav-child {
  display: block;
}

.layui-layout-left .layui-nav-child {
  top: 60px;
}

.layui-layout-right .layui-nav-child {
  top: 60px;
  left: auto;
  right: 0;
}

.layui-layout-left .layui-nav-child dd a,
.layui-layout-right .layui-nav-child dd a {
  display: block;
  padding: 0 20px;
  color: rgba(0, 0, 0, 0.8);
  text-decoration: none;
}

/* ── Sharp & crisp light theme ── */
body {
  color: #1a1a1a;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  background: #ffffff;
}

/* Pure white backgrounds */
.layui-card {
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.customers-container {
  background: #f0f2f5 !important;
}

/* Stronger text colors */
.layui-table th {
  color: #1a1a1a;
  font-weight: 400 !important;
  background: #fafafa;
}

.layui-table th .layui-table-cell-text {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.layui-table td {
  color: #262626;
}

.layui-form-label {
  color: #1a1a1a;
  font-weight: 500;
}

/* Crisper borders */
.layui-table,
.layui-table th,
.layui-table td {
  border-color: #e0e0e0;
}

.layui-input,
.layui-textarea,
.layui-select {
  border-color: #d0d0d0;
  color: #1a1a1a;
}

.layui-input:focus,
.layui-textarea:focus {
  border-color: var(--global-primary-color);
}

.layui-input::placeholder {
  color: #999;
}

/* Header sharper */
.layui-layout-document > .layui-header {
  border-bottom-color: #d9d9d9;
}

/* Nav text sharper */
.layui-layout-document .layui-header .layui-nav .layui-nav-item *,
.layui-layout-document .layui-header .layui-nav .layui-nav-item a,
.layui-layout-document .layui-header .layui-nav .layui-nav-item a:hover {
  color: #1a1a1a;
  font-weight: 500;
}

/* Field title */
.layui-elem-field legend {
  color: #1a1a1a;
  font-weight: 600;
}

/* Buttons */
.layui-btn {
  font-weight: 500;
}

.layui-btn-primary {
  border-color: #d0d0d0;
  color: #333;
}

/* Dropdown sharper */
.layui-nav-child {
  border-color: #d9d9d9;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1);
}

.layui-nav-child dd a {
  color: #262626 !important;
}

/* Tag sharper */
.layui-tag {
  font-weight: 500;
}

/* Pagination */
.layui-laypage a,
.layui-laypage span {
  color: #333;
}

/* Settings / EE88 dialog */
.settings-subpage {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.ee88-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 12px 20px;
  border-bottom: 1px solid #e8e8e8;
}

.ee88-header-right {
  display: flex;
  gap: 8px;
}

.ee88-table-wrap {
  flex: 1;
  padding: 12px 20px;
  overflow: visible;
}
.ee88-table-wrap .layui-table-body {
  overflow: visible;
}
.ee88-table-wrap .layui-table-box {
  overflow: visible;
}
.ee88-table-wrap .layui-table th:last-child,
.ee88-table-wrap .layui-table td:last-child {
  border-right: none;
}
.ee88-table-wrap .layui-table-view {
  width: 100%;
  margin: 0;
  padding: 0;
}
.ee88-table-wrap .layui-table-header,
.ee88-table-wrap .layui-table-body {
  width: 100%;
}
.ee88-table-wrap .layui-table-header table,
.ee88-table-wrap .layui-table-body table {
  width: 100%;
  table-layout: fixed;
}

/* Add agent form */
.add-agent-form {
  padding: 20px 30px;
}

.add-agent-actions {
  display: flex;
  gap: 10px;
  width: 100%;
}

.add-agent-actions .layui-btn {
  flex: 1;
}

/* Layer shade overlay: 70% đen (light), DarkReader tự đảo sang trắng (dark) */
.layui-layer-shade {
  background-color: rgba(0, 0, 0, 0.7) !important;
  opacity: 1 !important;
}
</style>
