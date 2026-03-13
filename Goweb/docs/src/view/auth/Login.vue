<template>
  <div class="auth-page" :class="{ light: appStore.theme === 'light' }">
    <!-- Theme Toggle -->
    <button class="theme-toggle" @click="toggle_theme">
      <svg v-if="appStore.theme !== 'light'" class="icon-moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <svg v-else class="icon-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
    </button>

    <!-- Language Selector -->
    <div class="lang-selector">
      <button
        v-for="lang in languages"
        :key="lang.code"
        class="lang-btn"
        :class="{ active: current_lang === lang.code }"
        @click="current_lang = lang.code"
      >
        <img :src="lang.flag" :alt="lang.label" class="lang-flag" />
      </button>
    </div>

    <div class="auth-container">
      <!-- LEFT PANEL — Branding -->
      <div class="brand-panel">
        <div class="orbital-ring"></div>
        <div class="orbital-ring-2"></div>
        <div class="glow-orb-2"></div>
        <div class="glow-orb-orange"></div>

        <div class="brand-logo">
          <img src="/icons/duango_logo.png" alt="MaxHub" />
        </div>

        <div class="brand-tagline">
          <h2 v-html="t('brand_tagline')"></h2>
          <p>{{ t('brand_desc') }}</p>
        </div>

        <div class="feature-pills">
          <div class="pill"><span class="dot cyan"></span>Realtime Sync</div>
          <div class="pill"><span class="dot orange"></span>AI Powered</div>
          <div class="pill"><span class="dot blue"></span>Enterprise</div>
        </div>

        <a href="/GoDesktop-v1.0.zip" download class="download-btn">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          {{ t('download_pc') }}
        </a>
      </div>

      <!-- RIGHT PANEL — Form -->
      <div class="form-panel">
        <div class="form-grid-bg"></div>
        <div class="form-wrapper">
          <!-- Tab Switcher -->
          <div class="tab-switcher">
            <button
              class="tab-btn"
              :class="{ active: active_tab === 'login' }"
              @click="switch_tab('login')"
            >
              {{ t('tab_login') }}
            </button>
            <button
              class="tab-btn"
              :class="{ active: active_tab === 'register' }"
              @click="switch_tab('register')"
            >
              {{ t('tab_register') }}
            </button>
            <div class="tab-indicator" :class="{ right: active_tab === 'register' }"></div>
          </div>

          <!-- ═══ LOGIN FORM ═══ -->
          <form v-if="active_tab === 'login'" class="auth-form" @submit.prevent="on_login">
            <div class="form-header">
              <h1>{{ t('login_title') }}</h1>
              <p>{{ t('login_desc') }}</p>
            </div>

            <div class="input-group">
              <label>{{ t('username') }}</label>
              <div class="input-wrap">
                <span class="icon">
                  <svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </span>
                <input
                  v-model="login_form.username"
                  type="text"
                  :placeholder="t('username_ph')"
                  autocomplete="username"
                  @keyup.enter="focus_ref(loginPassRef)"
                />
              </div>
            </div>

            <div class="input-group">
              <label>{{ t('password') }}</label>
              <div class="input-wrap">
                <span class="icon">
                  <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </span>
                <input
                  ref="loginPassRef"
                  v-model="login_form.password"
                  :type="show_login_pass ? 'text' : 'password'"
                  placeholder="••••••••"
                  autocomplete="current-password"
                  @keyup.enter="on_login"
                />
                <button type="button" class="pass-toggle" @click="show_login_pass = !show_login_pass">
                  <svg v-if="!show_login_pass" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
            </div>

            <div class="form-row">
              <label class="checkbox-label">
                <input type="checkbox" v-model="remember_me" />
                <span>{{ t('remember') }}</span>
              </label>
            </div>

            <div v-if="error_msg" class="status-msg error">{{ error_msg }}</div>
            <div v-if="success_msg" class="status-msg success">{{ success_msg }}</div>

            <div class="btn-row">
              <button type="submit" class="btn-primary" :class="{ loading: loading }" :disabled="loading">
                <span class="btn-text">{{ t('btn_login') }}</span>
              </button>
              <button type="button" class="btn-cancel" @click="on_cancel">
                {{ t('btn_cancel') }}
              </button>
            </div>

            <!-- Social Login -->
            <div class="social-divider">
              <span>{{ t('or_continue') }}</span>
            </div>
            <div class="social-buttons">
              <button type="button" class="social-btn">
                <svg viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
                Google
              </button>
              <button type="button" class="social-btn">
                <svg viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" fill="currentColor"/></svg>
                GitHub
              </button>
            </div>
          </form>

          <!-- ═══ REGISTER FORM ═══ -->
          <form v-if="active_tab === 'register'" class="auth-form" @submit.prevent="on_register">
            <div class="form-header">
              <h1>{{ t('register_title') }}</h1>
              <p>{{ t('register_desc') }}</p>
            </div>

            <div class="input-group">
              <label>{{ t('username') }}</label>
              <div class="input-wrap">
                <span class="icon">
                  <svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </span>
                <input
                  v-model="reg_form.username"
                  type="text"
                  :placeholder="t('username_ph')"
                  autocomplete="username"
                  @keyup.enter="focus_ref(regPassRef)"
                />
              </div>
            </div>

            <div class="input-group">
              <label>{{ t('password') }}</label>
              <div class="input-wrap">
                <span class="icon">
                  <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </span>
                <input
                  ref="regPassRef"
                  v-model="reg_form.password"
                  :type="show_reg_pass ? 'text' : 'password'"
                  :placeholder="t('password_ph')"
                  autocomplete="new-password"
                  @input="calc_strength"
                  @keyup.enter="focus_ref(regConfirmRef)"
                />
                <button type="button" class="pass-toggle" @click="show_reg_pass = !show_reg_pass">
                  <svg v-if="!show_reg_pass" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
              <!-- Password Strength Meter -->
              <div v-if="reg_form.password" class="strength-meter">
                <div class="strength-bars">
                  <div class="strength-bar" :class="strength_class(1)"></div>
                  <div class="strength-bar" :class="strength_class(2)"></div>
                  <div class="strength-bar" :class="strength_class(3)"></div>
                  <div class="strength-bar" :class="strength_class(4)"></div>
                </div>
                <span class="strength-label" :class="'strength-' + password_strength">{{ strength_text }}</span>
              </div>
            </div>

            <div class="input-group">
              <label>{{ t('confirm_password') }}</label>
              <div class="input-wrap">
                <span class="icon">
                  <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </span>
                <input
                  ref="regConfirmRef"
                  v-model="reg_form.confirm"
                  :type="show_reg_confirm ? 'text' : 'password'"
                  :placeholder="t('confirm_ph')"
                  autocomplete="new-password"
                  @keyup.enter="on_register"
                />
                <button type="button" class="pass-toggle" @click="show_reg_confirm = !show_reg_confirm">
                  <svg v-if="!show_reg_confirm" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
            </div>

            <div class="form-row">
              <label class="checkbox-label">
                <input type="checkbox" v-model="agree_terms" />
                <span>{{ t('agree_prefix') }} <a href="#" @click.prevent="show_terms = true">{{ t('terms') }}</a> {{ t('and') }} <a href="#" @click.prevent="show_privacy = true">{{ t('privacy') }}</a></span>
              </label>
            </div>

            <div v-if="error_msg" class="status-msg error">{{ error_msg }}</div>
            <div v-if="success_msg" class="status-msg success">{{ success_msg }}</div>

            <div class="btn-row">
              <button type="submit" class="btn-primary" :class="{ loading: loading }" :disabled="loading">
                <span class="btn-text">{{ t('btn_register') }}</span>
              </button>
              <button type="button" class="btn-cancel" @click="on_cancel">
                {{ t('btn_cancel') }}
              </button>
            </div>

            <!-- Social Login -->
            <div class="social-divider">
              <span>{{ t('or_continue') }}</span>
            </div>
            <div class="social-buttons">
              <button type="button" class="social-btn">
                <svg viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
                Google
              </button>
              <button type="button" class="social-btn">
                <svg viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" fill="currentColor"/></svg>
                GitHub
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- ═══ TERMS OVERLAY ═══ -->
    <transition name="overlay-fade">
      <div v-if="show_terms" class="overlay-page" @click.self="show_terms = false">
        <div class="overlay-content">
          <div class="overlay-header">
            <h2>{{ t('terms_title') }}</h2>
            <button class="overlay-close" @click="show_terms = false">
              <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div class="overlay-body">
            <h3>1. {{ t('terms_s1_title') }}</h3>
            <p>{{ t('terms_s1_body') }}</p>
            <h3>2. {{ t('terms_s2_title') }}</h3>
            <p>{{ t('terms_s2_body') }}</p>
            <h3>3. {{ t('terms_s3_title') }}</h3>
            <p>{{ t('terms_s3_body') }}</p>
          </div>
        </div>
      </div>
    </transition>

    <!-- ═══ PRIVACY OVERLAY ═══ -->
    <transition name="overlay-fade">
      <div v-if="show_privacy" class="overlay-page" @click.self="show_privacy = false">
        <div class="overlay-content">
          <div class="overlay-header">
            <h2>{{ t('privacy_title') }}</h2>
            <button class="overlay-close" @click="show_privacy = false">
              <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div class="overlay-body">
            <h3>1. {{ t('privacy_s1_title') }}</h3>
            <p>{{ t('privacy_s1_body') }}</p>
            <h3>2. {{ t('privacy_s2_title') }}</h3>
            <p>{{ t('privacy_s2_body') }}</p>
            <h3>3. {{ t('privacy_s3_title') }}</h3>
            <p>{{ t('privacy_s3_body') }}</p>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "../../store/auth";
