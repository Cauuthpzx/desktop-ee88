<template>
  <div class="customers-container">
    <div class="customers-header">
      <h2>{{ t("nav.customers") }}</h2>
    </div>
    <div class="customers-body">
      <lay-empty></lay-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "layui-component/index";

const { t } = useI18n();
</script>

<style scoped>
.customers-container {
  margin-top: 60px;
  min-height: calc(100vh - 60px);
  padding: 24px 40px;
}

.customers-header {
  margin-bottom: 20px;
}

.customers-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.customers-body {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}
</style>
