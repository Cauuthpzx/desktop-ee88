<template>
  <lay-config-provider :theme="appStore.theme" :themeVariable="appStore.themeVariable">
    <div class="auth-page">
      <div class="auth-box">
        <div class="auth-left">
          <div class="auth-brand">
            <lay-icon type="layui-icon-app" size="42px" color="#fff" />
            <h1>MaxHub</h1>
          </div>
          <p class="auth-tagline">Tạo tài khoản mới<br/>Bắt đầu hành trình của bạn</p>
          <div class="auth-decoration">
            <lay-icon type="layui-icon-add-circle" size="120px" color="rgba(255,255,255,0.08)" />
          </div>
        </div>
        <div class="auth-right">
          <div class="auth-form-wrapper">
            <h2>Đăng ký</h2>
            <p class="auth-sub">Điền thông tin để tạo tài khoản</p>
            <lay-form :model="form" :pane="true">
              <lay-form-item prop="username">
                <lay-input
                  v-model="form.username"
                  placeholder="Tài khoản"
                  prefix-icon="layui-icon-username"
                  :allow-clear="true"
                />
              </lay-form-item>
              <lay-form-item prop="password">
                <lay-input
                  v-model="form.password"
                  type="password"
                  placeholder="Mật khẩu (tối thiểu 8 ký tự)"
                  prefix-icon="layui-icon-password"
                  password
                />
              </lay-form-item>
              <lay-form-item prop="confirm">
                <lay-input
                  v-model="form.confirm"
                  type="password"
                  placeholder="Xác nhận mật khẩu"
                  prefix-icon="layui-icon-password"
                  password
                  @keyup.enter="on_submit"
                />
              </lay-form-item>
              <lay-form-item v-if="error_msg">
                <div class="auth-error">
                  <lay-icon type="layui-icon-close-fill" size="14px" color="#ff5722" />
                  <span>{{ error_msg }}</span>
                </div>
              </lay-form-item>
              <lay-form-item>
                <div class="auth-btn-row">
                  <lay-button
                    type="primary"
                    :loading="loading"
                    size="lg"
                    @click="on_submit"
                  >
                    Đăng ký
                  </lay-button>
                  <lay-button
                    type="danger"
                    size="lg"
                    @click="on_cancel"
                  >
                    Huỷ
                  </lay-button>
                </div>
              </lay-form-item>
            </lay-form>
            <div class="auth-footer">
              <span>Đã có tài khoản?</span>
              <router-link to="/login">Đăng nhập</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </lay-config-provider>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../../store/auth";
import { useAppStore } from "../../store/app";

const router = useRouter();
const auth_store = useAuthStore();
const appStore = useAppStore();
const loading = ref(false);
const error_msg = ref("");

const form = reactive({
  username: "",
  password: "",
  confirm: "",
});

const on_cancel = () => {
  form.username = "";
  form.password = "";
  form.confirm = "";
  error_msg.value = "";
  router.push("/login");
};

const on_submit = async () => {
  if (!form.username || !form.password) {
    error_msg.value = "Vui lòng nhập đầy đủ thông tin";
    return;
  }
  if (form.password.length < 8) {
    error_msg.value = "Mật khẩu phải có tối thiểu 8 ký tự";
    return;
  }
  if (form.password !== form.confirm) {
    error_msg.value = "Mật khẩu xác nhận không khớp";
    return;
  }
  loading.value = true;
  error_msg.value = "";
  try {
    await auth_store.register(form.username, form.password);
    router.push("/");
  } catch (err: any) {
    error_msg.value = err.response?.data?.error || "Đăng ký thất bại";
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
}

.auth-box {
  display: flex;
  width: 820px;
  min-height: 520px;
  background: #fff;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.auth-left {
  width: 340px;
  background: linear-gradient(160deg, #16baaa 0%, #0d8a7e 50%, #065f56 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 48px 32px;
  position: relative;
  overflow: hidden;
}

.auth-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.auth-brand h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 2px;
}

.auth-tagline {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  text-align: center;
  line-height: 1.6;
  margin: 0;
}

.auth-decoration {
  position: absolute;
  bottom: -20px;
  right: -20px;
  opacity: 0.5;
}

.auth-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

.auth-form-wrapper {
  width: 100%;
  max-width: 360px;
}

.auth-form-wrapper h2 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 700;
  color: #333;
}

.auth-sub {
  margin: 0 0 24px 0;
  color: #999;
  font-size: 13px;
}

.auth-error {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #ff5722;
  font-size: 13px;
  padding: 8px 12px;
  background: #fff5f5;
  border: 1px solid #ffe0e0;
}

.auth-btn-row {
  display: flex;
  gap: 10px;
  width: 100%;
}

.auth-btn-row .layui-btn {
  flex: 1;
}

.auth-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: #999;
}

.auth-footer a {
  color: #16baaa;
  margin-left: 4px;
  text-decoration: none;
  font-weight: 500;
}

.auth-footer a:hover {
  text-decoration: underline;
}
</style>