import { useAppStore } from "../../store/app";

const router = useRouter();
const route = useRoute();
const auth_store = useAuthStore();
const appStore = useAppStore();

// ═══ Tab state ═══
const active_tab = ref<"login" | "register">("login");
const loading = ref(false);
const error_msg = ref("");
const success_msg = ref("");

// ═══ Login form ═══
const loginPassRef = ref<HTMLInputElement>();
const show_login_pass = ref(false);
const remember_me = ref(false);
const login_form = reactive({ username: "", password: "" });

// ═══ Register form ═══
const regPassRef = ref<HTMLInputElement>();
const regConfirmRef = ref<HTMLInputElement>();
const show_reg_pass = ref(false);
const show_reg_confirm = ref(false);
const agree_terms = ref(false);
const reg_form = reactive({ username: "", password: "", confirm: "" });
const password_strength = ref(0);

// ═══ Overlays ═══
const show_terms = ref(false);
const show_privacy = ref(false);

// ═══ i18n ═══
const current_lang = ref("vi");

const languages = [
  { code: "vi", label: "Tiếng Việt", flag: "/icons/flag-vn.svg" },
  { code: "en", label: "English", flag: "/icons/flag-us.svg" },
  { code: "zh", label: "中文", flag: "/icons/flag-cn.svg" },
];

