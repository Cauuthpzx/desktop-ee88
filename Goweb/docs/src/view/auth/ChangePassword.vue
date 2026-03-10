<template>
  <lay-config-provider :theme="appStore.theme" :themeVariable="appStore.themeVariable">
    <div class="auth-page">
      <div class="auth-box">
        <div class="auth-left">
          <div class="auth-brand">
            <lay-icon type="layui-icon-app" size="42px" color="#fff" />
            <h1>MaxHub</h1>
          </div>
          <p class="auth-tagline">Bảo mật tài khoản<br/>Thay đổi mật khẩu định kỳ</p>
          <div class="auth-decoration">
            <lay-icon type="layui-icon-password" size="120px" color="rgba(255,255,255,0.08)" />
          </div>
        </div>
        <div class="auth-right">
          <div class="auth-form-wrapper">
            <h2>Đổi mật khẩu</h2>
            <p class="auth-sub">Nhập mật khẩu cũ và mật khẩu mới</p>
            <lay-form :model="form" :pane="true">
              <lay-form-item prop="old_password">
                <lay-input
                  v-model="form.old_password"
                  type="password"
                  placeholder="Mật khẩu cũ"
                  prefix-icon="layui-icon-password"
                  password
                />
              </lay-form-item>
              <lay-form-item prop="new_password">
                <lay-input
                  v-model="form.new_password"
                  type="password"
                  placeholder="Mật khẩu mới (tối thiểu 8 ký tự)"
                  prefix-icon="layui-icon-password"
                  password
                />
              </lay-form-item>
              <lay-form-item prop="confirm">
                <lay-input
                  v-model="form.confirm"
                  type="password"
                  placeholder="Xác nhận mật khẩu mới"
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
              <lay-form-item v-if="success_msg">
                <div class="auth-success">
                  <lay-icon type="layui-icon-ok-circle" size="14px" color="#16b777" />
                  <span>{{ success_msg }}</span>
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
                    Đổi mật khẩu
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
              <router-link to="/">Quay về trang chính</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </lay-config-provider>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { useAuthStore } from "../../store/auth";
import { useAppStore } from "../../store/app";

const auth_store = useAuthStore();
const appStore = useAppStore();
const loading = ref(false);
const error_msg = ref("");
const success_msg = ref("");

const form = reactive({
  old_password: "",
  new_password: "",
  confirm: "",
});

const on_cancel = () => {
  form.old_password = "";
  form.new_password = "";
  form.confirm = "";
  error_msg.value = "";
  success_msg.value = "";
  window.history.back();
};

const on_submit = async () => {
  error_msg.value = "";
  success_msg.value = "";

  if (!form.old_password || !form.new_password) {
    error_msg.value = "Vui lòng nhập đầy đủ thông tin";
    return;
  }
  if (form.new_password.length < 8) {
    error_msg.value = "Mật khẩu mới phải có tối thiểu 8 ký tự";
    return;
  }
  if (form.new_password !== form.confirm) {
    error_msg.value = "Mật khẩu xác nhận không khớp";
    return;
  }
  if (form.old_password === form.new_password) {
    error_msg.value = "Mật khẩu mới phải khác mật khẩu cũ";
    return;
  }
  loading.value = true;
  try {
    await auth_store.change_password(form.old_password, form.new_password);
    success_msg.value = "Đổi mật khẩu thành công!";
    form.old_password = "";
    form.new_password = "";
    form.confirm = "";
  } catch (err: any) {
    error_msg.value =
      err.response?.data?.error || "Đổi mật khẩu thất bại";
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

.auth-success {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #16b777;
  font-size: 13px;
  padding: 8px 12px;
  background: #f0fff4;
  border: 1px solid #c6f6d5;
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