const i18n: Record<string, Record<string, string>> = {
  vi: {
    brand_tagline: "Quản lý thông minh,<br>Kết nối mọi thứ",
    brand_desc: "Nền tảng quản lý tập trung giúp bạn kiểm soát, tự động hóa và tối ưu hiệu suất làm việc.",
    download_pc: "Tải bản PC",
    tab_login: "Đăng nhập",
    tab_register: "Đăng ký",
    login_title: "Chào mừng trở lại",
    login_desc: "Đăng nhập để tiếp tục quản lý dự án của bạn",
    register_title: "Tạo tài khoản",
    register_desc: "Đăng ký để bắt đầu sử dụng MaxHub",
    username: "Tên tài khoản",
    username_ph: "Nhập tên tài khoản",
    password: "Mật khẩu",
    password_ph: "Tối thiểu 8 ký tự",
    confirm_password: "Xác nhận mật khẩu",
    confirm_ph: "Nhập lại mật khẩu",
    remember: "Ghi nhớ đăng nhập",
    btn_login: "Đăng nhập",
    btn_register: "Đăng ký",
    btn_cancel: "Huỷ",
    or_continue: "Hoặc tiếp tục với",
    agree_prefix: "Tôi đồng ý với",
    terms: "Điều khoản",
    and: "và",
    privacy: "Chính sách bảo mật",
    strength_weak: "Yếu",
    strength_fair: "Trung bình",
    strength_good: "Tốt",
    strength_strong: "Mạnh",
    err_required: "Vui lòng nhập đầy đủ thông tin",
    err_min_pass: "Mật khẩu phải có tối thiểu 8 ký tự",
    err_confirm: "Mật khẩu xác nhận không khớp",
    err_terms: "Vui lòng đồng ý với điều khoản sử dụng",
    err_login_fail: "Đăng nhập thất bại",
    err_register_fail: "Đăng ký thất bại",
    success_login: "Đăng nhập thành công!",
    success_register: "Đăng ký thành công!",
    terms_title: "Điều khoản sử dụng",
    terms_s1_title: "Chấp nhận điều khoản",
    terms_s1_body: "Bằng việc truy cập và sử dụng MaxHub, bạn đồng ý tuân thủ các điều khoản và điều kiện được nêu trong tài liệu này.",
    terms_s2_title: "Tài khoản người dùng",
    terms_s2_body: "Bạn chịu trách nhiệm bảo mật thông tin tài khoản của mình, bao gồm mật khẩu, và chịu trách nhiệm cho mọi hoạt động diễn ra dưới tài khoản của bạn.",
    terms_s3_title: "Sử dụng dịch vụ",
    terms_s3_body: "Bạn đồng ý sử dụng dịch vụ chỉ cho các mục đích hợp pháp và không vi phạm bất kỳ luật pháp hiện hành nào.",
    privacy_title: "Chính sách bảo mật",
    privacy_s1_title: "Thu thập thông tin",
    privacy_s1_body: "Chúng tôi thu thập thông tin bạn cung cấp trực tiếp, bao gồm tên, email và thông tin tài khoản khi bạn đăng ký sử dụng dịch vụ.",
    privacy_s2_title: "Sử dụng thông tin",
    privacy_s2_body: "Thông tin của bạn được sử dụng để cung cấp, duy trì và cải thiện dịch vụ, cũng như để liên lạc với bạn về cập nhật và thông báo quan trọng.",
    privacy_s3_title: "Bảo vệ dữ liệu",
    privacy_s3_body: "Chúng tôi áp dụng các biện pháp bảo mật tiêu chuẩn ngành để bảo vệ thông tin cá nhân của bạn khỏi truy cập trái phép.",
  },
  en: {
    brand_tagline: "Smart Management,<br>Connect Everything",
    brand_desc: "A centralized management platform to help you control, automate, and optimize your workflow.",
    download_pc: "Download PC",
    tab_login: "Login",
    tab_register: "Register",
    login_title: "Welcome Back",
    login_desc: "Sign in to continue managing your projects",
    register_title: "Create Account",
    register_desc: "Register to start using MaxHub",
    username: "Username",
    username_ph: "Enter username",
    password: "Password",
    password_ph: "Minimum 8 characters",
    confirm_password: "Confirm Password",
    confirm_ph: "Re-enter password",
    remember: "Remember me",
    btn_login: "Sign In",
    btn_register: "Register",
    btn_cancel: "Cancel",
    or_continue: "Or continue with",
    agree_prefix: "I agree to the",
    terms: "Terms of Service",
    and: "and",
    privacy: "Privacy Policy",
    strength_weak: "Weak",
    strength_fair: "Fair",
    strength_good: "Good",
    strength_strong: "Strong",
    err_required: "Please fill in all fields",
    err_min_pass: "Password must be at least 8 characters",
    err_confirm: "Passwords do not match",
    err_terms: "Please agree to the terms of service",
    err_login_fail: "Login failed",
    err_register_fail: "Registration failed",
    success_login: "Login successful!",
    success_register: "Registration successful!",
    terms_title: "Terms of Service",
    terms_s1_title: "Acceptance of Terms",
    terms_s1_body: "By accessing and using MaxHub, you agree to comply with the terms and conditions outlined in this document.",
    terms_s2_title: "User Account",
    terms_s2_body: "You are responsible for maintaining the security of your account information, including your password, and for all activities that occur under your account.",
    terms_s3_title: "Use of Service",
    terms_s3_body: "You agree to use the service only for lawful purposes and not to violate any applicable laws.",
    privacy_title: "Privacy Policy",
    privacy_s1_title: "Information Collection",
    privacy_s1_body: "We collect information you provide directly, including name, email, and account information when you register.",
    privacy_s2_title: "Use of Information",
    privacy_s2_body: "Your information is used to provide, maintain, and improve the service, and to communicate important updates.",
    privacy_s3_title: "Data Protection",
    privacy_s3_body: "We apply industry-standard security measures to protect your personal information from unauthorized access.",
  },
  zh: {
    brand_tagline: "智能管理,<br>连接一切",
    brand_desc: "一个集中管理平台，帮助您控制、自动化和优化工作流程。",
    download_pc: "下载PC版",
    tab_login: "登录",
    tab_register: "注册",
    login_title: "欢迎回来",
    login_desc: "登录以继续管理您的项目",
    register_title: "创建账号",
    register_desc: "注册以开始使用 MaxHub",
    username: "用户名",
    username_ph: "输入用户名",
    password: "密码",
    password_ph: "最少8个字符",
    confirm_password: "确认密码",
    confirm_ph: "再次输入密码",
    remember: "记住登录",
    btn_login: "登录",
    btn_register: "注册",
    btn_cancel: "取消",
    or_continue: "或者通过以下方式继续",
    agree_prefix: "我同意",
    terms: "服务条款",
    and: "和",
    privacy: "隐私政策",
    strength_weak: "弱",
    strength_fair: "一般",
    strength_good: "良好",
    strength_strong: "强",
    err_required: "请填写所有字段",
    err_min_pass: "密码至少需要8个字符",
    err_confirm: "两次密码不一致",
    err_terms: "请同意服务条款",
    err_login_fail: "登录失败",
    err_register_fail: "注册失败",
    success_login: "登录成功！",
    success_register: "注册成功！",
    terms_title: "服务条款",
    terms_s1_title: "接受条款",
    terms_s1_body: "访问和使用 MaxHub，即表示您同意遵守本文件中列出的条款和条件。",
    terms_s2_title: "用户账号",
    terms_s2_body: "您有责任维护账号信息（包括密码）的安全，并对账号下发生的所有活动负责。",
    terms_s3_title: "使用服务",
    terms_s3_body: "您同意仅将服务用于合法目的，且不违反任何适用法律。",
    privacy_title: "隐私政策",
    privacy_s1_title: "信息收集",
    privacy_s1_body: "我们收集您直接提供的信息，包括注册时的姓名、电子邮件和账号信息。",
    privacy_s2_title: "信息使用",
    privacy_s2_body: "您的信息用于提供、维护和改进服务，以及传达重要更新和通知。",
    privacy_s3_title: "数据保护",
    privacy_s3_body: "我们采用行业标准安全措施保护您的个人信息免受未经授权的访问。",
  },
};

const t = (key: string): string => {
  return i18n[current_lang.value]?.[key] || i18n["vi"][key] || key;
};

// ═══ Password strength ═══
const calc_strength = () => {
  const p = reg_form.password;
  let score = 0;
  if (p.length >= 8) score++;
  if (/[a-z]/.test(p) && /[A-Z]/.test(p)) score++;
  if (/\d/.test(p)) score++;
  if (/[^a-zA-Z0-9]/.test(p)) score++;
  password_strength.value = score;
};

const strength_class = (level: number) => {
  if (password_strength.value >= level) {
    if (password_strength.value <= 1) return "weak";
    if (password_strength.value === 2) return "fair";
    if (password_strength.value === 3) return "good";
    return "strong";
  }
  return "";
};

const strength_text = computed(() => {
  const labels = ["", "strength_weak", "strength_fair", "strength_good", "strength_strong"];
  return t(labels[password_strength.value] || "");
});

// ═══ Actions ═══
const focus_ref = (r: any) => { r.value?.focus(); };

const toggle_theme = () => {
  appStore.theme = appStore.theme === "light" ? "dark" : "light";
};

const switch_tab = (tab: "login" | "register") => {
  active_tab.value = tab;
  error_msg.value = "";
  success_msg.value = "";
};

const on_cancel = () => {
  login_form.username = "";
  login_form.password = "";
  reg_form.username = "";
  reg_form.password = "";
  reg_form.confirm = "";
  error_msg.value = "";
  success_msg.value = "";
  router.push("/");
};

const on_login = async () => {
  if (!login_form.username || !login_form.password) {
    error_msg.value = t("err_required");
    return;
  }
  loading.value = true;
  error_msg.value = "";
  success_msg.value = "";
  try {
    await auth_store.login(login_form.username, login_form.password);
    success_msg.value = t("success_login");
    setTimeout(() => router.push("/"), 500);
  } catch (err: any) {
    error_msg.value = err.response?.data?.error || t("err_login_fail");
  } finally {
    loading.value = false;
  }
};

const on_register = async () => {
  if (!reg_form.username || !reg_form.password) {
    error_msg.value = t("err_required");
    return;
  }
  if (reg_form.password.length < 8) {
    error_msg.value = t("err_min_pass");
    return;
  }
  if (reg_form.password !== reg_form.confirm) {
    error_msg.value = t("err_confirm");
    return;
  }
  if (!agree_terms.value) {
    error_msg.value = t("err_terms");
    return;
  }
  loading.value = true;
  error_msg.value = "";
  success_msg.value = "";
  try {
    await auth_store.register(reg_form.username, reg_form.password);
    success_msg.value = t("success_register");
    setTimeout(() => router.push("/"), 500);
  } catch (err: any) {
    error_msg.value = err.response?.data?.error || t("err_register_fail");
  } finally {
    loading.value = false;
  }
};

// Auto-detect tab from route
onMounted(() => {
  if (route.path === "/register") {
    active_tab.value = "register";
  }
});
</script>

<style scoped>
/* ═══════════════════════════════════════════════
   CSS VARIABLES — MaxHub Brand Palette
   ═══════════════════════════════════════════════ */
.auth-page {
  --bg-deep: #060B18;
  --bg-panel: #0A1128;
  --bg-input: #0B1226;
  --border-subtle: rgba(255,255,255,0.04);
  --border-input: rgba(255,255,255,0.08);
  --border-focus: #00BCD4;
  --cyan: #00BCD4;
  --cyan-bright: #00E5FF;
  --cyan-glow: rgba(0,188,212,0.15);
  --blue: #1565C0;
  --blue-light: #29B6F6;
  --blue-glow: rgba(21,101,192,0.12);
  --orange: #F57C00;
  --orange-glow: rgba(245,124,0,0.15);
  --text-primary: #EDF1F9;
  --text-secondary: #94A3BE;
  --text-muted: #5A6E8A;
  --text-bright: #FFFFFF;
  --error: #F87171;
  --success: #4ADE80;
  --radius-sm: 8px;
  --radius-md: 12px;

  min-height: 100vh;
  display: flex;
  background: var(--bg-deep);
  color: var(--text-primary);
  font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ═══ Light theme overrides ═══ */
.auth-page.light {
  --bg-deep: #F4F7FB;
  --bg-panel: #FFFFFF;
  --bg-input: #F0F3F8;
  --border-subtle: rgba(0,0,0,0.06);
  --border-input: rgba(0,0,0,0.1);
  --cyan-glow: rgba(0,188,212,0.1);
  --blue-glow: rgba(21,101,192,0.08);
  --orange-glow: rgba(245,124,0,0.1);
  --text-primary: #1A2332;
  --text-secondary: #5A6B82;
  --text-muted: #9BAABE;
  --text-bright: #0C1929;
  --error: #DC2626;
  --success: #16A34A;
}

.auth-page.light .brand-panel {
  background: linear-gradient(160deg, #EAF1FA 0%, #F7FAFF 40%, #FFF8F0 100%);
  border-right: 1px solid rgba(0,0,0,0.06);
}

.auth-page.light .form-panel { background: var(--bg-deep); }

.auth-page.light .input-wrap input {
  background: var(--bg-input);
  border-color: rgba(0,0,0,0.1);
  color: var(--text-primary);
}

.auth-page.light .input-wrap input::placeholder { color: #B0BDCE; }

.auth-page.light .input-wrap input:focus {
  border-color: var(--cyan);
  box-shadow: 0 0 0 3px rgba(0,188,212,0.12);
  background: #fff;
}

.auth-page.light .pill {
  background: rgba(0,0,0,0.03);
  border-color: rgba(0,0,0,0.06);
}

.auth-page.light .theme-toggle,
.auth-page.light .lang-btn {
  border-color: rgba(0,0,0,0.1);
  background: rgba(255,255,255,0.8);
  color: var(--text-secondary);
}

.auth-page.light .orbital-ring { border-color: rgba(0,188,212,0.35); }
.auth-page.light .orbital-ring::before { background: var(--cyan); box-shadow: 0 0 16px var(--cyan), 0 0 30px rgba(0,188,212,0.4); }
.auth-page.light .orbital-ring-2 { border-color: rgba(245,124,0,0.3); }
.auth-page.light .orbital-ring-2::before { background: var(--orange); box-shadow: 0 0 14px var(--orange), 0 0 28px rgba(245,124,0,0.35); }
.auth-page.light .glow-orb-2 { background: radial-gradient(circle, rgba(21,101,192,0.2) 0%, transparent 70%); }
.auth-page.light .glow-orb-orange { background: radial-gradient(circle, rgba(245,124,0,0.2) 0%, transparent 70%); }
.auth-page.light .brand-panel::after { background: radial-gradient(circle, rgba(0,188,212,0.25) 0%, transparent 70%); }

.auth-page.light .tab-switcher {
  background: rgba(0,0,0,0.04);
}

.auth-page.light .tab-btn {
  color: var(--text-secondary);
}

.auth-page.light .tab-btn.active {
  color: var(--text-bright);
}

.auth-page.light .tab-indicator {
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.auth-page.light .social-btn {
  background: rgba(0,0,0,0.03);
  border-color: rgba(0,0,0,0.08);
  color: var(--text-primary);
}

.auth-page.light .social-btn:hover {
  background: rgba(0,0,0,0.06);
  border-color: rgba(0,0,0,0.12);
}

.auth-page.light .overlay-content {
  background: #fff;
  border-color: rgba(0,0,0,0.1);
}

/* ═══ Layout ═══ */
.auth-container {
  display: flex;
  width: 100%;
  min-height: 100vh;
}

/* ═══ Language Selector ═══ */
.lang-selector {
  position: fixed;
  top: 24px;
  right: 80px;
  z-index: 999;
  display: flex;
  gap: 6px;
}

.lang-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(12px);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all 0.3s;
}

.lang-btn:hover,
.lang-btn.active {
  border-color: var(--cyan);
  background: rgba(0,188,212,0.1);
}

.lang-flag {
  width: 20px;
  height: 14px;
  border-radius: 2px;
}

/* ═══ Brand Panel (Left) ═══ */
.brand-panel {
  flex: 0 0 45%;
  background: var(--bg-panel);
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 60px;
  overflow: hidden;
}

.brand-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 45%, black 30%, transparent 100%);
}

.brand-panel::after {
  content: '';
  position: absolute;
  top: 15%;
  left: 20%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, var(--cyan-glow) 0%, transparent 70%);
  animation: float-glow 8s ease-in-out infinite;
  pointer-events: none;
}

@keyframes float-glow {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.6; }
  50% { transform: translate(40px, -30px) scale(1.2); opacity: 1; }
}

.glow-orb-2 {
  position: absolute;
  bottom: 20%;
  right: 15%;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, var(--blue-glow) 0%, transparent 70%);
  animation: float-glow-2 10s ease-in-out infinite;
  pointer-events: none;
}

@keyframes float-glow-2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-30px, 20px) scale(1.15); }
}

.glow-orb-orange {
  position: absolute;
  top: 55%;
  left: 60%;
  width: 120px;
  height: 120px;
  background: radial-gradient(circle, var(--orange-glow) 0%, transparent 70%);
  animation: float-glow-3 12s ease-in-out infinite;
  pointer-events: none;
}

@keyframes float-glow-3 {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(20px, -40px); }
  66% { transform: translate(-15px, 15px); }
}

.orbital-ring {
  position: absolute;
  width: 500px;
  height: 500px;
  border: 1px solid rgba(0,188,212,0.12);
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: spin-slow 60s linear infinite;
}

.orbital-ring::before {
  content: '';
  position: absolute;
  width: 8px;
  height: 8px;
  background: var(--cyan);
  border-radius: 50%;
  top: -4px;
  left: 50%;
  margin-left: -4px;
  box-shadow: 0 0 16px var(--cyan), 0 0 30px rgba(0,188,212,0.3);
}

.orbital-ring-2 {
  position: absolute;
  width: 380px;
  height: 380px;
  border: 1px solid rgba(245,124,0,0.1);
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: spin-slow 45s linear infinite reverse;
}

.orbital-ring-2::before {
  content: '';
  position: absolute;
  width: 6px;
  height: 6px;
  background: var(--orange);
  border-radius: 50%;
  bottom: -3px;
  left: 50%;
  margin-left: -3px;
  box-shadow: 0 0 14px var(--orange), 0 0 24px rgba(245,124,0,0.25);
}

@keyframes spin-slow {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to { transform: translate(-50%, -50%) rotate(360deg); }
}

.brand-logo {
  position: relative;
  z-index: 2;
  margin-bottom: 40px;
}

.brand-logo img {
  width: 280px;
  height: auto;
  filter: brightness(1.3) drop-shadow(0 4px 24px rgba(0,188,212,0.35));
}

.auth-page.light .brand-logo img {
  filter: drop-shadow(0 4px 20px rgba(0,0,0,0.1));
}

.brand-tagline {
  position: relative;
  z-index: 2;
  text-align: center;
  max-width: 340px;
}

.brand-tagline h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-bright);
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.brand-tagline p {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.7;
  margin: 0;
  opacity: 0.85;
}

.auth-page.light .brand-tagline h2 {
  color: #1A2332;
}

.auth-page.light .brand-tagline p {
  color: #5A6B82;
  opacity: 1;
}

.feature-pills {
  display: flex;
  gap: 10px;
  margin-top: 36px;
  position: relative;
  z-index: 2;
  flex-wrap: wrap;
  justify-content: center;
}

.download-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 28px;
  padding: 12px 28px;
  background: linear-gradient(135deg, var(--cyan), var(--orange));
  border: none;
  border-radius: 100px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  text-decoration: none;
  cursor: pointer;
  position: relative;
  z-index: 2;
  transition: transform 0.2s, box-shadow 0.2s;
}

.download-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 255, 255, 0.3);
}

.pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 100px;
  font-size: 12px;
  color: var(--text-primary);
  transition: all 0.3s;
}

.pill:hover {
  border-color: var(--cyan);
  color: var(--cyan);
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.dot.cyan { background: var(--cyan); box-shadow: 0 0 8px var(--cyan-glow); }
.dot.blue { background: var(--blue-light); box-shadow: 0 0 8px var(--blue-glow); }
.dot.orange { background: var(--orange); box-shadow: 0 0 8px var(--orange-glow); }

/* ═══ Form Panel (Right) ═══ */
.form-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px;
  position: relative;
  background: var(--bg-deep);
  overflow-y: auto;
}

.form-grid-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.012) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.012) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 50%, black 20%, transparent 90%);
  pointer-events: none;
}

.form-wrapper {
  width: 100%;
  max-width: 460px;
  position: relative;
  z-index: 2;
  background: var(--bg-panel);
  border: 1px solid var(--border-subtle);
  padding: 36px 32px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.3), 0 0 80px rgba(0,188,212,0.06);
}

.auth-page.light .form-wrapper {
  box-shadow: 0 8px 40px rgba(0,0,0,0.08), 0 2px 12px rgba(0,0,0,0.04);
  border-color: rgba(0,0,0,0.08);
}

/* ═══ Tab Switcher ═══ */
.tab-switcher {
  display: flex;
  position: relative;
  background: rgba(255,255,255,0.04);
  border-radius: 0;
  padding: 4px;
  margin-bottom: 24px;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  border: none;
  background: none;
  color: var(--text-muted);
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  position: relative;
  z-index: 2;
  transition: color 0.3s;
}

.tab-btn.active {
  color: var(--text-bright);
}

.tab-indicator {
  position: absolute;
  top: 4px;
  left: 4px;
  width: calc(50% - 4px);
  height: calc(100% - 8px);
  background: rgba(0,188,212,0.12);
  border: 1px solid rgba(0,188,212,0.2);
  border-radius: 0;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab-indicator.right {
  transform: translateX(100%);
}

/* ═══ Form ═══ */
.form-header {
  margin-bottom: 20px;
}

.form-header h1 {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-bright);
  margin: 0 0 4px 0;
  letter-spacing: -0.5px;
}

.form-header p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.input-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 5px;
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.input-wrap .icon {
  position: absolute;
  left: 12px;
  color: var(--text-muted);
  font-size: 16px;
  pointer-events: none;
  display: flex;
  transition: color 0.3s;
}

.input-wrap .icon svg {
  width: 16px;
  height: 16px;
  stroke: currentColor;
  fill: none;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.input-wrap input {
  width: 100%;
  height: 42px;
  padding: 0 14px 0 40px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: 0;
  color: var(--text-primary);
  font-family: inherit;
  font-size: 13px;
  outline: none;
  transition: all 0.25s;
}

.input-wrap input::placeholder { color: var(--text-muted); }

.input-wrap input:focus {
  border-color: var(--cyan);
  box-shadow: 0 0 0 3px var(--cyan-glow);
}

.input-wrap:focus-within .icon { color: var(--cyan); }

.pass-toggle {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  display: flex;
  transition: color 0.2s;
}

.pass-toggle:hover { color: var(--cyan); }

.pass-toggle svg {
  width: 18px;
  height: 18px;
  stroke: currentColor;
  fill: none;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* ═══ Password Strength Meter ═══ */
.strength-meter {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}

.strength-bars {
  display: flex;
  gap: 4px;
  flex: 1;
}

.strength-bar {
  height: 4px;
  flex: 1;
  background: var(--border-input);
  border-radius: 2px;
  transition: background 0.3s;
}

.strength-bar.weak { background: #F87171; }
.strength-bar.fair { background: #FBBF24; }
.strength-bar.good { background: #34D399; }
.strength-bar.strong { background: #4ADE80; }

.strength-label {
  font-size: 11px;
  font-weight: 600;
  min-width: 60px;
  text-align: right;
}

.strength-1 { color: #F87171; }
.strength-2 { color: #FBBF24; }
.strength-3 { color: #34D399; }
.strength-4 { color: #4ADE80; }

/* ═══ Form Row ═══ */
.form-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-secondary);
  user-select: none;
  line-height: 1.4;
}

.checkbox-label a {
  color: var(--cyan);
  text-decoration: none;
}

.checkbox-label a:hover {
  text-decoration: underline;
}

.checkbox-label input[type="checkbox"] {
  appearance: none;
  width: 16px;
  height: 16px;
  min-width: 16px;
  border: 1.5px solid var(--border-input);
  border-radius: 4px;
  background: var(--bg-input);
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
  margin-top: 1px;
}

.checkbox-label input[type="checkbox"]:checked {
  background: var(--cyan);
  border-color: var(--cyan);
}

.checkbox-label input[type="checkbox"]:checked::after {
  content: '';
  position: absolute;
  left: 4px;
  top: 1px;
  width: 5px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

/* ═══ Status Messages ═══ */
.status-msg {
  padding: 8px 12px;
  border-radius: 0;
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-msg.error {
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.2);
  color: var(--error);
}

.status-msg.success {
  background: rgba(74,222,128,0.08);
  border: 1px solid rgba(74,222,128,0.2);
  color: var(--success);
}

/* ═══ Buttons ═══ */
.btn-row {
  display: flex;
  gap: 10px;
}

.btn-primary {
  flex: 1;
  height: 42px;
  border: none;
  border-radius: 0;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  color: white;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, var(--cyan) 0%, var(--blue) 50%, var(--orange) 100%);
  background-size: 200% 200%;
  animation: gradient-shift 4s ease infinite;
  transition: transform 0.15s, box-shadow 0.3s;
  letter-spacing: 0.5px;
}

@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 30px rgba(0,188,212,0.25);
}

.btn-primary:active {
  transform: translateY(0) scale(0.99);
}

.btn-primary::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 50%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
  transition: left 0.5s;
}

.btn-primary:hover::after { left: 100%; }

.btn-primary.loading {
  pointer-events: none;
  opacity: 0.8;
}

.btn-primary.loading .btn-text { visibility: hidden; }

.btn-primary.loading::before {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-cancel {
  flex: 1;
  height: 42px;
  border: 1px solid rgba(248,113,113,0.3);
  border-radius: 0;
  background: transparent;
  color: var(--error);
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s;
}

.btn-cancel:hover {
  background: rgba(248,113,113,0.1);
  border-color: var(--error);
}

/* ═══ Social Login ═══ */
.social-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 4px 0;
}

.social-divider::before,
.social-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-input);
}

.social-divider span {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}

.social-buttons {
  display: flex;
  gap: 10px;
}

.social-btn {
  flex: 1;
  height: 40px;
  border: 1px solid var(--border-input);
  border-radius: 0;
  background: rgba(255,255,255,0.03);
  color: var(--text-secondary);
  font-family: inherit;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.25s;
}

.social-btn:hover {
  background: rgba(255,255,255,0.06);
  border-color: var(--cyan);
  color: var(--text-primary);
}

.social-btn svg {
  width: 18px;
  height: 18px;
}

/* ═══ Theme Toggle ═══ */
.theme-toggle {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 999;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(12px);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.35s;
  color: var(--text-secondary);
}

.theme-toggle:hover {
  border-color: var(--cyan);
  background: rgba(0,188,212,0.1);
  color: var(--cyan);
}

.theme-toggle svg {
  width: 16px;
  height: 16px;
  stroke: currentColor;
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* ═══ Overlay Pages (Terms / Privacy) ═══ */
.overlay-page {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.overlay-content {
  width: 100%;
  max-width: 600px;
  max-height: 80vh;
  background: var(--bg-panel);
  border: 1px solid var(--border-subtle);
  border-radius: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.overlay-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-subtle);
}

.overlay-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-bright);
}

.overlay-close {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255,255,255,0.05);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  transition: all 0.2s;
}

.overlay-close:hover {
  background: rgba(248,113,113,0.1);
  color: var(--error);
}

.overlay-close svg {
  width: 16px;
  height: 16px;
  stroke: currentColor;
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
}

.overlay-body {
  padding: 24px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.overlay-body h3 {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 20px 0 8px 0;
}

.overlay-body h3:first-child {
  margin-top: 0;
}

.overlay-body p {
  margin: 0 0 12px 0;
}

/* ═══ Overlay Transitions ═══ */
.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.25s;
}

.overlay-fade-enter-active .overlay-content,
.overlay-fade-leave-active .overlay-content {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

.overlay-fade-enter-from .overlay-content {
  transform: scale(0.95) translateY(10px);
}

.overlay-fade-leave-to .overlay-content {
  transform: scale(0.95) translateY(10px);
}
</style>
